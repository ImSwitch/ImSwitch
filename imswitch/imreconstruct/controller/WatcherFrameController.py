# type: ignore

from .basecontrollers import ImRecWidgetController

from imswitch.imcommon.view.guitools.FileWatcher import FileWatcher
from imswitch.imreconstruct.controller.karl_workers.ZarrInitWorker import ZarrInitWorker
from imswitch.imreconstruct.controller.karl_workers.ZarrStreamWorker import ZarrStreamWorker

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

import os
from os.path import isdir, join

import json
import tifffile as tiff
import h5py
import zarr
from ome_zarr.io import parse_url
from ome_zarr.writer import write_image

import numpy as np
from time import perf_counter
from qtpy import QtCore




class WatcherFrameController(ImRecWidgetController):

    """ Linked to WatcherFrame. """

    sigRunInitSequence = QtCore.Signal(str)
    sigTriggerRun = QtCore.Signal(str)
    sigTriggerZarrStream = QtCore.Signal(str)

    sigRunDirectory = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._widget.sigWatchChanged.connect(self.toggle_watch)

        self._logger = initLogger(self, tryInheritParent=False)

        self.root_path = None

        self.processed_directories = []

        self.file_watcher = None


#     def sort_zarr_files(self, zarrFileList):
#         zarrFileList.sort(key=lambda x : int(x.split("__")[1]))

    def toggle_watch(self, checked):
        self.root_path = self._widget.folderEdit.text()
        if checked and not isdir(self.root_path):
            self._logger.error("[toggle_watch] >> Select a valid folder")
            self.uncheck_button()
        elif checked:
            self.start_file_watcher()
        else:
            self.stop_all_watchers()


    def uncheck_button(self):
        button = self._widget.liveModeCheck
        button.blockSignals(True)
        button.setChecked(False)
        button.blockSignals(False)


    def start_file_watcher(self):
        self.file_watcher = FileWatcher(self.root_path)
        self.file_watcher.sigFinishedDirectory.connect(self.new_files)
        self.file_watcher.start()

    # temporary test method
    @QtCore.Slot(list)
    def new_files(self, files):
        print(f"files = {files}")

    def runZarrInitWorker(self):
        self.zarrInitWorker = ZarrInitWorker()
        self.sigRunInitSequence.connect(self.zarrInitWorker.runInitSequence)
        self.zarrInitWorker.initComplete.connect(self.runZarrStreamWorker)
        self.zarrInitWorker.start()


    def stopZarrInitWorker(self):
        if hasattr(self, 'zarrInitWorker') and self.zarrInitWorker.isRunning():
            self.zarrInitWorker.quit()
            self.zarrInitWorker.terminate()
            self.zarrInitWorker.wait()


    @QtCore.Slot(object)
    def runZarrStreamWorker(self, streamArgs: object):
        self.stopZarrInitWorker()

        self.numFramesInStack = streamArgs.numFramesInStack

        self.rawData = np.zeros((
            streamArgs.numFramesInStack,
            streamArgs.dataBuffRows,
            streamArgs.dataBuffCols
        ))

        self._commChannel.sigSetupLiveStream.emit(
            streamArgs.processor,
            self.rawData,
            [streamArgs.reconRows, streamArgs.reconCols, streamArgs.numTimepoints]
        )

        self.zarrStreamWorker = ZarrStreamWorker(
            numFramesInStack=streamArgs.numFramesInStack,
            rawData=self.rawData, # shared data buffer with ProcessorWorker
            _commChannel=self._commChannel
        )

        self.zarrStreamWorkerThread = QtCore.QThread()
        self.zarrStreamWorker.moveToThread(self.zarrStreamWorkerThread)

        self.sigTriggerZarrStream.connect(self.zarrStreamWorker.run)
        self.zarrStreamWorker.sigZarrFileFinished.connect(self.zarrStreamFinished)
        self.zarrStreamWorkerThread.start()

        self.runInitSequence = False

        self.execution = False

        self.runNextFile()


    @QtCore.Slot(list)
    def newFiles(self, files):
        newZarrFiles = [f for f in files if f.endswith(".zarr")]

        if not newZarrFiles:
            return

        self.sortZarrFileList(newZarrFiles)

        for zarrFile in newZarrFiles:
            if zarrFile not in self.toExecute:
                self.toExecute.append(zarrFile)

        if not self.execution:
            self.runNextFile()


    def runNextFile(self):
        if self.execution and self.zarrFileToProcess:
            self._logger.debug(f"[runNextFile] >> Zarr Streamer is currently working on {self.zarrFileToProcess}")
            return

        if not self.toExecute:
            self._logger.debug("[runNextFile] >> No files to process")
            return

        self.execution = True

        if self.runInitSequence:
            self.zarrFileToProcess = self.toExecute[0]
            self.sigRunInitSequence.emit(self.zarrFileToProcess)
        else:
            self.zarrFileToProcess = self.toExecute.pop(0)
            self.sigTriggerZarrStream.emit(self.zarrFileToProcess)


    def zarrStreamFinished(self):
        self._logger.debug(f"[zarrStreamFinished] Processed: {self.zarrFileToProcess}")
        self.execution = False
        self.runNextFile()


    def stop_all_watchers(self):
        if self.directory_watcher is not None:
            self.directory_watcher.stop()
            self.directory_watcher.quit()
            self.directory_watcher.terminate()
            self.directory_watcher.wait()

        if self.file_watcher is not None:
            self.file_watcher.stop()
            self.file_watcher.quit()
            self.file_watcher.wait()

        self.directory_index = 0


    def _stop_all_watchers(self):
        self._commChannel.sigStopLiveStream.emit()
        self._commChannel.blockSignals(True)

        if self.zarrInitWorker is not None:
            self.zarrInitWorker.quit()
            self.zarrInitWorker.terminate()
            self.zarrInitWorker.wait()

        if self.fileWatcher is not None:
            self.fileWatcher.stop()
            self.fileWatcher.quit()
            self.fileWatcher.terminate()
            self.fileWatcher.wait()

        if self.zarrStreamWorkerThread is not None:
            self.zarrStreamWorker.stop()
            self.zarrStreamWorkerThread.quit()
            self.zarrStreamWorkerThread.terminate()
            self.zarrStreamWorkerThread.wait()

        self._commChannel.blockSignals(False)
        self.execution = False
        self.toExecute = []

        self._logger.debug(f"[stop_all_watchers] >> fileWatcher and ZarrStreamWorker threads have been cleared")


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