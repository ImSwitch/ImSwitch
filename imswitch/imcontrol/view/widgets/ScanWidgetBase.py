import pyqtgraph as pg
from qtpy import QtCore, QtWidgets
from abc import abstractmethod

from imswitch.imcontrol.view import guitools as guitools
from imswitch.imcommon.model import initLogger
from .basewidgets import Widget


class SuperScanWidget(Widget):
    """ Widget containing scanner interface and beadscan reconstruction.
            This class uses the classes GraphFrame, MultipleScanWidget and IllumImageWidget"""

    sigSaveScanClicked = QtCore.Signal()
    sigLoadScanClicked = QtCore.Signal()
    sigRunScanClicked = QtCore.Signal()
    sigSeqTimeParChanged = QtCore.Signal()
    sigStageParChanged = QtCore.Signal()
    sigSignalParChanged = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self, instanceName='ScanWidget')

        self.setMinimumHeight(200)

        self.scanInLiveviewWar = QtWidgets.QMessageBox()
        self.scanInLiveviewWar.setInformativeText(
            "You need to be in liveview to scan")

        self.saveScanBtn = guitools.BetterPushButton('Save Scan')
        self.loadScanBtn = guitools.BetterPushButton('Load Scan')

        self.scanDims = []

        self.scanButton = guitools.BetterPushButton('Run Scan')

        self.repeatBox = QtWidgets.QCheckBox('Repeat')

        self.scrollContainer = QtWidgets.QGridLayout()
        self.scrollContainer.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.scrollContainer)

        self.grid = QtWidgets.QGridLayout()
        self.gridContainer = QtWidgets.QWidget()
        self.gridContainer.setLayout(self.grid)

        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollArea.setWidget(self.gridContainer)
        self.scrollArea.setWidgetResizable(True)
        self.scrollContainer.addWidget(self.scrollArea)
        self.gridContainer.installEventFilter(self)

        # Connect signals
        self.saveScanBtn.clicked.connect(self.sigSaveScanClicked)
        self.loadScanBtn.clicked.connect(self.sigLoadScanClicked)
        self.scanButton.clicked.connect(self.sigRunScanClicked)

    @abstractmethod
    def initControls(self, positionerNames, TTLDeviceNames, TTLTimeUnits):
        pass

    @abstractmethod
    def getTTLIncluded(self, deviceName):
        pass

    def repeatEnabled(self):
        return self.repeatBox.isChecked()

    def getScanDim(self, index):
        return self.scanPar['scanDim' + str(index)].currentText()

    def getScanSize(self, positionerName):
        return float(self.scanPar['size' + positionerName].text())

    def getScanStepSize(self, positionerName):
        return float(self.scanPar['stepSize' + positionerName].text())

    def getScanCenterPos(self, positionerName):
        return float(self.scanPar['center' + positionerName].text())

    @abstractmethod
    def getSeqTimePar(self):
        pass

    def setRepeatEnabled(self, enabled):
        self.repeatBox.setChecked(enabled)

    def setScanButtonChecked(self, checked):
        self.scanButton.setEnabled(not checked)
        self.scanButton.setCheckable(checked)
        self.scanButton.setChecked(checked)

    def setScanDim(self, index, positionerName):
        scanDimPar = self.scanPar['scanDim' + str(index)]
        scanDimPar.setCurrentIndex(scanDimPar.findText(positionerName))

    def setScanSize(self, positionerName, size):
        self.scanPar['size' + positionerName].setText(str(round(size, 3)))

    def setScanStepSize(self, positionerName, stepSize):
        self.scanPar['stepSize' + positionerName].setText(str(round(stepSize, 3)))

    def setScanCenterPos(self, positionerName, centerPos):
        self.scanPar['center' + positionerName].setText(str(round(centerPos, 3)))

    def setScanPixels(self, positionerName, pixels):
        self.scanPar['pixels' + positionerName].setText(str(pixels))

    @abstractmethod
    def unsetTTL(self, deviceName):
        pass

    def setScanDimEnabled(self, index, enabled):
        self.scanPar['scanDim' + str(index)].setEnabled(enabled)

    def setScanSizeEnabled(self, positionerName, enabled):
        self.scanPar['size' + positionerName].setEnabled(enabled)

    def setScanStepSizeEnabled(self, positionerName, enabled):
        self.scanPar['stepSize' + positionerName].setEnabled(enabled)

    def setScanCenterPosEnabled(self, positionerName, enabled):
        self.scanPar['center' + positionerName].setEnabled(enabled)

    def eventFilter(self, source, event):
        if source is self.gridContainer and event.type() == QtCore.QEvent.Resize:
            # Set correct minimum width (otherwise things can go outside the widget because of the
            # scroll area)
            width = self.gridContainer.minimumSizeHint().width() \
                    + self.scrollArea.verticalScrollBar().width()
            self.scrollArea.setMinimumWidth(width)
            self.setMinimumWidth(width)

        return False


