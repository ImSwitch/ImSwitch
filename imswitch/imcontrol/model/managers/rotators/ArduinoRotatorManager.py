from imswitch.imcontrol.model.interfaces import (
    MockTelemetrixBoard,
    MotorInterface
)
from imswitch.imcommon.model import initLogger
from imswitch.imcommon.model.mathutils import stepsToAngle, angleToSteps
from .RotatorManager import RotatorManager
from typing import Union, Tuple, Dict
from telemetrix import telemetrix


class TelemetrixInterface(telemetrix.Telemetrix):
    """ Expanding the Telemetrix
    class to store additional parameters
    related to the manager handling.
    """
    currentPosition: Tuple[int, int] = (0, 0)  # (steps, degrees)
    stepsPerTurn: int = 0


class ArduinoRotatorManager(RotatorManager):
    """ Wrapper of a Telemetrix interface to an Arduino-controlled stepper motor.

    Manager properties:
        - stepsPerTurn (`int`): conversion factor for calculating the rotation angle from the number of steps.
        - startSpeed (`int`): initial speed of the motor.
        - maximumSpeed (`int`): maximum speed of the motor.
        - acceleration (`int`): acceleration of the motor.
        - interface (`str`): the type of interface used to control the motor;
            can be one of the following values: 'StepperDriver', 'FULL2WIRE', 'FULL3WIRE', 'FULL4WIRE', 'HALF3WIRE', 'HALF4WIRE'.
        - pinConfig (`Dict[str, int]`): a string-int pair dictionary with the pin configuration for the selected interface;
            the keys are `pin1`, `pin2`, `pin3`, `pin4`; the values are the pin numbers (integers).
    """

    def __init__(self, rotatorInfo, name, *args, **kwargs):
        super().__init__(rotatorInfo, name, *args, **kwargs)
        self.__logger = initLogger(self)

        if rotatorInfo is None:
            self.__logger.error('No rotator info provided in the configuration file')
            raise ValueError('No rotator info providided in the configuration file')
        self._stepsPerTurn = rotatorInfo.managerProperties['stepsPerTurn']
        self.speed = rotatorInfo.managerProperties['startSpeed']
        self.maximumspeed = rotatorInfo.managerProperties['maximumSpeed']
        self.acceleration = rotatorInfo.managerProperties['acceleration']
        print(rotatorInfo, dir(rotatorInfo))
        try:
            self.interface: MotorInterface = MotorInterface[rotatorInfo.managerProperties['interface']]
            self.pinConfig: Dict[str, int] = rotatorInfo.managerProperties['pinConfig']
            if not self.interface.isPinConfigOK(self.pinConfig):
                raise ValueError('Invalid pin configuration for the selected interface')
        except ValueError:
            self.__logger.error('Invalid interface value in the configuration file. Check the configuration file.')
            raise ValueError('Invalid interface value in the configuration file. Check the configuration file.')
        self.board = None
        self.motorID = None
        self.__setupBoardConnection()

    def __setupBoardConnection(self):
        """ Initializes the handle to the hardware interface. If no hardware
        is found, a mock object is used instead.
        """
        self.__logger.info(f'Trying to initialize Arduino stepper motor (interface: {self.interface})')
        self.board = self.__initializeBoard()
        self.board.stepsPerTurn = self._stepsPerTurn
        self.board.currentPosition = (0, 0)
        self.__initializeMotor()

    def close(self):
        """
        Shutdown board. If the motor is currently moving, it will stop it.
        """
        self.__logger.info('Motor shutting down.')
        try:
            self.board.stepper_stop(self.motorID)
        except:
            pass
        self.board.shutdown()

    def __initializeBoard(self) -> Union[TelemetrixInterface, MockTelemetrixBoard]:
        """ Initializes communication with the Telemetrix firmware. If no board is found, a mock object is used instead.
        """
        # board = None
        try:
            self.__logger.info('Initializing Telemetrix interface.')
            board = TelemetrixInterface()
            self.__logger.info('Telemetrix interface initialized')
        except Exception:
            self.__logger.warning('Failed to initialize Telemetrix board. Setting up mock object.')
            board = MockTelemetrixBoard()
        return board

    def __initializeMotor(self):
        """ Initializes the board motor pin configuration.
        If the board handle is a mock object, it will call placeholder methods.
        """
        self.motorID = self.board.set_pin_mode_stepper(interface=self.interface.value, **self.pinConfig)
        # self.motorID = self.board.set_pin_mode_stepper(
        #                     interface=1,
        #                     pin1=2, pin2=3,
        #                 )
        self.board.stepper_set_max_speed(self.motorID, self.maximumspeed)
        self.set_rot_speed(self.speed)
        self.board.stepper_set_current_position(self.motorID, 0)
        self.board.stepper_set_acceleration(self.motorID, self.acceleration)

    def set_rot_speed(self, speed):
        self.__logger.info(f'Motor speed set to: {speed}')
        self.board.stepper_set_speed(self.motorID, speed)

    def move_rel(self, angle):
        """Method implemented from base class.
        Performs a movement relative to the current position.
        """
        steps = angleToSteps(angle, self._stepsPerTurn)
        self.board.stepper_move(self.motorID, steps)
        self.board.stepper_run(self.motorID, self.__moveFinishedCallback)

    def move_abs(self, value, inSteps=False):
        """Method implemented from base class.
        Moves the stepper to an absolute position, based on the current
        stored position (in steps).

        Args:
            angle (int): rotation angle.
        """
        # TODO: move this check to controller
        if inSteps:
            steps = value
        else:
            steps = angleToSteps(value, self._stepsPerTurn)

        # convert from numpy.int32 to int()
        self.board.stepper_move(self.motorID, int(steps - self.board.currentPosition[0]))
        self.board.stepper_run(self.motorID, self.__moveFinishedCallback)

    def get_position(self) -> Tuple[int, int]:
        return self.board.currentPosition

    #######################
    # Continuous rotation #
    #######################
    def start_cont_rot(self):
        """ Continuous stepping of the motor """
        self.board.stepper_set_speed(self.motorID, self.speed)
        self.__logger.info(f'Continuous move, motor {self.motorID}')
        self.board.stepper_run_speed(self.motorID)

    def stop_cont_rot(self):
        """Stop continuous move of the motor. Since the position
        cannot be tracked, it will be zeroed.
        """
        self.__logger.info('Stoping continuous move')
        self.board.stepper_stop(self.motorID)
        # zero position, because position is lost during cont move
        self.board.currentPosition = (0, 0)
        self.sigRotatorPositionUpdated.emit()

    #############
    # Callbacks #
    #############
    def __moveFinishedCallback(self, data: Tuple[int, int, float]) -> None:
        # tuple is return report_type, motorID, timestamp
        # we make a second callback to be sure of the final position
        self.board.stepper_get_current_position(self.motorID,
                                                self.__currentPositionCallback)

    def __currentPositionCallback(self, data: Tuple[int, int, int, float]) -> None:
        # tuple is REPORT_TYPE=17, motor_id, current position in steps, time_stamp
        steps = data[2] % self.board.stepsPerTurn
        self.board.currentPosition = (steps, stepsToAngle(steps, self._stepsPerTurn))
        if steps != data[2]:
            self.board.stepper_set_current_position(self.motorID, steps)
        self.sigRotatorPositionUpdated.emit()

    def set_zero_pos(self) -> None:
        self.board.stepper_set_current_position(self.motorID, 0)
        self.board.currentPosition = (0, 0)
        # this updates th position in the widget.
        self.sigRotatorPositionUpdated.emit()


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
