# type: ignore


from os import listdir
from os.path import join 
from qtpy import QtCore
from typing import List
import zarr


class FileWatcher(QtCore.QObject):

    """
    ...
    """

    sigFileFound = QtCore.Signal(str)    

    def __init__(self, directory_path: str):
        super().__init__()
        self.directory_path = directory_path
        self.seen_files = set()
        self.running = True

    def run(self):
        while self.running: 
            try: 
                self._check_for_files()
            except Exception as e:
                print(f"[FileWatcher] [run] >> Error scanning directory: {e}") 
            
            QtCore.QThread.msleep(200) 

    def stop(self):
        self.running = False

    def _check_for_files(self):
        for f in listdir(self.directory_path):
            f_abs = join(self.directory_path, f)
            if f.lower().endswith(".zarr") and f_abs not in self.seen_files:
                self.seen_files.add(f_abs)
                self.sigFileFound.emit(f_abs)


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