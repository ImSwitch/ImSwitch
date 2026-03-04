from os import listdir
from os.path import isfile, join, isdir
from qtpy import QtCore
import os


class FileWatcher(QtCore.QThread): 

    sigNewFiles = QtCore.Signal(list) # type: ignore

    def __init__(self, path, extension=".tif", interval=1.0): 
        super().__init__()
        self.path = path
        self.target_ext = extension.lower().lstrip('.')

        self.extension = extension if extension.startswith('.') else '.' + extension
        
        self.interval = interval 
        
        self.running = True       
        
        self._last_seen_files = set(self.filesInDirectory())    

    def filesInDirectory(self):
        """
        Returns a list of files/folders in the directory that match the 
        supported image extensions.
        """
        target_ext = self.extension.lower().lstrip('.')

        # valid_exts = [target_ext, 'tif', 'tiff', 'zarr', 'hdf5', 'h5']
        # But usually, we want to follow what the user selected in the UI.
        all_items = listdir(self.path)
        matches = []

        for f in all_items:
            full_path = join(self.path, f)
            f_lower = f.lower()

            # TODO: The .hdf5 reading is not working as it should right now FIX this later

            # check if it matches our target extension 
            # note: .zarr is a directory; .tif AND .hdf5 are files 
            if f_lower.endswith('.' + target_ext) and (isfile(full_path) or isdir(full_path)):
                matches.append(f)

            # special case: people use .tif and .tiff interchangeably 
            elif target_ext in ["tif", "tiff"]: 
                matches.append(f)  
            
            # special case: hdf5 variations
            elif target_ext in ["h5", "hdf5"] and f_lower.endswith((".h5", ".hdf5")):
                matches.append(f) 

        # print(f"DEBUG: Polling {self.path}... Found {len(matches)} matches for '{target_ext}'")        
        
        return matches
        
    def run(self):
        """ Watches for new files """
        while self.running: 
            current_files = set(self.filesInDirectory())
            new_files = list(current_files - self._last_seen_files) # set subtraction
            
            if new_files:
                self._last_seen_files.update(new_files)
                self.sigNewFiles.emit(sorted(new_files)) 

            # files deleted => remove them from memory and allow them to be re-detected
            if len(self._last_seen_files) > len(current_files): 
                self._last_seen_files = self._last_seen_files.intersection(current_files)

            # use QtCore.QThread sleep method
            self.msleep(int(self.interval * 1000))
    
    def stop(self): 
        self.running = False
    
    def addToLog(self, filename, info_list): 
        """ Specifically kept for WatcherController's script logging. """
        log_path = os.path.join(self.path, "watcher_log.txt")
        try:
            with open(log_path, 'a') as f:
                # append line at the end of the log file
                line = f"{filename} | " + " | ".join(info_list) + "\n"
                f.write(line)
        except Exception as e:
            print(f"ERROR: Can't add to log: {e}")
        
# Adapted from https://towardsdatascience.com/implementing-a-file-watcher-in-python-73f8356a425d
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