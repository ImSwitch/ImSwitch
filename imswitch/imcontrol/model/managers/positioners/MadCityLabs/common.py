from enum import IntEnum
from ctypes import *
from dataclasses import dataclass

class MCLException(Exception):
    pass

class MCLMicroDevice(IntEnum):
    MicroDrive  = 0x2500
    MicroDrive1 = 0x2501
    MicroDrive3 = 0x2503
    MicroDrive4 = 0x2504
    MicroDrive6	= 0x2506
    NanoCyte    = 0x3500

class MCLAxis(IntEnum):
    M1AXIS = 1
    M2AXIS = 2
    M3AXIS = 3
    M4AXIS = 4
    M5AXIS = 5
    M6AXIS = 6

class MCLRetVal(IntEnum):
    MCL_SUCCESS = 0
    MCL_GENERAL_ERROR = -1
    MCL_DEV_ERROR = -2	
    MCL_DEV_NOT_ATTACHED =	-3
    MCL_USAGE_ERROR = -4
    MCL_DEV_NOT_READY = -5
    MCL_ARGUMENT_ERROR = -6  
    MCL_INVALID_AXIS = -7 
    MCL_INVALID_HANDLE = -8

@dataclass(frozen=True)
class MCLDeviceInfo:
    deviceType : MCLMicroDevice # todo: extend to MCLNanoDevice with Union
    encoderResolution : c_double()
    stepSize : c_double()
    maxSpeed1Axis : c_double()
    maxSpeed2Axis : c_double()
    maxSpeed3Axis : c_double()
    minSpeed : c_double()
    axis : dict[str, MCLAxis]