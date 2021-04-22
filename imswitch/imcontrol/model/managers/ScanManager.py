from abc import ABC, abstractmethod

from imswitch.imcontrol.model import IncompatibilityError
from imswitch.imcontrol.model.SignalDesigner import SignalDesignerFactory


class ScanManagerFactory:
    """Factory class for creating a ScanManager object. Factory checks
    that the new object is a valid ScanManager."""

    def __new__(cls, className, setupInfo, *args):
        scanManager = globals()[className](setupInfo, *args)
        if scanManager.isValidChild():
            return scanManager


class SuperScanManager(ABC):
    def isValidChild(self):  # For future possible implementation
        return True

    @abstractmethod
    def _parameterCompatibility(self, parameterDict):
        pass


class ScanManager(SuperScanManager):
    """ ScanManager helps with generating signals for scanning. """

    def __init__(self, setupInfo):
        super().__init__()
        self._setupInfo = setupInfo
        self._scanDesigner = SignalDesignerFactory(setupInfo, 'scanDesigner')
        self._TTLCycleDesigner = SignalDesignerFactory(setupInfo, 'TTLCycleDesigner')

        self._expectedSyncParameters = []

    @property
    def TTLTimeUnits(self):
        return self._TTLCycleDesigner.timeUnits

    def _parameterCompatibility(self, parameterDict):
        stageExpected = set(self._scanDesigner.expectedParameters)
        stageIncoming = set(parameterDict['stageParameterList'])

        if not stageExpected.issubset(stageIncoming):
            raise IncompatibilityError('Incompatible stage scan parameters')

        TTLExpected = set(self._TTLCycleDesigner.expectedParameters)
        TTLIncoming = set(parameterDict['TTLParameterList'])

        if not TTLExpected.issubset(TTLIncoming):
            raise IncompatibilityError('Incompatible TTL parameters')

        # syncExpected = set(self.expectedSyncParameters)
        # syncIncoming = set(stageParameterList)

        # if not syncExpected.issubset(syncIncoming):
        #     raise IncompatibilityError('Incompatible sync parameters')

    def getTTLCycleSignalsDict(self, TTLParameters):
        """ Generates TTL scan signals. """
        return self._TTLCycleDesigner.make_signal(TTLParameters, self._setupInfo)

    def makeFullScan(self, scanParameters, TTLParameters, staticPositioner=False):
        """ Generates stage and TTL scan signals. """
        if not staticPositioner:
            scanSignalsDict, positions, scanInfoDict = self._scanDesigner.make_signal(
                scanParameters, self._setupInfo
            )
            if not self._scanDesigner.checkSignalComp(
                    scanParameters, self._setupInfo, scanInfoDict
            ):
                print('Signal voltages outside scanner ranges: try scanning a smaller ROI or a'
                      ' slower scan.')
                return

            TTLCycleSignalsDict = self._TTLCycleDesigner.make_signal(
                TTLParameters, self._setupInfo, scanInfoDict
            )
        else:
            TTLCycleSignalsDict = self._TTLCycleDesigner.make_signal(
                TTLParameters, self._setupInfo
            )
            scanSignalsDict = {}
            scanInfoDict = {}

        return (
            {'scanSignalsDict': scanSignalsDict,
             'TTLCycleSignalsDict': TTLCycleSignalsDict},
            scanInfoDict
        )


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
