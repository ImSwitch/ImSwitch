import numpy as np

from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.view.guitools.FileWatcher import FileWatcher
from imswitch.imcommon.model import initLogger
import os


class WatcherController(ImConWidgetController):
    """ Linked to WatcherWidget. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.sigWatchChanged.connect(self.toggleWatch)
        self.__logger = initLogger(self)
        self._commChannel.sigScriptExecutionFinished.connect(self.executionFinished)
        self.execution = False
        self.toExecute = []
        self.current = []

    def toggleWatch(self, checked):
        if checked:
            self.watcher = FileWatcher(self._widget.path, 'py', 5)
            files = self.watcher.filesInDirectory()
            self.toExecute = files
            self.watcher.sigNewFiles.connect(self.newFiles)
            self.watcher.start()
            self.runNextFile()
        else:
            self.watcher.stop()
            self.watcher.quit()

    def newFiles(self, files):
        self._widget.updateFileList()
        self.toExecute.extend(files)
        self.runNextFile()

    def runNextFile(self):
        if len(self.toExecute) and not self.execution:
            self.current = self._widget.path + '\\' + self.toExecute.pop()
            file = open(self.current, "r")
            text = file.read()
            file.close()
            self._commChannel.runScript(text)
            self.execution = True

    def executionFinished(self):
        self.execution = False
        os.remove(self.current)
        self._widget.updateFileList()
        self.runNextFile()


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
