from enum import IntEnum
from ctypes import *

class MCLException(Exception):
    pass

class MCLMicroDevice(IntEnum):
    MicroDrive = 0x2500
    MicroDrive1 = 0x2501
    MicroDrive3 = 0x2503
    MicroDrive4 = 0x2504
    MicroDrive6	= 0x2506
    NanoCyte = 0x3500

class MCLNanoDevice(IntEnum):
    NanoDriveSingleAxis	= 0x2001
    NanoDriveThreeAxis = 0x2003
    NanoDriveFourAxis = 0x2004
    NanoDrive16bitTipTiltZ = 0x2053
    NanoDrive20bitSingleAxis = 0x2201
    NanoDrive20bitThreeAxis = 0x2203
    NanoDrive20bitTipTiltZ = 0x2253
    NanoGauge = 0x2100
    CFocus = 0x2401

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
    MCL_INVALID_DRIVER = -9
    MCL_SEQ_NOT_VALID = -10
    MCL_BLOCKED_BY_TIRFLOCK = -11