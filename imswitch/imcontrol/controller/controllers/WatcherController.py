from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.view.guitools.FileWatcher import FileWatcher
import os
from time import perf_counter


class WatcherController(ImConWidgetController):
    """ Linked to WatcherWidget. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.t0 = None
        self._widget.sigWatchChanged.connect(self.toggleWatch)
        self._commChannel.sigScriptExecutionFinished.connect(self.executionFinished)
        self.execution = False
        self.toExecute = []
        self.current = []

    def toggleWatch(self, checked):
        if checked:
            self.watcher = FileWatcher(self._widget.path, 'py', 1)
            self._widget.updateFileList()
            files = self.watcher.filesInDirectory()
            self.toExecute = files
            self.watcher.sigNewFiles.connect(self.newFiles)
            self.watcher.start()
            self.runNextFile()
        else:
            self.watcher.stop()
            self.watcher.quit()
            self.toExecute = []

    def newFiles(self, files):
        self._widget.updateFileList()
        self.toExecute.extend(files)
        self.runNextFile()

    def runNextFile(self):
        if len(self.toExecute) and not self.execution:
            self.current = self._widget.path + '/' + self.toExecute.pop()
            file = open(self.current, "r")
            text = file.read()
            file.close()
            self.t0 = perf_counter()
            self._commChannel.runScript(text)
            self.execution = True

    def executionFinished(self):
        self.execution = False
        diff = perf_counter() - self.t0
        self.watcher.addToLog(self.current, [str(self.t0), str(diff)])
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
