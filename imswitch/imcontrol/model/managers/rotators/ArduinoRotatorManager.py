from imswitch.imcommon.model import initLogger
from .RotatorManager import RotatorManager
import time
import numpy as np
from telemetrix import telemetrix
from PyQt5.QtCore import pyqtSignal, pyqtSlot


class MockBoard():
    def stepper_get_current_position(self, *args, **kwargs):
        print('calling board')
        return

    def stepper_set_speed(self, *args, **kwargs):
        pass

    def stepper_set_max_speed(self, *args, **kwargs):
        pass

    def stepper_set_acceleration(self, *args, **kwargs):
        pass

    def stepper_move(self, *args, **kwargs):
        pass

    def stepper_run(self, *args, **kwargs):
        print('has to be stuck here')
        return True

    def stepper_run_speed(self, *args, **kwargs):
        pass

    def stepper_stop(self, *args, **kwargs):
        pass

    def shutdown(self):
        pass


class ArduinoRotatorManager(RotatorManager):
    """ Arduino stepper motor manager.
    """
    start_move = pyqtSignal()
    move_done = pyqtSignal(bool)
    update_position = pyqtSignal()

    def __init__(self, rotatorInfo, name, *args, **kwargs):
        super().__init__(rotatorInfo, name, *args, **kwargs)
        self.__logger = initLogger(self)
        self.__logger.info(name, self.name)

        if rotatorInfo is None:
            return
        self._device_id = rotatorInfo.managerProperties['motorListIndex']
        self._steps_per_turn = rotatorInfo.managerProperties['stepsPerTurn']

        self.speed = 100
        self.max_speed = 900
        self.acc = 200
        self.board = None
        self.motor = None
        self.turning = None
        self.current_pos = None
        # checking every wait_const if the movement is over
        self.wait_const = 0.5
        self._getMotorObj()

    def _getMotorObj(self):
        try:
            self.init_board()
            self.init_motor()
            self.__logger.info(f'Initialized Arduino stepper motor {self._device_id}')
        except Exception:
            self.__logger.warning(f'Failed to initialize Arduino stepper motor {self._device_id}, loading mocker')
            self.board = MockBoard()
            self.current_pos = (0, 0)
            self.init_mock()

    def close(self):
        """
        Shutdown board
        TODO: what if in continuous movement, or lost communication?
        """
        print('Motor shutting down.')
        return self.board.shutdown()

    def init_board(self):
        try:
            self.board = telemetrix.Telemetrix()
            time.sleep(4.5)
        except Exception:
            self.__logger.warning('Board Init failed')

    def init_motor(self):
        """Motor initialization

        Raises:
            ValueError: if unknown motor type
        """
        if self._device_id == 0:
            self.motor = self.board.set_pin_mode_stepper(
                            interface=4,
                            pin1=8, pin2=10, pin3=9, pin4=11,
                        )
        elif self._device_id == 1:
            self.motor = self.board.set_pin_mode_stepper(
                            interface=1,
                            pin1=2, pin2=3,
                        )

        self.set_max_speed(self.max_speed)
        self.turning = False
        self.board.stepper_set_current_position(
                                    self.motor, 0)

        self.set_rot_speed(self.speed)
        self.set_accel(self.acc)

    def get_position(self):
        """
        Get current absolute position of the motor.
        Position can be reset (set to 0) by set_zero_pos()

        Returns:
            tuple: position in (steps, degrees).
        """
        # updates self.current_pos in steps between 0- steps_per_turn
        self.board.stepper_get_current_position(
                                self.motor,
                                self.current_position_callback,
                                )
        time.sleep(.2)
        print('ArduinoRotatorManager current position', self.current_pos)
        return self.current_pos

    def set_rot_speed(self, speed):
        self.speed = speed
        try:
            self.board.stepper_set_speed(
                self.motor,
                speed)
        except Exception:
            self.__logger.warning('Initialize motor first')

    def set_max_speed(self, speed):
        """Set maximum speed of the given motor"""
        self.max_speed = speed
        try:
            self.board.stepper_set_max_speed(
                self.motor,
                self.max_speed)
        except Exception:
            self.__logger.warning('Initialize a motor first.')

    def set_accel(self, acc):
        self.acc = acc
        self.board.stepper_set_acceleration(self.motor, acc)

    def set_wait_const(self, const):
        self.wait_const = const

    @pyqtSlot()
    def moveRelSteps(self):
        """Move self.steps relative to the current position """
        self.board.stepper_move(self.motor, int(self.steps))
        self.turning = True
        if self.motor is not None:  # real rotator
            self.board.stepper_run(
                self.motor,
                completion_callback=self.move_finished_callback)
        else:  # mock rotator
            time.sleep(.2)
            self.move_finished_callback('Mock')

    def move_rel(self, angle):
        """Calculate steps from angle and run
        move_rel_steps method"""
        steps = self.deg2steps(angle)

        self.start_move.connect(self.moveRelSteps)
        self.move_done.connect(self.post_move)
        self.steps = steps
        self.start_move.emit()

    def move_abs(self, value, inSteps=False):
        """Converts angle to steps and calls
        move_abs_steps()

        Args:
            angle (int): rotation angle.
        """
        if inSteps:
            steps = value
        else:
            steps = self.deg2steps(value)

        if self.motor is not None:  # real rotator
            self.board.stepper_get_current_position(
                            self.motor,
                            self.current_position_callback)
        else:
            self.current_position_callback((0, 0, 0))
        self.start_move.connect(self.moveRelSteps)
        self.move_done.connect(self.post_move)
        self.steps = steps - self.current_pos[0]
        self.start_move.emit()

    def post_move(self):
        """Every step's signal move_done ios connected to this
        function. Disconnects signal and takes care of current
        position values.
        """
        self.get_position()
        self.start_move.disconnect()
        self.move_done.disconnect()
        if self.motor is not None:  # real rotator
            self.board.stepper_get_current_position(
                            self.motor,
                            self.current_position_callback)
        else:
            self.current_position_callback((0, 0, 0))
        time.sleep(.2)
        self.trigger_update_position()

    def trigger_update_position(self):
        print('trigger_update_positin')
        self.emit_trigger_update_position()

    #######################
    # Continuous rotation #
    #######################
    def start_cont_rot(self):
        """
        Move the stepper motor and keep cheking the
        for the running is over in the while loop.
        """
        self.board.stepper_set_speed(self.motor, self.speed)
        self.turning = True
        self.board.stepper_run_speed(
            self.motor)

    def stop_cont_rot(self):
        self.turning = False
        self.board.stepper_stop(self.motor)

    #############
    # Callbacks #
    #############
    def move_finished_callback(self, data):
        print('callback move finished', data)
        self.turning = False
        self.move_done.emit(self.turning)
        self.sigOptStepDone.emit()

    def emit_trigger_update_position(self):
        self.update_position.emit()

    def current_position_callback(self, data):
        """
        Current position data in form of
        motor_id, current position in steps, time_stamp
        """
        # for now tuple of steps, degrees
        steps = data[2] % self._steps_per_turn
        self.current_pos = (steps, self.steps2deg(steps))
        if steps != data[2]:
            self.board.stepper_set_current_position(
                                    self.motor, steps)

    # def is_running_callback(self, data):
    #     """Check if motor is running"""
    #     if data[1]:
    #         self.turning = True
    #     else:
    #         self.turning = False

    def set_zero_pos(self):
        self.board.stepper_set_current_position(
                                    self.motor, 0)
        self.current_pos = (0, 0)

    def deg2steps(self, d_deg):
        d = d_deg/360 * self._steps_per_turn
        if d >= 0:
            d = np.floor(d)
        else:
            d = np.ceil(d)
        return d

    def steps2deg(self, position):
        if position >= 0:
            return position * 360 / self._steps_per_turn
        else:
            # second term is negative so + is correct (going counter clockwise)
            return 360 + position * 360 / self._steps_per_turn

    def init_mock(self):
        pass


class ArduinoRotatorManagerOld(RotatorManager):
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
        self._motor.start_move.disconnect()
        self._motor.move_done.disconnect()
        self._motor.board.stepper_get_current_position(
                        self._motor.motor,
                        self._motor.current_position_callback)
        time.sleep(.2)
        self.trigger_update_position()

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
        self.move_rel_steps(to_move)

    def trigger_update_position(self):
        self._motor.emit_trigger_update_position()

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
