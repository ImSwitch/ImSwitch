# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""
import configparser

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui

from .basecontrollers import SuperScanController


class ScanController(SuperScanController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.initControls(self._setupInfo.stagePiezzos, self._setupInfo.getTTLDevices())

        self._stageParameterDict = {
            'Sample_rate': self._setupInfo.scan.stage.sampleRate,
            'Return_time_seconds': self._setupInfo.scan.stage.returnTime
        }
        self._TTLParameterDict = {
            'Sample_rate': self._setupInfo.scan.ttl.sampleRate
        }
        self.getParameters()
        self.plotSignalGraph()

        # Connect NidaqHelper signals
        self._master.nidaqHelper.scanDoneSignal.connect(self.scanDone)

        # Connect CommunicationChannel signals
        self._commChannel.prepareScan.connect(lambda: self.setScanButton(True))

        # Connect ScanWidget signals
        self._widget.saveScanBtn.clicked.connect(self.saveScan)
        self._widget.loadScanBtn.clicked.connect(self.loadScan)
        self._widget.scanButton.clicked.connect(self.runScan)
        self._widget.previewButton.clicked.connect(self.previewScan)
        for deviceName in self._setupInfo.getTTLDevices():
            self._widget.pxParameters['sta' + deviceName].textChanged.connect(self.plotSignalGraph)
            self._widget.pxParameters['end' + deviceName].textChanged.connect(self.plotSignalGraph)

        print('Init Scan Controller')

    @property
    def parameterDict(self):
        stageParameterList = [*self._stageParameterDict]
        TTLParameterList = [*self._TTLParameterDict]

        return {'stageParameterList': stageParameterList,
                'TTLParameterList': TTLParameterList}

    def getDimsScan(self):
        # TODO: Make sure this works as intended
        self.getParameters()
        x = self._stageParameterDict['Sizes[x]'][0] / self._stageParameterDict['Step_sizes[x]'][0]
        y = self._stageParameterDict['Sizes[x]'][1] / self._stageParameterDict['Step_sizes[x]'][1]

        return x, y

    def getScanAttrs(self):
        stage = self._stageParameterDict.copy()
        ttl = self._TTLParameterDict.copy()
        stage['Targets[x]'] = np.string_(stage['Targets[x]'])
        ttl['Targets[x]'] = np.string_(ttl['Targets[x]'])

        stage.update(ttl)
        return stage

    def saveScan(self):
        self.getParameters()
        config = configparser.ConfigParser()
        config.optionxform = str

        config['stageParameterDict'] = self._stageParameterDict
        config['TTLParameterDict'] = self._TTLParameterDict
        config['Modes'] = {'scan_or_not': self._widget.scanRadio.isChecked()}
        fileName, _ = QtGui.QFileDialog.getSaveFileName(self._widget, 'Save scan',
                                                     self._widget.scanDir)
        if fileName == '':
            return

        with open(fileName, 'w') as configfile:
            config.write(configfile)

    def loadScan(self):
        config = configparser.ConfigParser()
        config.optionxform = str

        fileName, _ = QtGui.QFileDialog.getOpenFileName(self._widget, 'Load scan',
                                                     self._widget.scanDir)
        if fileName == '':
            return

        config.read(fileName)

        for key in self._stageParameterDict:
            self._stageParameterDict[key] = eval(config._sections['stageParameterDict'][key])

        for key in self._TTLParameterDict:
            self._TTLParameterDict[key] = eval(config._sections['TTLParameterDict'][key])

        scanOrNot = (config._sections['Modes']['scan_or_not'] == 'True')

        if scanOrNot:
            self._widget.scanRadio.setChecked(True)
        else:
            self._widget.contLaserPulsesRadio.setChecked(True)

        self.setParameters()
        # self._widget.updateScan(self._widget.allDevices)

    def setParameters(self):
        for i in range(len(self._setupInfo.stagePiezzos)):
            stagePiezzoId = self._stageParameterDict['Targets[x]'][i]

            scanDimPar = self._widget.scanPar['scanDim' + str(i)]
            scanDimPar.setCurrentIndex(scanDimPar.findText(stagePiezzoId))

            self._widget.scanPar['size' + stagePiezzoId].setText(
                str(round(self._stageParameterDict['Sizes[x]'][i], 3))
            )

            self._widget.scanPar['stepSize' + stagePiezzoId].setText(
                str(round(self._stageParameterDict['Step_sizes[x]'][i], 3))
            )

        for i in range(len(self._TTLParameterDict['Targets[x]'])):
            deviceName = self._TTLParameterDict['Targets[x]'][i]

            self._widget.pxParameters['sta' + deviceName].setText(
                str(round(1000 * self._TTLParameterDict['TTLStarts[x,y]'][i][0], 3))
            )
            self._widget.pxParameters['end' + deviceName].setText(
                str(round(1000 * self._TTLParameterDict['TTLEnds[x,y]'][i][0], 3))
            )

        self._widget.seqTimePar.setText(
            str(round(float(1000 * self._TTLParameterDict['Sequence_time_seconds']), 3))
        )

    def previewScan(self):
        print('previewScan')

    def runScan(self):
        self.getParameters()
        self.signalDic = self._master.scanHelper.makeFullScan(
            self._stageParameterDict, self._TTLParameterDict, self._setupInfo,
            staticPositioner=self._widget.contLaserPulsesRadio.isChecked()
        )
        self._master.nidaqHelper.runScan(self.signalDic)

    def scanDone(self):
        print("scan done")
        if not self._widget.continuousCheck.isChecked():
            self.setScanButton(False)
            self._commChannel.endScan.emit()
        else:
            self._master.nidaqHelper.runScan(self.signalDic)

    def getParameters(self):
        self._stageParameterDict['Targets[x]'] = []
        self._stageParameterDict['Sizes[x]'] = []
        self._stageParameterDict['Step_sizes[x]'] = []
        self._stageParameterDict['Start[x]'] = []
        for i in range(len(self._setupInfo.stagePiezzos)):
            stagePiezzoId = self._widget.scanPar['scanDim' + str(i)].currentText()
            size = float(self._widget.scanPar['size' + stagePiezzoId].text())
            stepSize = float(self._widget.scanPar['stepSize' + stagePiezzoId].text())
            start = self._commChannel.getStartPos()[stagePiezzoId]

            self._stageParameterDict['Targets[x]'].append(stagePiezzoId)
            self._stageParameterDict['Sizes[x]'].append(size)
            self._stageParameterDict['Step_sizes[x]'].append(stepSize)
            self._stageParameterDict['Start[x]'].append(start)

        self._TTLParameterDict['Targets[x]'] = []
        self._TTLParameterDict['TTLStarts[x,y]'] = []
        self._TTLParameterDict['TTLEnds[x,y]'] = []
        for deviceName, deviceInfo in self._setupInfo.getTTLDevices().items():
            self._TTLParameterDict['Targets[x]'].append(deviceName)

            deviceStarts = self._widget.pxParameters['sta' + deviceName].text().split(',')
            self._TTLParameterDict['TTLStarts[x,y]'].append([
                float(deviceStart) / 1000 for deviceStart in deviceStarts if deviceStart
            ])

            deviceEnds = self._widget.pxParameters['end' + deviceName].text().split(',')
            self._TTLParameterDict['TTLEnds[x,y]'].append([
                float(deviceEnd) / 1000 for deviceEnd in deviceEnds if deviceEnd
            ])

        self._TTLParameterDict['Sequence_time_seconds'] = float(self._widget.seqTimePar.text()) / 1000
        self._stageParameterDict['Sequence_time_seconds'] = float(self._widget.seqTimePar.text()) / 1000

    def setScanButton(self, b):
        self._widget.scanButton.setChecked(b)
        if b: self.runScan()

    def plotSignalGraph(self):
        self.getParameters()
        TTLCycleSignalsDict = self._master.scanHelper.getTTLCycleSignalsDict(self._TTLParameterDict,
                                                                             self._setupInfo)

        self._widget.graph.plot.clear()
        for deviceName, signal in TTLCycleSignalsDict.items():
            isLaser = deviceName in self._setupInfo.lasers

            self._widget.graph.plot.plot(
                np.linspace(0, self._TTLParameterDict['Sequence_time_seconds'] * self._widget.sampleRate, len(signal)),
                signal.astype(np.uint8),
                pen=pg.mkPen(self._setupInfo.lasers[deviceName].color if isLaser else '#ffffff')
            )

        self._widget.graph.plot.setYRange(-0.1, 1.1)
