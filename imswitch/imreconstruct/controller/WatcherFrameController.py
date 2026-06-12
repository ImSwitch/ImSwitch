# type: ignore

from .basecontrollers import ImRecWidgetController

from imswitch.imreconstruct.controller.karl_workers.DirectoryWatcher import DirectoryWatcher
from imswitch.imreconstruct.controller.karl_workers.ZarrInitWorker import ZarrInitWorker
from imswitch.imreconstruct.controller.karl_workers.ZarrStreamWorker import ZarrStreamWorker

from imswitch.imcommon.view.guitools.FileWatcher import FileWatcher

from typing import NewType
from imswitch.imreconstruct.model.karl_models.GaussProcessorCPU import GaussProcessorCPU
try:
    import cupy as cp
    from imswitch.imreconstruct.model.karl_models.GaussProcessorGPU import GaussProcessorGPU
    GPU_AVAILABLE = True 
    Processor = NewType("GaussProcessorGPU", GaussProcessorGPU)
except Exception as e:
    print("[WatcherFrameController] [import] >> Could not import GPU GaussProcessor => Defaulting to CPU Gauss Processor")
    GPU_AVAILABLE = False
    Processor = NewType("GaussProcessorCPU", GaussProcessorCPU)

from imswitch.imcommon.model.logging import initLogger

from os.path import isdir

import numpy as np
from qtpy import QtCore


