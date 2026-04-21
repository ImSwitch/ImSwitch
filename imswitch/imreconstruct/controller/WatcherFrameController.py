# type: ignore

from .basecontrollers import ImRecWidgetController

from imswitch.imcommon.view.guitools.FileWatcher import FileWatcher
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
        """ 
        Helper method that sorts the name of the zarr files in a list based on their scan number.  
        The naming convention of the zarr files is: (time)_rec_scan__(scanNumber)__(detectorName).zarr.
        """
        try: 
            zarrFileList.sort(key=lambda x : int(x.split("__")[1]))
        except Exception as e:
            self._logger.error(f"[sortZarrFileList] >> Could not sort zarrFileList: {e}.")


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
                with open("loc_parms.json", 'r') as f:
                    params = json.load(f)
                self.numFramesInStack = int(params.get("nx_s", 60) * params.get("ny_s", 60))
                numRowsInFrame = params.get("num_rows", 512)
                numColsInFrame = params.get("num_cols", 512)
                self.recImageBuffer = np.zeros((self.numFramesInStack, numRowsInFrame, numColsInFrame), dtype=np.float32)
                self._commChannel.sigSetupLiveStream.emit(params, self.recImageBuffer)
                self._logger.debug(f"[toggleWatch] >> Reconstruction Image Buffer: (numFramesInStack, frameHeight, frameWidth) = {self.recImageBuffer.shape} ready!")
                self.frameCounter = 0
                self.stackCounter = 0
                
                self.toExecute = []
                existingZarrFiles = []
                for file in os.listdir(self._widget.path):
                    if file.endswith(".zarr"): 
                        existingZarrFiles.append(file)
                if existingZarrFiles:
                    self.sortZarrFileList(existingZarrFiles)
                    self.toExecute.extend(existingZarrFiles)
                    self._logger.debug(f"[toggleWatch] >> Found {len(self.toExecute)} Zarr files in: {self._widget.path}")

            except Exception as e:
                self._logger.error(f"[toggleWatch] >> Could not setup Buffer from with loc_parms.json file: {e}")
                return

            self.watcher = FileWatcher(self._widget.path, interval=0.5)
            self.watcher.sigNewFiles.connect(self.newFiles)
            self.watcher.start() 
            self.runNextFile()

        else: 
            self.stopAllWorkers()            


    @QtCore.Slot(list)
    def newFiles(self, files):
        newZarrFiles = []
        for file in files:
            if file.endswith(".zarr"): 
                newZarrFiles.append(file)
        
        if not newZarrFiles:
            return

        self.sortZarrFileList(newZarrFiles)
        for zarrFile in newZarrFiles:
            # avoid duplication
            if zarrFile not in self.toExecute: 
                self.toExecute.append(zarrFile)
        
        self._widget.updateFileList(self.extension) 
        
        if not self.execution:
            self.runNextFile()


    def runNextFile(self):        
        if self.execution:
            self._logger.debug("[runNextFile] >> The filewatcher is busy.")
            return
        
        if not self.toExecute:
            self._logger.debug("[runNextFile] >> There are no files to process.")
            return
    
        self.execution = True
        self.frameCounter = 0 

        self.nextZarrFile = self.toExecute.pop(0)
        self._logger.debug(f"[runNextFile] >> Starting processing: {self.nextZarrFile} => Frames to Process: {self.numFramesInStack}")
        fullPathToFile = os.path.join(self._widget.path, self.nextZarrFile)
        self.startZarrStream(fullPathToFile)


    def startZarrStream(self, zarrFilePath):
        self.zarrStreamWorkerThread = QtCore.QThread()
        self.zarrStreamWorker = ZarrStreamWorker(zarrFilePath, self.numFramesInStack)
        self.zarrStreamWorker.moveToThread(self.zarrStreamWorkerThread) 
        
        self.zarrStreamWorker.sigChunkLoaded.connect(self.onFileLoaded)
        self.zarrStreamWorker.sigFinished.connect(self.onZarrStreamFinished)
        self.zarrStreamWorker.sigFinished.connect(self.zarrStreamWorkerThread.quit) 
        
        self.zarrStreamWorkerThread.finished.connect(self.zarrStreamWorker.deleteLater) 
        self.zarrStreamWorkerThread.finished.connect(self.zarrStreamWorkerThread.deleteLater) 
        
        self.zarrStreamWorkerThread.started.connect(self.zarrStreamWorker.run)
        self.zarrStreamWorkerThread.start()
        

    @QtCore.Slot(np.ndarray, str)                                     
    def onFileLoaded(self, chunk, zarrFileName):
        """ 
        Slot received from ZarrStreamWorker. 
        The chunk variable consists of 3D np array: (numFramesInChunk, numRows, numCols)
        """
        numFramesInChunk = chunk.shape[0]        
        startIndex = self.frameCounter
        endIndex = startIndex + numFramesInChunk

        # TODO: use <<zarrFileName>> for some DEBUG printing

        if endIndex > self.numFramesInStack:
            self._logger.warning("[onFileLoaded] >> Incoming data exceeds stack size => Clipping chunk")
            chunk = chunk[:self.numFramesInStack - startIndex]
            endIndex = self.numFramesInStack

        self.recImageBuffer[startIndex:endIndex, :, :] = chunk
        self.frameCounter += numFramesInChunk
        # self._commChannel.sigLiveChunkReady.emit(chunk, endIndex)
        self._commChannel.sigLiveChunkReady.emit(startIndex, endIndex)

        # if self.frameCounter % (numFramesInChunk * 5) == 0:
        #     percent = (self.frameCounter / self.numFramesInStack) * 100
        #     self._logger.info(f"Streaming {zarrFileName}: {percent:.1f}% complete")


    def onZarrStreamFinished(self):
        if self.frameCounter < self.numFramesInStack - 1 or self.zarrStreamWorker == None:
            self._logger.warning(f"[onZarrStreamFinished] >> Scan Processing interrupted => Frames processed: {self.frameCounter + 1}/{self.numFramesInStack}")
            return
        else:
            self._logger.debug(f"[onZarrStreamFinished] >> Finished processing: {self.nextZarrFile} => Frames processed: {self.frameCounter + 1}/{self.numFramesInStack}")

        
        if hasattr(self, "zarrStreamWorkerThread") and self.zarrStreamWorkerThread.isRunning():
            self.zarrStreamWorkerThread.quit()
            self.zarrStreamWorkerThread.wait()
        
        self.execution = False
        self.frameCounter = 0
        
        self.runNextFile()


    def stopAllWorkers(self):
        if self.zarrStreamWorker and self.zarrStreamWorkerThread:
            try:
                self.zarrStreamWorker.stop()
                self.zarrStreamWorkerThread.quit()
                if not self.zarrStreamWorkerThread.wait(2000):
                    self._logger.warning("[stopAllWorkers] >> Thread timed out during stop => forcing termination")
                    self.zarrStreamWorkerThread.terminate()

            except RuntimeWarning as e:
                self._logger.error(f"[stopAllWorkers] >> Shutdown warning: {e}")

            except Exception as e:
                self._logger.error(f"[stopAllWorkers] >> Error during zarrStreamWorker shutdown: {e}")        

            finally:
                self.zarrStreamWorker = None
                self.zarrStreamWorkerThread = None
        
        if self.watcher: 
            try: 
                self.watcher.stop()
                self.watcher.wait()
            
            except Exception as e:
                self._logger.error(f"[stopAllWorkers] >> Error during file watcher shutdown: {e}")
            
            finally:
                self.watcher = None   

        self.toExecute = []
        self.execution = False 
        
        self._logger.debug("[stopAllWorkers] >> Watcher and Streamers stopped")


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