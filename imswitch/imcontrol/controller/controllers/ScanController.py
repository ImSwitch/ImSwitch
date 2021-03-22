import configparser
import os

import numpy as np

from imswitch.imcommon import constants
from imswitch.imcommon.model import APIExport
from imswitch.imcontrol.view import guitools as guitools
from .basecontrollers import SuperScanController


class ScanController(SuperScanController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.initControls(self._setupInfo.positioners.keys(),
                                  self._setupInfo.getTTLDevices().keys())

        self.scanDir = os.path.join(constants.rootFolderPath, 'scans')
        if not os.path.exists(self.scanDir):
            os.makedirs(self.scanDir)

        self._stageParameterDict = {
            'Sample_rate': self._setupInfo.scan.stage.sampleRate,
            'Return_time_seconds': self._setupInfo.scan.stage.returnTime
        }
        self._TTLParameterDict = {
            'Sample_rate': self._setupInfo.scan.ttl.sampleRate
        }
        self._settingParameters = False

        self.getParameters()
        self.plotSignalGraph()

        # Connect NidaqManager signals
        self._master.nidaqManager.sigScanDone.connect(self.scanDone)

        # Connect CommunicationChannel signals
        self._commChannel.sigPrepareScan.connect(lambda: self.setScanButton(True))

        # Connect ScanWidget signals
        self._widget.sigSaveScanClicked.connect(self.saveScan)
        self._widget.sigLoadScanClicked.connect(self.loadScan)
        self._widget.sigRunScanClicked.connect(self.runScan)
        self._widget.sigContLaserPulsesToggled.connect(self.setContLaserPulses)
        self._widget.sigSeqTimeParChanged.connect(self.plotSignalGraph)
        self._widget.sigSignalParChanged.connect(self.plotSignalGraph)

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

    def getScanStageAttrs(self):
        self.getParameters()
        prefix = 'ScanStage'

        stage = {}
        for key, value in self._stageParameterDict.items():
            stage[f'{prefix}:{key}'] = value
        stage[f'{prefix}:Targets[x]'] = np.string_(stage[f'{prefix}:Targets[x]'])

        stage[f'{prefix}:Positive_direction[x]'] = []
        for i in range(len(self._setupInfo.positioners)):
            positionerName = self._stageParameterDict['Targets[x]'][i]
            positiveDirection = self._setupInfo.positioners[positionerName].isPositiveDirection
            stage[f'{prefix}:Positive_direction[x]'].append(positiveDirection)

        return stage

    def getScanTTLAttrs(self):
        self.getParameters()
        prefix = 'ScanTTL'

        ttl = {}
        for key, value in self._TTLParameterDict.items():
            ttl[f'{prefix}:{key}'] = value
        ttl[f'{prefix}:Targets[x]'] = np.string_(ttl[f'{prefix}:Targets[x]'])

        return ttl

    def saveScan(self):
        fileName = guitools.askForFilePath(self._widget, 'Save scan', self.scanDir, isSaving=True)
        if not fileName:
            return

        self.saveScanParamsToFile(fileName)

    @APIExport
    def saveScanParamsToFile(self, filePath):
        """ Saves the set scanning parameters to the specified file. """
        self.getParameters()
        config = configparser.ConfigParser()
        config.optionxform = str

        config['stageParameterDict'] = self._stageParameterDict
        config['TTLParameterDict'] = self._TTLParameterDict
        config['Modes'] = {'scan_or_not': self._widget.isScanMode()}

        with open(filePath, 'w') as configfile:
            config.write(configfile)

    def loadScan(self):
        fileName = guitools.askForFilePath(self._widget, 'Load scan', self.scanDir)
        if not fileName:
            return

        self.loadScanParamsFromFile(fileName)

    @APIExport
    def loadScanParamsFromFile(self, filePath):
        """ Loads scanning parameters from the specified file. """

        config = configparser.ConfigParser()
        config.optionxform = str

        config.read(filePath)

        for key in self._stageParameterDict:
            self._stageParameterDict[key] = eval(config._sections['stageParameterDict'][key])

        for key in self._TTLParameterDict:
            self._TTLParameterDict[key] = eval(config._sections['TTLParameterDict'][key])

        scanOrNot = (config._sections['Modes']['scan_or_not'] == 'True')

        if scanOrNot:
            self._widget.setScanMode()
        else:
            self._widget.setContLaserMode()

        self.setParameters()

    def setParameters(self):
        self._settingParameters = True
        try:
            for i in range(len(self._setupInfo.positioners)):
                positionerName = self._stageParameterDict['Targets[x]'][i]
                self._widget.setScanDim(i, positionerName)
                self._widget.setScanSize(positionerName, self._stageParameterDict['Sizes[x]'][i])
                self._widget.setScanStepSize(positionerName, self._stageParameterDict['Step_sizes[x]'][i])

            for i in range(len(self._TTLParameterDict['Targets[x]'])):
                deviceName = self._TTLParameterDict['Targets[x]'][i]
                self._widget.setTTLStarts(deviceName, self._TTLParameterDict['TTLStarts[x,y]'][i])
                self._widget.setTTLEnds(deviceName, self._TTLParameterDict['TTLEnds[x,y]'][i])

            self._widget.setSeqTimePar(self._TTLParameterDict['Sequence_time_seconds'])
        finally:
            self._settingParameters = False
            self.plotSignalGraph()

    @APIExport
    def runScan(self):
        """ Runs a scan with the set scanning parameters. """
        self.getParameters()
        self.signalDic = self._master.scanManager.makeFullScan(
            self._stageParameterDict, self._TTLParameterDict, self._setupInfo,
            staticPositioner=self._widget.isContLaserMode()
        )
        self._master.nidaqManager.runScan(self.signalDic)

    def scanDone(self):
        print("scan done")
        if not self._widget.isContLaserMode() and not self._widget.continuousCheckEnabled():
            self.setScanButton(False)
            self._commChannel.sigScanEnded.emit()
        else:
            self._master.nidaqManager.runScan(self.signalDic)

    def getParameters(self):
        if self._settingParameters:
            return

        self._stageParameterDict['Targets[x]'] = []
        self._stageParameterDict['Sizes[x]'] = []
        self._stageParameterDict['Step_sizes[x]'] = []
        self._stageParameterDict['Start[x]'] = []
        for i in range(len(self._setupInfo.positioners)):
            positionerName = self._widget.getScanDim(i)
            size = self._widget.getScanSize(positionerName)
            stepSize = self._widget.getScanStepSize(positionerName)
            start = self._commChannel.getStartPos()[positionerName]

            self._stageParameterDict['Targets[x]'].append(positionerName)
            self._stageParameterDict['Sizes[x]'].append(size)
            self._stageParameterDict['Step_sizes[x]'].append(stepSize)
            self._stageParameterDict['Start[x]'].append(start)

        self._TTLParameterDict['Targets[x]'] = []
        self._TTLParameterDict['TTLStarts[x,y]'] = []
        self._TTLParameterDict['TTLEnds[x,y]'] = []
        for deviceName, deviceInfo in self._setupInfo.getTTLDevices().items():
            self._TTLParameterDict['Targets[x]'].append(deviceName)
            self._TTLParameterDict['TTLStarts[x,y]'].append(self._widget.getTTLStarts(deviceName))
            self._TTLParameterDict['TTLEnds[x,y]'].append(self._widget.getTTLEnds(deviceName))

        self._TTLParameterDict['Sequence_time_seconds'] = self._widget.getSeqTimePar()
        self._stageParameterDict['Sequence_time_seconds'] = self._widget.getSeqTimePar()

    def setContLaserPulses(self, isContLaserPulses):
        for i in range(len(self._setupInfo.positioners)):
            positionerName = self._widget.scanPar['scanDim' + str(i)].currentText()
            self._widget.setScanDimEnabled(i, not isContLaserPulses)
            self._widget.setScanSizeEnabled(positionerName, not isContLaserPulses)
            self._widget.setScanStepSizeEnabled(positionerName, not isContLaserPulses)

    def setScanButton(self, b):
        self._widget.setScanButtonChecked(b)
        if b: self.runScan()

    def plotSignalGraph(self):
        if self._settingParameters:
            return

        self.getParameters()
        TTLCycleSignalsDict = self._master.scanManager.getTTLCycleSignalsDict(self._TTLParameterDict,
                                                                              self._setupInfo)

        areas = []
        signals = []
        colors = []
        for deviceName, signal in TTLCycleSignalsDict.items():
            isLaser = deviceName in self._setupInfo.lasers
            areas.append(np.linspace(0, self._TTLParameterDict['Sequence_time_seconds'] * self._widget.sampleRate, len(signal))),
            signals.append(signal.astype(np.uint8))
            colors.append(
                guitools.colorutils.wavelengthToHex(
                    self._setupInfo.lasers[deviceName].wavelength
                ) if isLaser else '#ffffff'
            )
        self._widget.plotSignalGraph(areas, signals, colors)

        

# Copyright (C) 2020, 2021 TestaLab
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
