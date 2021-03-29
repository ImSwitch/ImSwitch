from PyQt5 import QtCore, QtWidgets

from .guitools import BetterPushButton


class FilesView(QtWidgets.QWidget):
    sigItemDoubleClicked = QtCore.Signal(str)  # (itemPath)
    # TODO: Root picker

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath('')

        self.tree = QtWidgets.QTreeView()
        self.tree.setModel(self.model)

        for i in range(1, self.tree.header().length()):
            self.tree.hideColumn(i)
        self.tree.setHeaderHidden(True)

        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(0, QtCore.Qt.AscendingOrder)

        self.tree.doubleClicked.connect(
            lambda index: self.sigItemDoubleClicked.emit(self.model.filePath(index))
        )
        
        self.rootPickerLayout = QtWidgets.QHBoxLayout()
        self.rootPathEdit = QtWidgets.QLineEdit()
        self.rootPathBrowse = BetterPushButton('Browse…')
        self.rootPickerLayout.addWidget(self.rootPathEdit)
        self.rootPickerLayout.addWidget(self.rootPathBrowse)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.rootPickerLayout)
        layout.addWidget(self.tree)
        self.setLayout(layout)

    def setRootPath(self, path):
        self.tree.setRootIndex(self.model.index(path))
        self.rootPathEdit.setText(path)


# Copyright (C) 2020, 2021 TestaLab
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
