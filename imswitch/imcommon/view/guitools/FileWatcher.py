# type: ignore

from os import listdir
from os.path import join, isdir
from qtpy import QtCore
from typing import List


class FileWatcher(QtCore.QThread):

    sigFinishedDirectory = QtCore.Signal(list)

    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self.root_path = path
        self.directories = []
        self.directory_index = 0
        self.running = True

    def run(self):
        while self.running:
            self._find_directories()

            if self.directories and self.directory_index <= len(self.directories) - 1:
                d = self.directories[self.directory_index]
                self.directory_index += 1
                # TODO: fix proper loop for the files and condition for when to break it
                files = self._find_files(d)
                self.sigFinishedDirectory.emit(files)

            self.msleep(500)

    def stop(self):
        self.running = False

    def _find_directories(self):
        path = self.root_path
        for d in listdir(path):
            d_abs = join(path, d)
            if isdir(d_abs) and not d_abs in self.directories:
                self.directories.append(d_abs)

    def _find_files(self, d) -> List[str]:
        files = []
        for f in listdir(d):
            f_abs = join(d, f)
            if f.lower().endswith(".zarr"):
                files.append(f_abs)

        return files
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