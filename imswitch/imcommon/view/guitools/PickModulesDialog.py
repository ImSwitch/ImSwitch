from pyqtgraph.Qt import QtCore, QtWidgets


class PickModulesDialog(QtWidgets.QDialog):
    """ Dialog for picking the modules to enable in ImSwitch. """

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint,
                         *args, **kwargs)
        self.setWindowTitle('Select ImSwitch modules')

        self.informationLabel = QtWidgets.QLabel('Select the modules to enable:')
        self.modulesPicker = QtWidgets.QListWidget()

        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,
            self
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.informationLabel)
        layout.addWidget(self.modulesPicker)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def setModules(self, moduleIdsAndNamesDict):
        self.modulesPicker.clear()
        for moduleId, moduleName in moduleIdsAndNamesDict.items():
            listItem = QtWidgets.QListWidgetItem(moduleName)
            listItem.setData(1, moduleId)
            listItem.setFlags(listItem.flags() | QtCore.Qt.ItemIsUserCheckable)
            listItem.setCheckState(QtCore.Qt.Unchecked)
            self.modulesPicker.addItem(listItem)

    def getCheckedModules(self):
        moduleIds = []
        for i in range(self.modulesPicker.count()):
            item = self.modulesPicker.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                moduleIds.append(item.data(1))

        return moduleIds

    def setCheckedModules(self, moduleIds):
        for i in range(self.modulesPicker.count()):
            item = self.modulesPicker.item(i)
            item.setCheckState(QtCore.Qt.Checked if item.data(1) in moduleIds
                               else QtCore.Qt.Unchecked)

    @classmethod
    def showAndWaitForResult(cls, parent, moduleIdsAndNamesDict, preselectedModules=None):
        dialog = cls(parent)
        dialog.setModules(moduleIdsAndNamesDict)
        if preselectedModules is not None:
            dialog.setCheckedModules(preselectedModules)
        result = dialog.exec_()

        if result == QtWidgets.QDialog.Accepted:
            value = dialog.getCheckedModules()
        else:
            value = None

        dialog.deleteLater()  # Prevent memory leak
        return value


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
