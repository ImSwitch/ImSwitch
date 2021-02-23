import os
import time

from PyQt5 import QtCore, QtWidgets

from imcontrol.view import guitools as guitools
from .basewidgets import Widget


class RecordingWidget(Widget):
    """ Widget to control image or sequence recording.
    Recording only possible when liveview active. """

    sigDetectorChanged = QtCore.Signal()
    sigOpenRecFolderClicked = QtCore.Signal()
    sigSpecFileToggled = QtCore.Signal(bool)  # (enabled)
    sigSnapRequested = QtCore.Signal()
    sigRecToggled = QtCore.Signal(bool)  # (enabled)
    sigSpecFramesPicked = QtCore.Signal()
    sigSpecTimePicked = QtCore.Signal()
    sigScanOncePicked = QtCore.Signal()
    sigScanLapsePicked = QtCore.Signal()
    sigDimLapsePicked = QtCore.Signal()
    sigUntilStopPicked = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        recTitle = QtWidgets.QLabel('<h2><strong>Recording settings</strong></h2>')
        recTitle.setTextFormat(QtCore.Qt.RichText)

        # Detector list
        self.detectorList = QtWidgets.QComboBox()

        # Folder and filename fields
        baseOutputFolder = self._defaultPreset.recording.outputFolder
        if self._defaultPreset.recording.includeDateInOutputFolder:
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
        self.dimLapse = QtWidgets.QRadioButton('3D-lapse')
        self.currentSlice = QtWidgets.QLabel('0 / ')
        self.totalSlices = QtWidgets.QLineEdit('5')
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

        self.saveModeLabel = QtWidgets.QLabel('<strong>Save mode:</strong>')
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

        recGrid = QtWidgets.QGridLayout()
        self.setLayout(recGrid)

        recGrid.addWidget(recTitle, 0, 0, 1, 3)
        recGrid.addWidget(QtWidgets.QLabel('Detector to capture'), 1, 0)
        recGrid.addWidget(self.detectorList, 1, 1, 1, 4)
        recGrid.addWidget(QtWidgets.QLabel('Folder'), 2, 0)
        recGrid.addWidget(self.folderEdit, 2, 1, 1, 3)
        recGrid.addWidget(self.openFolderButton, 2, 4)
        recGrid.addWidget(self.filenameEdit, 3, 1, 1, 3)

        recGrid.addWidget(self.specifyfile, 3, 0)

        recGrid.addWidget(modeTitle, 4, 0)
        recGrid.addWidget(self.specifyFrames, 5, 0, 1, 5)
        recGrid.addWidget(self.currentFrame, 5, 1)
        recGrid.addWidget(self.numExpositionsEdit, 5, 2)
        recGrid.addWidget(self.specifyTime, 6, 0, 1, 5)
        recGrid.addWidget(self.currentTime, 6, 1)
        recGrid.addWidget(self.timeToRec, 6, 2)
        recGrid.addWidget(self.tRemaining, 6, 3, 1, 2)
        recGrid.addWidget(self.recScanOnceBtn, 7, 0, 1, 5)
        recGrid.addWidget(self.recScanLapseBtn, 8, 0, 1, 5)
        recGrid.addWidget(self.currentLapse, 8, 1)
        recGrid.addWidget(self.timeLapseEdit, 8, 2)
        recGrid.addWidget(self.freqLabel, 8, 3)
        recGrid.addWidget(self.freqEdit, 8, 4)
        recGrid.addWidget(self.dimLapse, 9, 0, 1, 5)
        recGrid.addWidget(self.currentSlice, 9, 1)
        recGrid.addWidget(self.totalSlices, 9, 2)
        recGrid.addWidget(self.stepSizeLabel, 9, 3)
        recGrid.addWidget(self.stepSizeEdit, 9, 4)
        recGrid.addWidget(self.untilSTOPbtn, 10, 0, 1, -1)
        recGrid.addWidget(self.saveModeLabel, 12, 0)
        recGrid.addWidget(self.saveModeList, 12, 1, 1, -1)
        recGrid.addWidget(buttonWidget, 13, 0, 1, -1)

        # Initial condition of fields and checkboxes.
        self.writable = True
        self.readyToRecord = False
        self.filenameEdit.setEnabled(False)
        self.untilSTOPbtn.setChecked(True)

        # Connect signals
        self.detectorList.currentIndexChanged.connect(self.sigDetectorChanged)
        self.openFolderButton.clicked.connect(self.sigOpenRecFolderClicked)
        self.specifyfile.toggled.connect(self.sigSpecFileToggled)
        self.snapTIFFButton.clicked.connect(self.sigSnapRequested)
        self.recButton.toggled.connect(self.sigRecToggled)
        self.specifyFrames.clicked.connect(self.sigSpecFramesPicked)
        self.specifyTime.clicked.connect(self.sigSpecTimePicked)
        self.recScanOnceBtn.clicked.connect(self.sigScanOncePicked)
        self.recScanLapseBtn.clicked.connect(self.sigScanLapsePicked)
        self.dimLapse.clicked.connect(self.sigDimLapsePicked)
        self.untilSTOPbtn.clicked.connect(self.sigUntilStopPicked)

    def getDetectorsToCapture(self):
        """ Returns a list of which detectors the user has selected to be
        captured. Note: If "current detector at start" is selected, this
        returns -1, and if "all detectors" is selected, this returns -2. """
        return self.detectorList.itemData(self.detectorList.currentIndex())

    def getSaveMode(self):
        return self.saveModeList.currentIndex() + 1

    def getRecFolder(self):
        return self.folderEdit.text()

    def getCustomFilename(self):
        return self.filenameEdit.text() if self.specifyfile.isChecked() else None

    def getNumExpositions(self):
        return int(self.numExpositionsEdit.text())

    def getTimeToRec(self):
        return float(self.timeToRec.text())

    def getTimelapseTime(self):
        return int(self.timeLapseEdit.text())

    def getTimelapseFreq(self):
        return float(self.freqEdit.text())

    def getDimlapseSlices(self):
        return int(self.totalSlices.text())

    def getDimlapseStepSize(self):
        return float(self.stepSizeEdit.text())

    def setDetectorList(self, detectorModels):
        if len(detectorModels) > 1:
            self.detectorList.addItem('Current detector at start', -1)
            self.detectorList.addItem('All detectors', -2)

        for detectorName, detectorModel in detectorModels.items():
            self.detectorList.addItem(f'{detectorModel} ({detectorName})', detectorName)

    def setSaveMode(self, saveMode):
        self.saveModeList.setCurrentIndex(saveMode - 1)

    def setSaveModeVisible(self, value):
        self.saveModeList.setVisible(value)

    def setCustomFilenameEnabled(self, enabled):
        """ Enables the ability to type a specific filename for the data to. """
        self.filenameEdit.setEnabled(enabled)
        self.filenameEdit.setText('Filename' if enabled else 'Current time')

    def setEnabledParams(self, numExpositions=False, timeToRec=False,
                         timelapseTime=False, timelapseFreq=False,
                         dimlapseSlices=False, dimlapseStepSize=False):
        self.numExpositionsEdit.setEnabled(numExpositions)
        self.timeToRec.setEnabled(timeToRec)
        self.timeLapseEdit.setEnabled(timelapseTime)
        self.freqEdit.setEnabled(timelapseFreq)
        self.totalSlices.setEnabled(dimlapseSlices)
        self.stepSizeEdit.setEnabled(dimlapseStepSize)

    def setSpecifyFramesAllowed(self, allowed):
        self.specifyFrames.setEnabled(allowed)
        if not allowed and self.specifyFrames.isChecked():
            self.untilSTOPbtn.setChecked(True)

    def setRecButtonChecked(self, checked):
        self.recButton.setChecked(checked)

    def updateRecFrameNum(self, frameNum):
        self.currentFrame.setText(str(frameNum) + ' /')

    def updateRecTime(self, recTime):
        self.currentTime.setText(str(recTime) + ' /')

    def updateRecLapseNum(self, lapseNum):
        self.currentLapse.setText(str(lapseNum) + ' /')

    def updateRecSliceNum(self, sliceNum):
        self.currentSlice.setText(str(sliceNum) + ' /')