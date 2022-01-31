import os

from qtpy import QtCore, QtWidgets


class PickDatasetsDialog(QtWidgets.QDialog):
    """ Dialog for picking datasets to load from a file. """

    def __init__(self, parent, allowMultiSelect, *args, **kwargs):
        super().__init__(parent, QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint,
                         *args, **kwargs)
        self.allowMultiSelect = allowMultiSelect

        self.setWindowTitle('Select dataset(s) to load' if allowMultiSelect
                            else 'Select dataset to load')

        self.informationLabel = QtWidgets.QLabel('')
        self.datasetsPicker = QtWidgets.QListWidget()
        if allowMultiSelect:
            self.datasetsPicker.setSelectionMode(QtWidgets.QListWidget.ExtendedSelection)
        self.datasetsPicker.itemDoubleClicked.connect(self.accept)

        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,
            self
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.informationLabel)
        layout.addWidget(self.datasetsPicker)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def setDatasets(self, dataPath, datasetNames):
        singularPlural = 'one(s)' if self.allowMultiSelect else 'one'
        self.informationLabel.setText(f'{os.path.basename(dataPath)} contains multiple datasets.'
                                      f'\nPlease select the {singularPlural} to load:')

        self.datasetsPicker.clear()
        for datasetName in datasetNames:
            self.datasetsPicker.addItem(datasetName)

        if self.allowMultiSelect:
            self.datasetsPicker.selectAll()
            self.datasetsPicker.setFocus()

    def getSelectedDatasets(self):
        return [item.text() for item in self.datasetsPicker.selectedItems()]


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