class ScanWidgetBase(SuperScanWidget):

    sigContLaserPulsesToggled = QtCore.Signal(bool)  # (enabled)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.seqTimePar = QtWidgets.QLineEdit('1')  # ms

        self.scanPar = {
                        'seqTime': self.seqTimePar
                        }

        self.pxParameters = {}

        self.scanRadio = QtWidgets.QRadioButton('Scan')
        self.scanRadio.setChecked(True)
        self.contLaserPulsesRadio = QtWidgets.QRadioButton('Cont. Laser Pulses')

        # Connect signals
        self.seqTimePar.textChanged.connect(self.sigSeqTimeParChanged)
        self.contLaserPulsesRadio.toggled.connect(self.sigContLaserPulsesToggled)

    def initControls(self, positionerNames, TTLDeviceNames, TTLTimeUnits):
        currentRow = 0
        self.scanDims = list(positionerNames)
        self._logger.debug(positionerNames)
        self._logger.debug(type(positionerNames))
        self.scanDims.append('None')

        # Add general buttons
        self.grid.addWidget(self.loadScanBtn, currentRow, 0)
        self.grid.addWidget(self.saveScanBtn, currentRow, 1)
        self.grid.addWidget(self.scanRadio, currentRow, 2)
        self.grid.addWidget(self.contLaserPulsesRadio, currentRow, 3)
        self.grid.addItem(
            QtWidgets.QSpacerItem(40, 20,
                                  QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum),
            currentRow, 4
        )
        self.grid.addWidget(self.repeatBox, currentRow, 5)
        self.grid.addWidget(self.scanButton, currentRow, 6)
        currentRow += 1

        # Add space item to make the grid look nicer
        self.grid.addItem(
            QtWidgets.QSpacerItem(20, 40,
                                  QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding),
            currentRow, 0, 1, -1
        )
        currentRow += 1

        # Add param labels
        sizeLabel = QtWidgets.QLabel('Size (µm)')
        stepLabel = QtWidgets.QLabel('Step size (µm)')
        pixelsLabel = QtWidgets.QLabel('Pixels (#)')
        centerLabel = QtWidgets.QLabel('Center (µm)')
        scandimLabel = QtWidgets.QLabel('Scan dim')
        sizeLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        stepLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        pixelsLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        centerLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        scandimLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.grid.addWidget(sizeLabel, currentRow, 1)
        self.grid.addWidget(stepLabel, currentRow, 2)
        self.grid.addWidget(pixelsLabel, currentRow, 3)
        self.grid.addWidget(centerLabel, currentRow, 4)
        self.grid.addWidget(scandimLabel, currentRow, 6)
        currentRow += 1

        for index, positionerName in enumerate(positionerNames):
            # Scan params
            sizePar = QtWidgets.QLineEdit('5')
            self.scanPar['size' + positionerName] = sizePar
            stepSizePar = QtWidgets.QLineEdit('0.1')
            self.scanPar['stepSize' + positionerName] = stepSizePar
            numPixelsPar = QtWidgets.QLineEdit('50')
            numPixelsPar.setEnabled(False)
            self.scanPar['pixels' + positionerName] = numPixelsPar
            centerPar = QtWidgets.QLineEdit('0')
            self.scanPar['center' + positionerName] = centerPar
            self.grid.addWidget(QtWidgets.QLabel(positionerName), currentRow, 0)
            self.grid.addWidget(sizePar, currentRow, 1)
            self.grid.addWidget(stepSizePar, currentRow, 2)
            self.grid.addWidget(numPixelsPar, currentRow, 3)
            self.grid.addWidget(centerPar, currentRow, 4)

            # Scan dimension label and picker
            dimlabel = QtWidgets.QLabel(
                f'{index + 1}{guitools.ordinalSuffix(index + 1)} dimension:'
            )
            dimlabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.grid.addWidget(dimlabel, currentRow, 5)
            scanDimPar = QtWidgets.QComboBox()
            scanDimPar.addItems(self.scanDims)
            scanDimPar.setCurrentIndex(index)
            self.scanPar['scanDim' + str(index)] = scanDimPar
            self.grid.addWidget(scanDimPar, currentRow, 6)

            currentRow += 1

            # Connect signals
            self.scanPar['size' + positionerName].textChanged.connect(self.sigStageParChanged)
            self.scanPar['stepSize' + positionerName].textChanged.connect(self.sigStageParChanged)
            self.scanPar['pixels' + positionerName].textChanged.connect(self.sigStageParChanged)
            self.scanPar['center' + positionerName].textChanged.connect(self.sigStageParChanged)
            self.scanPar['scanDim' + str(index)].currentIndexChanged.connect(
                self.sigStageParChanged
            )

        currentRow += 1

        # Add dwell time parameter
        self.grid.addWidget(QtWidgets.QLabel('Dwell (ms):'), currentRow, 5)
        self.grid.addWidget(self.seqTimePar, currentRow, 6)

        currentRow += 1

        # Add space item to make the grid look nicer
        self.grid.addItem(
            QtWidgets.QSpacerItem(20, 40,
                                  QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding),
            currentRow, 0, 1, -1
        )
        currentRow += 1
        graphRow = currentRow

        # TTL pulse param labels
        startLabel = QtWidgets.QLabel(f'Start ({TTLTimeUnits})')
        endLabel = QtWidgets.QLabel(f'End ({TTLTimeUnits})')
        startLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        endLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.grid.addWidget(startLabel, currentRow, 1)
        self.grid.addWidget(endLabel, currentRow, 2)
        currentRow += 1

        for deviceName in TTLDeviceNames:
            # TTL pulse params
            self.grid.addWidget(QtWidgets.QLabel(deviceName), currentRow, 0)
            self.pxParameters['sta' + deviceName] = QtWidgets.QLineEdit('')
            self.pxParameters['end' + deviceName] = QtWidgets.QLineEdit('')
            self.grid.addWidget(self.pxParameters['sta' + deviceName], currentRow, 1)
            self.grid.addWidget(self.pxParameters['end' + deviceName], currentRow, 2)
            currentRow += 1

            # Connect signals
            self.pxParameters['sta' + deviceName].textChanged.connect(self.sigSignalParChanged)
            self.pxParameters['end' + deviceName].textChanged.connect(self.sigSignalParChanged)

    def isScanMode(self):
        return self.scanRadio.isChecked()

    def isContLaserMode(self):
        return self.contLaserPulsesRadio.isChecked()

    def getTTLIncluded(self, deviceName):
        return (self.pxParameters['sta' + deviceName].text() != '' and
                self.pxParameters['end' + deviceName].text() != '')

    def getTTLStarts(self, deviceName):
        return list(map(lambda s: float(s) / 1000 if s else None,
                        self.pxParameters['sta' + deviceName].text().split(',')))

    def getTTLEnds(self, deviceName):
        return list(map(lambda e: float(e) / 1000 if e else None,
                        self.pxParameters['end' + deviceName].text().split(',')))

    def getSeqTimePar(self):
        return float(self.seqTimePar.text()) / 1000

    def setScanMode(self):
        self.scanRadio.setChecked(True)

    def setContLaserMode(self):
        self.contLaserPulsesRadio.setChecked(True)

    def setTTLStarts(self, deviceName, starts):
        self.pxParameters['sta' + deviceName].setText(
            ','.join(map(lambda s: str(round(1000 * s, 3)), starts))
        )

    def setTTLEnds(self, deviceName, ends):
        self.pxParameters['end' + deviceName].setText(
            ','.join(map(lambda e: str(round(1000 * e, 3)), ends))
        )

    def unsetTTL(self, deviceName):
        self.pxParameters['sta' + deviceName].setText('')
        self.pxParameters['end' + deviceName].setText('')

    def setSeqTimePar(self, seqTimePar):
        self.seqTimePar.setText(str(round(float(1000 * seqTimePar), 3)))



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
