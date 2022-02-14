"""
Created on Wed Jan 13 09:40:00 2021

@author: jonatanalvelid
"""
from imswitch.imcommon.model import initLogger
from .PositionerManager import PositionerManager



class ESP32StageManager(PositionerManager):
    SPEED=1000
    PHYS_FACTOR = 1

    def __init__(self, positionerInfo, name, **lowLevelManagers):
        super().__init__(positionerInfo, name, initialPosition={
            axis: 0 for axis in positionerInfo.axes
        })
        self._rs232manager = lowLevelManagers['rs232sManager'][
            positionerInfo.managerProperties['rs232device']
        ]
        self.__logger = initLogger(self, instanceName=name)

        self.backlash_x = 0
        self.backlash_y = 0
        self.backlash_z= 0 # TODO: Map that to the JSON!



    def move(self, value, axis):
        if axis == 'X':
            self._rs232manager._esp32.move_x(value*self.PHYS_FACTOR, self.SPEED, is_blocking=False, backlash = self.backlash_x)
        elif axis == 'Y':
            self._rs232manager._esp32.move_y(value*self.PHYS_FACTOR, self.SPEED, is_blocking=False, backlash = self.backlash_y)
        elif axis == 'Z':
            self._rs232manager._esp32.move_z(value*self.PHYS_FACTOR, self.SPEED, is_blocking=False, backlash = self.backlash_z)
        else:
            print('Wrong axis, has to be "X" "Y" or "Z".')
            return
        self._position[axis] = self._position[axis] + value

    def setPosition(self, value, axis):
        self._position[axis] = value

    def closeEvent(self):
        pass
    
    def get_abs(self):
        return self._position




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
