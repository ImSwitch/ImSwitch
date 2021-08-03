import os
import time

from qtpy import QtCore, QtWidgets

from imswitch.imcommon.model.shortcut import shortcut
from imswitch.imcontrol.view import guitools
from .basewidgets import Widget


class RecordingWidget(Widget):
    """ Widget to control image or sequence recording.
    Recording only possible when liveview active. """

    sigDetectorModeChanged = QtCore.Signal()
    sigDetectorSpecificChanged = QtCore.Signal()
    sigOpenRecFolderClicked = QtCore.Signal()
    sigSpecFileToggled = QtCore.Signal(bool)  # (enabled)
    sigSnapRequested = QtCore.Signal()
    sigRecToggled = QtCore.Signal(bool)  # (enabled)
    sigSpecFramesPicked = QtCore.Signal()
    sigSpecTimePicked = QtCore.Signal()
    sigScanOncePicked = QtCore.Signal()
    sigScanLapsePicked = QtCore.Signal()
    sigUntilStopPicked = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        recTitle = QtWidgets.QLabel('<h2><strong>Recording settings</strong></h2>')
        recTitle.setTextFormat(QtCore.Qt.RichText)

        # Detector list
        self.detectorModeList = QtWidgets.QComboBox()
        self.detectorList = guitools.CheckableComboBox()
        self.detectorList.setItemTypeName(singular='detector', plural='detectors')
        self.detectorList.setVisible(False)

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
        self.specifyTime = QtWidgets.QRadioButton('Time (s)')
        self.recScanOnceBtn = QtWidgets.QRadioButton('Scan once')
        self.recScanLapseBtn = QtWidgets.QRadioButton('Time-lapse scan')
        self.currentLapse = QtWidgets.QLabel('0 / ')
        self.timeLapseEdit = QtWidgets.QLineEdit('5')
        self.freqLabel = QtWidgets.QLabel('Freq [s]')
        self.freqEdit = QtWidgets.QLineEdit('0')
        self.stepSizeLabel = QtWidgets.QLabel('Step size [um]')
        self.stepSizeEdit = QtWidgets.QLineEdit('0.05')
        self.untilSTOPbtn = QtWidgets.QRadioButton('Run until STOP')
        self.timeToRec = QtWidgets.QLineEdit('1')
        self.currentTime = QtWidgets.QLabel('0 / ')
        self.currentTime.setAlignment((QtCore.Qt.AlignRight |
                                       QtCore.Qt.AlignVCenter))
        self.currentFrame = QtWidgets.QLabel('0 /')
        self.currentFrame.setAlignment((QtCore.Qt.AlignRight |
                                        QtCore.Qt.AlignVCenter))
        self.numExpositionsEdit = QtWidgets.QLineEdit('100')
        self.tRemaining = QtWidgets.QLabel()
        self.tRemaining.setAlignment((QtCore.Qt.AlignCenter |
                                      QtCore.Qt.AlignVCenter))

        self.saveModeLabel = QtWidgets.QLabel('<strong>Rec save mode:</strong>')
        self.saveModeList = QtWidgets.QComboBox()
        self.saveModeList.addItems(['Save on disk',
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

        recGrid.addWidget(QtWidgets.QLabel('Detector to capture'), gridRow, 0)
        recGrid.addWidget(self.detectorModeList, gridRow, 1, 1, 4)
        gridRow += 1

        recGrid.addWidget(self.detectorList, gridRow, 1, 1, 4)
        gridRow += 1

        recGrid.addWidget(QtWidgets.QLabel('Folder'), gridRow, 0)
        recGrid.addWidget(self.folderEdit, gridRow, 1, 1, 3)
        recGrid.addWidget(self.openFolderButton, gridRow, 4)
        gridRow += 1

        recGrid.addWidget(self.filenameEdit, gridRow, 1, 1, 3)
        recGrid.addWidget(self.specifyfile, gridRow, 0)
        gridRow += 1

        recGrid.addWidget(modeTitle, gridRow, 0)
        gridRow += 1

        recGrid.addWidget(self.specifyFrames, gridRow, 0, 1, 5)
        recGrid.addWidget(self.currentFrame, gridRow, 1)
        recGrid.addWidget(self.numExpositionsEdit, gridRow, 2)
        gridRow += 1

        recGrid.addWidget(self.specifyTime, gridRow, 0, 1, 5)
        recGrid.addWidget(self.currentTime, gridRow, 1)
        recGrid.addWidget(self.timeToRec, gridRow, 2)
        recGrid.addWidget(self.tRemaining, gridRow, 3, 1, 2)
        gridRow += 1

        recGrid.addWidget(self.recScanOnceBtn, gridRow, 0, 1, 5)
        gridRow += 1

        recGrid.addWidget(self.recScanLapseBtn, gridRow, 0, 1, 5)
        recGrid.addWidget(self.currentLapse, gridRow, 1)
        recGrid.addWidget(self.timeLapseEdit, gridRow, 2)
        recGrid.addWidget(self.freqLabel, gridRow, 3)
        recGrid.addWidget(self.freqEdit, gridRow, 4)
        gridRow += 1

        recGrid.addWidget(self.untilSTOPbtn, gridRow, 0, 1, -1)
        gridRow += 1

        recGrid.addWidget(self.saveModeLabel, gridRow, 0)
        recGrid.addWidget(self.saveModeList, gridRow, 1, 1, -1)
        gridRow += 1

        self.recGridContainer = QtWidgets.QWidget()
        self.recGridContainer.setLayout(recGrid)

        layout.addWidget(self.recGridContainer)
        layout.addWidget(buttonWidget)

        # Initial condition of fields and checkboxes.
        self.writable = True
        self.readyToRecord = False
        self.filenameEdit.setEnabled(False)
        self.untilSTOPbtn.setChecked(True)

        # Connect signals
        self.detectorModeList.currentIndexChanged.connect(self.sigDetectorModeChanged)
        self.detectorList.sigCheckedChanged.connect(self.sigDetectorSpecificChanged)
        self.openFolderButton.clicked.connect(self.sigOpenRecFolderClicked)
        self.specifyfile.toggled.connect(self.sigSpecFileToggled)
        self.snapTIFFButton.clicked.connect(self.sigSnapRequested)
        self.recButton.toggled.connect(self.sigRecToggled)
        self.specifyFrames.clicked.connect(self.sigSpecFramesPicked)
        self.specifyTime.clicked.connect(self.sigSpecTimePicked)
        self.recScanOnceBtn.clicked.connect(self.sigScanOncePicked)
        self.recScanLapseBtn.clicked.connect(self.sigScanLapsePicked)
        self.untilSTOPbtn.clicked.connect(self.sigUntilStopPicked)

    def getDetectorMode(self):
        """ Returns -1 if "current detector at start" is selected, -2 if "all
        acquisition detectors" is selected, and -3 if "specific detector(s)" is
        selected. """
        return self.detectorModeList.itemData(self.detectorModeList.currentIndex())

    def getSelectedSpecificDetectors(self):
        """ Returns the names of the selected items in the "select specific
        detectors" list. """
        return self.detectorList.getCheckedItems()

    def getSaveMode(self):
        return self.saveModeList.currentIndex() + 1

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

    def getTimelapseTime(self):
        return int(float(self.timeLapseEdit.text()))

    def getTimelapseFreq(self):
        return float(self.freqEdit.text())

    def setDetectorList(self, detectorModels):
        if len(detectorModels) > 1:
            self.detectorModeList.addItem('Current detector at start', -1)
            self.detectorModeList.addItem('All acquisition detectors', -2)
            self.detectorModeList.addItem('Specific detector(s)', -3)

        for detectorName, detectorModel in detectorModels.items():
            self.detectorList.addItem(f'{detectorModel} ({detectorName})', detectorName)

    def setSpecificDetectorListVisible(self, visible):
        """ Sets whether the "select specific detectors" list is visible. """
        self.detectorList.setVisible(visible)

    def setDetectorMode(self, detectorMode):
        """ Sets the detector capture mode. The value -1  corresponds to
        "current detector at start", the value -2 corresponds to "all
        acquisition detectors", and the value -3 corresponds to "specific
        detector(s)". """
        for i in range(self.detectorModeList.count()):
            if self.detectorModeList.itemData(i) == detectorMode:
                self.detectorModeList.setCurrentIndex(i)
                return

    def setSaveMode(self, saveMode):
        self.saveModeList.setCurrentIndex(saveMode - 1)

    def setSaveModeVisible(self, value):
        self.saveModeLabel.setVisible(value)
        self.saveModeList.setVisible(value)

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

    def checkScanOnce(self):
        self.recScanOnceBtn.setChecked(True)

    def checkScanLapse(self):
        self.recScanLapseBtn.setChecked(True)

    def checkUntilStop(self):
        self.untilSTOPbtn.setChecked(True)

    def setFieldsEnabled(self, enabled):
        self.recGridContainer.setEnabled(enabled)

    def setEnabledParams(self, numExpositions=False, timeToRec=False,
                         timelapseTime=False, timelapseFreq=False):
        self.numExpositionsEdit.setEnabled(numExpositions)
        self.timeToRec.setEnabled(timeToRec)
        self.timeLapseEdit.setEnabled(timelapseTime)
        self.freqEdit.setEnabled(timelapseFreq)

    def setRecButtonChecked(self, checked):
        self.recButton.setChecked(checked)

    def setNumExpositions(self, numExpositions):
        self.numExpositionsEdit.setText(str(numExpositions))

    def setTimeToRec(self, secondsToRec):
        self.numExpositionsEdit.setText(str(secondsToRec))

    def setTimelapseTime(self, secondsToRec):
        self.timeLapseEdit.setText(str(secondsToRec))

    def setTimelapseFreq(self, freqSeconds):
        self.freqEdit.setText(str(freqSeconds))

    def updateRecFrameNum(self, recFrameNum):
        self.currentFrame.setText(str(recFrameNum) + ' /')

    def updateRecTime(self, recTime):
        self.currentTime.setText(str(recTime) + ' /')

    def updateRecLapseNum(self, lapseNum):
        self.currentLapse.setText(str(lapseNum) + ' /')

    @shortcut('Ctrl+R', "Record")
    def toggleRecButton(self):
        self.recButton.toggle()


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
