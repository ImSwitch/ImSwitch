# type: ignore

from .basecontrollers import ImRecWidgetController

from imswitch.imcommon.view.guitools.FileWatcher import FileWatcher

from imswitch.imreconstruct.controller.karl_workers.ZarrInitWorker import ZarrInitWorker
from imswitch.imreconstruct.controller.karl_workers.ZarrStreamWorker import ZarrStreamWorker

from typing import NewType, List
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

    """ Linked to WatcherFrame. """

    sigStartMonitoring = QtCore.Signal()
    sigRunInitWorker = QtCore.Signal()
    
    sigRunInitSequence = QtCore.Signal(str)
    sigTriggerRun = QtCore.Signal(str)
    sigRunZarrStream = QtCore.Signal(str)
    sigRunDirectory = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.sigWatchChanged.connect(self.toggle_watch)
        self._logger = initLogger(self, tryInheritParent=False)
        self.root_path = None
        self.file_watcher = None
        self.file_watcher_done = False
        self.file_queue = []
        self.run_init = True
        self.zarr_init_worker = None 
        self.zarr_stream_worker = None
        self.zarr_stream_thread = None

    def toggle_watch(self, checked: bool):
        self.root_path = self._widget.folderEdit.text()
        if checked and not isdir(self.root_path):
            self._logger.error("[toggle_watch] >> Select a valid folder")
            self.uncheck_button()
        elif checked:
            self.start_file_watcher()
        else:
            self.stop_all_workers()

    def uncheck_button(self):
        button = self._widget.liveModeCheck
        button.blockSignals(True)
        button.setChecked(False)
        button.blockSignals(False)

    def start_file_watcher(self):
        self.file_watcher = FileWatcher(self.root_path)
        self.file_watcher_thread = QtCore.QThread()  
        self.file_watcher.moveToThread(self.file_watcher_thread)
        self.file_watcher.sigSendFiles.connect(self.extend_file_queue)  
        self.sigStartMonitoring.connect(self.file_watcher.start_monitoring) 
        self.file_watcher_thread.start()
        self.sigStartMonitoring.emit() 
        # self.file_watcher.sigFinishedDirectory.connect(self.set_file_watcher_state) 
    
    def stop_file_watcher_thread(self):
        if self.file_watcher_thread != None:
            self.file_watcher.stop() 
            self.file_watcher_thread.quit()
            self.file_watcher_thread.wait()
            self.file_watcher = None

    def set_file_watcher_state():
        self.file_watcher_done = True

    @QtCore.Slot(list)
    def extend_file_queue(self, files: List[str]): 
        self.file_queue.extend(files)
        self.run_files()

    def run_files(self):
        if self.run_init:  
            init_file = self.file_queue[0] 
            self.start_zarr_init_worker(init_file)
            self.run_init = False 
        elif self.zarr_stream_worker != None and self.file_queue:
            file = self.file_queue.pop(0)
            self.sigRunZarrStream.emit(file)

    def start_zarr_init_worker(self, init_file: str):
        self.zarr_init_worker = ZarrInitWorker(init_file)
        self.zarr_init_thread = QtCore.QThread() 
        self.zarr_init_worker.moveToThread(self.zarr_init_thread)  
        self.sigRunInitWorker.connect(self.zarr_init_worker.run) 
        self.zarr_init_worker.sigInitComplete.connect(self.start_zarr_stream_worker) 
        self.zarr_init_thread.start()
        self.sigRunInitWorker.emit()

    def stop_zarr_init_thread(self):
        if self.zarr_init_thread != None: 
            self.zarr_init_thread.quit()
            self.zarr_init_thread.wait()
            self.zarr_init_worker = None

    @QtCore.Slot(object)
    def start_zarr_stream_worker(self, stream_args: object):
        self._logger.debug("[start_zarr_stream_worker] >> entered") 
        self.stop_zarr_init_thread()
        raw_data = np.zeros((stream_args.num_frames_in_stack, stream_args.raw_data_rows, stream_args.raw_data_rows))
        self.zarr_stream_worker = ZarrStreamWorker(stream_args.num_frames_in_stack, raw_data, self._commChannel) 
        self.zarr_stream_thread = QtCore.QThread() 
        self.zarr_stream_worker.moveToThread(self.zarr_stream_thread)
        self.sigRunZarrStream.connect(self.zarr_stream_worker.run)
        self.zarr_stream_worker.sigZarrFileFinished.connect(self.run_files)  
        self.zarr_stream_thread.start()
        self._commChannel.sigSetupLiveStream.emit(
            stream_args.processor, raw_data, 
            [stream_args.recon_rows, 
             stream_args.recon_cols, 
             stream_args.num_time_points]
        )
        self.run_files()

    def stop_zarr_stream_thread(self):
        if self.zarr_stream_thread != None: 
            self.zarr_stream_worker.stop() 
            self.zarr_stream_thread.quit()
            self.zarr_stream_thread.wait()

    def stop_all_workers(self):
        self._commChannel.sigStopLiveStream.emit()
        self._commChannel.blockSignals(True)
        self.stop_file_watcher_thread()
        self.stop_zarr_init_thread()
        self.stop_zarr_stream_thread()
        self._commChannel.blockSignals(False)
        self.execution = False
        self.toExecute = []
        self._logger.debug(f"[stop_all_watchers] >> file_watcher and ZarrStreamWorker threads have been cleared")


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