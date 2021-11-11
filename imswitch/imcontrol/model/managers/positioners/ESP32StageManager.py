"""
Created on Wed Jan 13 09:40:00 2021

@author: jonatanalvelid
"""
from imswitch.imcommon.model import initLogger
from .PositionerManager import PositionerManager
from imswitch.imcontrol.model.interfaces.ESP32RestAPI import ESP32Client

SPEED=200
PHYS_FACTOR = 1
class ESP32StageManager(PositionerManager):

    def __init__(self, positionerInfo, name, *args, **kwargs):
        self.__logger = initLogger(self, instanceName=name)
        self.power = 0

        self.esp32 = ESP32Client(positionerInfo.managerProperties['host'], port=80)

        super().__init__(positionerInfo, name, initialPosition={
            axis: 0 for axis in positionerInfo.axes
        })

    def move(self, value, axis):
        if axis == 'X':
            self.esp32.move_x(value*PHYS_FACTOR, SPEED)
        elif axis == 'Y':
            self.esp32.move_y(value*PHYS_FACTOR, SPEED)
        elif axis == 'Z':
            self.esp32.move_z(value*PHYS_FACTOR, SPEED)
        else:
            print('Wrong axis, has to be "X" "Y" or "Z".')
            return
        self._position[axis] = self._position[axis] + value

    def setPosition(self, value, axis):
        self._position[axis] = value

    def closeEvent(self):
        pass



# Copyright (C) 2020, 2021 The imswitch developers
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
