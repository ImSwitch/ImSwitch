from imswitch.imcommon.view.guitools.FileWatcher import FileWatcher
from imswitch.imreconstruct.model import DataObj
import os
import json
from .basecontrollers import ImRecWidgetController
from imswitch.imcommon.model.logging import initLogger
import zarr
import numpy as np
from ome_zarr.io import parse_url
from ome_zarr.writer import write_image
from time import perf_counter
import tifffile as tiff
import h5py

from qtpy import QtCore



class WatcherFrameController(ImRecWidgetController):
    """ Linked to WatcherFrame. """

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
        
        # self._commChannel.sigDataFolderChanged.connect(self.recPath)
        
        self.execution = False
        self.toExecute = []
        self.current = None
        self.t0 = None
        self.extension = None
        

    def toggleWatch(self, checked):
        self._logger.debug(f"We've entered the toggleWatch() method, where checked = {checked}")
        
        self._widget.path = self._widget.folderEdit.text()
        self._logger.debug(f"File Watcher path: {self._widget.path}")

        if checked and (not self._widget.path or not os.path.isdir(self._widget.path)): 
            self._logger.error("Select a valid folder")            
            # silently uncheck buttons
            for button in [self._widget.watchCheck, self._widget.liveModeCheck]:
                button.blockSignals(True)
                button.setChecked(False)
                button.blockSignals(False) 
            return
        
        if checked:
            try:
                with open("loc_parms.json", 'r') as f:
                    params = json.load(f)

                # --- LOAD DIMENSIONS ---
                self.total_steps = params.get("nx_s", 60) * params.get("ny_s", 60)  
                frame_x_dim = params.get("num_cols", 512) 
                frame_y_dim = params.get("num_rows", 512)

                # --- PRE-ALLOC CIRCULAR BUFFER ---
                self.buffer = np.zeros((self.total_steps, frame_y_dim, frame_x_dim), dtype=np.float32) 

                self._commChannel.sigSetupLiveStream.emit(params)

                # --- SHARE REFERENCE TO BUFFER ---
                self._commChannel.sigBufferInitialized.emit(self.buffer)
                self._logger.debug(f"Buffer of shape {self.buffer.shape} ready!")

            except Exception as e:
                self._logger.error(f"Could not setup Buffer from .json file: {e}")
                return

            self._frameCounter = 0 
            self.extension = self._commChannel.extension.value()

            self.watcher = FileWatcher(self._widget.path, interval=0.1)
            self.watcher.sigNewFiles.connect(self.newFiles) 
            self.watcher.start()

            existing_files = self.watcher.filesInDirectory()
            self._logger.debug(f"Existing files: {existing_files}")
        
            if existing_files:
                self.newFiles(existing_files)
        
        # stop logic
        else: 
            if hasattr(self, "watcher"):
                self.watcher.stop()
                self.watcher.wait() 
            self.toExecute = []
            self.execution = False 
            self._logger.debug("Watcher stopped.")


    def extensionChanged(self):
        self._widget.updateFileList(self._commChannel.extension.value())
        self._widget.watchCheck.setChecked(False)


    def newFiles(self, files):
        self._logger.debug("We've entered newFiles()")
        self.toExecute.extend(files)
        # uncomment to see an update of the UI list
        self._widget.updateFileList(self.extension) 
        if not self.execution:
            self.runNextFile()


    def runNextFile(self): 
        # self._logger.debug(f"runNextFile has been called. is_live={self._widget.isLiveMode()}, toExecute={len(self.toExecute)}")
        if not self.toExecute or self.execution:
            return 
        
        filename = self.toExecute.pop(0) 
        full_path = os.path.join(self._widget.path, filename)
        is_live = self._widget.isLiveMode()
        total_steps = self.total_steps

        try: 
            if is_live: 
                # --- READ DATA ---
                extension = filename.lower()
                if extension.endswith((".tif", ".tiff")):
                    new_data = tiff.imread(full_path)   
                elif extension.endswith((".h5", ".hdf5")): 
                    with h5py.File(full_path, 'r') as f:
                        # assume that "data" is the key
                        first_key = list(f.keys())[0]
                        new_data = f[first_key][:] # type: ignore
                elif extension.endswith(".zarr"):
                    zarr_file = zarr.open(full_path, mode='r')
                    new_data = zarr_file[:]
                
                else:
                    self._logger.error("File format not supported!")
                    return 

                # --- ENSURE 3D SHAPE ---
                if new_data.ndim == 2: # type: ignore 
                    new_data = [new_data]
                        
                # --- PROCESS FRAMES --- 
                for frame in new_data: # type: ignore
                    # load frame into buffer
                    self.buffer[self._frameCounter] = frame  
                    # debug:
                    # print(f"DEBUG: Emitting frame {self._frameCounter}") 
                    # tell view controller which index is ready
                    self._commChannel.sigLiveFrameReady.emit(self._frameCounter) 
                    # increment counter
                    self._frameCounter = (self._frameCounter + 1) % total_steps
                
                # --- RECURSION --- 
                QtCore.QTimer.singleShot(0, self.runNextFile)
            
            else: 
                # --- LEGACY MODE ---
                self.execution = True
                datasets = DataObj.getDatasetNames(full_path)
                dataObjs = []
                for dataset in datasets: 
                    file_handle, dataset_name, = DataObj._open(full_path, dataset)   
                    dataObjs.append(DataObj(filename, dataset_name, path=full_path, file=file_handle))

                self._commChannel.sigReconstruct.emit(dataObjs, True)
        
        except Exception as e:
            self._logger.warning(f"File access error (retrying): {filename} - {e}")            
            self.toExecute.insert(0, filename)  
            QtCore.QTimer.singleShot(500, self.runNextFile)


    def executionFinished(self, image):
        if self.execution:
            self.execution = False
            self.saveImage(image)
            diff = perf_counter() - self.t0 # type: ignore
            self.watcher.addToLog(self.current, [str(self.t0), str(diff)])
            self._widget.updateFileList(self.extension)
            self.runNextFile()

    def saveImage(self, image):
        image = np.squeeze(image[:, 0, :, :, :, :])
        image = np.reshape(image, (1, *image.shape))
        extension = self._commChannel.extension.value()
        if not os.path.exists(self.recPath): # type: ignore
            if extension == 'zarr':
                store = parse_url(self.recPath + '.tmp', mode="w").store # type: ignore
                root = zarr.group(store=store)
                root.attrs["ImSwitchData"] = self.attrs["ImSwitchData"] # type: ignore
                write_image(image=image, group=root, axes="zyx")
                store.close()
                os.rename(self.recPath + '.tmp', self.recPath) # type: ignore
                tiff.imwrite(self.recPath.split('.')[0] + ".tiff", image) # type: ignore
            if extension == 'hdf5':
                h = h5py.File(self.recPath + '.tmp', 'w') # type: ignore
                dset = h.create_dataset('data', data=image)
                self._logger.debug(type(self.attrs))
                for k in self.attrs.keys(): # type: ignore
                    dset.attrs[k] = self.attrs[k] # type: ignore
                h.close()
                os.rename(self.recPath + '.tmp', self.recPath) # type: ignore
                tiff.imwrite(self.recPath.split('.')[0] + ".tiff", image) # type: ignore


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