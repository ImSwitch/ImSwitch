from ctypes import *
import time
import os
import sys
import platform
import tempfile
import re

if sys.version_info >= (3,0):
    import urllib.parse

from imswitch.imcommon.framework import Signal, SignalInterface
from imswitch.imcommon.model import initLogger


class StandaMotorManager(SignalInterface):
    """ StandaMotorManager that deals with a Standa-branded motor controller,
    for example 8SMC5 for a motorized rotation mount. 
    """
    def __init__(self, rotatorInfo, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        if rotatorInfo is None:
            return
        self._device_id = rotatorInfo.motorListIndex
        self._lib_loc = rotatorInfo.ximcLibLocation
        self._steps_per_turn = rotatorInfo.stepsPerTurn
        self._microsteps_per_step = rotatorInfo.microstepsPerStep
        self._position = 0

        self._motor = self._getMotorObj(self._device_id, self._lib_loc, self._steps_per_turn, self._microsteps_per_step)
        #self.get_info()

    def get_info(self):
        info = self._motor.test_info()
        for info_piece in info:
            self.__logger.debug(f'{info_piece}: {info[info_piece]}')

    def position(self):
        """ Return the position as a float. """
        return self._position

    def move_rel(self, move_dist):
        self.__logger.debug(f'Move relative {move_dist}')
        self._position += move_dist
        self._motor.moverel(move_dist)
        [pos, upos] = self._motor.get_pos()
        self.__logger.debug(f'Current position {pos}, {upos}')

    def move_abs(self, move_pos):
        self.__logger.debug(f'Position absolute {move_pos}')
        self._position = move_pos
        self._motor.moveabs(move_pos)
        [pos, upos] = self._motor.get_pos()
        self.__logger.debug(f'Current position {pos}, {upos}')

    def startMovement(self):
        self._motor.startmove()

    def stopMovement(self):
        self._motor.stopmove()

    def _performSafeMotorAction(self, function):
        """ Used to change motor properties that need idle state to be adjusted. """
        try:
            function()
        except Exception:
            self.stopMovement()
            function()
            self.startMovement()

    def _getMotorObj(self, device_id, lib_loc, steps_per_turn, microsteps_per_step):
        try:
            from imswitch.imcontrol.model.interfaces.standamotor import StandaMotor
            motor = StandaMotor(device_id, lib_loc, steps_per_turn, microsteps_per_step)
            self.__logger.info(f'Initialized Standa motor {device_id}')
        except Exception:
            self.__logger.warning(f'Failed to initialize Standa motor {device_id}, loading mocker')
            from imswitch.imcontrol.model.interfaces.standamotor import MockStandaMotor
            motor = MockStandaMotor(lib_loc)
        return motor

    def close(self):
        self._motor.close()


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
