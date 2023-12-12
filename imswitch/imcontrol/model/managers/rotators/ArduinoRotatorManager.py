from imswitch.imcommon.model import initLogger
from .RotatorManager import RotatorManager
import time
import pdb


class ArduinoRotatorManager(RotatorManager):
    """ Arduino stepper motor manager.
    """

    def __init__(self, rotatorInfo, name, *args, **kwargs):
        super().__init__(rotatorInfo, name, *args, **kwargs)
        self.__logger = initLogger(self)

        if rotatorInfo is None:
            return
        self._device_id = rotatorInfo.managerProperties['motorListIndex']
        self._steps_per_turn = rotatorInfo.managerProperties['stepsPerTurn']

        self._motor = self._getMotorObj(self._device_id, self._steps_per_turn)
        self._position = self._motor.get_pos()
        # pdb.set_trace()

    def get_position(self):
        """ Return the position as a float. """
        return self._position

    def move_rel(self, angle):
        """Calculate steps from angle and run
        move_rel_steps method"""
        steps = self._motor.deg2steps(angle)
        self.move_rel_steps(steps)

    def move_rel_steps(self, steps):
        """Move rotator relative by steps equal to steps.
        Connects arduinoStepper signals and waits until the movement
        finishes.

        Args:
            steps (int): number of motor steps
        """
        self._motor.start_move.connect(self._motor.moverel_steps)
        self._motor.move_done.connect(self.post_move)
        self._motor.steps = steps
        self._motor.start_move.emit()

    def post_move(self):
        """Every step's signal move_done ios connected to this
        function. Disconnects signal and takes care of current
        position values.
        """
        self._position = self._motor.get_pos()
        self.__logger.debug(f'position post move: {self._position}')
        self._motor.start_move.disconnect()
        self._motor.move_done.disconnect()
        self._motor.board.stepper_get_current_position(
                        self._motor.motor,
                        self._motor.current_position_callback)
        time.sleep(.2)
        self.trigger_update_position()

    def trigger_update_position(self):
        self._motor.emit_trigger_update_position()

    def move_abs(self, angle):
        """Converts angle to steps and calls
        move_abs_steps()

        Args:
            angle (int): rotation angle.
        """
        steps = self._motor.deg2steps(angle)
        self.move_abs_steps(steps)

    def move_abs_steps(self, steps):
        """Absolute movement, which is converted to relative in
        respect to current position.

        Args:
            steps (int): number of motor steps
        """
        self._motor.board.stepper_get_current_position(
                        self._motor.motor,
                        self._motor.current_position_callback)

        # calculate relative steps from current position
        to_move = steps - self._motor.current_pos[0]
        self.__logger.debug(f'func move_abs, steps to take: {to_move}')
        self.move_rel_steps(to_move)

    def set_zero_pos(self):
        self._motor.set_zero_pos()
        self._position = self._motor.get_pos()

    def set_rot_speed(self, speed):
        self._motor.set_rot_speed(speed)

    def start_cont_rot(self):
        self._motor.start_cont_rot()

    def stop_cont_rot(self):
        self._motor.stop_cont_rot()

    def set_sync_in_pos(self, abs_pos_deg):
        self._motor.set_sync_in_settings(abs_pos_deg)

    def _getMotorObj(self, device_id, steps_per_turn):
        try:
            from imswitch.imcontrol.model.interfaces.arduinoStepper import ArduinoStepper
            motor = ArduinoStepper(device_id, steps_per_turn)
            self.__logger.info(f'Initialized Arduino stepper motor {device_id}')
        except Exception:
            self.__logger.warning(f'Failed to initialize Arduino stepper motor {device_id}, loading mocker')
            from imswitch.imcontrol.model.interfaces.arduinoStepper import MockArduinoStepper
            motor = MockArduinoStepper(device_id, steps_per_turn)
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
