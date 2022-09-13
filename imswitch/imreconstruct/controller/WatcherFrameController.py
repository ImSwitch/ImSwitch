from imswitch.imcommon.view.guitools.FileWatcher import FileWatcher
from imswitch.imreconstruct.model import DataObj
import os
from .basecontrollers import ImRecWidgetController
from imswitch.imcommon.model.logging import initLogger


class WatcherFrameController(ImRecWidgetController):
    """ Linked to WatcherFrame. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.sigWatchChanged.connect(self.toggleWatch)
        self._commChannel.sigExecutionFinished.connect(self.executionFinished)
        self.execution = False
        self.toExecute = []
        self.current = []
        self.__logger = initLogger(self, tryInheritParent = False)

    def toggleWatch(self, checked):
        if checked:
            self.execution = False
            self.watcher = FileWatcher(self._widget.path, 'hdf5', 1)
            self._widget.updateFileList()
            files = self.watcher.filesInDirectory()
            self.toExecute = files
            self.watcher.sigNewFiles.connect(self.newFiles)
            self.watcher.start()
            self.runNextFile()
        else:
            self.execution = False
            self.watcher.stop()
            self.watcher.quit()
            self.toExecute = []

    def newFiles(self, files):
        self._widget.updateFileList()
        self.toExecute.extend(files)
        try:
            self.runNextFile()
        except OSError:
            self.watcher.removeFromList(files)

    def runNextFile(self):
        if len(self.toExecute) and not self.execution:
            self.current = self._widget.path + '\\' + self.toExecute.pop()
            datasets = DataObj.getDatasetNames(self.current)
            dataObjs = []
            for d in datasets:
                dataObjs.append(DataObj(os.path.basename(self.current), d, path=self.current))
            self._commChannel.sigReconstruct.emit(dataObjs, True)
            self.execution = True

    def executionFinished(self):
        if self.execution:
            self.execution = False
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
