# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""
import configparser

import numpy as np
from pyqtgraph.Qt import QtGui

from .basecontrollers import SuperScanController


class ScanController(SuperScanController):  # TODO
    def __init__(self, comm_channel, master, widget):
        super().__init__(comm_channel, master, widget)
        self._stageParameterDict = {
            'Targets[3]': ['StageX', 'StageY', 'StageZ'],
            'Sizes[3]': [5, 5, 0],
            'Step_sizes[3]': [1, 1, 1],
            'Start[3]': [0, 0, 0],
            'Sequence_time_seconds': 0.005,
            'Sample_rate': 100000,
            'Return_time_seconds': 0.01
        }
        self._TTLParameterDict = {
            'Targets[x]': ['405', '473', '488', 'CAM'],
            'TTLStarts[x,y]': [[0.0012], [0.002], [0], [0]],
            'TTLEnds[x,y]': [[0.0015], [0.0025], [0], [0]],
            'Sequence_time_seconds': 0.005,
            'Sample_rate': 100000
        }

        # Connect NidaqHelper signals
        self._master.nidaqHelper.scanDoneSignal.connect(self.scanDone)

        # Connect CommunicationChannel signals
        self._comm_channel.prepareScan.connect(lambda: self.setScanButton(True))

        # Connect ScanWidget signals
        self._widget.saveScanBtn.clicked.connect(self.saveScan)
        self._widget.loadScanBtn.clicked.connect(self.loadScan)
        self._widget.scanButton.clicked.connect(self.runScan)
        self._widget.previewButton.clicked.connect(self.previewScan)

        print('Init Scan Controller')

    @property
    def parameterDict(self):
        stageParameterList = [*self._stageParameterDict]
        TTLParameterList = [*self._TTLParameterDict]

        return {'stageParameterList': stageParameterList,
                'TTLParameterList': TTLParameterList}

    def getDimsScan(self):
        self.getParameters()
        x = self._stageParameterDict['Sizes[3]'][0] / self._stageParameterDict['Step_sizes[3]'][0]
        y = self._stageParameterDict['Sizes[3]'][1] / self._stageParameterDict['Step_sizes[3]'][1]

        return x, y

    def getScanAttrs(self):
        stage = self._stageParameterDict.copy()
        ttl = self._TTLParameterDict.copy()
        stage['Targets[3]'] = np.string_(stage['Targets[3]'])
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
        fileName = QtGui.QFileDialog.getSaveFileName(self._widget, 'Save scan',
                                                     self._widget.scanDir)
        if fileName == '':
            return

        with open(fileName, 'w') as configfile:
            config.write(configfile)

    def loadScan(self):
        config = configparser.ConfigParser()
        config.optionxform = str

        fileName = QtGui.QFileDialog.getOpenFileName(self._widget, 'Load scan',
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
        # self._widget.graph.update()

    def setParameters(self):
        primDim = self._stageParameterDict['Targets[3]'][0].split('_')[1]
        secDim = self._stageParameterDict['Targets[3]'][1].split('_')[1]
        thirdDim = self._stageParameterDict['Targets[3]'][2].split('_')[1]

        axis = {'X': 0, 'Y': 1, 'Z': 2}

        self._widget.primScanDim.setCurrentIndex(axis[primDim])
        self._widget.secScanDim.setCurrentIndex(axis[secDim])
        self._widget.thirdScanDim.setCurrentIndex(axis[thirdDim])

        self._widget.scanPar['size' + primDim].setText(
            str(round(1000 * self._stageParameterDict['Sizes[3]'][0], 3))
        )
        self._widget.scanPar['size' + secDim].setText(
            str(round(1000 * self._stageParameterDict['Sizes[3]'][1], 3))
        )
        self._widget.scanPar['size' + thirdDim].setText(
            str(round(1000 * self._stageParameterDict['Sizes[3]'][2], 3))
        )

        self._widget.scanPar['stepSize' + primDim].setText(
            str(round(1000 * self._stageParameterDict['Step_sizes[3]'][0], 3))
        )
        self._widget.scanPar['stepSize' + secDim].setText(
            str(round(1000 * self._stageParameterDict['Step_sizes[3]'][1], 3))
        )
        self._widget.scanPar['stepSize' + thirdDim].setText(
            str(round(1000 * self._stageParameterDict['Step_sizes[3]'][2], 3))
        )

        for i in range(len(self._TTLParameterDict['Targets[x]'])):
            self._widget.pxParameters['sta' + self._TTLParameterDict['Targets[x]'][i]].setText(
                str(round(self._TTLParameterDict['TTLStarts[x,y]'][i][0], 3))
            )
            self._widget.pxParameters['end' + self._TTLParameterDict['Targets[x]'][i]].setText(
                str(round(self._TTLParameterDict['TTLEnds[x,y]'][i][0], 3))
            )

        self._widget.seqTimePar.setText(
            str(round(float(self._TTLParameterDict['Sequence_time_seconds']) * 1000, 3))
        )

    def previewScan(self):
        print('previewScan')

    def runScan(self):
        self.getParameters()
        self.signalDic = self._master.scanHelper.make_full_scan(self._stageParameterDict,
                                                                self._TTLParameterDict)
        self._master.nidaqHelper.runScan(self.signalDic)

    def scanDone(self):
        print("scan done")
        if not self._widget.continuousCheck.isChecked():
            self.setScanButton(False)
            self._comm_channel.endScan.emit()
        else:
            self._master.nidaqHelper.runScan(self.signalDic)

    def getParameters(self):
        primDim = self._widget.primScanDim.currentText()
        secDim = self._widget.secScanDim.currentText()
        thirdDim = self._widget.thirdScanDim.currentText()

        self._stageParameterDict['Targets[3]'] = (
            'Stage_' + primDim, 'Stage_' + secDim, 'Stage_' + thirdDim
        )

        self._stageParameterDict['Sizes[3]'] = (
            float(self._widget.scanPar['size' + primDim].text()),
            float(self._widget.scanPar['size' + secDim].text()),
            float(self._widget.scanPar['size' + thirdDim].text())
        )

        self._stageParameterDict['Step_sizes[3]'] = (
            float(self._widget.scanPar['stepSize' + primDim].text()),
            float(self._widget.scanPar['stepSize' + secDim].text()),
            float(self._widget.scanPar['stepSize' + thirdDim].text())
        )

        start = self._comm_channel.getStartPos()
        self._stageParameterDict['Start[3]'] = (start[primDim], start[secDim], start[thirdDim])
        for i in range(len(self._TTLParameterDict['Targets[x]'])):
            self._TTLParameterDict['TTLStarts[x,y]'][i] = [
                float(self._widget.pxParameters['sta' + self._TTLParameterDict['Targets[x]'][i]].text()) / 1000
            ]

            self._TTLParameterDict['TTLEnds[x,y]'][i] = [
                float(self._widget.pxParameters['end' + self._TTLParameterDict['Targets[x]'][i]].text()) / 1000
            ]

        self._TTLParameterDict['Sequence_time_seconds'] = float(
            self._widget.seqTimePar.text()) / 1000
        self._stageParameterDict['Sequence_time_seconds'] = float(
            self._widget.seqTimePar.text()) / 1000

    def setScanButton(self, b):
        self._widget.scanButton.setChecked(b)
        if b: self.runScan()
