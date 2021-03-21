import os

import PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets, Qsci
from pyqtgraph.dockarea import Dock, DockArea
# TODO: Have output in separate dock (and separate file), use comm channel to update?

from .guitools import BetterPushButton


# from spyder.plugins.editor.widgets.editor import EditorPluginExample
# class EditorViewSpyder(spyder.plugins.editor.widgets.editor.EditorPluginExample):
#     pass


class EditorView(QtWidgets.QWidget):
    sigRunAllClicked = QtCore.Signal(str)  # (text)
    sigRunSelectedClicked = QtCore.Signal(str)  # (selectedText)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        topContainer = QtWidgets.QHBoxLayout()
        topContainer.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(topContainer, 0)

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

        self.scintilla = Scintilla()
        layout.addWidget(self.scintilla, 3)

        layout.addWidget(QtWidgets.QLabel('Output:'), 0)

        self.outputBox = QtWidgets.QPlainTextEdit()
        self.outputBox.setReadOnly(True)
        outputBoxFont = QtGui.QFont('Courier')
        outputBoxFont.setStyleHint(QtGui.QFont.TypeWriter)
        outputBoxFont.setPointSize(10)
        self.outputBox.setFont(outputBoxFont)
        layout.addWidget(self.outputBox, 1)

    def getSelectedText(self):
        return self.scintilla.selectedText()

    def getText(self):
        return self.scintilla.text()

    def setOutput(self, text):
        self.outputBox.setPlainText(text)


class Scintilla(Qsci.QsciScintilla):  # TODO: Maybe qutepart is better?
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

        font = self.font()
        font.setFamily('Courier')
        font.setPointSize(11)

        bgColor = QtGui.QColor('#32414B')
        #self.setMarginBackgroundColor(0, bgColor)

        fgColor = QtGui.QColor('#F0F0F0')
        strColor = QtGui.QColor('#AD80F3')

        lexer = Qsci.QsciLexerPython()
        lexer.setFont(font)
        lexer.setDefaultFont(font)
        #lexer.setPaper(bgColor)
        #lexer.setDefaultPaper(bgColor)
        #lexer.setColor(fgColor, Qsci.QsciLexerPython.Default)
        #lexer.setColor(fgColor, Qsci.QsciLexerPython.Identifier)
        #lexer.setColor(strColor, Qsci.QsciLexerPython.SingleQuotedString)
        #lexer.setColor(strColor, Qsci.QsciLexerPython.SingleQuotedFString)
        #lexer.setColor(strColor, Qsci.QsciLexerPython.DoubleQuotedString)
        #lexer.setColor(strColor, Qsci.QsciLexerPython.DoubleQuotedFString)
        #lexer.setDefaultColor(fgColor)
        self.setLexer(lexer)

        api = Qsci.QsciAPIs(lexer)
        api.load(os.path.join(os.path.dirname(PyQt5.__file__), 'Qt/qsci/api/python/Python-3.7.api'))
        api.prepare()
        self.setAutoCompletionThreshold(1)
        self.setAutoCompletionSource(Qsci.QsciScintilla.AcsAPIs)
        self.setCallTipsStyle(Qsci.QsciScintilla.CallTipsContext)


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
