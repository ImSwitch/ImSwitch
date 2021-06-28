from qtpy import QtCore, QtWidgets

from .guitools import BetterPushButton


class FilesView(QtWidgets.QWidget):
    """ View that displays a file tree. """

    sigItemDoubleClicked = QtCore.Signal(str)  # (itemPath)
    sigRootPathSubmit = QtCore.Signal(str)  # (rootPath)
    sigBrowseClicked = QtCore.Signal()
    sigOpenRootInOSClicked = QtCore.Signal()

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
        self.rootPathEdit.returnPressed.connect(
            lambda: self.sigRootPathSubmit.emit(self.rootPathEdit.text())
        )
        self.rootPathBrowse = BetterPushButton('Browse…')
        self.rootPathBrowse.clicked.connect(self.sigBrowseClicked)

        self.rootPickerLayout.addWidget(self.rootPathEdit)
        self.rootPickerLayout.addWidget(self.rootPathBrowse)

        self.openRootButton = QtWidgets.QPushButton('Show folder in OS file explorer')
        self.openRootButton.clicked.connect(self.sigOpenRootInOSClicked)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.rootPickerLayout)
        layout.addWidget(self.openRootButton)
        layout.addWidget(self.tree)
        self.setLayout(layout)

    def setRootPath(self, path):
        """ Sets the root path of the file tree. Files outside this will not be
        displayed. """
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
