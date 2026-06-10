# type: ignore

from os import listdir
from os.path import join, isdir
from qtpy import QtCore
from typing import List
import zarr

class FileWatcher(QtCore.QObject):

    """
    ...
    """
    
    sigSendFiles = QtCore.Signal(list)
    sigFinishedDirectory = QtCore.Signal()

    def __init__(self, path: str):
        super().__init__()
        self.root_path = path
        self.directories = []
        self.directory_index = 0
        self.running = True

    def start_monitoring(self):
        while self.running: 
            self._update_directories() 
            if self.directory_index <= len(self.directories) - 1: 
                d = self.directories[self.directory_index]
                self.directory_index += 1
                self._poll_directory(d)  
            QtCore.QThread.msleep(100)

    def stop(self):
        self.running = False

    def _update_directories(self):
        path = self.root_path
        for d in listdir(path):
            d_abs = join(path, d)
            if isdir(d_abs) and not d_abs in self.directories:
                self.directories.append(d_abs)

    def _find_files(self, dir_path: str) -> List[str]:
        files = set()
        for f in listdir(dir_path):
            f_abs = join(dir_path, f)
            if f.lower().endswith(".zarr"):
                files.add(f_abs)
        return files

    def _get_meta_value(self, dir_path: str, meta_key: str) -> object:
        while True:
            for f in listdir(dir_path):
                if f.endswith(".zattrs"):
                    z = zarr.open(dir_path)
                    imswitch_meta = z.attrs.get("ImswitchData", None) 
                    meta_val = imswitch_meta.get(meta_key, None) if imswitch_meta != None else None
                    return meta_val
            QtCore.QThread.msleep(100)

    def _poll_directory(self, dir_path: str): 
        old_files = set()  
        num_files = self._get_meta_value(dir_path, "Rec:LapseTime") 
        while True: 
            new_files = self._find_files(dir_path) - old_files
            old_files |= new_files # set operation: insert new files into old files 

            files = list(new_files)
            if files:
                files.sort() 
                self.sigSendFiles.emit(files)

            if num_files != None and len(old_files) >= num_files:
                self.sigFinishedDirectory.emit() 
                break 
            
            scan_flag = self._get_meta_value(dir_path, "scan_flag")
            if scan_flag != None and not scan_flag:
                self.sigFinishedDirectory.emit() 
                break
            
            QtCore.QThread.msleep(100) 

    
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