from imswitch.imcommon.model import initLogger
from imswitch.imcommon.framework import Signal, SignalInterface
from imswitch.imcommon.model.utils import stepsToAngle, angleToSteps
from .RotatorManager import RotatorManager
from typing import Union, Tuple, Dict, Callable
from enum import IntEnum
from telemetrix import telemetrix
from time import sleep
from apscheduler.schedulers.background import BackgroundScheduler

class MotorInterface(IntEnum):
    StepperDriver = 1
    FULL2WIRE     = 2
    FULL3WIRE     = 3
    FULL4WIRE     = 4
    HALF3WIRE     = 6
    HALF4WIRE     = 8

    def isPinConfigOK(self, pinConfig: Dict[str, int]) -> bool:
        return len(pinConfig) == PIN_CONFIGS_NUM[self]

PIN_CONFIGS_NUM = {
    MotorInterface.StepperDriver: 2,
    MotorInterface.FULL2WIRE    : 2,
    MotorInterface.FULL3WIRE    : 3,
    MotorInterface.FULL4WIRE    : 4,
    MotorInterface.HALF3WIRE    : 3,
    MotorInterface.HALF4WIRE    : 4
}

class TelemetrixInterface(telemetrix.Telemetrix):
    """ Expanding the Telemetrix 
    class to store additional parameters 
    related to the manager handling.
    """
    currentPosition : Tuple[int, int] = (0, 0) # (steps, degrees)
    stepsPerTurn : int = 0

class MockBoard(SignalInterface):
    """ Mock class implementing placeholder methods for the a Telemetrix-supported board.
    It's instantiated when the actual board is not found, or when the user wants 
    to run the software in a non-hardware environment. Uses `APScheduler` to simulate
    a continously rotating stepper motor when requested.
    """

    def __init__(self) -> None:
        super().__init__()
        self.__logger = initLogger(self)
        self.__speed: int = 0
        self.__maxSpeed: int = 0
        self.__stepsToTurn: int = 0
        self.currentPosition: Tuple[int, int] = (0, 0) # (steps, degrees)
        self.stepsPerTurn: int = 0
        self.motorIDCount: int = 0
        self.__mockScheduler = BackgroundScheduler()

    def stepper_get_current_position(self, motor_id: int, callback: Callable) -> None:
        self.__logger.info(f'Mock board (motor {motor_id}) getting current position. Callback name: {callback.__name__}')
    
    def set_pin_mode_stepper(self, interface=1, pin1=2, pin2=3, pin3=4, pin4=5, enable=True) -> int:
        interface = MotorInterface(interface)
        pins = {
            'pin1': pin1,
            'pin2': pin2,
            'pin3': pin3,
            'pin4': pin4
        }
        self.__logger.info(f'Mock board setting pin mode for stepper motor. Interface: {interface}, pins: {pins}, enable: {enable}')
        self.motorIDCount += 1
        return self.motorIDCount
        

    def stepper_set_speed(self, motor_id: int, speed: int) -> None:
        if speed > self.__maxSpeed:
            self.__logger.warning(f"Exceeding maximum speed for motor {motor_id}. Setting to maximum speed {self.__maxSpeed}.")
        else:
            self.__logger.info(f"Mock board setting speed to {speed}")
            self.__speed = speed

    def stepper_set_max_speed(self, _: int, max_speed: int) -> None:
        self.__maxSpeed = max_speed

    def stepper_set_acceleration(self, _: int, acceleration: int) -> None:
        self.__logger.info(f"Mock board setting acceleration to {acceleration}")

    def stepper_move(self, _: int, steps: int) -> None:
        self.__stepsToTurn = steps

    def stepper_run(self, _: int, callback: Callable) -> None:
        """ Simulates the movement of the stepper motor.

        Args:
            _ (`int`): motor ID (unused in this method)
            callback (`Callable`): callback function to execute after the movement is done.
                                Receives the new position as an argument, formatted as a tuple (steps, degrees).
        """
        newPosition = (self.currentPosition[0] + self.__stepsToTurn) % self.stepsPerTurn
        self.currentPosition = (newPosition, stepsToAngle(newPosition))
        callback(self.currentPosition)

    def stepper_run_speed(self, motor_id: int) -> None:
        self.__logger.info(f"Mock board running motor {motor_id} continously at speed {self.__speed}")
        self.__mockScheduler.add_job(self.__mock_continous_movement, 'interval', seconds=1)

    def stepper_stop(self, motor_id: int) -> None:
        self.__logger.info(f"Mock board stopping motor {motor_id} continous movement.")
    
    def stepper_set_current_position(self, _: int, position: int) -> None:
        self.currentPosition = (position, stepsToAngle(position))

    def shutdown(self):
        self.__logger.info('Mock board shutting down.')
    
    def __mock_continous_movement(self):
        """ Simulates the continous movement of the stepper motor.
        Triggered by the background schedulers, calculates the new position.
        """
        newPosition = (self.currentPosition[0] + self.__stepsToTurn) % self.stepsPerTurn
        self.currentPosition = (newPosition, stepsToAngle(newPosition))

