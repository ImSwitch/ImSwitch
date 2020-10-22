# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 17:08:54 2020

@author: _Xavi
"""
import os

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui

import constants
from .basewidgets import Widget


class ScanWidget(Widget):
    ''' Widget containing scanner interface and beadscan reconstruction.
            This class uses the classes GraphFrame, MultipleScanWidget and IllumImageWidget'''

    def __init__(self, deviceInfo, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.allDevices = [x[0] for x in deviceInfo]
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

        self.saveScanBtn = QtGui.QPushButton('Save Scan')
        self.loadScanBtn = QtGui.QPushButton('Load Scan')

        self.sampleRateEdit = QtGui.QLineEdit()
        self.sizeXPar = QtGui.QLineEdit('2')
        self.sizeYPar = QtGui.QLineEdit('2')
        self.sizeZPar = QtGui.QLineEdit('10')
        self.seqTimePar = QtGui.QLineEdit('10')  # ms
        self.nrFramesPar = QtGui.QLabel()
        self.scanDuration = 0
        self.scanDurationLabel = QtGui.QLabel(str(self.scanDuration))
        self.stepSizeXPar = QtGui.QLineEdit('0.1')
        self.stepSizeYPar = QtGui.QLineEdit('0.1')
        self.stepSizeZPar = QtGui.QLineEdit('1')

        self.primScanDim = QtGui.QComboBox()
        self.scanDims = ['X', 'Y', 'Z']
        self.primScanDim.addItems(self.scanDims)
        self.primScanDim.setCurrentIndex(0)

        self.secScanDim = QtGui.QComboBox()
        self.secScanDim.addItems(self.scanDims)
        self.secScanDim.setCurrentIndex(1)

        self.thirdScanDim = QtGui.QComboBox()
        self.thirdScanDim.addItems(self.scanDims)
        self.thirdScanDim.setCurrentIndex(2)

        self.scanPar = {'sizeX': self.sizeXPar,
                        'sizeY': self.sizeYPar,
                        'sizeZ': self.sizeZPar,
                        'seqTime': self.seqTimePar,
                        'stepSizeX': self.stepSizeXPar,
                        'stepSizeY': self.stepSizeYPar,
                        'stepSizeZ': self.stepSizeZPar}

        self.pxParameters = dict()
        self.pxParValues = dict()

        for i in range(0, len(self.allDevices)):
            self.pxParameters['sta' + self.allDevices[i]] = QtGui.QLineEdit('0')
            self.pxParameters['end' + self.allDevices[i]] = QtGui.QLineEdit('10')

        self.scanRadio = QtGui.QRadioButton('Scan')
        self.scanRadio.setChecked(True)
        self.contLaserPulsesRadio = QtGui.QRadioButton('Cont. Laser Pulses')
        self.scanButton = QtGui.QPushButton('Scan')
        self.scanning = False

        self.previewButton = QtGui.QPushButton('Plot scan path')
        self.previewButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                         QtGui.QSizePolicy.Expanding)

        self.continuousCheck = QtGui.QCheckBox('Repeat')

        self.sampleRate = 10000
        self.graph = GraphFrame()
        self.graph.plot.getAxis('bottom').setScale(1000 / self.sampleRate)
        self.graph.setFixedHeight(100)

        grid = QtGui.QGridLayout()
        self.setLayout(grid)

        grid.addWidget(self.loadScanBtn, 0, 0)
        grid.addWidget(self.saveScanBtn, 0, 1)
        grid.addWidget(self.scanRadio, 0, 2)
        grid.addWidget(self.contLaserPulsesRadio, 0, 3)  #
        grid.addWidget(self.scanButton, 0, 4, 1, 2)
        grid.addWidget(self.continuousCheck, 0, 6)

        grid.addWidget(QtGui.QLabel('Size X (µm):'), 2, 0)
        grid.addWidget(self.sizeXPar, 2, 1)
        grid.addWidget(QtGui.QLabel('Size Y (µm):'), 3, 0)
        grid.addWidget(self.sizeYPar, 3, 1)
        grid.addWidget(QtGui.QLabel('Size Z (µm):'), 4, 0)
        grid.addWidget(self.sizeZPar, 4, 1)
        grid.addWidget(QtGui.QLabel('Step X (µm):'), 2, 2)
        grid.addWidget(self.stepSizeXPar, 2, 3)
        grid.addWidget(QtGui.QLabel('Step Y (µm):'), 3, 2)
        grid.addWidget(self.stepSizeYPar, 3, 3)
        grid.addWidget(QtGui.QLabel('Step Z (µm):'), 4, 2)
        grid.addWidget(self.stepSizeZPar, 4, 3)

        grid.addWidget(QtGui.QLabel('First dimension:'), 2, 4)
        grid.addWidget(self.primScanDim, 2, 5)
        grid.addWidget(QtGui.QLabel('Second dimension:'), 3, 4)
        grid.addWidget(self.secScanDim, 3, 5)
        grid.addWidget(QtGui.QLabel('Third dimension:'), 4, 4)
        grid.addWidget(self.thirdScanDim, 4, 5)
        grid.addWidget(QtGui.QLabel('Number of frames:'), 5, 4)
        grid.addWidget(self.nrFramesPar, 5, 5)
        grid.addWidget(self.previewButton, 2, 6, 3, 2)

        grid.addWidget(QtGui.QLabel('Dwell time (ms):'), 7, 0)
        grid.addWidget(self.seqTimePar, 7, 1)
        grid.addWidget(QtGui.QLabel('Total time (s):'), 7, 2)
        grid.addWidget(self.scanDurationLabel, 7, 3)
        grid.addWidget(QtGui.QLabel('Start (ms):'), 8, 1)
        grid.addWidget(QtGui.QLabel('End (ms):'), 8, 2)

        start_row = 9
        for i in range(0, len(self.allDevices)):
            grid.addWidget(QtGui.QLabel(self.allDevices[i]), start_row + i, 0)
            grid.addWidget(
                self.pxParameters['sta' + self.allDevices[i]], start_row + i, 1)
            grid.addWidget(
                self.pxParameters['end' + self.allDevices[i]], start_row + i, 2)

        grid.addWidget(self.graph, 8, 3, 5, 5)

    def registerListener(self, controller):
        self.saveScanBtn.clicked.connect(controller.saveScan)
        self.loadScanBtn.clicked.connect(controller.loadScan)
        self.scanButton.clicked.connect(controller.runScan)
        self.previewButton.clicked.connect(controller.previewScan)


class GraphFrame(pg.GraphicsWindow):
    """Creates the plot that plots the preview of the pulses.
    Fcn update() updates the plot of "device" with signal "signal"."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Take params from model
        # self.pxCycle = pxCycle
        # devs = list(pxCycle.sigDict.keys())
        self.plot = self.addPlot(row=1, col=0)
        self.plot.setYRange(0, 1)
        self.plot.showGrid(x=False, y=False)
        # self.plotSigDict = dict()
#        for i in range(0, len(pxCycle.sigDict)):
#            r = deviceInfo[i][2][0]
#            g = deviceInfo[i][2][1]
#            b = deviceInfo[i][2][2]
#            self.plotSigDict[devs[i]] = self.plot.plot(pen=pg.mkPen(r, g, b))
