import configparser
import functools
from logging import exception
import os
import traceback
from ast import literal_eval

import numpy as np

from imswitch.imcommon.model import APIExport, dirtools, initLogger
from imswitch.imcommon.view.guitools import colorutils
from imswitch.imcontrol.view import guitools
from ..basecontrollers import SuperScanController


class ScanController(SuperScanController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        self.settingAttr = False
        self.settingParameters = False

        self._analogParameterDict = {}
        self._digitalParameterDict = {}
        self.signalDict = None
        self.scanInfoDict = None
        self.isRunning = False
        self.doingNonFinalPartOfSequence = False

        self.positioners = {
            pName: pManager for pName, pManager in self._setupInfo.positioners.items()
            if pManager.forScanning
        }
        self.TTLDevices = self._setupInfo.getTTLDevices()

        self._widget.initControls(
            self.positioners.keys(),
            self.TTLDevices.keys()
        )

        self.scanDir = os.path.join(dirtools.UserFileDirs.Root, 'imcontrol_scans')
        if not os.path.exists(self.scanDir):
            os.makedirs(self.scanDir)

        self.getParameters()
        self.updatePixels()
        #self.plotSignalGraph()
        self.updateScanStageAttrs()
        self.updateScanTTLAttrs()

        # Connect NidaqManager signals
        self._master.nidaqManager.sigScanBuilt.connect(
            lambda _, deviceList: self.emitScanSignal(self._commChannel.sigScanBuilt, deviceList)
        )
        self._master.nidaqManager.sigScanStarted.connect(
            lambda: self.emitScanSignal(self._commChannel.sigScanStarted)
        )
        self._master.nidaqManager.sigScanDone.connect(self.scanDone)
        self._master.nidaqManager.sigScanBuildFailed.connect(self.scanFailed)

        # Connect CommunicationChannel signals
        self._commChannel.sigRunScan.connect(self.runScanExternal)
        self._commChannel.sigAbortScan.connect(self.abortScan)
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged)
        self._commChannel.sigToggleBlockScanWidget.connect(lambda block: self.toggleBlockWidget(block))
        self._commChannel.sigRequestScanParameters.connect(self.sendScanParameters)
        self._commChannel.sigSetAxisCenters.connect(lambda devices, centers: self.setCenterParameters(devices, centers))

        # Connect ScanWidget signals
        self._widget.sigSaveScanClicked.connect(self.saveScan)
        self._widget.sigLoadScanClicked.connect(self.loadScan)
        self._widget.sigRunScanClicked.connect(self.runScan)
        #self._widget.sigSeqTimeParChanged.connect(self.plotSignalGraph)
        self._widget.sigSeqTimeParChanged.connect(self.updateScanTTLAttrs)
        self._widget.sigStageParChanged.connect(self.updatePixels)
        self._widget.sigStageParChanged.connect(self.updateScanStageAttrs)
        #self._widget.sigSignalParChanged.connect(self.plotSignalGraph)
        self._widget.sigSignalParChanged.connect(self.updateScanTTLAttrs)


    def getDimsScan(self):
        # TODO: Make sure this works as intended
        self.getParameters()

        lengths = self._analogParameterDict['axis_length']
        stepSizes = self._analogParameterDict['axis_step_size']

        x = lengths[0] / stepSizes[0]
        y = lengths[1] / stepSizes[1]

        return x, y

    def getNumScanPositions(self):
        """ Returns the number of scan positions for the configured scan. """
        _, positions, _ = self._master.scanManager.getScanSignalsDict(self._analogParameterDict)
        numPositions = functools.reduce(lambda x, y: x * y, positions)
        return numPositions

    def saveScan(self):
        fileName = guitools.askForFilePath(self._widget, 'Save scan', self.scanDir, isSaving=True)
        if not fileName:
            return

        self.saveScanParamsToFile(fileName)

    @APIExport(runOnUIThread=True)
    def saveScanParamsToFile(self, filePath: str) -> None:
        """ Saves the set scanning parameters to the specified file. """
        self.getParameters()
        config = configparser.ConfigParser()
        config.optionxform = str

        config['analogParameterDict'] = self._analogParameterDict
        config['digitalParameterDict'] = self._digitalParameterDict

        with open(filePath, 'w') as configfile:
            config.write(configfile)

    def loadScan(self):
        fileName = guitools.askForFilePath(self._widget, 'Load scan', self.scanDir)
        if not fileName:
            return

        self.loadScanParamsFromFile(fileName)

    @APIExport(runOnUIThread=True)
    def loadScanParamsFromFile(self, filePath: str) -> None:
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
            for i in range(len(self._analogParameterDict['target_device'])):
                positionerName = self._analogParameterDict['target_device'][i]
                self._widget.setScanDim(i, positionerName)
                self._widget.setScanSize(positionerName,
                                         self._analogParameterDict['axis_length'][i])
                self._widget.setScanStepSize(positionerName,
                                             self._analogParameterDict['axis_step_size'][i])
                self._widget.setScanCenterPos(positionerName,
                                              self._analogParameterDict['axis_centerpos'][i])

            setTTLDevices = []
            for i in range(len(self._digitalParameterDict['target_device'])):
                deviceName = self._digitalParameterDict['target_device'][i]
                self._widget.setTTLSequences(deviceName, self._digitalParameterDict['TTL_sequence'][i])
                setTTLDevices.append(deviceName)

            for deviceName in self.TTLDevices:
                if deviceName not in setTTLDevices:
                    self._widget.unsetTTL(deviceName)

            self._widget.setSeqTimePar(self._digitalParameterDict['sequence_time'])
        finally:
            self.settingParameters = False
            #self.plotSignalGraph()

    def runScanExternal(self, recalculateSignals, isNonFinalPartOfSequence):
        self._widget.setScanMode()
        self._widget.setRepeatEnabled(False)
        self.runScanAdvanced(recalculateSignals=recalculateSignals,
                             isNonFinalPartOfSequence=isNonFinalPartOfSequence,
                             sigScanStartingEmitted=True)

    def runScanAdvanced(self, *, recalculateSignals=True, isNonFinalPartOfSequence=False,
                        sigScanStartingEmitted):
        """ Runs a scan with the set scanning parameters. """
        try:
            self._widget.setScanButtonChecked(True)
            self.isRunning = True

            if recalculateSignals or self.signalDict is None or self.scanInfoDict is None:
                self.getParameters()
                try:
                    self.signalDict, self.scanInfoDict = self._master.scanManager.makeFullScan(
                        self._analogParameterDict, self._digitalParameterDict
                    )
                except TypeError:
                    self.__logger.error(traceback.format_exc())
                    self.isRunning = False
                    self.abortScan()
                    return

            self.doingNonFinalPartOfSequence = isNonFinalPartOfSequence

            if not sigScanStartingEmitted:
                self.emitScanSignal(self._commChannel.sigScanStarting)
            # set positions of scanners not in scan from centerpos
            for index, positionerName in enumerate(self._analogParameterDict['target_device']):
                if positionerName not in self._positionersScan:
                    position = self._analogParameterDict['axis_centerpos'][index]
                    self._master.positionersManager[positionerName].setPosition(position, 0)
                    self.__logger.debug(f'Set {positionerName} center to {position} before scan')
            # run scan
            self._master.nidaqManager.runScan(self.signalDict, self.scanInfoDict)
        except Exception:
            self.__logger.error(traceback.format_exc())
            self.isRunning = False
            self.abortScan()

    def abortScan(self):
        self.doingNonFinalPartOfSequence = False  # So that sigScanEnded is emitted
        if not self.isRunning:
            self.scanFailed()

    def scanDone(self):
        self.isRunning = False

        if not self._widget.repeatEnabled():
            self.emitScanSignal(self._commChannel.sigScanDone)
            if not self.doingNonFinalPartOfSequence:
                self._widget.setScanButtonChecked(False)
                self.emitScanSignal(self._commChannel.sigScanEnded)
            # set positions of certain scanners to centerpos
            # TODO: fix this in a nicer way, to not hardcode the positionerNames here that should be centered.
            # Make it a .json parameter of the scanners?
            for index, positionerName in enumerate(self._analogParameterDict['target_device']):
                if positionerName == 'ND-PiezoZ':
                    position = self._analogParameterDict['axis_centerpos'][index]
                    self._master.positionersManager[positionerName].setPosition(position, 0)
                    self.__logger.debug(f'set {positionerName} center to {position} after scan')
        else:
            self.runScanAdvanced(sigScanStartingEmitted=True)

    def scanFailed(self):
        self.__logger.error('Scan failed')
        self.isRunning = False
        self.doingNonFinalPartOfSequence = False
        self._widget.setScanButtonChecked(False)
        self.emitScanSignal(self._commChannel.sigScanEnded)

    def getParameters(self):
        if self.settingParameters:
            return
        self._analogParameterDict['target_device'] = []
        self._analogParameterDict['axis_length'] = []
        self._analogParameterDict['axis_step_size'] = []
        self._analogParameterDict['axis_centerpos'] = []
        self._analogParameterDict['axis_startpos'] = []
        self._positionersScan = []
        for i in range(len(self.positioners)):
            self._positionersScan.append(self._widget.getScanDim(i))
        for positionerName in self._positionersScan:
            if positionerName != 'None':
                size = self._widget.getScanSize(positionerName)
                stepSize = self._widget.getScanStepSize(positionerName)
                center = self._widget.getScanCenterPos(positionerName)
                start = list(self._master.positionersManager[positionerName].position.values())
                self._analogParameterDict['target_device'].append(positionerName)
                self._analogParameterDict['axis_length'].append(size)
                self._analogParameterDict['axis_step_size'].append(stepSize)
                self._analogParameterDict['axis_centerpos'].append(center)
                self._analogParameterDict['axis_startpos'].append(start)
        for positionerName in self.positioners:
            if positionerName not in self._positionersScan:
                size = 1.0
                stepSize = 1.0
                center = self._widget.getScanCenterPos(positionerName)
                start = [0]
                self._analogParameterDict['target_device'].append(positionerName)
                self._analogParameterDict['axis_length'].append(size)
                self._analogParameterDict['axis_step_size'].append(stepSize)
                self._analogParameterDict['axis_centerpos'].append(center)
                self._analogParameterDict['axis_startpos'].append(start)

        self._digitalParameterDict['target_device'] = []
        self._digitalParameterDict['TTL_sequence'] = []
        self._digitalParameterDict['TTL_sequence_axis'] = []
        for deviceName, _ in self.TTLDevices.items():
            if not self._widget.getTTLIncluded(deviceName):
                continue

            self._digitalParameterDict['target_device'].append(deviceName)
            self._digitalParameterDict['TTL_sequence'].append(self._widget.getTTLSequence(deviceName))
            self._digitalParameterDict['TTL_sequence_axis'].append(self._widget.getTTLSequenceAxis(deviceName))

        self._digitalParameterDict['sequence_time'] = self._widget.getSeqTimePar()
        self._analogParameterDict['sequence_time'] = self._widget.getSeqTimePar()
        self._analogParameterDict['phase_delay'] = self._widget.getPhaseDelayPar()
        #self._analogParameterDict['extra_laser_on'] = self._widget.getExtraLaserOnPar()

    def updatePixels(self):
        self.getParameters()
        for index, positionerName in enumerate(self._analogParameterDict['target_device']):
            if float(self._analogParameterDict['axis_step_size'][index]) != 0:
                pixels = round(float(self._analogParameterDict['axis_length'][index]) /
                               float(self._analogParameterDict['axis_step_size'][index]))
                self._widget.setScanPixels(positionerName, pixels)

    def setCenterParameters(self, devices, centers):
        for centerpos, scannerSet in zip(centers, devices):
            # for every incoming device, listed in order of scanAxes
            for scannerAxis in self.positioners:
                # for every device, listed in order as device list
                if scannerSet == scannerAxis:
                    self._widget.setScanCenterPos(scannerSet, centerpos)

    def emitScanSignal(self, signal, *args):
        signal.emit(*args)

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
            if positionerName != 'None':
                positiveDirection = self._setupInfo.positioners[positionerName].isPositiveDirection
                positiveDirections.append(positiveDirection)

        self.setSharedAttr(_attrCategoryStage, 'positive_direction', positiveDirections)

    def updateScanTTLAttrs(self):
        self.getParameters()

        for key, value in self._digitalParameterDict.items():
            self.setSharedAttr(_attrCategoryTTL, key, value)

    @APIExport(runOnUIThread=True)
    def runScan(self) -> None:
        """ Runs a scan with the set scanning parameters. """
        self.runScanAdvanced(sigScanStartingEmitted=False)

    def toggleBlockWidget(self, block):
        """ Blocks/unblocks scan widget if scans are run from elsewhere. """
        self._widget.setEnabled(block)
        
    def sendScanParameters(self):
        self.getParameters()
        self._commChannel.sigSendScanParameters.emit(self._analogParameterDict, self._digitalParameterDict, self._positionersScan)


_attrCategoryStage = 'ScanStage'
_attrCategoryTTL = 'ScanTTL'


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
