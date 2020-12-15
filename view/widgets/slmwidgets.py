# -*- coding: utf-8 -*-
"""
Created on Tue Dec 15 17:18:00 2020

@author: jonatanalvelid
"""
import os

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui

import constants
import view.guitools as guitools
from .basewidgets import Widget


class SLMWidget(Widget):
    ''' Widget containing slm interface.
            This class uses the classes (((MultipleScanWidget and IllumImageWidget)))'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)

        self.updateButton = guitools.BetterPushButton('Update')
        #self.updateButton.setCheckable(True)
        #self.updateButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
        #                                QtGui.QSizePolicy.Expanding)

        self.ppview = SLMFrame()
        self.ppview.setAspectLocked(True)

        # CONTINUE HERE WITH ARROWS MODULE AND SLM PARAMETER TREE AND SLM ABER PARAM TREE (FROM PYQTGRAPH PARAMETERTREE)



        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)







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

        self.seqTimePar = QtGui.QLineEdit(self._defaultPreset.scan.dwellTime)  # ms
        self.nrFramesPar = QtGui.QLabel()
        self.scanDuration = 0
        self.scanDurationLabel = QtGui.QLabel(str(self.scanDuration))

        self.scanDims = []

        self.scanPar = {'seqTime': self.seqTimePar}

        self.pxParameters = {}
        self.pxParValues = {}





    def initControls(self, stagePiezzoInfos, TTLDeviceInfos):
        self.scanDims = list(stagePiezzoInfos.keys())

        self.grid.addWidget(self.loadScanBtn, 0, 0)
        self.grid.addWidget(self.saveScanBtn, 0, 1)
        self.grid.addWidget(self.scanRadio, 0, 2)
        self.grid.addWidget(self.contLaserPulsesRadio, 0, 3)
        self.grid.addItem(QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum), 0, 6)
        self.grid.addWidget(self.scanButton, 1, 7, len(stagePiezzoInfos), 1)
        self.grid.addWidget(self.continuousCheck, 0, 7)

        currentRow = 1

        stagePiezzoPresets = self._defaultPreset.scan.stagePiezzos
        for index, (stagePiezzoId, stagePiezzoInfo) in enumerate(stagePiezzoInfos.items()):
            stagePiezzoPreset = (
                stagePiezzoPresets[stagePiezzoId] if stagePiezzoId in stagePiezzoPresets
                else guitools.ScanPresetStagePiezzo()
            )

            sizePar = QtGui.QLineEdit(str(stagePiezzoPreset.size))
            self.scanPar['size' + stagePiezzoId] = sizePar
            stepSizePar = QtGui.QLineEdit(str(stagePiezzoPreset.stepSize))
            self.scanPar['stepSize' + stagePiezzoId] = stepSizePar

            self.grid.addWidget(QtGui.QLabel('Size {} (µm):'.format(stagePiezzoId)), currentRow, 0)
            self.grid.addWidget(sizePar, currentRow, 1)
            self.grid.addWidget(QtGui.QLabel('Step {} (µm):'.format(stagePiezzoId)), currentRow, 2)
            self.grid.addWidget(stepSizePar, currentRow, 3)

            dimLabelText = '{}{} dimension:'.format(index + 1, guitools.ordinalSuffix(index + 1))
            self.grid.addWidget(QtGui.QLabel(dimLabelText), currentRow, 4)
            scanDimPar = QtGui.QComboBox()
            scanDimPar.addItems(self.scanDims)
            scanDimPar.setCurrentIndex(index)
            self.scanPar['scanDim' + str(index)] = scanDimPar
            self.grid.addWidget(scanDimPar, currentRow, 5)

            currentRow += 1

        self.grid.addWidget(QtGui.QLabel('Number of frames:'), currentRow, 4)
        self.grid.addWidget(self.nrFramesPar, currentRow, 5)
        currentRow += 1

        self.grid.addWidget(QtGui.QLabel('Dwell time (ms):'), currentRow, 0)
        self.grid.addWidget(self.seqTimePar, currentRow, 1)
        self.grid.addWidget(QtGui.QLabel('Total time (s):'), currentRow, 2)
        self.grid.addWidget(self.scanDurationLabel, currentRow, 3)
        currentRow += 1

        self.grid.addWidget(QtGui.QLabel('Start (ms):'), currentRow, 1)
        self.grid.addWidget(QtGui.QLabel('End (ms):'), currentRow, 2)
        self.grid.addWidget(self.graph, currentRow, 3, 1 + len(TTLDeviceInfos), 5)
        currentRow += 1

        pulsePresets = self._defaultPreset.scan.pulses
        for deviceName in TTLDeviceInfos.keys():
            pulsePreset = (pulsePresets[deviceName] if deviceName in pulsePresets
                           else guitools.ScanPresetTTL())

            self.grid.addWidget(QtGui.QLabel(deviceName), currentRow, 0)
            self.pxParameters['sta' + deviceName] = QtGui.QLineEdit(pulsePreset.start)
            self.pxParameters['end' + deviceName] = QtGui.QLineEdit(pulsePreset.end)
            self.grid.addWidget(self.pxParameters['sta' + deviceName], currentRow, 1)
            self.grid.addWidget(self.pxParameters['end' + deviceName], currentRow, 2)
            currentRow += 1


class SLMFrame(pg.GraphicsLayoutWidget):
    """Creates a display for displaying the phase pattern displayed on the SLM."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vb = self.addViewBox(row=1, col=1)
        self.img = pg.ImageItem()
