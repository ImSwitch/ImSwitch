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
        self.firstRun = True

    def run(self):
        while self.running: 
            current_files = set(self.getFilesInPath())
            new_files = list(current_files - self.previous_files) # set subtraction

            if self.firstRun and not new_files:
                self.sigNewFiles.emit(list(current_files))
                self.firstRun = False

            if new_files:
                self.previous_files.update(new_files)
                self.sigNewFiles.emit(new_files)


            if len(self.previous_files) > len(current_files):
                self.previous_files = self.previous_files.intersection(current_files)

            self.msleep(int(self.interval * 1000))
    

    def stop(self): 
        self.running = False


    def getFilesInPath(self) -> List[str]:
        all_items = listdir(self.path)
        matches = []
        for f in all_items:
            full_path = join(self.path, f)
            if f.lower().endswith(".zarr") and isdir(full_path):
                if f not in matches:
                    matches.append(full_path)
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