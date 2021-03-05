import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

from imcontrol.view import guitools as guitools
from .basewidgets import Widget


class ScanWidget(Widget):
    ''' Widget containing scanner interface and beadscan reconstruction.
            This class uses the classes GraphFrame, MultipleScanWidget and IllumImageWidget'''

    sigSaveScanClicked = QtCore.Signal()
    sigLoadScanClicked = QtCore.Signal()
    sigRunScanClicked = QtCore.Signal()
    sigContLaserPulsesToggled = QtCore.Signal(bool)  # (enabled)
    sigSeqTimeParChanged = QtCore.Signal()
    sigSignalParChanged = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.scanInLiveviewWar = QtWidgets.QMessageBox()
        self.scanInLiveviewWar.setInformativeText(
            "You need to be in liveview to scan")

        self.digModWarning = QtWidgets.QMessageBox()
        self.digModWarning.setInformativeText(
            "You need to be in digital laser modulation and external "
            "frame-trigger acquisition mode")

        self.saveScanBtn = guitools.BetterPushButton('Save Scan')
        self.loadScanBtn = guitools.BetterPushButton('Load Scan')

        self.sampleRateEdit = QtWidgets.QLineEdit()

        self.seqTimePar = QtWidgets.QLineEdit(self._defaultPreset.scan.dwellTime)  # ms
        self.nrFramesPar = QtWidgets.QLabel()
        self.scanDuration = 0
        self.scanDurationLabel = QtWidgets.QLabel(str(self.scanDuration))

        self.scanDims = []

        self.scanPar = {'seqTime': self.seqTimePar}

        self.pxParameters = {}
        self.pxParValues = {}

        self.scanRadio = QtWidgets.QRadioButton('Scan')
        self.scanRadio.setChecked(True)
        self.contLaserPulsesRadio = QtWidgets.QRadioButton('Cont. Laser Pulses')

        self.scanButton = guitools.BetterPushButton('Scan', 96)
        self.scanButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)

        self.continuousCheck = QtWidgets.QCheckBox('Repeat')

        self.sampleRate = 10000
        self.graph = GraphFrame()
        self.graph.setEnabled(False)
        self.graph.plot.getAxis('bottom').setScale(1000 / self.sampleRate)
        self.graph.setFixedHeight(100)

        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        # Connect signals
        self.saveScanBtn.clicked.connect(self.sigSaveScanClicked)
        self.loadScanBtn.clicked.connect(self.sigLoadScanClicked)
        self.scanButton.clicked.connect(self.sigRunScanClicked)
        self.seqTimePar.textChanged.connect(self.sigSeqTimeParChanged)
        self.contLaserPulsesRadio.toggled.connect(self.sigContLaserPulsesToggled)

    def initControls(self, positionerNames, TTLDeviceNames):
        self.scanDims = positionerNames

        self.grid.addWidget(self.loadScanBtn, 0, 0)
        self.grid.addWidget(self.saveScanBtn, 0, 1)
        self.grid.addWidget(self.scanRadio, 0, 2)
        self.grid.addWidget(self.contLaserPulsesRadio, 0, 3)
        self.grid.addItem(QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum), 0, 6)
        self.grid.addWidget(self.scanButton, 1, 7, len(positionerNames), 1)
        self.grid.addWidget(self.continuousCheck, 0, 7)

        currentRow = 1

        positionerPresets = self._defaultPreset.scan.positioners
        for index, positionerName in enumerate(positionerNames):
            positionerPreset = (
                positionerPresets[positionerName] if positionerName in positionerPresets
                else guitools.ScanPresetPositioner()
            )

            sizePar = QtWidgets.QLineEdit(str(positionerPreset.size))
            self.scanPar['size' + positionerName] = sizePar
            stepSizePar = QtWidgets.QLineEdit(str(positionerPreset.stepSize))
            self.scanPar['stepSize' + positionerName] = stepSizePar

            self.grid.addWidget(QtWidgets.QLabel('Size {} (µm):'.format(positionerName)), currentRow, 0)
            self.grid.addWidget(sizePar, currentRow, 1)
            self.grid.addWidget(QtWidgets.QLabel('Step {} (µm):'.format(positionerName)), currentRow, 2)
            self.grid.addWidget(stepSizePar, currentRow, 3)

            dimLabelText = '{}{} dimension:'.format(index + 1, guitools.ordinalSuffix(index + 1))
            self.grid.addWidget(QtWidgets.QLabel(dimLabelText), currentRow, 4)
            scanDimPar = QtWidgets.QComboBox()
            scanDimPar.addItems(self.scanDims)
            scanDimPar.setCurrentIndex(index)
            self.scanPar['scanDim' + str(index)] = scanDimPar
            self.grid.addWidget(scanDimPar, currentRow, 5)

            currentRow += 1

        self.grid.addWidget(QtWidgets.QLabel('Number of frames:'), currentRow, 4)
        self.grid.addWidget(self.nrFramesPar, currentRow, 5)
        currentRow += 1

        self.grid.addWidget(QtWidgets.QLabel('Dwell time (ms):'), currentRow, 0)
        self.grid.addWidget(self.seqTimePar, currentRow, 1)
        self.grid.addWidget(QtWidgets.QLabel('Total time (s):'), currentRow, 2)
        self.grid.addWidget(self.scanDurationLabel, currentRow, 3)
        currentRow += 1

        self.grid.addWidget(QtWidgets.QLabel('Start (ms):'), currentRow, 1)
        self.grid.addWidget(QtWidgets.QLabel('End (ms):'), currentRow, 2)
        self.grid.addWidget(self.graph, currentRow, 3, 1 + len(TTLDeviceNames), 5)
        currentRow += 1

        pulsePresets = self._defaultPreset.scan.pulses
        for deviceName in TTLDeviceNames:
            pulsePreset = (pulsePresets[deviceName] if deviceName in pulsePresets
                           else guitools.ScanPresetTTL())

            self.grid.addWidget(QtWidgets.QLabel(deviceName), currentRow, 0)
            self.pxParameters['sta' + deviceName] = QtWidgets.QLineEdit(pulsePreset.start)
            self.pxParameters['end' + deviceName] = QtWidgets.QLineEdit(pulsePreset.end)
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

    def continuousCheckEnabled(self):
        return self.continuousCheck.isChecked()

    def getScanDim(self, index):
        return self.scanPar['scanDim' + str(index)].currentText()

    def getScanSize(self, positionerName):
        return float(self.scanPar['size' + positionerName].text())

    def getScanStepSize(self, positionerName):
        return float(self.scanPar['stepSize' + positionerName].text())

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

    def setScanButtonChecked(self, checked):
        self.scanButton.setChecked(checked)

    def setScanDim(self, index, positionerName):
        scanDimPar = self.scanPar['scanDim' + str(index)]
        scanDimPar.setCurrentIndex(scanDimPar.findText(positionerName))

    def setScanSize(self, positionerName, size):
        self.scanPar['size' + positionerName].setText(str(round(size, 3)))

    def setScanStepSize(self, positionerName, stepSize):
        self.scanPar['stepSize' + positionerName].setText(str(round(stepSize, 3)))

    def setTTLStarts(self, deviceName, starts):
        self.pxParameters['sta' + deviceName].setText(
            ','.join(map(lambda s: str(round(1000 * s, 3)), starts))
        )

    def setTTLEnds(self, deviceName, ends):
        self.pxParameters['end' + deviceName].setText(
            ','.join(map(lambda e: str(round(1000 * e, 3)), ends))
        )

    def setSeqTimePar(self, seqTimePar):
        self.seqTimePar.setText(str(round(float(1000 * seqTimePar), 3)))

    def setScanDimEnabled(self, index, enabled):
        self.scanPar['scanDim' + str(index)].setEnabled(enabled)

    def setScanSizeEnabled(self, positionerName, enabled):
        self.scanPar['size' + positionerName].setEnabled(enabled)

    def setScanStepSizeEnabled(self, positionerName, enabled):
        self.scanPar['stepSize' + positionerName].setEnabled(enabled)

    def plotSignalGraph(self, areas, signals, colors):
        if len(areas) != len(signals) or len(signals) != len(colors):
            raise ValueError('Arguments "areas", "signals" and "colors" must be of equal length')

        self.graph.plot.clear()
        for i in range(len(areas)):
            self.graph.plot.plot(areas[i], signals[i],  pen=pg.mkPen(colors[i]))

        self.graph.plot.setYRange(-0.1, 1.1)


class GraphFrame(pg.GraphicsWindow):
    """Creates the plot that plots the preview of the pulses."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plot = self.addPlot(row=1, col=0)