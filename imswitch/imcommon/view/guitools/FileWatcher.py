# type: ignore

from os import listdir
from os.path import join, isdir
from qtpy import QtCore
from typing import List


class FileWatcher(QtCore.QThread): 

    sigNewFiles = QtCore.Signal(list) 

    def __init__(self, path, extension=".tif", interval=1.0): 
        super().__init__()
        self.path = path
        self.target_ext = extension.lower().lstrip('.')
        self.extension = extension if extension.startswith('.') else '.' + extension
        self.interval = interval 
        self.running = True       
        self.previous_files = set(self.getFilesInPath())    


    def run(self):
        """ Watches for new files """
        while self.running: 
            current_files = set(self.getFilesInPath())
            new_files = list(current_files - self.previous_files) # set subtraction
            
            if new_files:
                self.previous_files.update(new_files)
                self.sigNewFiles.emit(new_files) 

            # files deleted => remove them from memory and allow them to be re-detected
            if len(self.previous_files) > len(current_files): 
                self.previous_files = self.previous_files.intersection(current_files)

            # QtCore.QThread.msleep() method
            self.msleep(int(self.interval * 1000))
    

    def stop(self): 
        self.running = False


    def getFilesInPath(self) -> List[str]:
        """ Returns a List of files/folders in the directory that match the supported image extensions. """
        target_ext = self.extension.lower().lstrip('.')
        all_items = listdir(self.path)
        matches = []

        for f in all_items:
            full_path = join(self.path, f)
            f_lower = f.lower()

            if f_lower.endswith(".zarr") and isdir(full_path):
                if f not in matches: # avoid duplicates   
                    matches.append(f)

            elif target_ext in ["h5", "hdf5"] and f_lower.endswith((".h5", ".hdf5")):
                matches.append(f) 

            elif target_ext in ["tif", "tiff"]: 
                matches.append(f)  
         
        return matches


    def setNewPath(self, path: str):
        self.path = path

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