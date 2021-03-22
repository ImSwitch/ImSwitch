from PyQt5 import QtCore, QtWidgets

from .ConsoleView import ConsoleView
from .EditorView import EditorView
from .FilesView import FilesView


class ImScrMainView(QtWidgets.QMainWindow):
    sigClosing = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Scripting')

        # Actions in menubar
        menuBar = self.menuBar()
        file = menuBar.addMenu('&File')

        openFileAction = QtWidgets.QAction('Open…', self)
        openFileAction.setShortcut('Ctrl+O')
        file.addAction(openFileAction)
        saveFileAction = QtWidgets.QAction('Save', self)
        saveFileAction.setShortcut('Ctrl+S')
        file.addAction(saveFileAction)
        saveAsFileAction = QtWidgets.QAction('Save as…', self)
        saveAsFileAction.setShortcut('Ctrl+Shift+S')
        file.addAction(saveAsFileAction)

        # Main layout
        layout = QtWidgets.QHBoxLayout()
        self.cwidget = QtWidgets.QWidget()
        self.setCentralWidget(self.cwidget)
        self.cwidget.setLayout(layout)

        self.files = FilesView()
        layout.addWidget(self.files, 1)

        self.editor = EditorView()
        layout.addWidget(self.editor, 3)

        self.console = ConsoleView()
        layout.addWidget(self.console, 1)

        self.showMaximized()

    def closeEvent(self, event):
        self.sigClosing.emit()
        event.accept()


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
