import uuid

from PyQt5 import QtCore, QtGui, QtWidgets, Qsci

from .guitools import BetterPushButton


class EditorView(QtWidgets.QTabWidget):
    sigRunAllClicked = QtCore.Signal(str, str)  # (instanceID, text)
    sigRunSelectedClicked = QtCore.Signal(str, str)  # (instanceID, selectedText)
    sigStopClicked = QtCore.Signal(str)  # (instanceID)
    sigTextChanged = QtCore.Signal(str)  # (instanceID)
    sigInstanceCloseClicked = QtCore.Signal(str)  # (instanceID)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTabsClosable(True)

        self.tabCloseRequested.connect(
            lambda index: self.sigInstanceCloseClicked.emit(self.widget(index).getID())
        )

    def addEditor(self, name):
        editorInstance = EditorInstanceView()
        editorInstance.sigRunAllClicked.connect(
            lambda text: self.sigRunAllClicked.emit(editorInstance.getID(), text)
        )
        editorInstance.sigRunSelectedClicked.connect(
            lambda text: self.sigRunSelectedClicked.emit(editorInstance.getID(), text)
        )
        editorInstance.sigTextChanged.connect(
            lambda: self.sigTextChanged.emit(editorInstance.getID())
        )
        editorInstance.sigStopClicked.connect(
            lambda: self.sigStopClicked.emit(editorInstance.getID())
        )
        self.addTab(editorInstance, name)
        self.setCurrentWidget(editorInstance)
        return editorInstance

    def setEditorName(self, instanceID, name):
        for i in range(self.count()):
            if self.widget(i).getID() == instanceID:
                self.setTabText(i, name)
                return

    def getCurrentInstance(self):
        return self.currentWidget()

    def setCurrentInstanceByID(self, instanceID):
        for i in range(self.count()):
            widget = self.widget(i)
            if widget.getID() == instanceID:
                self.setCurrentWidget(widget)
                return

    def getInstanceByID(self, instanceID):
        for i in range(self.count()):
            widget = self.widget(i)
            if widget.getID() == instanceID:
                return widget

    def closeInstance(self, instanceID):
        for i in range(self.count()):
            widget = self.widget(i)
            if widget.getID() == instanceID:
                widget.deleteLater()
                self.removeTab(i)
                return


class EditorInstanceView(QtWidgets.QWidget):
    sigRunAllClicked = QtCore.Signal(str)  # (text)
    sigRunSelectedClicked = QtCore.Signal(str)  # (selectedText)
    sigStopClicked = QtCore.Signal()
    sigTextChanged = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = str(uuid.uuid4())

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        topContainer = QtWidgets.QHBoxLayout()
        topContainer.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(topContainer, 0)

        topContainer.addSpacerItem(
            QtWidgets.QSpacerItem(
                40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
            )
        )

        self.runAllButton = BetterPushButton('Run all')
        self.runAllButton.clicked.connect(
            lambda: self.sigRunAllClicked.emit(self.getText())
        )
        topContainer.addWidget(self.runAllButton, 0)

        self.runSelectionButton = BetterPushButton('Run selection')
        self.runSelectionButton.clicked.connect(
            lambda: self.sigRunSelectedClicked.emit(self.getSelectedText())
        )
        topContainer.addWidget(self.runSelectionButton, 0)

        self.stopButton = BetterPushButton('Stop')
        self.stopButton.clicked.connect(
            lambda: self.sigStopClicked.emit()
        )
        topContainer.addWidget(self.stopButton, 0)

        self.scintilla = Scintilla()
        self.scintilla.textChanged.connect(self.sigTextChanged)
        layout.addWidget(self.scintilla, 3)

    def getID(self):
        return self.id

    def getSelectedText(self):
        return self.scintilla.selectedText()

    def getText(self):
        return self.scintilla.text()

    def setText(self, text):
        self.scintilla.setText(text)


class Scintilla(Qsci.QsciScintilla):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setMargins(1)
        self.setMarginWidth(0, '00000000')
        self.setMarginType(0, Qsci.QsciScintilla.NumberMargin)

        self.setTabWidth(4)
        self.setIndentationGuides(True)
        self.setAutoIndent(True)

        self.setScrollWidth(1)
        self.setScrollWidthTracking(True)

        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        font.setPointSize(11)

        lexer = Qsci.QsciLexerPython()
        lexer.setFont(font)
        lexer.setDefaultFont(font)
        self.setLexer(lexer)


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
