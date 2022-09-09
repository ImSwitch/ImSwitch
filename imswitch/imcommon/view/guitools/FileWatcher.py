from os import listdir
from os.path import isfile, join
import time
from qtpy import QtCore


class FileWatcher(QtCore.QThread):
    sigNewFiles = QtCore.Signal(list)

    def __init__(self, path, extension, pollTime):
        super().__init__()
        self.path = path
        self.extension = extension
        self.pollTime = pollTime
        self.list = self.filesInDirectory()
        self.watching = False
        self.active = False

    def filesInDirectory(self):
        return [f for f in listdir(self.path) if (isfile(join(self.path, f)) and x.endswith('.' + self.extension))]

    def updateList(self, newList):
        differencesList = [x for x in newList if
                           x not in self.list]  # Note if files get deleted, this will not highlight them
        self.list = newList
        return differencesList

    def run(self):
        self.active = True
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
        self.active = False

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
