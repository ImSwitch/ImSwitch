import traceback
import configparser

from ast import literal_eval

from ..basecontrollers import SuperScanController


class ScanControllerPointScan(SuperScanController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._widget.initControls(
            self.positioners.keys(),
            self.TTLDevices.keys()
        )

        self.updatePixels()
        self.updateScanStageAttrs()
        self.updateScanTTLAttrs()

    def setParameters(self):
        self.settingParameters = True
        try:
            for i in range(len(self._analogParameterDict['target_device'])):
                positionerName = self._analogParameterDict['target_device'][i]
                self._widget.setScanSize(positionerName,
                                         self._analogParameterDict['axis_length'][i])
                self._widget.setScanStepSize(positionerName,
                                             self._analogParameterDict['axis_step_size'][i])
                self._widget.setScanCenterPos(positionerName,
                                              self._analogParameterDict['axis_centerpos'][i])
            for i in range(len(self._analogParameterDict['scan_dim_target_device'])):
                scanDimName = self._analogParameterDict['scan_dim_target_device']
                self._widget.setScanDim(i, scanDimName)

            setTTLDevices = []
            for i in range(len(self._digitalParameterDict['target_device'])):
                deviceName = self._digitalParameterDict['target_device'][i]
                self._widget.setTTLSequences(deviceName, self._digitalParameterDict['TTL_sequence'][i])
                self._widget.setTTLSequenceAxis(deviceName, self._digitalParameterDict['TTL_sequence_axis'][i])
                setTTLDevices.append(deviceName)

            for deviceName in self.TTLDevices:
                if deviceName not in setTTLDevices:
                    self._widget.unsetTTL(deviceName)

            self._widget.setSeqTimePar(self._digitalParameterDict['sequence_time'])
        finally:
            self.settingParameters = False

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
                    self._logger.error(traceback.format_exc())
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
                    #self._logger.debug(f'Set {positionerName} center to {position} before scan')
            # run scan
            self._master.nidaqManager.runScan(self.signalDict, self.scanInfoDict)
        except Exception:
            self._logger.error(traceback.format_exc())
            self.isRunning = False
            self.abortScan()

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
        else:
            self.runScanAdvanced(sigScanStartingEmitted=True)

    def getParameters(self):
        self._logger.debug('getParameters')
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
        self._analogParameterDict['scan_dim_target_device'] = self._positionersScan
        self._logger.debug(self._analogParameterDict['scan_dim_target_device'])
        for positionerName in self.positioners:
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
        self._logger.debug('updatePixels')
        self.getParameters()
        for index, positionerName in enumerate(self._analogParameterDict['target_device']):
            if float(self._analogParameterDict['axis_step_size'][index]) != 0:
                pixels = round(float(self._analogParameterDict['axis_length'][index]) /
                               float(self._analogParameterDict['axis_step_size'][index]))
                self._widget.setScanPixels(positionerName, pixels)

    def emitScanSignal(self, signal, *args):
        signal.emit(*args)

    def saveScanParamsToFile(self, filePath: str) -> None:
        """ Saves the set scanning parameters to the specified file. """
        self.getParameters()
        config = configparser.ConfigParser()
        config.optionxform = str

        config['analogParameterDict'] = self._analogParameterDict
        config['digitalParameterDict'] = self._digitalParameterDict

        with open(filePath, 'w') as configfile:
            config.write(configfile)

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

        self.setParameters()


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
