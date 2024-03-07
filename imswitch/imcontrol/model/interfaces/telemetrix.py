from imswitch.imcommon.model import initLogger
from imswitch.imcommon.model.mathutils import stepsToAngle
from apscheduler.schedulers.background import BackgroundScheduler
from enum import IntEnum
from typing import Dict, Tuple, Callable
import time


class MotorInterface(IntEnum):
    StepperDriver = 1
    FULL2WIRE     = 2
    FULL3WIRE     = 3
    FULL4WIRE     = 4
    HALF3WIRE     = 6
    HALF4WIRE     = 8

    def isPinConfigOK(self, pinConfig: Dict[str, int]) -> bool:
        # TODO: check keys string formatting
        return len(pinConfig) == PIN_CONFIGS_NUM[self]


PIN_CONFIGS_NUM = {
    MotorInterface.StepperDriver: 2,
    MotorInterface.FULL2WIRE    : 2,
    MotorInterface.FULL3WIRE    : 3,
    MotorInterface.FULL4WIRE    : 4,
    MotorInterface.HALF3WIRE    : 3,
    MotorInterface.HALF4WIRE    : 4
}


class MockTelemetrixBoard:
    """ Mock class implementing placeholder methods for the a Telemetrix-supported board.
    It's instantiated when the actual board is not found, or when the user wants 
    to run the software in a non-hardware environment. Uses `APScheduler` to simulate
    a continously rotating stepper motor when requested.
    """

    def __init__(self) -> None:
        self.__logger = initLogger(self)
        self.__speed: int = 0
        self.__maxSpeed: int = 0
        self.__stepsToTurn: int = 0
        self.callbackResponse: Tuple[int, int, int, float] = (0, 0)
        self.currentPosition = (0, 0)   # (steps, degrees)
        self.stepsPerTurn: int = 0
        self.motorIDCount: int = 0
        self.__mockScheduler = BackgroundScheduler()

    def stepper_get_current_position(self, _: int, callback: Callable) -> None:
        callback(self.callbackResponse)

    def set_pin_mode_stepper(self, interface=1, pin1=2, pin2=3, pin3=4, pin4=5,
                             enable=True) -> int:
        interface = MotorInterface(interface)
        pins = {
            'pin1': pin1,
            'pin2': pin2,
            'pin3': pin3,
            'pin4': pin4
        }
        self.__logger.info(f'Mock board setting pin mode for stepper motor.')
        self.__logger.info(f"Interface: {interface}")
        self.__logger.info(f"Pins: {pins}")
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
        self.currentPosition = (newPosition, stepsToAngle(newPosition, self.stepsPerTurn))
        
        # this is a hack due to the fact that in the manager, the callback
        # does not actually use this response, but instead is immediatly passed
        # to the callback retrieving the current position.
        self.callbackResponse = (17, 0, self.currentPosition[0] + self.__stepsToTurn, 0.1)
        time.sleep(.3)
        callback(self.callbackResponse)

    def stepper_run_speed(self, motor_id: int) -> None:
        self.__logger.info(f"Mock board running motor {motor_id} continously at speed {self.__speed}")
        self.__mockScheduler.add_job(self.__mock_continous_movement, 'interval', seconds=1)
        self.__mockScheduler.start()

    def stepper_stop(self, motor_id: int) -> None:
        self.__logger.info(f"Mock board stopping motor {motor_id} continous movement.")

    def stepper_set_current_position(self, _: int, position: int) -> None:
        self.currentPosition = (position, stepsToAngle(position, self.stepsPerTurn))

    def shutdown(self):
        self.__logger.info('Mock board shutting down.')

    def __mock_continous_movement(self):
        """ Simulates the continous movement of the stepper motor.
        Triggered by the background schedulers, calculates the new position.
        """
        newPosition = (self.currentPosition[0] + self.__stepsToTurn) % self.stepsPerTurn
        self.currentPosition = (newPosition, stepsToAngle(newPosition))
        self.__logger.info(f"Mock board continous movement. New position: {self.currentPosition}")
    