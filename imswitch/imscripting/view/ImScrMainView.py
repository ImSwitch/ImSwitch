from pyqtgraph.dockarea import Dock, DockArea
from qtpy import QtCore, QtWidgets

from .ConsoleView import ConsoleView
from .EditorView import EditorView
from .FilesView import FilesView
from .OutputView import OutputView


class ImScrMainView(QtWidgets.QMainWindow):
    """ Main view of imscripting. """

    sigNewFile = QtCore.Signal()
    sigOpenFile = QtCore.Signal()
    sigSaveFile = QtCore.Signal()
    sigSaveAsFile = QtCore.Signal()
    sigClosing = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Scripting')

        # Actions in menubar
        menuBar = self.menuBar()
        file = menuBar.addMenu('&File')

        self.newFileAction = QtWidgets.QAction('New…', self)
        self.newFileAction.setShortcut('Ctrl+N')
        self.newFileAction.triggered.connect(self.sigNewFile)
        file.addAction(self.newFileAction)
        self.openFileAction = QtWidgets.QAction('Open…', self)
        self.openFileAction.setShortcut('Ctrl+O')
        self.openFileAction.triggered.connect(self.sigOpenFile)
        file.addAction(self.openFileAction)
        self.saveFileAction = QtWidgets.QAction('Save', self)
        self.saveFileAction.setShortcut('Ctrl+S')
        self.saveFileAction.triggered.connect(self.sigSaveFile)
        file.addAction(self.saveFileAction)
        self.saveAsFileAction = QtWidgets.QAction('Save as…', self)
        self.saveAsFileAction.setShortcut('Ctrl+Shift+S')
        self.saveAsFileAction.triggered.connect(self.sigSaveAsFile)
        file.addAction(self.saveAsFileAction)

        # Main layout
        self.dockArea = DockArea()
        self.setCentralWidget(self.dockArea)

        self.editor = EditorView()
        self.editorDock = Dock('Script Editor')
        self.editorDock.addWidget(self.editor)
        self.dockArea.addDock(self.editorDock)

        self.files = FilesView()
        self.filesDock = Dock('Files')
        self.filesDock.addWidget(self.files)
        self.dockArea.addDock(self.filesDock, 'left', self.editorDock)

        self.console = ConsoleView()
        self.consoleDock = Dock('Console')
        self.consoleDock.addWidget(self.console)
        self.dockArea.addDock(self.consoleDock, 'right', self.editorDock)

        self.output = OutputView()
        self.outputDock = Dock('Output')
        self.outputDock.addWidget(self.output)
        self.dockArea.addDock(self.outputDock, 'bottom', self.editorDock)

        self.editorDock.setStretch(20, 30)

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
