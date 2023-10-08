import os
import time

from qtpy import QtCore, QtWidgets

from imswitch.imcommon.model import dirtools
from imswitch.imcommon.model.shortcut import shortcut
from imswitch.imcommon.view.guitools import PositionsTableDialog, askForFilePath, showWarningMessage
from imswitch.imcontrol.view import guitools
from .basewidgets import Widget


class PycroManagerWidget(Widget):
    """ Widget to control image or sequence recording. """

    sigOpenRecFolderClicked = QtCore.Signal()
    sigSpecFileToggled = QtCore.Signal(bool)  # (enabled)

    sigSpecFramesPicked = QtCore.Signal()
    sigSpecTimePicked = QtCore.Signal()
    sigSpecZStackPicked = QtCore.Signal()
    sigSpecXYListPicked = QtCore.Signal()
    sigSpecXYZListPicked = QtCore.Signal()
    
    sigSnapSaveModeChanged = QtCore.Signal()
    sigRecSaveModeChanged = QtCore.Signal()

    sigSnapRequested = QtCore.Signal()
    sigRecToggled = QtCore.Signal(bool)  # (enabled)
    
    sigTableDataDumped = QtCore.Signal(str, list) # ("XY"/"XYZ", tableData)
    sigTableLoaded = QtCore.Signal(str, str) # ("XY"/"XYZ", filePath)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Table widgets; they need to remain alive otherwise
        # the widget automatically closes.
        self.XYTableWidget = None
        self.XYZTableWidget = None
        
        # Graphical elements
        recTitle = QtWidgets.QLabel('<h2><strong>PycroManager acquisition engine</strong></h2>')
        recTitle.setTextFormat(QtCore.Qt.RichText)
        
        # Folder and filename fields
        baseOutputFolder = self._options.recording.outputFolder
        if self._options.recording.includeDateInOutputFolder:
            self.initialDir = os.path.join(baseOutputFolder, time.strftime('%Y-%m-%d'))
        else:
            self.initialDir = baseOutputFolder
        
        self.folderEdit = QtWidgets.QLineEdit(self.initialDir)
        self.openFolderButton = guitools.BetterPushButton('Open')
        self.specifyfile = QtWidgets.QCheckBox('Specify file name')
        self.filenameEdit = QtWidgets.QLineEdit('Current time')
        
        # Snap and recording buttons
        self.snapTIFFButton = guitools.BetterPushButton('Snap')
        self.snapTIFFButton.setStyleSheet("font-size:16px")
        self.snapTIFFButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                          QtWidgets.QSizePolicy.Expanding)
        self.recButton = guitools.BetterPushButton('REC')
        self.recButton.setStyleSheet("font-size:16px")
        self.recButton.setCheckable(True)
        self.recButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                     QtWidgets.QSizePolicy.Expanding)

        # Number of frames and measurement timing
        modeTitle = QtWidgets.QLabel('<strong>Recording mode</strong>')
        modeTitle.setTextFormat(QtCore.Qt.RichText)

        self.specifyFrames = QtWidgets.QRadioButton('Number of frames')
        self.currentFrame = QtWidgets.QLabel('0 /')
        self.currentFrame.setAlignment((QtCore.Qt.AlignRight |
                                        QtCore.Qt.AlignVCenter))
        self.numExpositionsEdit = QtWidgets.QLineEdit('100')
        
        self.specifyZStack = QtWidgets.QRadioButton('Z-stack (µm)')
        self.startZLabel = QtWidgets.QLabel('Start: ')
        self.startZLabel.setAlignment((QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter))
        self.startZEdit = QtWidgets.QLineEdit('0')
        
        self.endZLabel = QtWidgets.QLabel('End: ')
        self.endZLabel.setAlignment((QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter))
        self.endZEdit = QtWidgets.QLineEdit('10')
        
        self.stepZLabel = QtWidgets.QLabel('Step: ')
        self.stepZLabel.setAlignment((QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter))
        self.stepZEdit = QtWidgets.QLineEdit('1')
        
        self.specifyXYList = QtWidgets.QRadioButton('XY coordinates list')
        self.openXYListTableButton = guitools.BetterPushButton('Make list...')
        self.loadXYListButton = guitools.BetterPushButton('Load list...')
        
        self.specifyXYZList = QtWidgets.QRadioButton('XYZ coordinates list')
        self.openXYZListTableButton = guitools.BetterPushButton('Make list...')
        self.loadXYZListButton = guitools.BetterPushButton('Load list...')

        self.specifyTime = QtWidgets.QRadioButton('Time (s)')
        self.currentTime = QtWidgets.QLabel('0 / ')
        self.currentTime.setAlignment((QtCore.Qt.AlignRight |
                                       QtCore.Qt.AlignVCenter))
        self.timeToRec = QtWidgets.QLineEdit('1')

        self.snapSaveModeLabel = QtWidgets.QLabel('<strong>Snap save mode:</strong>')
        self.snapSaveModeList = QtWidgets.QComboBox()
        self.snapSaveModeList.addItems(['Save on disk',
                                        'Save to image display',
                                        'Save on disk and to image display'])

        self.recSaveModeLabel = QtWidgets.QLabel('<strong>Rec save mode:</strong>')
        self.recSaveModeList = QtWidgets.QComboBox()
        self.recSaveModeList.addItems(['Save on disk',
                                       'Save in memory for reconstruction',
                                       'Save on disk and keep in memory'])
        
        # Add items to GridLayout
        buttonWidget = QtWidgets.QWidget()
        buttonGrid = QtWidgets.QGridLayout()
        buttonWidget.setLayout(buttonGrid)
        buttonGrid.addWidget(self.snapTIFFButton, 0, 0)
        buttonWidget.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                   QtWidgets.QSizePolicy.Expanding)
        buttonGrid.addWidget(self.recButton, 0, 2)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        recGrid = QtWidgets.QGridLayout()
        gridRow = 0

        recGrid.addWidget(recTitle, gridRow, 0, 1, 3)
        gridRow += 1

        recGrid.addWidget(QtWidgets.QLabel('Folder'), gridRow, 0)
        recGrid.addWidget(self.folderEdit, gridRow, 1, 1, 5)
        recGrid.addWidget(self.openFolderButton, gridRow, 6)
        gridRow += 1

        recGrid.addWidget(self.filenameEdit, gridRow, 1, 1, 5)
        recGrid.addWidget(self.specifyfile, gridRow, 0)
        gridRow += 1

        recGrid.addWidget(modeTitle, gridRow, 0)
        gridRow += 1

        recGrid.addWidget(self.specifyFrames, gridRow, 0, 1, 6)
        recGrid.addWidget(self.currentFrame, gridRow, 1)
        recGrid.addWidget(self.numExpositionsEdit, gridRow, 2, 1, 5)
        gridRow += 1

        recGrid.addWidget(self.specifyTime, gridRow, 0, 1, 6)
        recGrid.addWidget(self.currentTime, gridRow, 1)
        recGrid.addWidget(self.timeToRec, gridRow, 2, 1, 5)
        gridRow += 1
        
        recGrid.addWidget(self.specifyZStack, gridRow, 0, 1, 6)
        recGrid.addWidget(self.startZLabel, gridRow, 1)
        recGrid.addWidget(self.startZEdit, gridRow, 2)
        recGrid.addWidget(self.endZLabel, gridRow, 3)
        recGrid.addWidget(self.endZEdit, gridRow, 4)
        recGrid.addWidget(self.stepZLabel, gridRow, 5)
        recGrid.addWidget(self.stepZEdit, gridRow, 6)
        gridRow += 1
        
        recGrid.addWidget(self.specifyXYList, gridRow, 0, 1, 6)
        recGrid.addWidget(self.openXYListTableButton, gridRow, 2, 1, 3)
        recGrid.addWidget(self.loadXYListButton, gridRow, 5, 1, 2)
        gridRow += 1
        
        recGrid.addWidget(self.specifyXYZList, gridRow, 0, 1, 6)
        recGrid.addWidget(self.openXYZListTableButton, gridRow, 2, 1, 3)
        recGrid.addWidget(self.loadXYZListButton, gridRow, 5, 1, 2)
        gridRow += 1

        recGrid.addWidget(self.snapSaveModeLabel, gridRow, 0)
        recGrid.addWidget(self.snapSaveModeList, gridRow, 1, 1, -1)
        gridRow += 1

        recGrid.addWidget(self.recSaveModeLabel, gridRow, 0)
        recGrid.addWidget(self.recSaveModeList, gridRow, 1, 1, -1)
        gridRow += 1

        self.recGridContainer = QtWidgets.QWidget()
        self.recGridContainer.setLayout(recGrid)

        layout.addWidget(self.recGridContainer)
        layout.addWidget(buttonWidget)
        
        # Initial condition of fields and checkboxes.
        self.filenameEdit.setEnabled(False)

        # Connect signals
        self.openFolderButton.clicked.connect(self.sigOpenRecFolderClicked)
        self.specifyfile.toggled.connect(self.sigSpecFileToggled)

        self.specifyFrames.clicked.connect(self.sigSpecFramesPicked)
        self.specifyTime.clicked.connect(self.sigSpecTimePicked)
        self.specifyZStack.clicked.connect(self.sigSpecZStackPicked)
        self.specifyXYList.clicked.connect(self.sigSpecXYListPicked)
        self.specifyXYZList.clicked.connect(self.sigSpecXYZListPicked)
        
        self.openXYListTableButton.clicked.connect(self.openXYTableWidget)
        self.loadXYListButton.clicked.connect(self.loadXYTableData)
        
        self.openXYZListTableButton.clicked.connect(self.openXYZTableWidget)
        self.loadXYZListButton.clicked.connect(self.loadXYZTableData)
        
        self.snapSaveModeList.currentIndexChanged.connect(self.sigSnapSaveModeChanged)
        self.recSaveModeList.currentIndexChanged.connect(self.sigRecSaveModeChanged)

        self.snapTIFFButton.clicked.connect(self.sigSnapRequested)
        self.recButton.toggled.connect(self.sigRecToggled)
    
    def openXYTableWidget(self):
        """ Opens a dialog to specify the XY coordinates list. """
        self.XYtableWidget = PositionsTableDialog(
            title="XY coordinates table",
            default=0.0, 
            coordinates=["X", "Y"]
        )
        self.XYtableWidget.sigTableDataDumped.connect(lambda tableData: 
            self.sigTableDataDumped.emit("XY", tableData)
        )
        self.XYtableWidget.show()
    
    def loadXYTableData(self):
        fileFilter = "JSON (*.json);;CSV (*.csv)"
        filePath = askForFilePath(self, 
                                caption="Load XY coordinates table", 
                                defaultFolder=dirtools.UserFileDirs.Root,
                                nameFilter=fileFilter)
        if filePath is not None:
            self.sigTableLoaded.emit("XY", filePath)
    
    def openXYZTableWidget(self):
        """ Opens a dialog to specify the XYZ coordinates list. """
        self.XYZtableWidget = PositionsTableDialog(
            title="XYZ coordinates table",
            default=0.0, 
            coordinates=["X", "Y", "Z"]
        )
        self.XYtableWidget.sigTableDataDumped.connect(lambda tableData: 
            self.sigTableDataDumped.emit("XYZ", tableData)
        )
        self.XYZtableWidget.show()
    
    def loadXYZTableData(self):
        fileFilter = "JSON (*.json);;CSV (*.csv)"
        filePath = askForFilePath(self, 
                                caption="Load XYZ coordinates table", 
                                defaultFolder=dirtools.UserFileDirs.Root,
                                nameFilter=fileFilter)
        if filePath is not None:
            self.sigTableLoaded.emit("XYZ", filePath)
    
    def displayFailedJSONLoad(self, errorMsg: str):
        showWarningMessage(self, "Failed to load JSON file", errorMsg)

    def getSnapSaveMode(self):
        return self.snapSaveModeList.currentIndex() + 1

    def getRecSaveMode(self):
        return self.recSaveModeList.currentIndex() + 1

    def getRecFolder(self):
        return self.folderEdit.text()

    def getCustomFilename(self):
        return self.filenameEdit.text() if self.specifyfile.isChecked() else None

    def isRecButtonChecked(self):
        return self.recButton.isChecked()

    def getNumExpositions(self):
        return int(float(self.numExpositionsEdit.text()))

    def getTimeToRec(self):
        return float(self.timeToRec.text())

    def setSnapSaveMode(self, saveMode):
        self.snapSaveModeList.setCurrentIndex(saveMode - 1)

    def setSnapSaveModeVisible(self, value):
        self.snapSaveModeLabel.setVisible(value)
        self.snapSaveModeList.setVisible(value)

    def setRecSaveMode(self, saveMode):
        self.recSaveModeList.setCurrentIndex(saveMode - 1)

    def setRecSaveModeVisible(self, value):
        self.recSaveModeLabel.setVisible(value)
        self.recSaveModeList.setVisible(value)

    def setCustomFilenameEnabled(self, enabled):
        """ Enables the ability to type a specific filename for the data to. """
        self.filenameEdit.setEnabled(enabled)
        self.filenameEdit.setText('Filename' if enabled else 'Current time')

    def setCustomFilename(self, filename):
        self.setCustomFilenameEnabled(True)
        self.filenameEdit.setText(filename)

    def setRecFolder(self, folderPath):
        self.folderEdit.setText(folderPath)

    def checkSpecFrames(self):
        self.specifyFrames.setChecked(True)

    def checkSpecTime(self):
        self.specifyTime.setChecked(True)
    
    def checkSpecZStack(self):
        self.specifyZStack.setChecked(True)
    
    def checkXYList(self):
        self.specifyXYList.setChecked(True)
    
    def checkXYZList(self):
        self.specifyXYZList.setChecked(True)

    def setFieldsEnabled(self, enabled):
        self.recGridContainer.setEnabled(enabled)

    def setEnabledParams(self, specFrames=False, specTime=False, specZStack=False, specXYList=False, specXYZList=False):
        self.numExpositionsEdit.setEnabled(specFrames)
        self.timeToRec.setEnabled(specTime)
        self.startZEdit.setEnabled(specZStack)
        self.endZEdit.setEnabled(specZStack)
        self.stepZEdit.setEnabled(specZStack)
        self.openXYListTableButton.setEnabled(specXYList)
        self.loadXYListButton.setEnabled(specXYList)
        self.openXYZListTableButton.setEnabled(specXYZList)
        self.loadXYZListButton.setEnabled(specXYZList)

    def setRecButtonChecked(self, checked):
        self.recButton.setChecked(checked)

    def setNumExpositions(self, numExpositions):
        self.numExpositionsEdit.setText(str(numExpositions))

    def setTimeToRec(self, secondsToRec):
        self.numExpositionsEdit.setText(str(secondsToRec))

    def updateRecFrameNum(self, recFrameNum):
        self.currentFrame.setText(str(recFrameNum) + ' /')

    def updateRecTime(self, recTime):
        self.currentTime.setText(str(recTime) + ' /')

    @shortcut('Ctrl+R', "Record")
    def toggleRecButton(self):
        self.recButton.toggle()


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
