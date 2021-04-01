# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 17:08:54 2020

@author: _Xavi
"""
import os

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

import constants
import view.guitools as guitools
from .basewidgets import Widget


class ScanWidget(Widget):
    ''' Widget containing scanner interface and beadscan reconstruction.
            This class uses the classes GraphFrame, MultipleScanWidget and IllumImageWidget'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.scanDir = os.path.join(constants.rootFolderPath, 'scans')

        if not os.path.exists(self.scanDir):
            os.makedirs(self.scanDir)

        self.scanInLiveviewWar = QtGui.QMessageBox()
        self.scanInLiveviewWar.setInformativeText(
            "You need to be in liveview to scan")

        self.digModWarning = QtGui.QMessageBox()
        self.digModWarning.setInformativeText(
            "You need to be in digital laser modulation and external "
            "frame-trigger acquisition mode")

        self.saveScanBtn = guitools.BetterPushButton('Save Scan')
        self.loadScanBtn = guitools.BetterPushButton('Load Scan')

        self.sampleRateEdit = QtGui.QLineEdit()

        #self.seqTimePar = QtGui.QLineEdit(self._defaultPreset.scan.dwellTime)  # ms
        self.seqTimePar = QtGui.QLineEdit('0.01')  # ms
        self.scanDuration = 0
        self.scanDurationLabel = QtGui.QLabel(str(self.scanDuration))

        self.scanDims = []

        self.scanPar = {'seqTime': self.seqTimePar}

        self.pxParameters = {}
        self.pxParValues = {}

        self.scanRadio = QtGui.QRadioButton('Scan')
        self.scanRadio.setChecked(True)
        self.contLaserPulsesRadio = QtGui.QRadioButton('Cont. Laser Pulses')

        self.scanButton = guitools.BetterPushButton('Scan', 96)
        self.scanButton.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)

        self.continuousCheck = QtGui.QCheckBox('Repeat')

        self.sampleRate = 10000
        self.graph = GraphFrame()
        self.graph.setEnabled(False)
        self.graph.plot.getAxis('bottom').setScale(1000 / self.sampleRate)
        self.graph.setFixedHeight(130)

        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)

    def initControls(self, positionerInfos, TTLDeviceInfos):
        self.scanDims = list()
        for index, (positionerName, positionerInfo) in enumerate(positionerInfos.items()):
            if positionerInfo.managerProperties['scanner']:
                self.scanDims.append(positionerName)
        self.scanDims.append('None')

        currentRow = 0

        # add general buttons to grid
        self.grid.addWidget(self.loadScanBtn, currentRow, 0)
        self.grid.addWidget(self.saveScanBtn, currentRow, 1)
        self.grid.addWidget(self.scanRadio, currentRow, 2)
        self.grid.addWidget(self.contLaserPulsesRadio, currentRow, 3)
        self.grid.addWidget(self.continuousCheck, currentRow, 7)
        currentRow += 1

        # add space item to make the grid look nicer
        self.grid.addItem(QtGui.QSpacerItem(10, 30, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum), currentRow, 0, 1, 7)
        currentRow += 1

        # add param labels to grid
        sizeLabel = QtGui.QLabel('Size (µm)')
        stepLabel = QtGui.QLabel('Step size (µm)')
        pixelsLabel = QtGui.QLabel('Pixels (#)')
        centerLabel = QtGui.QLabel('Center (µm)')
        scandimLabel = QtGui.QLabel('Scan dim')
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

        positionerPresets = self._defaultPreset.scan.positioners
        for index, (positionerName, positionerInfo) in enumerate(positionerInfos.items()):
            if positionerInfo.managerProperties['scanner']:
                positionerPreset = (
                    positionerPresets[positionerName] if positionerName in positionerPresets
                    else guitools.ScanPresetPositioner()
                )

                # create params for inputs
                sizePar = QtGui.QLineEdit(str(positionerPreset.size))
                self.scanPar['size' + positionerName] = sizePar
                stepSizePar = QtGui.QLineEdit(str(positionerPreset.stepSize))
                self.scanPar['stepSize' + positionerName] = stepSizePar
                numPixelsPar = QtGui.QLineEdit(str(round(float(positionerPreset.size)/float(positionerPreset.stepSize))))
                numPixelsPar.setReadOnly(True)
                self.scanPar['pixels' + positionerName] = numPixelsPar
                centerPar = QtGui.QLineEdit(str(positionerPreset.center))
                self.scanPar['center' + positionerName] = centerPar

                # add positioner name to grid
                self.grid.addWidget(QtGui.QLabel('{}'.format(positionerName)), currentRow, 0)

                # add params to grid
                self.grid.addWidget(sizePar, currentRow, 1)
                self.grid.addWidget(stepSizePar, currentRow, 2)
                self.grid.addWidget(numPixelsPar, currentRow, 3)
                self.grid.addWidget(centerPar, currentRow, 4)

                # create scandim label and param and add to grid
                dimLabelText = '{}{}'.format(index + 1, guitools.ordinalSuffix(index + 1))
                dimlabel = QtGui.QLabel(dimLabelText)
                dimlabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                self.grid.addWidget(dimlabel, currentRow, 5)
                scanDimPar = QtGui.QComboBox()
                scanDimPar.addItems(self.scanDims)
                scanDimPar.setCurrentIndex(index)
                self.scanPar['scanDim' + str(index)] = scanDimPar
                self.grid.addWidget(scanDimPar, currentRow, 6)

                currentRow += 1

        # add scan button to grid, covering in height all positioner rows
        self.grid.addWidget(self.scanButton, 3, 7, currentRow-2, 1)

        # add dwell time to grid
        self.grid.addWidget(QtGui.QLabel('Dwell (ms)'), currentRow, 5)
        self.grid.addWidget(self.seqTimePar, currentRow, 6)
        currentRow += 1

        # add space item to make the grid look nicer
        self.grid.addItem(QtGui.QSpacerItem(10, 30, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum), currentRow, 0, 1, 7)
        currentRow += 1
        graphRow = currentRow

        # add TTL pulse start and end labels to grid
        startLabel = QtGui.QLabel('Start (lines)')
        endLabel = QtGui.QLabel('End (lines)')
        startLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        endLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.grid.addWidget(startLabel, currentRow, 1)
        self.grid.addWidget(endLabel, currentRow, 2)
        currentRow += 1

        pulsePresets = self._defaultPreset.scan.pulses
        for deviceName in TTLDeviceInfos.keys():
            pulsePreset = (pulsePresets[deviceName] if deviceName in pulsePresets
                           else guitools.ScanPresetTTL())
            # add TTL pulse params to grid
            self.grid.addWidget(QtGui.QLabel(deviceName), currentRow, 0)
            self.pxParameters['sta' + deviceName] = QtGui.QLineEdit(pulsePreset.start)
            self.pxParameters['end' + deviceName] = QtGui.QLineEdit(pulsePreset.end)
            self.grid.addWidget(self.pxParameters['sta' + deviceName], currentRow, 1)
            self.grid.addWidget(self.pxParameters['end' + deviceName], currentRow, 2)
            currentRow += 1
        
        # add pulse graph to grid
        self.grid.addWidget(self.graph, graphRow, 3, currentRow-graphRow, 4)


class GraphFrame(pg.GraphicsWindow):
    """Creates the plot that plots the preview of the pulses."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plot = self.addPlot(row=1, col=0)
