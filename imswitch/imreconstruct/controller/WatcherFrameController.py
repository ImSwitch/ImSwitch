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

# --- new start ---
from qtpy import QtCore, QtWidgets 
# --- new end ---



class WatcherFrameController(ImRecWidgetController):
    """ Linked to WatcherFrame. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs = None
        self.recPath = None
        self._widget.sigWatchChanged.connect(self.toggleWatch)
    
        # --- new start () ---
        try:
            self._widget.sigLiveReconChanged.connect(self.toggleWatch)
        except AttributeError:
            print(f"DEBUG: Available widget signals: {self._widget.__dict__.keys()}")
        # --- new end () ---
     
        self._widget.sigChangeFolder.connect(lambda: self._widget.updateFileList(self._commChannel.extension.value()))
        self._commChannel.sigExecutionFinished.connect(self.executionFinished)
        self._commChannel.extension.sigValueChanged.connect(self.extensionChanged)
        self.execution = False
        self.toExecute = []
        self.current = None
        self.t0 = None
        self.extension = None
        self.__logger = initLogger(self, tryInheritParent=False)

        # --- new start (0) ---
        self._frameCounter = 0 # init cyclic tag 
        self.nx_s = 1 # def val
        self.ny_s = 1 # def val
        self.total_steps = 0 # total number of steps to cover ROI <- set this from meta data
        # --- new end (0) ---

    def toggleWatch(self, checked):
        # 1. Always grab the latest path from the widget's line edit
        self._widget.path = self._widget.folderEdit.text()
        
        # 2. Guard against empty or invalid paths
        if not self._widget.path or not os.path.isdir(self._widget.path):
            if checked: # Only warn if they are trying to turn it ON
                print("Error: Please select a valid folder before starting.")
                # Uncheck buttons to prevent inconsistent UI state
                self._widget.watchCheck.blockSignals(True)
                self._widget.liveModeCheck.blockSignals(True)
                self._widget.watchCheck.setChecked(False)
                self._widget.liveModeCheck.setChecked(False)
                self._widget.watchCheck.blockSignals(False)
                self._widget.liveModeCheck.blockSignals(False)
            return

        # 3. Determine which modes are active
        live_active = self._widget.isLiveMode()
        batch_active = self._widget.watchCheck.isChecked()

        # 4. Start logic: if the clicked button is ON and at least one mode is active
        if checked and (live_active or batch_active):
            print(f"DEBUG: Watcher Ignition! Path: {self._widget.path}")
            
            # Handle extension with fallback to 'tif' if the dropdown is empty
            ext = self._commChannel.extension.value()
            if not ext:
                print("DEBUG: Extension was empty! Defaulting to 'tif'")
                ext = "tif"

            self.extension = ext
            print(f"DEBUG: Watcher Starting for extension: {self.extension}")

            # Reset cyclic tag if we are in Live Mode
            if live_active:
                print("DEBUG: Live Reconstruction Mode Active - Resetting frame counter.")
                self._frameCounter = 0
            
            # 5. Cleanly restart the watcher thread
            if hasattr(self, 'watcher'): 
                self.watcher.stop()
                self.watcher.wait() # Ensure the old thread is fully closed
                        
            # --- MARK --> FileWatcher instance created ---    
            self.watcher = FileWatcher(self._widget.path, self.extension, 1)
            self.watcher.sigNewFiles.connect(self.newFiles)
            self.watcher.start()
            
            # 6. Immediately check for files already sitting in the folder
            self.toExecute = self.watcher.filesInDirectory()
            if self.toExecute:
                print(f"DEBUG: Found {len(self.toExecute)} existing files. Scheduling processing...")
                # Use a timer instead of calling it directly to avoid the NoneType race condition
                QtCore.QTimer.singleShot(1000, self.runNextFile)
        
        # 7. Stop logic: only shut down if BOTH buttons are now unchecked
        else:
            if not live_active and not batch_active:
                if hasattr(self, 'watcher'):
                    self.watcher.stop()
                    print("DEBUG: Watcher Stopped.")
                self.toExecute = []
    
    def extensionChanged(self):
        self._widget.updateFileList(self._commChannel.extension.value())
        self._widget.watchCheck.setChecked(False)

    def newFiles(self, files):
        print(f"DEBUG: Watcher detected NEW files: {files}")
        
        self._widget.updateFileList(self.extension)
        self.toExecute.extend(files)
        try:
            self.runNextFile()
        except OSError:
            self.__logger.error("Writing in progress.")
            self.watcher.removeFromList(files)
        # --- new start () ---
        QtCore.QTimer.singleShot(500, self.runNextFile)
        # --- new end () ---

    def runNextFile(self):
        if not self.toExecute or self.execution: 
            # not self.toExecute: checks if the list self.toExecute is empty or not
            return

        newFile = self.toExecute[0]
        self.current = os.path.join(self._widget.path, newFile)

        try:
            # detect file type
            is_tiff = self.current.lower().endswith((".tif", ".tiff")) 
            is_hdf5 = self.current.lower().endswith((".hdf5", ".h5"))

            # 1. Force the file to open and load data/metadata
            datasets = DataObj.getDatasetNames(self.current)
            dataObjs = []
            
            for d in datasets:
                # Use the helper to get the actual file handle
                file_handle, ds_name = DataObj._open(self.current, d)
        
                # each data set becomes a unique DataObj and is appened to the dataObjs list
                dataObj = DataObj(newFile, ds_name, path=self.current, file=file_handle)
                
                if is_tiff:
                    self.attrs = {"writing": False, "pixel_size": [1.0, 1.0]}
                else:
                    # both hdf5 and zarr use checkLock() to wait for the "writing" attribute to be false
                    dataObj.checkLock()
                    self.attrs = dataObj.attrs

                dataObjs.append(dataObj)
            
            # fetch and remove first element in list
            self.toExecute.pop(0) 
            
            if self._widget.isLiveMode():
                self._processLiveStream(dataObjs)
            else:
                self.execution = True
                self._commChannel.sigReconstruct.emit(dataObjs, True)

        except Exception as e:
            # If it's a real error, log it. If it's just a file lock, it will retry.
            print(f"RETRYING: {newFile} not ready yet. Error: {e}")
            QtCore.QTimer.singleShot(1000, self.runNextFile)
    



    # --- new start (2) ---
    def _processLiveStream(self, dataObjs):
        """ New method to handle frame-by-frame streaming. """   
        try: 
            # read and open loc_parms.json file and fetch the relevant parameters
            with open("loc_parms.json", "r") as f: 
                params = json.load(f)
            nx_s = params["nx_s"]
            ny_s = params["ny_s"]
            self._logger.debug(
                "Succesfully read loc_parms.json file with parameters scanning step parameters"
                + f": nx_s = {nx_s} and ny_s = {ny_s}"
            )
        except Exception:
            # Fallback to the pattern/widget values if the dict is failing
            self._logger.error("Failed to load localizer parameters via .json file -> defaulting to fixed values")
            nx_s = getattr(self, "nx_s", 60)
            ny_s = getattr(self, "ny_s", 60)
        
        # calculate max steps based on the resolved dimensions
        max_steps = nx_s * ny_s 
        self._logger.debug(f"Live Reconstruction Grid: {nx_s}x{ny_s} with ({max_steps} total steps)")

        # iterate through files (data objects)
        for obj in dataObjs:
            # accessing .data triggers the TiffFile.asarray() call for TIFFs
            frames = obj.data
            
            if frames is None:
                print(f"WARNING: No data found in {obj.name}")
                continue

            # ensure we have a 3D array (stack) even for single frames
            if frames.ndim == 2: 
                frames = np.expand_dims(frames, axis=0)
            
            # stream frames to the processor
            for frame in frames: 
                
                print(f"DEBUG: Emitting frame {self._frameCounter}/{max_steps}") 
                # emit frame + position index (cyclic tag)
                #TODO: .emit(ptr_to_frame. tag) receiver knows how to grab the frame
                self._commChannel.sigLiveFrameReady.emit(frame, self._frameCounter)
                
                # increment index and wrap around at max_steps
                self._frameCounter = (self._frameCounter + 1) % max_steps 
        
        # --- ADD THIS NUDGE ---
        # This tells the main window that the underlying data has changed 
        # and it should re-run the 'transpose' and 'paint' logic.
        if hasattr(self._widget, "update"):
            self._widget.update()
        
        # If there's a specific method to refresh the reconstruction view:
        if hasattr(self._widget, "reconstructionWidget"):
            self._widget.reconstructionWidget.update()

        # 4. Reset execution flag
        # This is vital because Live Mode doesn't wait for a 'Finished' signal
        self.execution = False
        
        # 5. Check if more files arrived while we were processing this one
        self.runNextFile() 
    # --- new end (2) ---




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
                self.__logger.debug(type(self.attrs))
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