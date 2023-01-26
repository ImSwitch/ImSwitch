from imswitch.imcommon.model import initLogger
from .PositionerManager import PositionerManager
from thorlabs_apt_device.devices.bsc import BSC
from serial.serialutil import SerialException
import numpy as np
import time

STEPS_PER_REV = 409600
REV_PER_MM = 2


move_step_mm = 1


class BSC203StageManager(PositionerManager):

    def __init__(self, positionerInfo, name, **lowLevelManagers):
        super().__init__(positionerInfo, name, initialPosition={
            axis: 0 for axis in positionerInfo.axes
        })
        self.__logger = initLogger(self, instanceName=name)
        home = False
        port = 'COM9'
        try:
            self.dev = BSC(serial_port=port, vid=None, pid=None, manufacturer=None, product=None, serial_number=None,
                           location=None, home=home, x=3, invert_direction_logic=False, swap_limit_switches=True)
            #self.initialize()
        except SerialException:
            self.__logger.debug('Could not initialize NanoMax motorized stage, might not be switched on.')
            self.dev = None
        if home:
            self.__logger.debug('Is homing')
            while self.homing():
                pass
            self.__logger.debug('Finished homing')

    def initialize(self):
        self.dev.set_velocity_params(acceleration=4506, max_velocity=21987328 * 5, bay=0, channel=0)
        self.dev.set_velocity_params(acceleration=4506, max_velocity=21987328 * 5, bay=1, channel=0)
        self.dev.set_velocity_params(acceleration=4506, max_velocity=21987328 * 5, bay=2, channel=0)

    def homeAll(self):
        self.dev.home(bay=0)
        self.dev.home(bay=1)
        self.dev.home(bay=2)
        while self.homing():
            pass

    def homing(self):
        return not all([self.dev.status_[0][0]['homed'],
                        self.dev.status_[1][0]['homed'],
                        self.dev.status_[2][0]['homed']])

    def to_enc_steps(self, mm):
        steps = mm * REV_PER_MM * STEPS_PER_REV
        return int(steps)

    def to_mm(self, steps):
        mm = steps / (REV_PER_MM * STEPS_PER_REV)
        return mm

    def move(self, dist, axis):
        self._position[axis] = self._position[axis] + dist
        if axis == "X":
            channel = 0
        elif axis == "Y":
            channel = 1
        elif axis == "Z":
            channel = 2
        self.move_relative_mm(dist, channel)

    def setPosition(self, value, axis):
        if axis == "X":
            channel = 0
        elif axis == "Y":
            channel = 1
        elif axis == "Z":
            channel = 2
        pos = self.to_enc_steps(value / 1000)
        self.dev.move_absolute(pos, now=True, bay=channel, channel=0)

    def move_relative_mm(self, value, axis):
        self.setJogPars(np.abs(value / 1000), axis)
        self.jog(np.sign(value), axis)

    def setJogPars(self, size_mm, axis):
        self.dev.set_jog_params(self.to_enc_steps(size_mm),
                                4506,
                                21987328 * 5,
                                continuous=False,
                                immediate_stop=False,
                                bay=axis,
                                channel=0)

    def jog(self, sign, axis):
        if sign == 1:
            direction = "forward"
        else:
            direction = "reverse"
        self.dev.move_jog(direction=direction, bay=axis, channel=0)

    def get_abs(self, axis):
        return self._position[axis]

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
