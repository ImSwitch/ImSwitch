# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""
import configparser
import time

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui

from .basecontrollers import SuperScanController
import view.guitools as guitools

class ScanController(SuperScanController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.initControls(self._setupInfo.positioners, self._setupInfo.getTTLDevices())

        self._analogParameterDict = {
            'sample_rate': self._setupInfo.scan.stage.sampleRate,
            'return_time': self._setupInfo.scan.stage.returnTime
        }
        self._digitalParameterDict = {
            'sample_rate': self._setupInfo.scan.ttl.sampleRate
        }
        self._settingParameters = False

        self.getParameters()
        self.plotSignalGraph()

        # Connect NidaqManager signals
        self._master.nidaqManager.scanDoneSignal.connect(self.scanDone)

        # Connect CommunicationChannel signals
        self._commChannel.prepareScan.connect(lambda: self.setScanButton(True))

        # Connect ScanWidget signals
        self._widget.saveScanBtn.clicked.connect(self.saveScan)
        self._widget.loadScanBtn.clicked.connect(self.loadScan)
        self._widget.scanButton.clicked.connect(self.runScan)
        self._widget.seqTimePar.textChanged.connect(self.plotSignalGraph)
        self._widget.contLaserPulsesRadio.toggled.connect(self.setContLaserPulses)
        for deviceName in self._setupInfo.getTTLDevices():
            self._widget.pxParameters['sta' + deviceName].textChanged.connect(self.plotSignalGraph)
            self._widget.pxParameters['end' + deviceName].textChanged.connect(self.plotSignalGraph)

        for positionerName, positionerInfo in self._setupInfo.positioners.items():
            if positionerInfo.managerProperties['scanner']:
                self._widget.scanPar['size' + positionerName].textChanged.connect(self.update_pixels)
                self._widget.scanPar['stepSize' + positionerName].textChanged.connect(self.update_pixels)

        print('Init Scan Controller')

    @property
    def parameterDict(self):
        stageParameterList = [*self._analogParameterDict]
        TTLParameterList = [*self._digitalParameterDict]

        return {'stageParameterList': stageParameterList,
                'TTLParameterList': TTLParameterList}

    def getDimsScan(self):
        # TODO: Make sure this works as intended
        self.getParameters()
        x = self._analogParameterDict['axis_length'][0] / self._analogParameterDict['axis_step_size'][0]
        y = self._analogParameterDict['axis_length'][1] / self._analogParameterDict['axis_step_size'][1]

        return x, y

    def getScanAttrs(self):
        stage = self._analogParameterDict.copy()
        ttl = self._digitalParameterDict.copy()
        stage['target_device'] = np.string_(stage['target_device'])
        ttl['target_device'] = np.string_(ttl['target_device'])

        stage.update(ttl)
        return stage

    def saveScan(self):
        self.getParameters()
        config = configparser.ConfigParser()
        config.optionxform = str

        config['analogParameterDict'] = self._analogParameterDict
        config['digitalParameterDict'] = self._digitalParameterDict
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

        for key in self._analogParameterDict:
            self._analogParameterDict[key] = eval(config._sections['analogParameterDict'][key])

        for key in self._digitalParameterDict:
            self._digitalParameterDict[key] = eval(config._sections['digitalParameterDict'][key])

        scanOrNot = (config._sections['Modes']['scan_or_not'] == 'True')

        if scanOrNot:
            self._widget.scanRadio.setChecked(True)
        else:
            self._widget.contLaserPulsesRadio.setChecked(True)

        self.setParameters()
        # self._widget.updateScan(self._widget.allDevices)

    def setParameters(self):
        self._settingParameters = True
        try:
            for index, (positionerName, positionerInfo) in enumerate(self._setupInfo.positioners.items()):
                if positionerInfo.managerProperties['scanner']:
                    positionerName = self._analogParameterDict['target_device'][i]

                    scanDimPar = self._widget.scanPar['scanDim' + str(index)]
                    scanDimPar.setCurrentIndex(scanDimPar.findText(positionerName))

                    self._widget.scanPar['size' + positionerName].setText(
                        str(round(self._analogParameterDict['axis_length'][i], 3))
                    )

                    self._widget.scanPar['stepSize' + positionerName].setText(
                        str(round(self._analogParameterDict['axis_step_size'][i], 3))
                    )

            for i in range(len(self._digitalParameterDict['target_device'])):
                deviceName = self._digitalParameterDict['target_device'][i]

                self._widget.pxParameters['sta' + deviceName].setText(
                    str(round(1000 * self._digitalParameterDict['TTL_start'][i][0], 3))
                )
                self._widget.pxParameters['end' + deviceName].setText(
                    str(round(1000 * self._digitalParameterDict['TTL_end'][i][0], 3))
                )

            self._widget.seqTimePar.setText(
                str(round(float(1000 * self._digitalParameterDict['sequence_time']), 3))
            )
        finally:
            self._settingParameters = False
            self.plotSignalGraph()

    def runScan(self):
        self.getParameters()
        try:
            self.signalDic, self.scanInfoDict = self._master.scanManager.makeFullScan(
                self._analogParameterDict, self._digitalParameterDict, self._setupInfo,
                staticPositioner=self._widget.contLaserPulsesRadio.isChecked()
            )
        except:
            #TODO: should raise an error here probably, but that does not crash the program.
            return
        self._master.nidaqManager.runScan(self.signalDic, self.scanInfoDict)

    def scanDone(self):
        if not self._widget.contLaserPulsesRadio.isChecked() and not self._widget.continuousCheck.isChecked():
            #print("scan done")
            self.setScanButton(False)
            self._commChannel.endScan.emit()
        else:
            self._master.nidaqManager.runScan(self.signalDic, self.scanInfoDict)

    def getParameters(self):
        if self._settingParameters:
            return

        self._analogParameterDict['target_device'] = []
        self._analogParameterDict['axis_length'] = []
        self._analogParameterDict['axis_step_size'] = []
        self._analogParameterDict['axis_centerpos'] = []
        self._analogParameterDict['axis_startpos'] = []
        # TODO: this looks a bit wrong, as I am not using the enumerated info much anyway, and taking
        # the values in the order of how they are listed in the scanWidget (correct order). Fix?
        for index, (positionerName, positionerInfo) in enumerate(self._setupInfo.positioners.items()):
            if positionerInfo.managerProperties['scanner']:
                positionerName = self._widget.scanPar['scanDim' + str(index)].currentText()
                self._analogParameterDict['target_device'].append(positionerName)
                if positionerName != 'None':
                    size = float(self._widget.scanPar['size' + positionerName].text())
                    stepSize = float(self._widget.scanPar['stepSize' + positionerName].text())
                    center = float(self._widget.scanPar['center' + positionerName].text())
                    start = self._commChannel.getStartPos()[positionerName]
                    self._analogParameterDict['axis_length'].append(size)
                    self._analogParameterDict['axis_step_size'].append(stepSize)
                    self._analogParameterDict['axis_centerpos'].append(center)
                    self._analogParameterDict['axis_startpos'].append(start)
                else:
                    self._analogParameterDict['axis_length'].append(1.0)
                    self._analogParameterDict['axis_step_size'].append(1.0)
                    # TODO: make this read the actual center position of the axis that is missing, but put 0 for now.
                    self._analogParameterDict['axis_centerpos'].append(0.0)
                    self._analogParameterDict['axis_startpos'].append(start)

        self._digitalParameterDict['target_device'] = []
        self._digitalParameterDict['TTL_start'] = []
        self._digitalParameterDict['TTL_end'] = []
        for deviceName, deviceInfo in self._setupInfo.getTTLDevices().items():
            self._digitalParameterDict['target_device'].append(deviceName)

            deviceStarts = self._widget.pxParameters['sta' + deviceName].text().split(',')
            self._digitalParameterDict['TTL_start'].append([
                float(deviceStart) / 1000 for deviceStart in deviceStarts if deviceStart
            ])

            deviceEnds = self._widget.pxParameters['end' + deviceName].text().split(',')
            self._digitalParameterDict['TTL_end'].append([
                float(deviceEnd) / 1000 for deviceEnd in deviceEnds if deviceEnd
            ])

        self._digitalParameterDict['sequence_time'] = float(self._widget.seqTimePar.text()) / 1000
        self._analogParameterDict['sequence_time'] = float(self._widget.seqTimePar.text()) / 1000

    def setContLaserPulses(self, isContLaserPulses):
        for i in range(len(self._setupInfo.positioners)):
            positionerName = self._widget.scanPar['scanDim' + str(i)].currentText()
            self._widget.scanPar['scanDim' + str(i)].setEnabled(not isContLaserPulses)
            self._widget.scanPar['size' + positionerName].setEnabled(not isContLaserPulses)
            self._widget.scanPar['stepSize' + positionerName].setEnabled(not isContLaserPulses)

    def setScanButton(self, b):
        self._widget.scanButton.setChecked(b)
        if b: self.runScan()

    def update_pixels(self):
        self.getParameters()
        for index, (positionerName, positionerInfo) in enumerate(self._setupInfo.positioners.items()):
            if positionerInfo.managerProperties['scanner']:
                if float(self._analogParameterDict['axis_step_size'][index]) != 0:
                    pixels = round(float(self._analogParameterDict['axis_length'][index]) / float(self._analogParameterDict['axis_step_size'][index]))
                    self._widget.scanPar['pixels' + positionerName].setText(str(pixels))

    def plotSignalGraph(self):
        if self._settingParameters:
            return

        self.getParameters()
        TTLCycleSignalsDict = self._master.scanManager.getTTLCycleSignalsDict(self._digitalParameterDict,
                                                                             self._setupInfo)

        self._widget.graph.plot.clear()
        for deviceName, signal in TTLCycleSignalsDict.items():
            isLaser = deviceName in self._setupInfo.lasers

            self._widget.graph.plot.plot(
                np.linspace(0, self._digitalParameterDict['sequence_time'] * self._widget.sampleRate, len(signal)),
                signal.astype(np.uint8),        
                pen=pg.mkPen(guitools.color_utils.wavelength_to_hex(self._setupInfo.lasers[deviceName].wavelength) if isLaser else '#ffffff')
            )

        self._widget.graph.plot.setYRange(-0.1, 1.1)
