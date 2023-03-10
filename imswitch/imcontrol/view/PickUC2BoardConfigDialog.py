from qtpy import QtCore, QtWidgets


class PickUC2BoardConfigDialog(QtWidgets.QDialog):
    """ Dialog for picking the setup to use for imcontrol. """

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint,
                         *args, **kwargs)
        self.setWindowTitle('Select pin configuration for the board')

        self.informationLabel = QtWidgets.QLabel(
            'Select the configuration file for your UC2 Board setup:'
        )
        self.configPicker = QtWidgets.QComboBox()

        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,
            self
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.informationLabel)
        layout.addWidget(self.configPicker)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def setUC2BoardConfig(self, configList):
        self.configPicker.clear()
        for config in configList:
            self.configPicker.addItem(config)

    def getSelectedConfig(self):
        return self.configPicker.currentText()

    def setSelectedConfig(self, config):
        index = self.configPicker.findText(config)
        if index > -1:
            self.configPicker.setCurrentIndex(index)


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
