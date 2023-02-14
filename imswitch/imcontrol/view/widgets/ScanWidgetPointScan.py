from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools as guitools
from .ScanWidgetBase import SuperScanWidget


class ScanWidgetPointScan(SuperScanWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.seqTimePar = QtWidgets.QLineEdit('0.02')  # ms
        self.phaseDelayPar = QtWidgets.QLineEdit('100')  # samples
        #self.extraLaserOnPar = QtWidgets.QLineEdit('10')  # samples

        self.scanPar = {
                        'seqTime': self.seqTimePar,
                        'phaseDelay': self.phaseDelayPar
                        }

        self.ttlParameters = {}

        # Connect signals
        self.seqTimePar.textChanged.connect(self.sigSeqTimeParChanged)
        self.phaseDelayPar.textChanged.connect(self.sigStageParChanged)
        #self.extraLaserOnPar.textChanged.connect(self.sigStageParChanged)  # for debugging

    def initControls(self, positionerNames, TTLDeviceNames):
        currentRow = 0
        self.scanDims = list(positionerNames)
        self.scanDims.append('None')

        # Add general buttons
        self.grid.addWidget(self.loadScanBtn, currentRow, 0)
        self.grid.addWidget(self.saveScanBtn, currentRow, 1)
        self.grid.addItem(
            QtWidgets.QSpacerItem(40, 20,
                                  QtWidgets.QSizePolicy.Expanding,
                                  QtWidgets.QSizePolicy.Minimum),
            currentRow, 2, 1, 3
        )
        self.grid.addWidget(self.repeatBox, currentRow, 5)
        self.grid.addWidget(self.scanButton, currentRow, 6)
        currentRow += 1

        # Add space item to make the grid look nicer
        self.grid.addItem(
            QtWidgets.QSpacerItem(20, 40,
                                  QtWidgets.QSizePolicy.Minimum,
                                  QtWidgets.QSizePolicy.Expanding),
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
            if 'mock' in positionerName.lower():
                stepSizePar.setText('-')
                stepSizePar.setEnabled(False)
            self.scanPar['stepSize' + positionerName] = stepSizePar
            numPixelsPar = QtWidgets.QLineEdit('50')
            numPixelsPar.setEnabled(False)
            self.scanPar['pixels' + positionerName] = numPixelsPar
            centerPar = QtWidgets.QLineEdit('0')
            self.scanPar['center' + positionerName] = centerPar
            if 'mock' in positionerName.lower():
                centerPar.setText('-')
                centerPar.setEnabled(False)
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
            scanDimPar.setCurrentIndex(index if index < 2 else self.scanDims.index('None'))
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
        self.grid.addWidget(QtWidgets.QLabel('Dwell time (ms):'), currentRow, 5)
        self.grid.addWidget(self.seqTimePar, currentRow, 6)

        currentRow += 1
        
        # Add detection phase delay parameter
        self.grid.addWidget(QtWidgets.QLabel('Phase delay (samples):'), currentRow, 5)
        self.grid.addWidget(self.phaseDelayPar, currentRow, 6)

        #currentRow += 1
        
        # Add detection phase delay parameter
        #self.grid.addWidget(QtWidgets.QLabel('Extra laser on (samples):'), currentRow, 5)
        #self.grid.addWidget(self.extraLaserOnPar, currentRow, 6)

        # Add space item to make the grid look nicer
        self.grid.addItem(
            QtWidgets.QSpacerItem(20, 40,
                                  QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding),
            currentRow, 0, 1, -1
        )
        currentRow += 1

        # TTL param labels
        sequenceLabel = QtWidgets.QLabel('Sequence (h#,l#,...)')
        sequenceLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.grid.addWidget(sequenceLabel, currentRow, 1)
        sequenceAxisLabel = QtWidgets.QLabel('Axis')
        sequenceAxisLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.grid.addWidget(sequenceAxisLabel, currentRow, 2)
        currentRow += 1

        for deviceName in TTLDeviceNames:
            # TTL sequence param
            self.grid.addWidget(QtWidgets.QLabel(deviceName), currentRow, 0)
            self.ttlParameters['seq' + deviceName] = QtWidgets.QLineEdit('l1')
            self.grid.addWidget(self.ttlParameters['seq' + deviceName], currentRow, 1)

            # TTL sequence axis param
            ttlAxisPar = QtWidgets.QComboBox()
            ttlAxisPar.addItems(self.scanDims)
            ttlAxisPar.setCurrentIndex(self.scanDims.index('None'))
            self.ttlParameters['seqAxis' + deviceName] = ttlAxisPar
            self.grid.addWidget(ttlAxisPar, currentRow, 2)

            currentRow += 1

            # Connect signals
            self.ttlParameters['seq' + deviceName].textChanged.connect(self.sigSignalParChanged)
            self.ttlParameters['seqAxis' + deviceName].currentIndexChanged.connect(self.sigSignalParChanged)
        
        # Set grid layout options
        self.grid.setColumnMinimumWidth(6, 90)

    def getScanStepSize(self, positionerName):
        if self.scanPar['stepSize' + positionerName].isEnabled():
            return float(self.scanPar['stepSize' + positionerName].text())
        else:
            return float(1)

    def getScanCenterPos(self, positionerName):
        if self.scanPar['center' + positionerName].isEnabled():
            return float(self.scanPar['center' + positionerName].text())
        else:
            return float(0)

    def getTTLIncluded(self, deviceName):
        return (self.ttlParameters['seq' + deviceName].text() != '')

    def getTTLSequence(self, deviceName):
        return self.ttlParameters['seq' + deviceName].text()

    def getTTLSequenceAxis(self, deviceName):
        if self.ttlParameters['seqAxis' + deviceName].currentText() == 'None':
            return 'None'
        return self.ttlParameters['seqAxis' + deviceName].currentText()

    def getSeqTimePar(self):
        return float(self.seqTimePar.text()) / 1000

    def getPhaseDelayPar(self):
        return float(self.phaseDelayPar.text())

    #def getExtraLaserOnPar(self):
    #    return float(self.extraLaserOnPar.text())

    def setScanPixels(self, positionerName, pixels):
        txt = str(pixels) if pixels > 1 else '-'
        self.scanPar['pixels' + positionerName].setText(txt)

    def setTTLSequences(self, deviceName, sequence):
        self.ttlParameters['seq' + deviceName].setText(sequence)

    def setTTLSequenceAxis(self, deviceName, axis):
        idx = self.ttlParameters['seqAxis' + deviceName].findText(axis)
        if idx >= 0:
            self.ttlParameters['seqAxis' + deviceName].setCurrentIndex(idx)

    def unsetTTL(self, deviceName):
        self.ttlParameters['seq' + deviceName].setText('')

    def setSeqTimePar(self, seqTimePar):
        self.seqTimePar.setText(str(round(float(1000 * seqTimePar), 3)))

    def setPhaseDelayPar(self, phaseDelayPar):
        self.phaseDelayPar.setText(str(round(int(phaseDelayPar))))


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
