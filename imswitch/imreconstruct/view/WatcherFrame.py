from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools
import os


class WatcherFrame(QtWidgets.QFrame):
    """Frame for reconstructing files from a folder automatically."""

    sigWatchChanged = QtCore.Signal(bool)  # type: ignore (enabled)
    sigChangeFolder = QtCore.Signal() # type: ignore

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.path = ''
        self.folderEdit = QtWidgets.QLineEdit(self.path)

        self.browseFolderButton = guitools.BetterPushButton('Browse')
        self.watchCheck = QtWidgets.QCheckBox('Watch and run')

        self.liveModeCheck = QtWidgets.QCheckBox("Live Reconstruction")
        self.liveModeCheck.setToolTip("Stream frames to Python GaussProcessor in real-time")

        self.listWidget = QtWidgets.QListWidget()
        #self.updateFileList()
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        layout.addWidget(self.folderEdit, 0, 1)
        layout.addWidget(self.browseFolderButton, 0, 0)
        layout.addWidget(self.listWidget, 1, 0, 1, 2)
        layout.addWidget(self.watchCheck, 2, 0)

        layout.addWidget(self.liveModeCheck, 2, 1)

        self.watchCheck.toggled.connect(self.sigWatchChanged)

        self.liveModeCheck.toggled.connect(self.sigWatchChanged)

        self.browseFolderButton.clicked.connect(self.browse)

    def isLiveMode(self):
        return self.liveModeCheck.isChecked()
    
    def updateFileList(self, extension):
        self.path = self.folderEdit.text()
        res = []
        for file in os.listdir(self.path):
            if file.endswith('.' + extension):
                res.append(file)

        self.listWidget.clear()
        self.listWidget.addItems(res)

    def browse(self):
        path = guitools.askForFolderPath(self, defaultFolder=self.path)
        if path:
            self.path = path
            self.folderEdit.setText(self.path)
            self.sigChangeFolder.emit()


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