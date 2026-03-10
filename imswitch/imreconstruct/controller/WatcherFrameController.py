# type: ignore

from imswitch.imcommon.view.guitools.FileWatcher import FileWatcher
from imswitch.imreconstruct.model import DataObj
from imswitch.imreconstruct.controller.karl_workers.io_workers import FileLoaderWorker
from imswitch.imcommon.model.logging import initLogger
from .basecontrollers import ImRecWidgetController


import os
import json
import zarr
from ome_zarr.io import parse_url
from ome_zarr.writer import write_image
import tifffile as tiff
import h5py

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
            self._logger.debug(f"DEBUG: Available widget signals: {self._widget.__dict__.keys()}")
     
        self._widget.sigChangeFolder.connect(lambda: self._widget.updateFileList(self._commChannel.extension.value()))
        
        self._commChannel.sigExecutionFinished.connect(self.executionFinished)
        
        self._commChannel.extension.sigValueChanged.connect(self.extensionChanged)
                
        self.execution = False
        self.toExecute = []
        
        self.current = None
        
        self.t0 = None
        
        self.extension = None
        
        self.watcher = None
        

    def toggleWatch(self, checked):
        self._widget.path = self._widget.folderEdit.text()
        if checked and (not self._widget.path or not os.path.isdir(self._widget.path)):
            self._logger.error("Select a valid folder")
            for button in [self._widget.watchCheck, self._widget.liveModeCheck]:
                button.blockSignals(True)
                button.setChecked(False)
                button.blockSignals(False)
            return
        
        if checked:
            try:
                with open("loc_parms.json", 'r') as f:
                    params = json.load(f)
                
                self.numFramesInStack = params.get("nx_s", 60) * params.get("ny_s", 60)
                numRowsInFrame = params.get("num_rows", 512)
                numColsInFrame = params.get("num_cols", 512)

                self.buffer = np.zeros((self.numFramesInStack, numRowsInFrame, numColsInFrame), dtype=np.float32)
                self._commChannel.sigSetupLiveStream.emit(params, self.buffer)
                self._logger.debug(f"Buffer of shape {self.buffer.shape} ready!")

            except Exception as e:
                self._logger.error(f"Could not setup Buffer from .json file: {e}")
                return

            self.frameCounter = 0
            self.stackCounter = 0

            self.extension = self._commChannel.extension.value()

            self.loaderThread = QtCore.QThread()
            # delete thread object from memory after its event loop is done
            self.loaderThread.finished.connect(self.loaderThread.deleteLater)

            self.loaderWorker = FileLoaderWorker(None) 
            self.loaderWorker.moveToThread(self.loaderThread)

            self.loaderWorker.sigFileLoaded.connect(self.onFileLoaded)

            self.sigTriggerRun.connect(self.loaderWorker.run)
            self.loaderThread.start()
            
            self.watcher = FileWatcher(self._widget.path, interval=0.1)
            self.watcher.sigNewFiles.connect(self.newFiles) 
            self.watcher.start()

            existingFiles = self.watcher.filesInDirectory()        
            if existingFiles:
                self.newFiles(existingFiles)

        else: 
            if hasattr(self, "watcher"):
                self.watcher.stop()
                self.watcher.wait() 
            
            self.loaderThread.quit()
            self.loaderThread.wait()

            self.toExecute = []
            self.execution = False 
            self._logger.debug("Watcher stopped.")


    def extensionChanged(self):
        self._widget.updateFileList(self._commChannel.extension.value())
        self._widget.watchCheck.setChecked(False)


    def newFiles(self, files):
        self.toExecute.extend(files)
        self._widget.updateFileList(self.extension) 
        
        if not self.execution:
            self.runNextFile()


    def runNextFile(self):
        if not self.toExecute or self.execution:
            return
        
        self.execution = True

        filename = self.toExecute.pop(0)
        fullPath = os.path.join(self._widget.path, filename)

        self.loaderWorker.fullPath = fullPath
        self.sigTriggerRun.emit(fullPath)


    @QtCore.Slot(np.ndarray, str)                                     
    def onFileLoaded(self, data, filename):
        """ 
        Runs the MAIN THREAD, receives data from I/O worker 
        and hands it off to the Processor thread/queue.
        """
        self._logger.debug(f"File successfully loaded: {filename}")

        if data.ndim == 2: 
            data = np.expand_dims(data, axis=0) 

        for frame in data:
            self.buffer[self.frameCounter] = frame 
            self._commChannel.sigLiveFrameReady.emit(self.frameCounter)
            
            # self._logger.debug(f"Frames processed: {self.frameCounter + 1}")
            
            self.frameCounter = (self.frameCounter + 1) % self.numFramesInStack
        
        self.stackCounter += 1
        self._logger.debug(f"Stack/Chunk Processed: {self.stackCounter} with {self.numFramesInStack} frames")
        
        self.execution = False

        self.runNextFile()


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