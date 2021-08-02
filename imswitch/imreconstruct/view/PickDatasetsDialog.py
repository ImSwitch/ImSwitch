import os

from qtpy import QtCore, QtWidgets


class PickDatasetsDialog(QtWidgets.QDialog):
    """ Dialog for picking datasets to load from a file. """

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint,
                         *args, **kwargs)
        self.setWindowTitle('Select datasets to load')

        self.informationLabel = QtWidgets.QLabel('')
        self.datasetsPicker = QtWidgets.QListWidget()
        self.datasetsPicker.setSelectionMode(QtWidgets.QListWidget.ExtendedSelection)

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
        self.informationLabel.setText(f'{os.path.basename(dataPath)} contains multiple datasets.'
                                      f'\nPlease select the one(s) to load:')

        self.datasetsPicker.clear()
        for datasetName in datasetNames:
            self.datasetsPicker.addItem(datasetName)

    def getSelectedDatasets(self):
        return [item.text() for item in self.datasetsPicker.selectedItems()]


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