class ArduinoRotatorManager(RotatorManager):
    """ Arduino stepper motor manager.
    """
    sigMoveStarted = Signal()

    def __init__(self, rotatorInfo, name, *args, **kwargs):
        super().__init__(rotatorInfo, name, *args, **kwargs)
        self.__logger = initLogger(self)

        if rotatorInfo is None:
            self.__logger.error('No rotator info provided in the configuration file')
            raise ValueError('No rotator info providided in the configuration file')
        self._deviceID = rotatorInfo.managerProperties['motorListIndex']
        self._stepsPerTurn = rotatorInfo.managerProperties['stepsPerTurn']
        self.speed = rotatorInfo.managerProperties['startSpeed']
        self.maximumspeed = rotatorInfo.managerProperties['maximumSpeed']
        self.acceleration = rotatorInfo.managerProperties['acceleration']
        self.board = None
        self.motorID = None
        self.turning = False
        self.__setupBoardConnection()

        # to interface with the asynchronous communication with the Telemetrix interface,
        # we use sigOptStepDone signal to notify the end of the movement
        # and call the relative method to update the position
        self.sigOptStepDone.connect(self.readPositionAfterMove)

    def __setupBoardConnection(self):
        """ Initializes the handle to the hardware interface. If no hardware is found, a mock object is used instead.
        """
        try:
            self.__logger.info(f'Trying to initialize Arduino stepper motor {self._deviceID}')
            self.board = self.__initializeBoard()
            self.__logger.info("Success")
        except Exception:
            self.__logger.warning(f'Failed to initialize Arduino stepper motor {self._deviceID}, loading mocker')
            self.board = MockBoard()
        
        self.__initializeMotor()
        self.board.stepsPerTurn = self._stepsPerTurn
        self.board.currentPosition = (0, 0)

    def close(self):
        """
        Shutdown board. If the motor is currently moving, it will stop it.
        """
        self.__logger.info('Motor shutting down.')
        if self.turning:
            self.board.stepper_stop(self.motorID)
        self.sigOptStepDone.disconnect(self.readPositionAfterMove)
        self.board.shutdown()

    def __initializeBoard(self) -> Union[TelemetrixInterface, MockBoard]:
        """ Initializes communication with the Telemetrix firmware. If no board is found, a mock object is used instead.
        """
        board = None
        try:
            self.__logger.info('Initializing Telemetrix interface.')
            board = TelemetrixInterface()
            self.__logger.info('Telemetrix interface initialized')
        except Exception:
            self.__logger.warning('Failed to initialize Telemetrix board. Setting up mock object.')
            board = MockBoard()
        return board

    def __initializeMotor(self):
        """ Initializes the board motor pin configuration.
        If the board handle is a mock object, it will call placeholder methods.
        """
        # TODO: move pin configuration to the JSON configuration file
        if self._deviceID == 0:
            self.motorID = self.board.set_pin_mode_stepper(interface=4,
                                                        pin1=8, pin2=10, pin3=9, pin4=11)
        elif self._deviceID == 1:
            self.motorID = self.board.set_pin_mode_stepper(interface=1,
                                                        pin1=2, pin2=3)
        self.board.stepper_set_max_speed(self.motorID, self.maximumspeed)
        self.board.stepper_set_current_position(self.motorID, 0)
        
        self.board.stepper_set_speed(self.motorID, self.speed)
        self.board.stepper_set_acceleration(self.motorID, self.acceleration)
    
    def moveRelSteps(self, steps: int) -> None:
        """ Move self.steps relative to the current position """
        self.turning = True
        self.board.stepper_move(self.motorID, int(steps))
        self.board.stepper_run(self.motorID, self.moveFinishedCallback)

    def move_rel(self, angle):
        """Method implemented from base class.
        Performs a movement relative to the current position.
        """
        steps = angleToSteps(angle)
        self.turning = True
        self.board.stepper_move(self.motorID, steps)
        self.board.stepper_run(self.motorID, self.moveFinishedCallback)

    def move_abs(self, value, inSteps=False):
        """Method implemented from base class.
        Moves the stepper to an absolute position, based on the current 
        stored position (in steps).

        Args:
            angle (int): rotation angle.
        """
        if inSteps:
            steps = value
        else:
            steps = angleToSteps(value)
        
        self.turning = True
        self.board.stepper_move(self.motorID, steps - self.currentPosition[0])
        self.board.stepper_run(self.motorID, self.moveFinishedCallback)

    def readPositionAfterMove(self):
        """ Slot connected to sigMoveDone signal.
        Updates the current position read by the interface.
        """
        self.board.stepper_get_current_position(self.motorID, self.currentPositionCallback)

    #######################
    # Continuous rotation #
    #######################
    def start_cont_rot(self):
        """
        Move the stepper motor and keep cheking the
        for the running is over in the while loop.
        """
        self.board.stepper_set_speed(self.motorID, self.speed)
        self.turning = True
        self.board.stepper_run_speed(self.motorID)

    def stop_cont_rot(self):
        self.turning = False
        self.board.stepper_stop(self.motorID)

    #############
    # Callbacks #
    #############
    def moveFinishedCallback(self, data: Tuple[int, int]) -> None:
        self.__logger.info(f'Move done (step: {data[0]}, angle: {data[1]}°)')
        self.turning = False
        self.sigOptStepDone.emit()

    def currentPositionCallback(self, data: Tuple[int, int]) -> None:
        """
        Current position data in form of
        motor_id, current position in steps, time_stamp
        """
        # for now tuple of steps, degrees
        steps = data[2] % self.board.stepsPerTurn
        self.board.currentPosition = (steps, stepsToAngle(steps))
        if steps != data[2]:
            self.board.stepper_set_current_position(self.motorID, steps)

    def set_zero_pos(self) -> None:
        self.board.stepper_set_current_position(self.motorID, 0)
        self.currentPosition = (0, 0)


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
