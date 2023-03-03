from imswitch.imcommon.model import initLogger
from .RotatorManager import RotatorManager


class StandaRotatorManager(RotatorManager):
    """ StandaMotorManager that deals with a Standa-branded motor controller,
    for example 8SMC5 for a motorized rotation mount. 
    """
    def __init__(self, rotatorInfo, name, *args, **kwargs):
        super().__init__(rotatorInfo, name, *args, **kwargs)
        self.__logger = initLogger(self)

        if rotatorInfo is None:
            return
        self._device_id = rotatorInfo.managerProperties['motorListIndex']
        self._lib_loc = rotatorInfo.managerProperties['ximcLibLocation']
        self._steps_per_turn = rotatorInfo.managerProperties['stepsPerTurn']
        self._microsteps_per_step = rotatorInfo.managerProperties['microstepsPerStep']

        self._motor = self._getMotorObj(self._device_id, self._lib_loc, self._steps_per_turn, self._microsteps_per_step)
        
        self.get_pos()

    def get_info(self):
        info = self._motor.test_info()
        for info_piece in info:
            self.__logger.debug(f'{info_piece}: {info[info_piece]}')

    def position(self):
        """ Return the position as a float. """
        return self._position

    def get_pos(self):
        self._position = self._motor.get_pos()

    def move_rel(self, move_dist):
        self._motor.moverel(move_dist)
        self.get_pos()

    def move_abs(self, move_pos):
        self._motor.moveabs(move_pos)
        self.get_pos()

    def set_zero_pos(self):
        self._motor.set_zero_pos()
        self.get_pos()

    def set_rot_speed(self, speed):
        self._motor.set_rot_speed(speed)

    def start_cont_rot(self):
        self._motor.start_cont_rot()

    def stop_cont_rot(self):
        self._motor.stop_cont_rot()

    def set_sync_in_pos(self, abs_pos_deg):
        self._motor.set_sync_in_settings(abs_pos_deg)

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


# Copyright (C) 2020-2023 ImSwitch developers
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
