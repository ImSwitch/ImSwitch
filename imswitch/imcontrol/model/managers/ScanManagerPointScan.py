from .ScanManagerBase import SuperScanManager


class ScanManagerPointScan(SuperScanManager):
    """ ScanManager helps with generating signals for scanning. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def makeFullScan(self, scanParameters, TTLParameters):
        """ Generates stage and TTL scan signals. """
        self._checkScanDefined()
        if not self._scanDesigner.checkSignalLength(
                scanParameters, self._setupInfo
        ):
            self._logger.error(
                'Signal too long: try scanning a smaller ROI, faster, or with a larger pixel'
                ' size.'
            )
            return
        scanSignalsDict, positions, scanInfoDict = self.getScanSignalsDict(scanParameters)
        if not self._scanDesigner.checkSignalComp(
                scanParameters, self._setupInfo, scanInfoDict
        ):
            self._logger.error(
                'Signal voltages outside scanner ranges: try scanning a smaller ROI or a slower'
                ' scan.'
            )
            return
        print(TTLParameters)
        TTLCycleSignalsDict = self.getTTLCycleSignalsDict(TTLParameters, scanInfoDict)

        return (
            {'scanSignalsDict': scanSignalsDict,
             'TTLCycleSignalsDict': TTLCycleSignalsDict},
            scanInfoDict
        )


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
