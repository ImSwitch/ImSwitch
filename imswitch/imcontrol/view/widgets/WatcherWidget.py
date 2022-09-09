from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools
from .basewidgets import Widget
import os


class WatcherWidget(Widget):
    """ Alignment widget that shows a grid of points on top of the image in the viewbox."""

    sigWatchChanged = QtCore.Signal(bool)  # (enabled)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = self._options.watcher.outputFolder
        self.folderEdit = QtWidgets.QLineEdit(self.path)

        self.browseFolderButton = guitools.BetterPushButton('Browse')
        self.watchCheck = QtWidgets.QCheckBox('Watch')
        self.runCombo = QtWidgets.QComboBox()
        self.runCombo.addItem("Run none")
        self.runCombo.addItem("Run selected")
        self.runCombo.addItem("Run all")

        self.listWidget = QtWidgets.QListWidget()
        self.updateFileList()

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        layout.addWidget(self.folderEdit, 0, 1)
        layout.addWidget(self.browseFolderButton, 0, 0)
        layout.addWidget(self.runCombo, 1, 0)
        layout.addWidget(self.listWidget, 2, 0, 1, 3)
        layout.addWidget(self.watchCheck, 3, 0)

        self.watchCheck.toggled.connect(self.sigWatchChanged)
        self.browseFolderButton.clicked.connect(self.browse)

    def updateFileList(self):
        res = []
        for file in os.listdir(self.path):
            if file.endswith('.py'):
                res.append(file)

        self.listWidget.clear()
        self.listWidget.addItems(res)

    def browse(self):
            path = guitools.askForFolderPath(self, defaultFolder=self.path)
            if path:
                self.path = path
                self.folderEdit.setText(self.path)
                self.updateFileList()

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
