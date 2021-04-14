import numpy as np

from imswitch.imcontrol.model import IncompatibilityError
from imswitch.imcontrol.model.SignalDesigner import SignalDesignerFactory


class ScanManagerFactory:
    """Factory class for creating a ScanManager object. Factory checks
    that the new object is a valid ScanManager."""

    def __new__(cls, className, setupInfo, *args):
        scanManager = globals()[className](setupInfo, *args)
        if scanManager.isValidChild():
            return scanManager


class SuperScanManager:
    def isValidChild(self):  # For future possible implementation
        return True

    def _parameterCompatibility(self, parameterDict):
        raise NotImplementedError("Method not implemented in child")


class ScanManager(SuperScanManager):
    """ ScanManager helps with generating signals for scanning. """

    def __init__(self, setupInfo):
        super().__init__()
        self.__setupInfo = setupInfo
        self.__stageScanDesigner = SignalDesignerFactory(setupInfo, 'stageScanDesigner')
        self.__TTLCycleDesigner = SignalDesignerFactory(setupInfo, 'TTLCycleDesigner')

        self._expectedSyncParameters = []

    def _parameterCompatibility(self, parameterDict):
        stageExpected = set(self.__stageScanDesigner.expectedParameters)
        stageIncoming = set(parameterDict['stageParameterList'])

        if not stageExpected == stageIncoming:
            raise IncompatibilityError('Incompatible stage scan parameters')

        TTLExpected = set(self.__TTLCycleDesigner.expectedParameters)
        TTLIncoming = set(parameterDict['TTLParameterList'])

        if not TTLExpected == TTLIncoming:
            raise IncompatibilityError('Incompatible TTL parameters')

        # syncExpected = set(self.expectedSyncParameters)
        # syncIncoming = set(stageParameterList)

        # if not syncExpected == syncIncoming:
        #     raise IncompatibilityError('Incompatible sync parameters')

    def getTTLCycleSignalsDict(self, TTLParameters):
        """ Generates TTL scan signals. """
        return self.__TTLCycleDesigner.make_signal(TTLParameters, self.__setupInfo)

    def makeFullScan(self, stageScanParameters, TTLParameters, staticPositioner=False):
        """ Generates stage and TTL scan signals. """

        TTLCycleSignalsDict = self.getTTLCycleSignalsDict(TTLParameters)

        # Calculate samples to zero pad TTL signals with
        TTLZeroPadSamples = stageScanParameters['Return_time_seconds'] * TTLParameters['Sample_rate']
        if not TTLZeroPadSamples.is_integer():
            print('WARNING: Non-integer number of return samples, rounding up')
        TTLZeroPadSamples = np.int(np.ceil(TTLZeroPadSamples))

        if not staticPositioner:
            stageScanSignalsDict, positions = self.__stageScanDesigner.make_signal(
                stageScanParameters, self.__setupInfo, returnFrames=True
            )

            # Tile and pad TTL signals according to sync parameters
            for target, signal in TTLCycleSignalsDict.items():
                signal = np.tile(signal, positions[0])
                signal = np.append(signal, np.zeros(TTLZeroPadSamples, dtype='bool'))
                signal = np.tile(signal, positions[1] * positions[2])

                TTLCycleSignalsDict[target] = signal
        else:
            stageScanSignalsDict = {}

        return {'stageScanSignalsDict': stageScanSignalsDict,
                'TTLCycleSignalsDict': TTLCycleSignalsDict}


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
