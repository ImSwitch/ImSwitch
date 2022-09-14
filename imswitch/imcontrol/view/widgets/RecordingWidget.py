import os
import time

from qtpy import QtCore, QtWidgets

from imswitch.imcommon.model.shortcut import shortcut
from imswitch.imcontrol.view import guitools
from .basewidgets import Widget


class RecordingWidget(Widget):
    """ Widget to control image or sequence recording. """

    sigDetectorModeChanged = QtCore.Signal()
    sigDetectorSpecificChanged = QtCore.Signal()
    sigOpenRecFolderClicked = QtCore.Signal()
    sigSpecFileToggled = QtCore.Signal(bool)  # (enabled)

    sigSpecFramesPicked = QtCore.Signal()
    sigSpecTimePicked = QtCore.Signal()
    sigScanOncePicked = QtCore.Signal()
    sigScanLapsePicked = QtCore.Signal()
    sigUntilStopPicked = QtCore.Signal()

    sigsaveFormatChanged = QtCore.Signal()
    sigSnapSaveModeChanged = QtCore.Signal()
    sigRecSaveModeChanged = QtCore.Signal()

    sigSnapRequested = QtCore.Signal()
    sigRecToggled = QtCore.Signal(bool)  # (enabled)

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
        self.singleFileMultiDetectorBox = QtWidgets.QCheckBox('Save recordings in a single file')
        self.singleFileMultiDetectorBox.setVisible(False)

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

        self.specifyTime = QtWidgets.QRadioButton('Time (s)')
        self.currentTime = QtWidgets.QLabel('0 / ')
        self.currentTime.setAlignment((QtCore.Qt.AlignRight |
                                       QtCore.Qt.AlignVCenter))
        self.timeToRec = QtWidgets.QLineEdit('1')

        self.recScanOnceBtn = QtWidgets.QRadioButton('Scan once')

        self.recScanLapseBtn = QtWidgets.QRadioButton('Time-lapse scan')
        self.currentLapse = QtWidgets.QLabel('0 / ')
        self.timeLapseEdit = QtWidgets.QLineEdit('5')
        self.freqLabel = QtWidgets.QLabel('Freq [s]')
        self.freqEdit = QtWidgets.QLineEdit('0')
        self.singleFileLapseBox = QtWidgets.QCheckBox('Save all scans in a single file')

        self.untilSTOPbtn = QtWidgets.QRadioButton('Run until STOP')

        self.saveFormatLabel = QtWidgets.QLabel('<strong>File format:</strong>')
        self.saveFormatList = QtWidgets.QComboBox()
        self.saveFormatList.addItems(['HDF5', 'TIFF', "TIFF_Single"])

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

        recGrid.addWidget(QtWidgets.QLabel('Detector(s) to capture'), gridRow, 0)
        recGrid.addWidget(self.detectorModeList, gridRow, 1, 1, 4)
        gridRow += 1
        recGrid.addWidget(self.detectorList, gridRow, 1, 1, 4)
        gridRow += 1
        recGrid.addWidget(self.singleFileMultiDetectorBox, gridRow, 1, 1, 4)
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
        gridRow += 1

        recGrid.addWidget(self.recScanOnceBtn, gridRow, 0, 1, 5)
        gridRow += 1

        recGrid.addWidget(self.recScanLapseBtn, gridRow, 0, 1, 5)
        recGrid.addWidget(self.currentLapse, gridRow, 1)
        recGrid.addWidget(self.timeLapseEdit, gridRow, 2)
        recGrid.addWidget(self.freqLabel, gridRow, 3)
        recGrid.addWidget(self.freqEdit, gridRow, 4)
        gridRow += 1
        recGrid.addWidget(self.singleFileLapseBox, gridRow, 1, 1, -1)
        gridRow += 1

        recGrid.addWidget(self.untilSTOPbtn, gridRow, 0, 1, -1)
        gridRow += 1

        recGrid.addWidget(self.saveFormatLabel, gridRow, 0)
        recGrid.addWidget(self.saveFormatList, gridRow, 1, 1, -1)
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
        self.untilSTOPbtn.setChecked(True)

        # Connect signals
        self.detectorModeList.currentIndexChanged.connect(self.sigDetectorModeChanged)
        self.detectorList.sigCheckedChanged.connect(self.sigDetectorSpecificChanged)
        self.openFolderButton.clicked.connect(self.sigOpenRecFolderClicked)
        self.specifyfile.toggled.connect(self.sigSpecFileToggled)

        self.specifyFrames.clicked.connect(self.sigSpecFramesPicked)
        self.specifyTime.clicked.connect(self.sigSpecTimePicked)
        self.recScanOnceBtn.clicked.connect(self.sigScanOncePicked)
        self.recScanLapseBtn.clicked.connect(self.sigScanLapsePicked)
        self.untilSTOPbtn.clicked.connect(self.sigUntilStopPicked)

        self.saveFormatList.currentIndexChanged.connect(self.sigsaveFormatChanged)
        self.snapSaveModeList.currentIndexChanged.connect(self.sigSnapSaveModeChanged)
        self.recSaveModeList.currentIndexChanged.connect(self.sigRecSaveModeChanged)

        self.snapTIFFButton.clicked.connect(self.sigSnapRequested)
        self.recButton.toggled.connect(self.sigRecToggled)

    def getDetectorMode(self):
        """ Returns -1 if "current detector at start" is selected, -2 if "all
        acquisition detectors" is selected, and -3 if "specific detector(s)" is
        selected. """
        return self.detectorModeList.itemData(self.detectorModeList.currentIndex())

    def getSelectedSpecificDetectors(self):
        """ Returns the names of the selected items in the "select specific
        detectors" list. """
        return self.detectorList.getCheckedItems()

    def getMultiDetectorSingleFile(self):
        return self.singleFileMultiDetectorBox.isChecked()

    def getsaveFormat(self):
        return self.saveFormatList.currentIndex() + 1

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

    def getTimelapseTime(self):
        return int(float(self.timeLapseEdit.text()))

    def getTimelapseFreq(self):
        return float(self.freqEdit.text())

    def getTimelapseSingleFile(self):
        return self.singleFileLapseBox.isChecked()

    def setDetectorList(self, detectorModels):
        self.detectorModeList.addItem('Current detector at start', -1)

        if len(detectorModels) > 1:
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

    def setSelectedSpecificDetectors(self, detectors):
        """ Sets the selected items in the "select specific detectors" list.
        """
        self.detectorList.setCheckedItems(detectors)

    def setMultiDetectorSingleFile(self, singleFile):
        self.singleFileMultiDetectorBox.setChecked(singleFile)

    def setMultiDetectorSingleFileVisible(self, visible):
        self.singleFileMultiDetectorBox.setVisible(visible)

    def setsaveFormat(self, saveMode):
        self.saveFormatList.setCurrentIndex(saveMode - 1)

    def setsaveFormatEnabled(self, value):
        self.saveFormatList.setEnabled(value)

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

    def checkScanOnce(self):
        self.recScanOnceBtn.setChecked(True)

    def checkScanLapse(self):
        self.recScanLapseBtn.setChecked(True)

    def checkUntilStop(self):
        self.untilSTOPbtn.setChecked(True)

    def setFieldsEnabled(self, enabled):
        self.recGridContainer.setEnabled(enabled)

    def setEnabledParams(self, specFrames=False, specTime=False, scanLapse=False):
        self.numExpositionsEdit.setEnabled(specFrames)
        self.timeToRec.setEnabled(specTime)
        self.timeLapseEdit.setEnabled(scanLapse)
        self.freqEdit.setEnabled(scanLapse)
        self.singleFileLapseBox.setEnabled(scanLapse)

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

    def setTimelapseSingleFile(self, singleFile):
        self.singleFileLapseBox.setChecked(singleFile)

    def updateRecFrameNum(self, recFrameNum):
        self.currentFrame.setText(str(recFrameNum) + ' /')

    def updateRecTime(self, recTime):
        self.currentTime.setText(str(recTime) + ' /')

    def updateRecLapseNum(self, lapseNum):
        self.currentLapse.setText(str(lapseNum) + ' /')

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
