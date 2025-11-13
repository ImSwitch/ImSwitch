import pyqtgraph as pg
from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools as guitools
from .ScanWidgetBase import SuperScanWidget


class ScanWidgetMoNaLISA(SuperScanWidget):

    sigContLaserPulsesToggled = QtCore.Signal(bool)  # (enabled)
    sigUpdateBeadRecCenter = QtCore.Signal(int,int) # (y,x)
    sigShowBeadRecCenterCross = QtCore.Signal(bool)
    sigAutoAxialToggled = QtCore.Signal(bool)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.digModWarning = QtWidgets.QMessageBox()
        self.digModWarning.setInformativeText(
            "You need to be in digital laser modulation and external "
            "frame-trigger acquisition mode")

        self.seqTimePar = QtWidgets.QLineEdit('1')  # ms

        self.scanPar = {
                        'seqTime': self.seqTimePar
                        }

        self.pxParameters = {}

        self.scanRadio = QtWidgets.QRadioButton('Scan')
        self.scanRadio.setChecked(True)
        self.contLaserPulsesRadio = QtWidgets.QRadioButton('Cont. Laser Pulses')

        self.graph = GraphFrame()
        self.graph.setEnabled(False)
        self.graph.setFixedHeight(128)

        # Connect signals
        self.contLaserPulsesRadio.toggled.connect(self.sigContLaserPulsesToggled)
        self.seqTimePar.textChanged.connect(self.sigSeqTimeParChanged)

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
            sizePar = QtWidgets.QLineEdit('0.0')
            self.scanPar['size' + positionerName] = sizePar
            stepSizePar = QtWidgets.QLineEdit('0.0')
            self.scanPar['stepSize' + positionerName] = stepSizePar
            numPixelsPar = QtWidgets.QLineEdit('5')
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
        dwellLabel = QtWidgets.QLabel('Dwell (ms):')
        dwellLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.grid.addWidget(dwellLabel, currentRow, 5)
        self.grid.addWidget(self.seqTimePar, currentRow, 6)
        currentRow+=1

        # Automatic XZ/YZ scan
        AxialLabel = QtWidgets.QLabel('Axial Scan')
        self.AutoXZScanBox = QtWidgets.QCheckBox('XZ')
        self.AutoYZScanBox = QtWidgets.QCheckBox('YZ')
        self.AutoXZScanBox.stateChanged.connect(self.toggleAxial)
        self.AutoYZScanBox.stateChanged.connect(self.toggleAxial)
        
        self.axialZlabel = QtWidgets.QLabel('Z')
        self.axialSizePar = QtWidgets.QLineEdit('0.0')
        self.scanPar['sizeAxial'] = self.axialSizePar
        self.axialStepSizePar = QtWidgets.QLineEdit('0.0')
        self.scanPar['stepSizeAxial'] = self.axialStepSizePar
        self.axialNumPixelsPar = QtWidgets.QLineEdit('5')
        self.axialNumPixelsPar.setEnabled(False)
        self.scanPar['pixelsAxial'] = self.axialNumPixelsPar
        self.axialCenterPar = QtWidgets.QLineEdit('0')
        self.scanPar['centerAxial'] = self.axialCenterPar
        
        for key in ['size','stepSize','pixels','center']:
            self.scanPar[key + 'Axial'].textChanged.connect(self.sigStageParChanged)

        self.axialMenuLabel = QtWidgets.QLabel('Center localization: ')
        self.axialMenu = QtWidgets.QComboBox()
        self.axialMenu.addItem("Manual")
        self.axialMenu.addItem("Maxima")
        self.axialMenu.addItem("Minima")
        self.centerLabel = QtWidgets.QLabel('Center Coordinates') 
        self.showCenterBox = QtWidgets.QCheckBox('Show')
        self.xCenterLabel = QtWidgets.QLabel('X') 
        self.yCenterLabel = QtWidgets.QLabel('Y')
        self.xCenterEdit = QtWidgets.QLineEdit('0')       
        self.yCenterEdit = QtWidgets.QLineEdit('0')
        
        self.axialMenu.currentIndexChanged.connect(self.axialMenuChanged)
        self.xCenterEdit.textChanged.connect(self.centerCoordChanged)
        self.yCenterEdit.textChanged.connect(self.centerCoordChanged)
        self.showCenterBox.stateChanged.connect(
            lambda state: self.sigShowBeadRecCenterCross.emit(bool(state))
        )
        
        currentRow+=1

        # layout
        self.grid.addWidget(AxialLabel,currentRow,0)
        self.grid.addWidget(self.AutoXZScanBox,currentRow,1)
        self.grid.addWidget(self.AutoYZScanBox,currentRow,2)
        self.grid.addWidget(self.axialMenuLabel,currentRow,3,QtCore.Qt.AlignRight)
        self.grid.addWidget(self.axialMenu,currentRow,4)
        currentRow+=1
        self.grid.addWidget(self.axialZlabel,currentRow,0)
        self.grid.addWidget(self.axialSizePar,currentRow,1)
        self.grid.addWidget(self.axialStepSizePar,currentRow,2)
        self.grid.addWidget(self.axialNumPixelsPar,currentRow,3)
        self.grid.addWidget(self.axialCenterPar,currentRow,4)

        # xycoord center grid layout
        centergrid = QtWidgets.QGridLayout()
        centergrid.addWidget(self.centerLabel,0,0,1,3,QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        centergrid.addWidget(self.showCenterBox,0,3,1,1,QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        centergrid.addWidget(self.xCenterLabel,1,0)
        centergrid.addWidget(self.xCenterEdit,1,1)
        centergrid.addWidget(self.yCenterLabel,1,2)
        centergrid.addWidget(self.yCenterEdit,1,3)
        self.xycoord = QtWidgets.QWidget()
        self.xycoord.setLayout(centergrid)  # Set the QGridLayout on it

        self.grid.addWidget(self.xycoord,currentRow-1,5,2,2,QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        
        self.setAxialGroupVisibility(state=False)   



        # Add space item to make the grid look nicer
        self.grid.addItem(
            QtWidgets.QSpacerItem(40, 40,
                                  QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed),
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

        # Add pulse graph
        self.grid.addWidget(self.graph, graphRow, 3, currentRow - graphRow, 5)

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

    def plotSignalGraph(self, areas, signals, colors, sampleRate):
        if len(areas) != len(signals) or len(signals) != len(colors):
            raise ValueError('Arguments "areas", "signals" and "colors" must be of equal length')

        self.graph.plot.clear()
        for i in range(len(areas)):
            self.graph.plot.plot(areas[i], signals[i], pen=pg.mkPen(colors[i]))

        self.graph.plot.setYRange(-0.1, 1.1)
        self.graph.plot.getAxis('bottom').setScale(1000 / sampleRate)

        
    def setAxialGroupVisibility(self,state:bool):
        list = [self.axialMenuLabel,self.axialSizePar,self.axialNumPixelsPar,self.xycoord,
                self.axialStepSizePar,self.axialCenterPar,self.axialMenu,self.axialZlabel]
        if state:
            for elem in list:
                elem.show()
        else:
            for elem in list:
                elem.hide()

    def toggleAxial(self):
        state1 = self.AutoXZScanBox.isChecked()
        state2 = self.AutoYZScanBox.isChecked()
        self.setAxialGroupVisibility(state=(state1 or state2))
        self.sigAutoAxialToggled.emit(state1 or state2)
        self.sigShowBeadRecCenterCross.emit((state1 or state2) and self.showCenterBox.isChecked())
    
    def axialMenuChanged(self):
        if self.axialMenu.currentText() in ["Minima","Maxima"]:
            self.xCenterEdit.setEnabled(False)
            self.yCenterEdit.setEnabled(False)
        elif self.axialMenu.currentText() in ["Manual"]:
            self.xCenterEdit.setEnabled(True)
            self.yCenterEdit.setEnabled(True)
            self.centerCoordChanged()
    
    def centerCoordChanged(self):
        y = self.yCenterEdit.text()
        x = self.xCenterEdit.text()
        if y != "" and x != "":
            self.sigUpdateBeadRecCenter.emit(int(y),int(x))

class GraphFrame(pg.GraphicsLayoutWidget):
    """Creates the plot that plots the preview of the pulses."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plot = self.addPlot(row=1, col=0)


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
