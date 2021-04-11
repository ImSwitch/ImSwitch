from .PositionerManager import PositionerManager


class NidaqAOPositionerManager(PositionerManager):
    """ PositionerManager for analog NI-DAQ-controlled positioners. """

    def __init__(self, positionerInfo, name, **kwargs):
        self._nidaqManager = kwargs['nidaqManager']
        self._conversionFactor = positionerInfo.managerProperties['conversionFactor']
        self._minVolt = positionerInfo.managerProperties['minVolt']
        self._maxVolt = positionerInfo.managerProperties['maxVolt']
        super().__init__(name, initialPosition=0)

    def move(self, dist):
        return self.setPosition(self._position + dist)

    def setPosition(self, position):
        self._position = position
        self._nidaqManager.setAnalog(target=self.name,
                                     voltage=position / self._conversionFactor,
                                     min_val=self._minVolt,
                                     max_val=self._maxVolt)
        return position


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
