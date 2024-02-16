import numpy as np
from telemetrix import telemetrix
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from imswitch.imcommon.model import initLogger
import time


class ArduinoStepper(QObject):
    """Arduino stepper motor control via telemetrix module, which is an
    extension to the accelstepper library.
    """
    start_move = pyqtSignal()
    move_done = pyqtSignal(bool)
    opt_step_done = pyqtSignal(str)
    update_position = pyqtSignal()

    def __init__(self, device_id, steps_per_turn):
        super(QObject, self).__init__()
        self.__logger = initLogger(self)
        self._device_id = device_id
        self._steps_per_turn = steps_per_turn

        self.speed = 100
        self.max_speed = 900
        self.acc = 200
        self.board = None
        self.motor = None
        self.turning = None
        self.current_pos = None
        # checking every wait_const if the movement is over
        self.wait_const = 0.5
        self.init_board()
        self.init_motor()

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
            time.sleep(5)
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

    def get_pos(self):
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
    def moverel_angle(self):
        """ Move relative distance from current position """
        self.steps = self.deg2steps(self.angle)
        self.set_rot_speed(self.speed)
        self.moverel_steps()

    @pyqtSlot()
    def moverel_steps(self):
        """Move self.steps relative to the current position """
        self.board.stepper_move(self.motor, int(self.steps))
        self.turning = True
        self.board.stepper_run(self.motor,
                               completion_callback=self.move_finished_callback)

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
        self.turning = False
        self.move_done.emit(self.turning)
        self.opt_step_done.emit('bla')

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

    def is_running_callback(self, data):
        """Check if motor is running"""
        if data[1]:
            self.turning = True
        else:
            self.turning = False

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


class MockBoard():
    def stepper_get_current_position(self, *args, **kwargs):
        print('calling board')
        return


class MockArduinoStepper(QObject):

    start_move = pyqtSignal()
    move_done = pyqtSignal(bool)
    opt_step_done = pyqtSignal(str)
    update_position = pyqtSignal()

    def __init__(self, device_id, steps_per_turn):
        super(QObject, self).__init__()
        self.__logger = initLogger(self)
        self._device_id = device_id
        self._steps_per_turn = steps_per_turn
        self.current_pos = (0, 0)
        self.turning = False
        self.board = MockBoard()
        self.motor = None

    def close(self):
        pass

    def current_position_callback(self):
        return

    def emit_trigger_update_position(self):
        self.update_position.emit()

    def get_pos(self):
        return self.current_pos

    def move_finished_callback(self):
        print('HAHHAHAHH')
        self.turning = False
        self.move_done.emit(self.turning)
        self.opt_step_done.emit('bla')

    @pyqtSlot()
    def moverel_angle(self):
        print('waiting moverel_angle')
        steps = self.deg2steps(self.angle)
        time.sleep(1)
        print('from moverel_angle', self.angle, steps)
        self.moverel_steps(steps)

    @pyqtSlot()
    def moverel_steps(self):
        print('waiting moverel_steps')
        self.turning = True
        time.sleep(1)
        self.current_pos = (100, 200)
        self.move_finished_callback()

        # self.turning = False
        # self.move_done.emit(self.turning)
        # # time.sleep(0.2)
        # print('inbetween emits from arduino stepper')
        # self.opt_step_done.emit('opt_step_done emit')

    def moveabs_angle(self):
        print('waiting')
        self.turning = True
        time.sleep(0.5)
        self.current_pos = (100, 100)
        self.move_finished_callback()
        # self.turning = False
        # self.move_done.emit(self.turning)
        # self.opt_step_done.emit()

    def moveabs_steps(self, position):
        print('waiting')
        self.turning = True
        time.sleep(1)
        self.current_pos = (position, position)
        self.turning = False
        self.move_done.emit(self.turning)
        self.opt_step_done.emit()

    def test_info(self):
        return {}

    def start_cont_rot(self):
        pass

    def stop_cont_rot(self):
        pass

    def deg2steps(self, d_deg):
        d = d_deg/360 * self._steps_per_turn
        if d >= 0:
            d = np.floor(d)
        else:
            d = np.ceil(d)
        return d
