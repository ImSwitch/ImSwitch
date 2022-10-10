from imswitch.imcommon.model import initLogger
from .PositionerManager import PositionerManager
from thorlabs_apt_device.devices.bsc import BSC


STEPS_PER_REV = 409600
REV_PER_MM = 2

move_step_mm = 1

Xchan = 1
Ychan = 0
Zchan = 2


class BSC203StageManager(PositionerManager):


    def __init__(self, positionerInfo, name, **lowLevelManagers):
        super().__init__(positionerInfo, name, initialPosition={
            axis: 0 for axis in positionerInfo.axes
        })
        self.port = positionerInfo.port
        self.__logger = initLogger(self, instanceName=name)

        self.is_enabled = False
        self.speed = 1000
        self.backlash_x = 0
        self.backlash_y = 0
        self.backlash_z= 0 # TODO: Map that to the JSON!

    def move(self, value=0, axis="X", is_blocking = False, is_absolute=False):
        if axis == 'X':
            self._rs232manager._esp32.move_x(value, self.speed, is_blocking=is_blocking, is_absolute=is_absolute, is_enabled=self.is_enabled)
            self._position[axis] = self._position[axis] + value
        elif axis == 'Y':
            self._rs232manager._esp32.move_y(value, self.speed, is_blocking=is_blocking, is_absolute=is_absolute, is_enabled=self.is_enabled)
            self._position[axis] = self._position[axis] + value
        elif axis == 'Z':
            self._rs232manager._esp32.move_z(value, self.speed, is_blocking=is_blocking, is_absolute=is_absolute, is_enabled=self.is_enabled)
            self._position[axis] = self._position[axis] + value
        elif axis == 'XYZ':
            self._rs232manager._esp32.move_xyz(value, self.speed, is_blocking=is_blocking, is_absolute=is_absolute, is_enabled=self.is_enabled)
            self._position["X"] = self._position["X"] + value[0]
            self._position["Y"] = self._position["Y"] + value[1]
            self._position["Z"] = self._position["Z"] + value[2]
        else:
            print('Wrong axis, has to be "X" "Y" or "Z".')
            return

    def setEnabled(self, is_enabled):
        self.is_enabled = is_enabled

    def setSpeed(self, speed):
        self.speed = speed

    def setPosition(self, value, axis):
        if value: value+=1 # TODO: Firmware weirdness
        self._rs232manager._esp32.set_position(axis=axis, position=value)
        self._position[axis] = value

    def closeEvent(self):
        pass

    def get_abs(self, axis=1):
        abspos = self._rs232manager._esp32.get_position(axis=axis)
        return abspos





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
