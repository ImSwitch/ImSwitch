from PyQt5 import QtGui, QtWidgets


class OutputView(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        self.outputBox = QtWidgets.QPlainTextEdit()
        self.outputBox.setReadOnly(True)
        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        font.setPointSize(9)
        self.outputBox.setFont(font)
        layout.addWidget(self.outputBox, 1, 1)

    def setText(self, text):
        self.outputBox.setPlainText(text)

    def appendText(self, text):
        self.outputBox.moveCursor(QtGui.QTextCursor.End)
        self.outputBox.insertPlainText(text)

    def clearText(self):
        self.outputBox.clear()


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
