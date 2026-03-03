from os import listdir
from os.path import isfile, join, isdir
import time
from qtpy import QtCore
from datetime import datetime
import os
import json
import socket


class FileWatcher(QtCore.QThread):
    sigNewFiles = QtCore.Signal(list) # type: ignore

    def __init__(self, path, extension, pollTime):
        super().__init__()
        self.path = path
        self.extension = extension
        self.pollTime = pollTime
        self.list = self.filesInDirectory()
        self.watching = False
        self.active = False
        self._log = {}
        self.startLog()

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
    
    def updateList(self, newList):
        differencesList = [x for x in newList if
                           x not in self.list]  # Note if files get deleted, this will not highlight them
        self.list = newList
        return differencesList

    def run(self):
        self.active = True
        print("DEBUG: FileWatcher loop started")
        while self.active:
            if not self.watching:  # Check if this is the first time the function has run
                self.list = self.filesInDirectory()
                self.watching = True

            time.sleep(self.pollTime)

            newFileList = self.filesInDirectory()

            fileDiff = self.updateList(newFileList)

            if len(fileDiff) == 0:
                continue

            self.sigNewFiles.emit(fileDiff)

    def stop(self):
        self.saveLog()
        self._log = {}
        self.active = False

    def removeFromList(self, files):
        for f in files:
            self.list.remove(f)

    def startLog(self):
        self._log["Starting time"] = str(datetime.now())
        self._log["Computer name"] = os.environ.get("ComputerName", socket.gethostname())

    def addToLog(self, key, value):
        self._log[key] = value

    def getLog(self):
        return self._log

    def saveLog(self):
        with open(self.path + '/' + 'log.json', 'a') as f:
            f.write(json.dumps(self._log, indent=4))

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