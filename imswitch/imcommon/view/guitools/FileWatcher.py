# type: ignore

from os import listdir
from os.path import join, isdir
from qtpy import QtCore
from typing import List


class FileWatcher(QtCore.QThread): 

    def __init__(
            self,
            dir_queue: list[str],
            file_queue: list[str],
    ):
        super().__init__()
        self.dir_queue = dir_queue
        self.file_queue = file_queue
        self._dir_to_monitor = None
        self.running = True

    def run(self):
        while self.running:
            if self.dir_queue:
                self._dir_to_monitor = dir_queue.pop(0)
                while True:
                    self._add_files_to_queue()
                    self.msleep(200)

    def _add_files_to_queue(self):
        dir_to_monitor = self._dir_to_monitor
        for f in listdir(dir_to_monitor):
            f_abs = join(dir_to_monitor, f)
            if f.lower().endswith(".zarr"):
                self.file_queue.append(f_abs)

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