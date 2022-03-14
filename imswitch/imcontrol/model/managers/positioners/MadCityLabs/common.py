from enum import IntEnum

class MCLRetVal(IntEnum):
    MCL_SUCCESS = 0
    MCL_GENERAL_ERROR = -1,  
    MCL_DEV_ERROR = -2	
    MCL_DEV_NOT_ATTACHED =	-3
    MCL_USAGE_ERROR = -4
    MCL_DEV_NOT_READY = -5
    MCL_ARGUMENT_ERROR = -6  
    MCL_INVALID_AXIS = -7 
    MCL_INVALID_HANDLE = -8
