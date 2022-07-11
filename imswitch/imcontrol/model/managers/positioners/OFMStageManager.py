from imswitch.imcommon.model import initLogger
from .PositionerManager import PositionerManager
import time

PHYS_FACTOR = 1
class OFMStageManager(PositionerManager):


    def __init__(self, positionerInfo, name, **lowLevelManagers):
        super().__init__(positionerInfo, name, initialPosition={
            axis: 0 for axis in positionerInfo.axes
        })
        self._rs232manager = lowLevelManagers['rs232sManager'][
            positionerInfo.managerProperties['rs232device']
        ]
        self.__logger = initLogger(self, instanceName=name)

        
        
    def move(self, value=0, axis="X", is_absolute=False, is_blocking=False):
        if axis == 'X':
            displacement = {"x":value, "y":0, "z":0}
            self._rs232manager._OFM.move_rel(displacement)
            self._position[axis] = self._position[axis] + value
        elif axis == 'Y':
            displacement = {"x":0, "y":value, "z":0}
            self._rs232manager._OFM.move_rel(displacement)
            self._position[axis] = self._position[axis] + value
        elif axis == 'Z':
            displacement = {"x":0, "y":0, "z":value}
            self._rs232manager._OFM.move_rel(displacement)
            self._position[axis] = self._position[axis] + value
        elif axis == 'XYZ':
            displacement = {"x":value[0], "y":value[1], "z":value[2]}
            self._rs232manager._OFM.move_rel(displacement)
            self._position["X"] = self._position["X"] + value[0]
            self._position["Y"] = self._position["Y"] + value[1]
            self._position["Z"] = self._position["Z"] + value[2]
        else:
            print('Wrong axis, has to be "X" "Y" or "Z".')
            return
    
    def closeEvent(self):
        pass

    def get_abs(self):
        return self._rs232manager._OFM.get_position_array()

    def setPosition(self, value, axis):
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