class WatcherFrameController(ImRecWidgetController):
    
    """ Linked to WatcherFrame. Coordinates the state machine on the Main Thread. """

    sigStartDirectoryWatcher = QtCore.Signal()
    sigStartFileWatcher = QtCore.Signal() 
    sigRunInitWorker = QtCore.Signal()
    sigRunZarrStream = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.sigWatchChanged.connect(self.toggle_watch)
        self._logger = initLogger(self, tryInheritParent=False)
        self.root_path = None

        self.directory_watcher = None 
        self.directory_watcher_thread = None
        self.directory_queue = [] 
        self.directory_index = 0
        self.directory_path = None 

        self.file_watcher = None
        self.file_watcher_thread = None 
        self.file_queue = []
        self.file_watcher_busy = False

        self.zarr_init_worker = None 
        self.zarr_init_thread = None
        self.zarr_stream_worker = None
        self.zarr_stream_thread = None

    def toggle_watch(self, checked: bool):
        self.root_path = self._widget.folderEdit.text()
        if checked and not isdir(self.root_path):
            self._logger.error("[toggle_watch] >> Select a valid folder")
            self.uncheck_button()
        elif checked:
            self._logger.debug(f"[toggle_watch] >> Started monitoring: {self.root_path}") 
            self.start_directory_watcher(self.root_path)
        else:
            self.stop_all_workers()
            #self.directory_queue.clear()
            #self.directory_index = 0
            self.file_queue.clear()

    def uncheck_button(self):
        button = self._widget.liveModeCheck
        button.blockSignals(True)
        button.setChecked(False)
        button.blockSignals(False)

    def start_directory_watcher(self, root_path: str):
        self.directory_watcher = DirectoryWatcher(root_path)
        self.directory_watcher_thread = QtCore.QThread()
        self.directory_watcher.moveToThread(self.directory_watcher_thread)
        self.directory_watcher.sigDirectoryFound.connect(self.handle_new_directory)
        self.sigStartDirectoryWatcher.connect(self.directory_watcher.run)
        self.directory_watcher_thread.start()
        self.sigStartDirectoryWatcher.emit() 

    def stop_directory_watcher(self):
        if self.directory_watcher:
            self.directory_watcher.stop()
            self.directory_watcher.deleteLater()
        if self.directory_watcher_thread:
            self.directory_watcher_thread.quit()
            self.directory_watcher_thread.wait()
            self.directory_watcher_thread = None
            self.directory_watcher = None

    @QtCore.Slot(str)
    def handle_new_directory(self, new_dir_path: str):
        if new_dir_path not in self.directory_queue: 
            self.directory_queue.append(new_dir_path)
            self._logger.debug(f"[handle_new_directory] >> Added folder: {new_dir_path}")
            if not self.file_watcher_busy:
                self.set_file_watcher_directory()

    def set_file_watcher_directory(self):
        if not self.file_watcher_busy and self.directory_index < len(self.directory_queue): 
            self.file_watcher_busy = True 
            self.directory_path = self.directory_queue[self.directory_index]
            self.directory_index += 1
            self._logger.debug(f"[set_file_watcher_directory] >> Loading Directory [{self.directory_index}]: {self.directory_path}")
            self.start_file_watcher(self.directory_path)

    def start_file_watcher(self, directory_path: str):
        self.stop_file_watcher()
        self.file_watcher = FileWatcher(directory_path)
        self.file_watcher_thread = QtCore.QThread()  
        self.file_watcher.moveToThread(self.file_watcher_thread)
        self.file_watcher.sigFileFound.connect(self.handle_new_file)
        self.sigStartFileWatcher.connect(self.file_watcher.run)
        self.file_watcher_thread.start()
        self.sigStartFileWatcher.emit()
    
    def stop_file_watcher(self):
        if self.file_watcher:
            try:
                self.file_watcher.sigFileFound.disconnect(self.handle_new_file)
            except TypeError:
                pass
            self.file_watcher.stop() 
            self.file_watcher.deleteLater()
        if self.file_watcher_thread:
            self.file_watcher_thread.quit()
            self.file_watcher_thread.wait()
            self.file_watcher_thread = None
            self.file_watcher = None

    @QtCore.Slot(str)
    def handle_new_file(self, new_file_path: str):
        if new_file_path not in self.file_queue:
            self.file_queue.append(new_file_path)
            self.file_queue.sort()
            # self._logger.debug(f"[handle_new_file] >> Added file to queue: {new_file_path}")
            if self.zarr_init_worker is None and self.zarr_stream_worker is None: 
                self._logger.debug("[handle_new_file] >> Starting INIT")
                self.start_zarr_init_worker(new_file_path)
            elif self.zarr_stream_worker is not None: 
                self._logger.debug("[handle_new_file] >> Starting processing next file")
                self.process_next_stream_file()
            else:
                # zarr_init_worker is currently running! 
                pass 

    def change_directory(self):
        self.stop_file_watcher()
        self.stop_zarr_init_worker()
        self.stop_zarr_stream()
        self.file_queue.clear()
        self.file_watcher_busy = False 
        self.set_file_watcher_directory() 

    @QtCore.Slot()  
    def handle_processing_finished(self):
        if not self.zarr_stream_worker:
            return
        if self.zarr_stream_worker.num_time_points_proc >= self.zarr_stream_worker.num_time_points:
            self._logger.debug("[handle_processing_finished] >> Directory Finished")
            self.change_directory() 
        else:
            self._logger.debug("[handle_processing_finished] >> File Finished")
            self.process_next_stream_file() 
    
    def process_next_stream_file(self):
        if self.file_queue:
            next_file = self.file_queue.pop(0)
            self._logger.debug(f"[process_next_stream_file] >> Streaming: {next_file}")
            self.sigRunZarrStream.emit(next_file)

    def start_zarr_init_worker(self, init_file: str):
        self.stop_zarr_init_worker()
        self.zarr_init_worker = ZarrInitWorker(init_file)
        self.zarr_init_thread = QtCore.QThread() 
        self.zarr_init_worker.moveToThread(self.zarr_init_thread)  
        self.sigRunInitWorker.connect(self.zarr_init_worker.run) 
        self.zarr_init_worker.sigInitComplete.connect(self.start_zarr_stream_worker) 
        self.zarr_init_thread.start()
        self.sigRunInitWorker.emit()

    def stop_zarr_init_worker(self):
        if self.zarr_init_worker:
            self.zarr_init_worker.stop()
            self.zarr_init_worker.deleteLater()
        if self.zarr_init_thread:
            self.zarr_init_thread.quit()
            self.zarr_init_thread.wait()
            self.zarr_init_thread = None
            self.zarr_init_worker = None

    @QtCore.Slot(object)
    def start_zarr_stream_worker(self, stream_args: object):
        self.stop_zarr_init_worker()
        self._logger.debug(f"[start_zarr_stream_worker] >> Starting zarr_stream_worker")
        recon_obj_name = self.directory_path.replace("\\", "/").split("/")[-1]
        raw_data = np.zeros((
            stream_args.num_frames_in_stack, stream_args.raw_data_rows, stream_args.raw_data_cols
        ))
        self.zarr_stream_worker = ZarrStreamWorker(
            stream_args.num_time_points, stream_args.num_frames_in_stack, raw_data, self._commChannel
        ) 
        self.zarr_stream_thread = QtCore.QThread() 
        self.zarr_stream_worker.moveToThread(self.zarr_stream_thread)
        self.sigRunZarrStream.connect(self.zarr_stream_worker.run)
        self.zarr_stream_worker.sigFinishedDirectory.connect(self.change_directory)  
        try:
            self._commChannel.sigProcessingFinished.disconnect(self.handle_processing_finished)
        except TypeError:
            pass
        self._commChannel.sigProcessingFinished.connect(self.handle_processing_finished)     
        self._commChannel.sigSetupLiveStream.emit(
            recon_obj_name, stream_args.processor, raw_data, 
            [stream_args.recon_rows, stream_args.recon_cols, stream_args.num_time_points]
        )
        self.zarr_stream_thread.start()
        self.process_next_stream_file()

    def stop_zarr_stream(self):
        if self.zarr_stream_worker:
            self.zarr_stream_worker.stop() 
            self.zarr_stream_worker.deleteLater()
        if self.zarr_stream_thread:
            self.zarr_stream_thread.quit()
            self.zarr_stream_thread.wait()
            self.zarr_stream_thread = None
            self.zarr_stream_worker = None

    def stop_all_workers(self):
        self._commChannel.sigStopLiveStream.emit()
        try:
            self._commChannel.sigProcessingFinished.disconnect(self.handle_processing_finished)
        except TypeError:
            pass
        self.stop_directory_watcher() 
        self.stop_file_watcher()
        self.stop_zarr_init_worker()
        self.stop_zarr_stream()
        self._logger.debug(f"[stop_all_workers] >> All workers stopped and terminated")


# Copyright (C) 2020-2021 ImSwitch developers
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.