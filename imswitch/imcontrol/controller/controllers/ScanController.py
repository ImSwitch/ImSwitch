import configparser
import os
from ast import literal_eval
from traceback import print_exc

import numpy as np

from imswitch.imcommon import constants
from imswitch.imcommon.model import APIExport
from imswitch.imcontrol.view import guitools
from .basecontrollers import SuperScanController


class ScanController(SuperScanController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settingAttr = False
        self.settingParameters = False

        self.positioners = {
            pName: pManager for pName, pManager in self._setupInfo.positioners.items()
            if pManager.forScanning
        }
        self.TTLDevices = self._setupInfo.getTTLDevices()

        self._widget.initControls(
            self.positioners.keys(),
            self.TTLDevices.keys(),
            self._master.scanManager.TTLTimeUnits
        )

        self.scanDir = os.path.join(constants.rootFolderPath, 'save/scans')
        if not os.path.exists(self.scanDir):
            os.makedirs(self.scanDir)

        self._analogParameterDict = {}
        self._digitalParameterDict = {}

        self.getParameters()
        self.updatePixels()
        self.plotSignalGraph()
        self.updateScanStageAttrs()
        self.updateScanTTLAttrs()

        # Connect NidaqManager signals
        self._master.nidaqManager.sigScanDone.connect(self.scanDone)

        # Connect CommunicationChannel signals
        self._commChannel.sigPrepareScan.connect(lambda: self.setScanButton(True))
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged)

        # Connect ScanWidget signals
        self._widget.sigSaveScanClicked.connect(self.saveScan)
        self._widget.sigLoadScanClicked.connect(self.loadScan)
        self._widget.sigRunScanClicked.connect(self.runScan)
        self._widget.sigContLaserPulsesToggled.connect(self.setContLaserPulses)
        self._widget.sigSeqTimeParChanged.connect(self.plotSignalGraph)
        self._widget.sigSeqTimeParChanged.connect(self.updateScanTTLAttrs)
        self._widget.sigStageParChanged.connect(self.updatePixels)
        self._widget.sigStageParChanged.connect(self.updateScanStageAttrs)
        self._widget.sigSignalParChanged.connect(self.plotSignalGraph)
        self._widget.sigSignalParChanged.connect(self.updateScanTTLAttrs)

        print('Init Scan Controller')

    def getDimsScan(self):
        # TODO: Make sure this works as intended
        self.getParameters()
        x = self._analogParameterDict['axis_length'][0] / self._analogParameterDict['axis_step_size'][0]
        y = self._analogParameterDict['axis_length'][1] / self._analogParameterDict['axis_step_size'][1]

        return x, y

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

        config['analogParameterDict'] = self._analogParameterDict
        config['digitalParameterDict'] = self._digitalParameterDict
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

        for key in self._analogParameterDict:
            self._analogParameterDict[key] = literal_eval(
                config._sections['analogParameterDict'][key]
            )

        for key in self._digitalParameterDict:
            self._digitalParameterDict[key] = literal_eval(
                config._sections['digitalParameterDict'][key]
            )

        scanOrNot = (config._sections['Modes']['scan_or_not'] == 'True')

        if scanOrNot:
            self._widget.setScanMode()
        else:
            self._widget.setContLaserMode()

        self.setParameters()

    def setParameters(self):
        self.settingParameters = True
        try:
            for i in range(len(self.positioners)):
                positionerName = self._analogParameterDict['target_device'][i]
                self._widget.setScanDim(i, positionerName)
                self._widget.setScanSize(positionerName, self._analogParameterDict['axis_length'][i])
                self._widget.setScanStepSize(positionerName, self._analogParameterDict['axis_step_size'][i])
                self._widget.setScanCenterPos(positionerName, self._analogParameterDict['axis_centerpos'][i])

            for i in range(len(self.TTLDevices)):
                deviceName = self._digitalParameterDict['target_device'][i]
                self._widget.setTTLStarts(deviceName, self._digitalParameterDict['TTL_start'][i])
                self._widget.setTTLEnds(deviceName, self._digitalParameterDict['TTL_end'][i])

            self._widget.setSeqTimePar(self._digitalParameterDict['sequence_time'])
        finally:
            self.settingParameters = False
            self.plotSignalGraph()

    @APIExport
    def runScan(self):
        """ Runs a scan with the set scanning parameters. """
        self.getParameters()
        try:
            self.signalDic, self.scanInfoDict = self._master.scanManager.makeFullScan(
                self._analogParameterDict, self._digitalParameterDict,
                staticPositioner=self._widget.isContLaserMode()
            )
        except:
            # TODO: should raise an error here probably, but that does not crash the program.
            print_exc()
            return

        self._master.nidaqManager.runScan(self.signalDic, self.scanInfoDict)
        self._commChannel.sigScanStarted.emit()

    def scanDone(self):
        print('Scan done')
        if not self._widget.isContLaserMode() and not self._widget.continuousCheckEnabled():
            self.setScanButton(False)
            self._commChannel.sigScanEnded.emit()
        else:
            print('Repeat scan')
            self._master.nidaqManager.runScan(self.signalDic, self.scanInfoDict)

    def getParameters(self):
        if self.settingParameters:
            return

        self._analogParameterDict['target_device'] = []
        self._analogParameterDict['axis_length'] = []
        self._analogParameterDict['axis_step_size'] = []
        self._analogParameterDict['axis_centerpos'] = []
        self._analogParameterDict['axis_startpos'] = []
        for i in range(len(self.positioners)):
            positionerName = self._widget.getScanDim(i)
            size = self._widget.getScanSize(positionerName)
            stepSize = self._widget.getScanStepSize(positionerName)
            center = self._widget.getScanCenterPos(positionerName)
            start = list(self._master.positionersManager[positionerName].position.values())

            self._analogParameterDict['target_device'].append(positionerName)
            self._analogParameterDict['axis_length'].append(size)
            self._analogParameterDict['axis_step_size'].append(stepSize)
            self._analogParameterDict['axis_centerpos'].append(center)
            self._analogParameterDict['axis_startpos'].append(start)

        self._digitalParameterDict['target_device'] = []
        self._digitalParameterDict['TTL_start'] = []
        self._digitalParameterDict['TTL_end'] = []
        for deviceName, deviceInfo in self.TTLDevices.items():
            self._digitalParameterDict['target_device'].append(deviceName)
            self._digitalParameterDict['TTL_start'].append(self._widget.getTTLStarts(deviceName))
            self._digitalParameterDict['TTL_end'].append(self._widget.getTTLEnds(deviceName))

        self._digitalParameterDict['sequence_time'] = self._widget.getSeqTimePar()
        self._analogParameterDict['sequence_time'] = self._widget.getSeqTimePar()

    def setContLaserPulses(self, isContLaserPulses):
        for i in range(len(self.positioners)):
            positionerName = self._widget.scanPar['scanDim' + str(i)].currentText()
            self._widget.setScanDimEnabled(i, not isContLaserPulses)
            self._widget.setScanSizeEnabled(positionerName, not isContLaserPulses)
            self._widget.setScanStepSizeEnabled(positionerName, not isContLaserPulses)
            self._widget.setScanCenterPosEnabled(positionerName, not isContLaserPulses)

    def setScanButton(self, b):
        self._widget.setScanButtonChecked(b)
        if b: self.runScan()

    def updatePixels(self):
        self.getParameters()
        for index, positionerName in enumerate(self.positioners):
            if float(self._analogParameterDict['axis_step_size'][index]) != 0:
                pixels = round(float(self._analogParameterDict['axis_length'][index]) /
                               float(self._analogParameterDict['axis_step_size'][index]))
                self._widget.setScanPixels(positionerName, pixels)

    def plotSignalGraph(self):
        if self.settingParameters:
            return

        self.getParameters()
        TTLCycleSignalsDict = self._master.scanManager.getTTLCycleSignalsDict(
            self._digitalParameterDict
        )

        sampleRate = self._master.scanManager.sampleRate

        areas = []
        signals = []
        colors = []
        for deviceName, signal in TTLCycleSignalsDict.items():
            isLaser = deviceName in self._setupInfo.lasers
            areas.append(
                np.linspace(
                    0, self._digitalParameterDict['sequence_time'] * sampleRate, len(signal)
                )
            )
            signals.append(signal.astype(np.uint8))
            colors.append(
                guitools.colorutils.wavelengthToHex(
                    self._setupInfo.lasers[deviceName].wavelength
                ) if isLaser else '#ffffff'
            )
        self._widget.plotSignalGraph(areas, signals, colors, sampleRate)

    def attrChanged(self, key, value):
        if self.settingAttr or len(key) != 2:
            return

        if key[0] == _attrCategoryStage:
            self._analogParameterDict[key[1]] = value
            self.setParameters()
        elif key[0] == _attrCategoryTTL:
            self._digitalParameterDict[key[1]] = value
            self.setParameters()

    def setSharedAttr(self, category, attr, value):
        self.settingAttr = True
        try:
            self._commChannel.sharedAttrs[(category, attr)] = value
        finally:
            self.settingAttr = False

    def updateScanStageAttrs(self):
        self.getParameters()

        for key, value in self._analogParameterDict.items():
            self.setSharedAttr(_attrCategoryStage, key, value)

        positiveDirections = []
        for i in range(len(self.positioners)):
            positionerName = self._analogParameterDict['target_device'][i]
            positiveDirection = self._setupInfo.positioners[positionerName].isPositiveDirection
            positiveDirections.append(positiveDirection)

        self.setSharedAttr(_attrCategoryStage, 'positive_direction', positiveDirections)

    def updateScanTTLAttrs(self):
        self.getParameters()

        for key, value in self._digitalParameterDict.items():
            self.setSharedAttr(_attrCategoryTTL, key, value)


_attrCategoryStage = 'ScanStage'
_attrCategoryTTL = 'ScanTTL'
        

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
