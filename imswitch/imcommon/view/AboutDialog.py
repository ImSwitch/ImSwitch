from qtpy import QtCore, QtWidgets

import imswitch


class AboutDialog(QtWidgets.QDialog):
    """ Dialog showing information about ImSwitch. """

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint,
                         *args, **kwargs)
        self.setWindowTitle('About ImSwitch')
        self.setMinimumWidth(480)

        self.label = QtWidgets.QLabel(
            f'<strong>ImSwitch {imswitch.__version__}</strong>'
            f'<br /><br />Code available at: '
            f'<a href="https://github.com/openUC2/ImSwitch" style="color: orange">'
            f'https://github.com/openUC2/ImSwitch'
            f'</a>'
            f'<br />Licensed under the GNU General Public License v3.0.'
        )
        self.label.setWordWrap(True)
        self.label.setTextFormat(QtCore.Qt.RichText)
        self.label.setOpenExternalLinks(True)
        self.label.setStyleSheet('font-size: 10pt')

        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok,
            QtCore.Qt.Horizontal,
            self
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(16)
        layout.addWidget(self.label)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    @classmethod
    def showDialog(cls, parent):
        dialog = cls(parent)
        dialog.exec_()
        dialog.deleteLater()  # Prevent memory leak


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
