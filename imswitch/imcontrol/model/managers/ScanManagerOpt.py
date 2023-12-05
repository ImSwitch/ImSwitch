from .ScanManagerBase import SuperScanManager


class ScanManagerOpt(SuperScanManager):
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
                'Signal length error'
            )
            print(scanParameters)
            print(TTLParameters)
            return

        scanSignalsDict = {'1': [0, 500, 100]}
        TTLCycleSignalsDict = {}
        scanInfoDict = {}

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
