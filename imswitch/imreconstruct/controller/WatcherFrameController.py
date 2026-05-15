# type: ignore

from .basecontrollers import ImRecWidgetController

from imswitch.imcommon.view.guitools.FileWatcher import FileWatcher
from imswitch.imreconstruct.model.karl_models.localizer import localizer
from imswitch.imreconstruct.controller.karl_workers.ZarrStreamWorker import ZarrStreamWorker

from imswitch.imcommon.model.logging import initLogger

import os
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

    sigTriggerRun = QtCore.Signal(str)
    sigTriggerZarrStream = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs = None
        self.recPath = None
        self._widget.sigWatchChanged.connect(self.toggleWatch)
        self._logger = initLogger(self, tryInheritParent=False)
        try:
            self._widget.sigLiveReconChanged.connect(self.toggleWatch)
        except AttributeError:
            self._logger.debug(f"[__init__] >> Available widget signals: {self._widget.__dict__.keys()}")
        self._widget.sigChangeFolder.connect(lambda: self._widget.updateFileList(self._commChannel.extension.value()))
        self._commChannel.sigExecutionFinished.connect(self.executionFinished)
        self._commChannel.extension.sigValueChanged.connect(self.extensionChanged)
        self.execution = False
        self.toExecute = []
        self.current = None
        self.t0 = None
        self.extension = None
        self.watcher = None
        

    def sortZarrFileList(self, zarrFileList):
        """ Sorts a list with Zarr files (names) based on their scan number in their name """
        try: 
            zarrFileList.sort(key=lambda x : int(x.split("__")[1]))
        except Exception as e:
            self._logger.error(f"[sortZarrFileList] >> Could not sort zarrFileList: {e}")


    def toggleWatch(self, checked):
        self._widget.path = self._widget.folderEdit.text()
        self.extension = self._commChannel.extension.value()

        if checked and (not self._widget.path or not os.path.isdir(self._widget.path)):
            self._logger.error("[toggleWatch] >> Select a valid folder!")
            for button in [self._widget.watchCheck, self._widget.liveModeCheck]:
                button.blockSignals(True)
                button.setChecked(False)
                button.blockSignals(False)
            return
        
        elif checked:
            try:
                # with open("loc_parms.json", 'r') as f:
                #     params = json.load(f)
                # self.numFramesInStack = int(params.get("nx_s", 60) * params.get("ny_s", 60))
                # self.rawDataBuffer = np.zeros((
                #     self.numFramesInStack, 
                #     params.get("num_rows", 512), 
                #     params.get("num_cols", 512)
                # )).astype(np.float32)

                # params["recImage_save_path"] = os.path.join(os.path.dirname(self._widget.path), "Timepoint_Recons")
                # self._commChannel.sigSetupLiveStream.emit(params, self.rawDataBuffer)
                # bufferShape = self.rawDataBuffer.shape
                # self._logger.debug(
                #     f"[toggleWatch] >> Reconstruction Image Buffer initialized: (nFrames, Y, X) = {bufferShape}"
                # )
                
                # self.zarrStreamWorker = ZarrStreamWorker(
                #     numFramesInStack=self.numFramesInStack,
                #     rawDataBuffer=self.rawDataBuffer,
                #     _commChannel=self._commChannel
                # )
                # self.zarrStreamWorkerThread = QtCore.QThread()
                # self.zarrStreamWorker.moveToThread(self.zarrStreamWorkerThread)
                # self.sigTriggerZarrStream.connect(self.zarrStreamWorker.streamZarrFile)
                # self.zarrStreamWorker.sigZarrFileFinished.connect(self.zarrStreamFinished)
                # self.zarrStreamWorkerThread.start()

                self.toExecute = []
                existingZarrFiles = [file for file in os.listdir(self._widget.path) if file.endswith(".zarr")]
                if existingZarrFiles:
                    self.sortZarrFileList(existingZarrFiles)
                    self.toExecute.extend(existingZarrFiles)
                    self._logger.debug(f"[toggleWatch] >> Found {len(self.toExecute)} Zarr files in: {self._widget.path}")
                    
                self.watcher = FileWatcher(self._widget.path, interval=0.1)
                self.watcher.sigNewFiles.connect(self.newFiles)
                self.watcher.start()
            
                self.runBootstrap = True
                self.runNextFile()

            except Exception as e:
                self._logger.error(f"[toggleWatch] >> Error occurred during setup: {e}")
                return
            
        else: 
            self.stopAllWorkers()            



    def bootstrapFileWatcher(self, filePath: str): 
        """
        Performs the necessarry initialization steps required for the live File Watcher:
            1. Localization 
            2. Scanning orientation determination 
            3. Processor creation 
            4. Super resolved image array initialization 
            5. Starting of live File Watching

        NOTE: this should run probably not run on the main thread, since it can cause small freezing  
        """        
        while True:
            try:
                zarrArrayPath = os.path.join(filePath, ".zarray")
                if not os.path.isdir(zarrArrayPath):
                    for entry in os.listdir(filePath):
                        subPath = os.path.join(filePath, entry)
                        self._logger.debug(f"[bootstapFileWatcher] >> subPath = {subPath}")
                        if os.path.isdir(subPath) and os.path.exists(os.path.join(subPath, ".zarray")):
                            zarrArrayPath = subPath
                zarrArray = zarr.open(zarrArrayPath, mode='r')
                zarrArray.store.close()
                numFramesInStack = zarrArray.attrs["numFramesInStack"]
                currNumFrames = zarrArray.shape[0]
                self._logger.debug(f"[bootstrapFileWatcher] >> numFramesInStack = {numFramesInStack}")
                if currNumFrames >= numFramesInStack:
                    break
            except Exception as e:
                self._logger.error(f"[bootstrapFileWatcher] >> Could not open {zarrArrayPath}: {e}")

        imSwitchMetaData = zarrArray.attrs["ImswitchData"]
        x0, y0, z0 = [x for y in imSwitchMetaData["ScanStage:axis_startpos"] for x in y] 
        x1, y1, z1 = imSwitchMetaData["ScanStage:axis_length"]
        dx, dy, dz = imSwitchMetaData["ScanStage:axis_step_size"]
        nx_s = int((x1 - x0) / dx) + 1
        ny_s = int((y1 - y0) / dy) + 1
        bootstrapParms = {}
        data = zarrArray[:]
        locParms = localizer(data)
        for key, value in locParms.items() :
            bootstrapParms[key] = value
        _, bootstrapParms["num_rows"], bootstrapParms["num_cols"] = zarrArray.shape 
        bootstrapParms["nx_s"] = nx_s 
        bootstrapParms["ny_s"] = ny_s
        
        self.numFramesInStack = nx_s * ny_s 
        self.rawDataBuffer = np.zeros((
            self.numFramesInStack,
            bootstrapParms["num_rows"],
            bootstrapParms["num_cols"]
        ))

        self._commChannel.sigSetupLiveStream.emit(bootstrapParms, self.rawDataBuffer)
        self._logger.debug(
            f"[bootstrapFileWatcher] >> Reconstruction Image Buffer initialized: (nFrames, Y, X) = {self.rawDataBuffer.shape}"
        )

        self.zarrStreamWorker = ZarrStreamWorker(
            numFramesInStack=self.numFramesInStack,
            rawDataBuffer=self.rawDataBuffer,
            _commChannel=self._commChannel
        )
        self.zarrStreamWorkerThread = QtCore.QThread()
        self.zarrStreamWorker.moveToThread(self.zarrStreamWorkerThread)
        self.sigTriggerZarrStream.connect(self.zarrStreamWorker.streamZarrFile)
        self.zarrStreamWorker.sigZarrFileFinished.connect(self.zarrStreamFinished)
        self.zarrStreamWorkerThread.start()

        # params["recImage_save_path"] = os.path.join(os.path.dirname(self._widget.path), "Timepoint_Recons")

        self.runBootstrap = False 
        self.runNextFile()



    @QtCore.Slot(list)
    def newFiles(self, files):
        newZarrFiles = [file for file in files if file.endswith(".zarr")]
        if not newZarrFiles:
            return

        self.sortZarrFileList(newZarrFiles)
        for zarrFile in newZarrFiles:
            if zarrFile not in self.toExecute: 
                self.toExecute.append(zarrFile)
        
        self._widget.updateFileList(self.extension) 
        
        if not self.execution:
            self.runNextFile()


    def runNextFile(self):        
        self.zarrFileToProcess = None
        
        if self.execution:
            self._logger.debug(f"[runNextFile] >> Zarr Streamer is currently working on {self.zarrFileToProcess}")
            return
    
        if not self.toExecute:
            self._logger.debug("[runNextFile] >> No files to process")
            return
        
        self.execution = True

        if self.runBootstrap:
            self.zarrFileToProcess = self.toExecute[0]
            zarrfilePath = os.path.join(self._widget.path, self.zarrFileToProcess)
            self._logger.debug(f"[runNextFile] >> Found {zarrfilePath} => running bootstrap")
            self.bootstrapFileWatcher(zarrfilePath)
        else:
            self.zarrFileToProcess = self.toExecute.pop(0)
            zarrfilePath = os.path.join(self._widget.path, self.zarrFileToProcess)
            self._logger.debug(
                f"[runNextFile] >> Streaming: {self.zarrFileToProcess} => Frames to Process: {self.numFramesInStack}"
            )
            self.sigTriggerZarrStream.emit(zarrfilePath)


    def zarrStreamFinished(self):
        self._logger.debug(f"[zarrStreamFinished] Finished processing: {self.zarrFileToProcess}")
        self.execution = False
        self.runNextFile()


    def stopAllWorkers(self):
        """ Shuts down all of the workers and their threads. """        
        self._commChannel.sigStopLiveStream.emit()
        self._commChannel.blockSignals(True)
        
        if self.zarrStreamWorkerThread.isRunning():
            self.zarrStreamWorker.stop()
            self.zarrStreamWorkerThread.quit()
            self.zarrStreamWorkerThread.terminate()
            self.zarrStreamWorkerThread.wait()
    
        if self.watcher: 
            self.watcher.stop()
            self.watcher.quit()
            self.watcher.terminate()
            self.watcher.wait()
        
        self._commChannel.blockSignals(False)
        self.execution = False
        self.toExecute = []
        self._logger.debug(f"[stopAllWorkers] >> All Live Watcher Threads have been shutdown")


    def extensionChanged(self):
        self._widget.updateFileList(self._commChannel.extension.value())
        self._widget.watchCheck.setChecked(False)


    def executionFinished(self, image):
        if self.execution:
            self.execution = False
            self.saveImage(image)
            diff = perf_counter() - self.t0 
            self.watcher.addToLog(self.current, [str(self.t0), str(diff)])
            self._widget.updateFileList(self.extension)
            self.runNextFile()


    def saveImage(self, image):
        image = np.squeeze(image[:, 0, :, :, :, :])
        image = np.reshape(image, (1, *image.shape))
        extension = self._commChannel.extension.value()
        if not os.path.exists(self.recPath): 
            if extension == 'zarr':
                store = parse_url(self.recPath + '.tmp', mode="w").store 
                root = zarr.group(store=store)
                root.attrs["ImSwitchData"] = self.attrs["ImSwitchData"] 
                write_image(image=image, group=root, axes="zyx")
                store.close()
                os.rename(self.recPath + '.tmp', self.recPath) 
                tiff.imwrite(self.recPath.split('.')[0] + ".tiff", image) 
            if extension == 'hdf5':
                h = h5py.File(self.recPath + '.tmp', 'w') 
                dset = h.create_dataset('data', data=image)
                self._logger.debug(type(self.attrs))
                for k in self.attrs.keys(): 
                    dset.attrs[k] = self.attrs[k] 
                h.close()
                os.rename(self.recPath + '.tmp', self.recPath) 
                tiff.imwrite(self.recPath.split('.')[0] + ".tiff", image) 


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