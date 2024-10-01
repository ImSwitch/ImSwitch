# /**********************************************************************
# * Copyright (c) 2006-2017 SmarAct GmbH
# *
# * File name: MCSControl_PythonWrapper.py
# * Author   : Marc Schiffner/ Jan Heye Buss
# * Version  : 2.0.24
# *
# * This is the software interface to the Modular Control System.
# * Please refer to the Programmer's Guide for a detailed documentation.
# *
# * THIS  SOFTWARE, DOCUMENTS, FILES AND INFORMATION ARE PROVIDED 'AS IS'
# * WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING,
# * BUT  NOT  LIMITED  TO,  THE  IMPLIED  WARRANTIES  OF MERCHANTABILITY,
# * FITNESS FOR A PURPOSE, OR THE WARRANTY OF NON-INFRINGEMENT.
# * THE  ENTIRE  RISK  ARISING OUT OF USE OR PERFORMANCE OF THIS SOFTWARE
# * REMAINS WITH YOU.
# * IN  NO  EVENT  SHALL  THE  SMARACT  GMBH  BE  LIABLE  FOR ANY DIRECT,
# * INDIRECT, SPECIAL, INCIDENTAL, CONSEQUENTIAL OR OTHER DAMAGES ARISING
# * OUT OF THE USE OR INABILITY TO USE THIS SOFTWARE.
# **********************************************************************/

# Import ctypes from standard python to import c.dll(s)
import ctypes as ct

#define standard SA_types // not really necessary in Python
SA_STATUS = ct.c_ulong()
SA_INDEX  = ct.c_ulong()
SA_PACKET_TYPE  = ct.c_ulong()

MCS_lib = ct.cdll.LoadLibrary("MCSControl")

# // defines a data packet for the asynchronous mode
class SA_packet(ct.Structure):
	_fields_ = [
    ("SA_PACKET_TYPE", ct.c_ulong),                      #// type of packet (see below)
    ("SA_INDEX", ct.c_ulong),                          #// source channel
    ("data1", ct.c_ulong),                             #// data field
    ("data2", ct.c_long),                               #// data field
    ("data3",ct.c_long),                               #// data field
    ("data4", ct.c_ulong)]                             #// data field


# function status return values
SA_OK                               =       0
SA_INITIALIZATION_ERROR             =       1
SA_NOT_INITIALIZED_ERROR            =       2
SA_NO_SYSTEMS_FOUND_ERROR           =       3
SA_TOO_MANY_SYSTEMS_ERROR           =       4
SA_INVALID_SYSTEM_INDEX_ERROR       =       5
SA_INVALID_CHANNEL_INDEX_ERROR      =       6
SA_TRANSMIT_ERROR                   =       7
SA_WRITE_ERROR                      =       8
SA_INVALID_PARAMETER_ERROR          =       9
SA_READ_ERROR                       =       10
SA_INTERNAL_ERROR                   =       12
SA_WRONG_MODE_ERROR                 =       13
SA_PROTOCOL_ERROR                   =       14
SA_TIMEOUT_ERROR                    =       15
SA_ID_LIST_TOO_SMALL_ERROR          =       17
SA_SYSTEM_ALREADY_ADDED_ERROR       =       18
SA_WRONG_CHANNEL_TYPE_ERROR         =       19
SA_CANCELED_ERROR                   =       20
SA_INVALID_SYSTEM_LOCATOR_ERROR     =       21
SA_INPUT_BUFFER_OVERFLOW_ERROR      =       22
SA_QUERYBUFFER_SIZE_ERROR           =       23
SA_DRIVER_ERROR                     =       24
SA_NO_SUCH_SLAVE_ERROR              =       128
SA_NO_SENSOR_PRESENT_ERROR          =       129
SA_AMPLITUDE_TOO_LOW_ERROR          =       130
SA_AMPLITUDE_TOO_HIGH_ERROR         =       131
SA_FREQUENCY_TOO_LOW_ERROR          =       132
SA_FREQUENCY_TOO_HIGH_ERROR         =       133
SA_SCAN_TARGET_TOO_HIGH_ERROR       =       135
SA_SCAN_SPEED_TOO_LOW_ERROR         =       136
SA_SCAN_SPEED_TOO_HIGH_ERROR        =       137
SA_SENSOR_DISABLED_ERROR            =       140
SA_COMMAND_OVERRIDDEN_ERROR         =       141
SA_END_STOP_REACHED_ERROR           =       142
SA_WRONG_SENSOR_TYPE_ERROR          =       143
SA_COULD_NOT_FIND_REF_ERROR         =       144
SA_WRONG_END_EFFECTOR_TYPE_ERROR    =       145
SA_MOVEMENT_LOCKED_ERROR            =       146
SA_RANGE_LIMIT_REACHED_ERROR        =       147
SA_PHYSICAL_POSITION_UNKNOWN_ERROR  =       148
SA_OUTPUT_BUFFER_OVERFLOW_ERROR     =       149
SA_COMMAND_NOT_PROCESSABLE_ERROR    =       150
SA_WAITING_FOR_TRIGGER_ERROR        =       151
SA_COMMAND_NOT_TRIGGERABLE_ERROR    =       152
SA_COMMAND_QUEUE_FULL_ERROR         =       153
SA_INVALID_COMPONENT_ERROR          =       154
SA_INVALID_SUB_COMPONENT_ERROR      =       155
SA_INVALID_PROPERTY_ERROR           =       156
SA_PERMISSION_DENIED_ERROR          =       157
SA_CALIBRATION_FAILED_ERROR         =       160
SA_UNKNOWN_COMMAND_ERROR            =       240
SA_OTHER_ERROR                      =       255

# general definitions
SA_UNDEFINED                        =       0
SA_FALSE                            =       0
SA_TRUE                             =       1
SA_DISABLED                         =       0
SA_ENABLED                          =       1
SA_FALLING_EDGE                     =       0
SA_RISING_EDGE                      =       1
SA_FORWARD                          =       0
SA_BACKWARD                         =       1

# component selectors
SA_GENERAL                          =       1
SA_DIGITAL_IN                       =       2
SA_ANALOG_IN                        =       3
SA_COUNTER                          =       4
SA_CAPTURE_BUFFER                   =       5
SA_COMMAND_QUEUE                    =       6
SA_SOFTWARE_TRIGGER                 =       7
SA_SENSOR                           =       8
SA_MONITOR                          =       9

# component sub selectors
SA_EMERGENCY_STOP                   =       1
SA_LOW_VIBRATION                    =       2

SA_BROADCAST_STOP                   =       4
SA_POSITION_CONTROL                 =       5

SA_REFERENCE_SIGNAL                 =       7

SA_POWER_SUPPLY                     =       11

SA_SCALE                            =       22
SA_ANALOG_AUX_SIGNAL                =       23

# component properties
SA_OPERATION_MODE                   =       1
SA_ACTIVE_EDGE                      =       2
SA_TRIGGER_SOURCE                   =       3
SA_SIZE                             =       4
SA_VALUE                            =       5
SA_CAPACITY                         =       6
SA_DIRECTION                        =       7
SA_SETPOINT                         =       8
SA_P_GAIN                           =       9
SA_P_RIGHT_SHIFT                    =       10
SA_I_GAIN                           =       11
SA_I_RIGHT_SHIFT                    =       12
SA_D_GAIN                           =       13
SA_D_RIGHT_SHIFT                    =       14
SA_ANTI_WINDUP                      =       15
SA_PID_LIMIT                        =       16
SA_FORCED_SLIP                      =       17

SA_THRESHOLD                        =       38
SA_DEFAULT_OPERATION_MODE           =       45

SA_OFFSET                           =       47
SA_DISTANCE_TO_REF_MARK             =       48
SA_REFERENCE_SPEED                  =       49

# operation mode property values for SA_EMERGENCY_STOP sub selector
SA_ESM_NORMAL                       =       0
SA_ESM_RESTRICTED                   =       1
SA_ESM_DISABLED                     =       2
SA_ESM_AUTO_RELEASE                 =       3

# configuration flags for SA_InitDevices
SA_SYNCHRONOUS_COMMUNICATION        =       0
SA_ASYNCHRONOUS_COMMUNICATION       =       1
SA_HARDWARE_RESET                   =       2

# return values from SA_GetInitState
SA_INIT_STATE_NONE                  =       0
SA_INIT_STATE_SYNC                  =       1
SA_INIT_STATE_ASYNC                 =       2

# return values for SA_GetChannelType
SA_POSITIONER_CHANNEL_TYPE          =       0
SA_END_EFFECTOR_CHANNEL_TYPE        =       1

# Hand Control Module modes for SA_SetHCMEnabled
SA_HCM_DISABLED                     =       0
SA_HCM_ENABLED                      =       1
SA_HCM_CONTROLS_DISABLED            =       2

# configuration values for SA_SetBufferedOutput_A
SA_UNBUFFERED_OUTPUT                =       0
SA_BUFFERED_OUTPUT                  =       1

# configuration values for SA_SetStepWhileScan_X
SA_NO_STEP_WHILE_SCAN               =       0
SA_STEP_WHILE_SCAN                  =       1

# configuration values for SA_SetAccumulateRelativePositions_X
SA_NO_ACCUMULATE_RELATIVE_POSITIONS =       0
SA_ACCUMULATE_RELATIVE_POSITIONS    =       1

# configuration values for SA_SetSensorEnabled_X
SA_SENSOR_DISABLED                  =       0
SA_SENSOR_ENABLED                   =       1
SA_SENSOR_POWERSAVE                 =       2

# movement directions for SA_FindReferenceMark_X
SA_FORWARD_DIRECTION                     		= 0
SA_BACKWARD_DIRECTION                    		= 1
SA_FORWARD_BACKWARD_DIRECTION            		= 2
SA_BACKWARD_FORWARD_DIRECTION            		= 3
SA_FORWARD_DIRECTION_ABORT_ON_ENDSTOP    		= 4
SA_BACKWARD_DIRECTION_ABORT_ON_ENDSTOP   		= 5
SA_FORWARD_BACKWARD_DIRECTION_ABORT_ON_ENDSTOP 	= 6
SA_BACKWARD_FORWARD_DIRECTION_ABORT_ON_ENDSTOP 	= 7

# configuration values for SA_FindReferenceMark_X
SA_NO_AUTO_ZERO                     =       0
SA_AUTO_ZERO                        =       1

# return values for SA_GetPhyscialPositionKnown_X
SA_PHYSICAL_POSITION_UNKNOWN        =       0
SA_PHYSICAL_POSITION_KNOWN          =       1

# infinite timeout for functions that wait
SA_TIMEOUT_INFINITE                 =       0xFFFFFFFF

# sensor types for SA_SetSensorType_X and SA_GetSensorType_X
SA_NO_SENSOR_TYPE                   =       0
SA_S_SENSOR_TYPE                    =       1
SA_SR_SENSOR_TYPE                   =       2
SA_ML_SENSOR_TYPE                   =       3
SA_MR_SENSOR_TYPE                   =       4
SA_SP_SENSOR_TYPE                   =       5
SA_SC_SENSOR_TYPE                   =       6
SA_M25_SENSOR_TYPE                  =       7
SA_SR20_SENSOR_TYPE                 =       8
SA_M_SENSOR_TYPE                    =       9
SA_GC_SENSOR_TYPE                   =       10
SA_GD_SENSOR_TYPE                   =       11
SA_GE_SENSOR_TYPE                   =       12
SA_RA_SENSOR_TYPE                   =       13
SA_GF_SENSOR_TYPE                   =       14
SA_RB_SENSOR_TYPE                   =       15
SA_G605S_SENSOR_TYPE                =       16
SA_G775S_SENSOR_TYPE                =       17
SA_SC500_SENSOR_TYPE                =       18
SA_G955S_SENSOR_TYPE                =       19
SA_SR77_SENSOR_TYPE                 =       20
SA_SD_SENSOR_TYPE                   =       21
SA_R20ME_SENSOR_TYPE                =       22
SA_SR2_SENSOR_TYPE                  =       23
SA_SCD_SENSOR_TYPE                  =       24
SA_SRC_SENSOR_TYPE                  =       25
SA_SR36M_SENSOR_TYPE                =       26
SA_SR36ME_SENSOR_TYPE               =       27
SA_SR50M_SENSOR_TYPE                =       28
SA_SR50ME_SENSOR_TYPE               =       29
SA_G1045S_SENSOR_TYPE               =       30
SA_G1395S_SENSOR_TYPE               =       31
SA_MD_SENSOR_TYPE                   =       32
SA_G935M_SENSOR_TYPE                =       33
SA_SHL20_SENSOR_TYPE                =       34
SA_SCT_SENSOR_TYPE                  =       35
SA_SR77T_SENSOR_TYPE                =       36
SA_SR120_SENSOR_TYPE                =       37
SA_LC_SENSOR_TYPE                   =       38
SA_LR_SENSOR_TYPE                   =       39
SA_LCD_SENSOR_TYPE                  =       40
SA_L_SENSOR_TYPE                    =       41
SA_LD_SENSOR_TYPE                   =       42
SA_LE_SENSOR_TYPE                   =       43
SA_LED_SENSOR_TYPE                  =       44
SA_GDD_SENSOR_TYPE                  =       45
SA_GED_SENSOR_TYPE                  =       46
SA_G935S_SENSOR_TYPE                =       47
SA_G605DS_SENSOR_TYPE               =       48
SA_G775DS_SENSOR_TYPE               =       49

# end effector types for SA_SetEndEffectorType_X and SA_GetEndEffectorType_X
SA_ANALOG_SENSOR_END_EFFECTOR_TYPE  =       0
SA_GRIPPER_END_EFFECTOR_TYPE        =       1
SA_FORCE_SENSOR_END_EFFECTOR_TYPE   =       2
SA_FORCE_GRIPPER_END_EFFECTOR_TYPE  =       3

# packet types for asynchronous mode
SA_NO_PACKET_TYPE                       =   0
SA_ERROR_PACKET_TYPE                    =   1
SA_POSITION_PACKET_TYPE                 =   2
SA_COMPLETED_PACKET_TYPE                =   3
SA_STATUS_PACKET_TYPE                   =   4
SA_ANGLE_PACKET_TYPE                    =   5
SA_VOLTAGE_LEVEL_PACKET_TYPE            =   6
SA_SENSOR_TYPE_PACKET_TYPE              =   7
SA_SENSOR_ENABLED_PACKET_TYPE           =   8
SA_END_EFFECTOR_TYPE_PACKET_TYPE        =   9
SA_GRIPPER_OPENING_PACKET_TYPE          =   10
SA_FORCE_PACKET_TYPE                    =   11
SA_MOVE_SPEED_PACKET_TYPE               =   12
SA_PHYSICAL_POSITION_KNOWN_PACKET_TYPE  =   13
SA_POSITION_LIMIT_PACKET_TYPE           =   14
SA_ANGLE_LIMIT_PACKET_TYPE              =   15
SA_SAFE_DIRECTION_PACKET_TYPE           =   16
SA_SCALE_PACKET_TYPE                    =   17
SA_MOVE_ACCELERATION_PACKET_TYPE        =   18
SA_CHANNEL_PROPERTY_PACKET_TYPE         =   19
SA_CAPTURE_BUFFER_PACKET_TYPE           =   20
SA_TRIGGERED_PACKET_TYPE                =   21
SA_INVALID_PACKET_TYPE                  =   255

# channel status codes
SA_STOPPED_STATUS                       =   0
SA_STEPPING_STATUS                      =   1
SA_SCANNING_STATUS                      =   2
SA_HOLDING_STATUS                       =   3
SA_TARGET_STATUS                        =   4
SA_MOVE_DELAY_STATUS                    =   5
SA_CALIBRATING_STATUS                   =   6
SA_FINDING_REF_STATUS                   =   7
SA_OPENING_STATUS                       =   8

# compatibility definitions
SA_NO_REPORT_ON_COMPLETE                =   0
SA_REPORT_ON_COMPLETE                   =   1


# /*******************
# * Helper Functions *
# *******************/

# // Decode Selector Value (for some property keys)
# MCSCONTROL_API
# void MCSCONTROL_CC SA_DSV(signed int value, unsigned int *selector, unsigned int *subSelector);
def SA_DSV(value, selector, subSelector):
	MCS_lib.SA_DSV(value, ct.byref(selector), ct.byref(subSelector))
	return

# // Encode Property Key (for SA_SetChannelProperty_X and SA_GetChannelProperty_X)
# MCSCONTROL_API
# unsigned int MCSCONTROL_CC SA_EPK(unsigned int selector, unsigned int subSelector, unsigned int property);
def SA_EPK(selector, subSelector, proper):
	VAR_unsigned_int = MCS_lib.SA_EPK(selector, subSelector, proper)
	return VAR_unsigned_int

# // Encode Selector Value (for some property keys)
# MCSCONTROL_API
# signed int MCSCONTROL_CC SA_ESV(unsigned int selector, unsigned int subSelector);
def SA_ESV(selector, subSelector):
	VAR_signed_int = MCS_lib.SA_ESV(selector, subSelector)
	return VAR_signed_int

# // Transform status code into human readable string
# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_GetStatusInfo(SA_STATUS status, const char **info);
# Output: print('SA_GetStatusInfo: {}'.format(info.value[:].decode('utf-8')))
# with info = ct.c_char_p() before function call
def SA_GetStatusInfo(status, info):
	#MCS_lib.SA_GetStatusInfo.argtypes = [ct.c_ulong, ct.POINTER(ct.c_char_p)]
	SA_STATUS = MCS_lib.SA_GetStatusInfo(status, ct.byref(info))
	return SA_STATUS

# /************************************************************************
# *************************************************************************
# **                 Section I: Initialization Functions                 **
# *************************************************************************
# ************************************************************************/

#/* new style initialization functions */

#MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_OpenSystem(SA_INDEX *systemIndex,const char *locator,const char *options);
def SA_OpenSystem(systemIndex,locator,options):
	SA_STATUS = MCS_lib.SA_OpenSystem(ct.byref(systemIndex), locator, options)
	return SA_STATUS

# #MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_CloseSystem(SA_INDEX systemIndex);
def SA_CloseSystem(systemIndex):
	SA_STATUS = MCS_lib.SA_CloseSystem(systemIndex)
	return SA_STATUS

# #MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_FindSystems(const char *options,char *outBuffer,unsigned int *ioBufferSize);
#Works just with MCS USB versions:
# use outBuffer = ct.create_string_buffer(17), ioBufferSize = ct.c_ulong(18)
# to convert the outBuffer to a Python 'str' use: outBuffer[:].decode("utf-8")
def SA_FindSystems(options,outBuffer,ioBufferSize):
	SA_STATUS = MCS_lib.SA_FindSystems(bytes(options,'utf-8'), outBuffer,ct.byref(ioBufferSize))
	return SA_STATUS

# #MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_GetSystemLocator(SA_INDEX systemIndex,char *outBuffer,unsigned int *ioBufferSize);
# use outBuffer = ct.create_string_buffer(17), ioBufferSize = ct.c_ulong(18)
def SA_GetSystemLocator(systemIndex, outBuffer, ioBufferSize):
	SA_STATUS = MCS_lib.SA_GetSystemLocator(systemIndex, outBuffer, ct.byref(ioBufferSize))
	return SA_STATUS

# /* old style initialization functions */

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_AddSystemToInitSystemsList(unsigned int systemId);
def SA_AddSystemToInitSystemsList(systemId):
	SA_STATUS = MCS_lib.SA_AddSystemToInitSystemsList(systemId)
	return SA_STATUS

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_ClearInitSystemsList(void);
def SA_ClearInitSystemsList():
	SA_STATUS = MCS_lib.SA_ClearInitSystemsList()
	return SA_STATUS

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_GetAvailableSystems(unsigned int *idList, unsigned int *idListSize);
def SA_GetAvailableSystems(idList, idListSize):
	SA_STATUS = MCS_lib.SA_GetAvailableSystems(ct.byref(idList), ct.byref(idListSize))
	return SA_STATUS

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_InitSystems(unsigned int configuration);
def SA_InitSystems(configuration):
	SA_STATUS = MCS_lib.SA_InitSystems(configuration)
	return SA_STATUS

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_ReleaseSystems(void);
def SA_ReleaseSystems():
	SA_STATUS = MCS_lib.SA_ReleaseSystems()
	return

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_GetInitState(unsigned int *initMode);
def SA_GetInitState(initMode):
	SA_STATUS = MCS_lib.SA_GetInitState(ct.byref(initMode))
	return SA_STATUS

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_GetNumberOfSystems(unsigned int *number);
def SA_GetNumberOfSystems(number):
	SA_STATUS = MCS_lib.SA_GetNumberOfSystems(ct.byref(number))
	return SA_STATUS

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_GetSystemID(SA_INDEX systemIndex, unsigned int *systemId);
def SA_GetSystemID(systemIndex, systemId):
	SA_STATUS = MCS_lib.SA_GetSystemID(systemIndex, ct.byref(systemId))
	return SA_STATUS

# /* --- */

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_GetChannelType(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int *type);
def SA_GetChannelType(systemIndex, channelIndex, typ):
	SA_STATUS = MCS_lib.SA_GetChannelType(systemIndex, channelIndex, ct.byref(typ))
	return SA_STATUS

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_GetDLLVersion(unsigned int *version);
def SA_GetDLLVersion(version):
	SA_STATUS = MCS_lib.SA_GetDLLVersion(ct.byref(version))
	return SA_STATUS

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_GetNumberOfChannels(SA_INDEX systemIndex, unsigned int *channels);
def SA_GetNumberOfChannels(systemIndex, channels):
	SA_STATUS = MCS_lib.SA_GetNumberOfChannels(systemIndex, ct.byref(channels))
	return SA_STATUS

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_SetHCMEnabled(SA_INDEX systemIndex, unsigned int enabled);
def SA_SetHCMEnabled(systemIndex, enabled):
	SA_STATUS = MCS_lib.SA_SetHCMEnabled(systemIndex, enabled)
	return SA_STATUS

# /************************************************************************
# *************************************************************************
# **        Section IIa:  Functions for SYNCHRONOUS communication        **
# *************************************************************************
# ************************************************************************/

# /*************************************************
# **************************************************
# **    Section IIa.1: Configuration Functions    **
# **************************************************
# *************************************************/

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetAngleLimit_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int *minAngle, signed int *minRevolution, unsigned int *maxAngle, signed int *maxRevolution);
def SA_GetAngleLimit_S(systemIndex, channelIndex, minAngle, minRevolution, maxAngle, maxRevolution):
	SA_STATUS = MCS_lib.SA_GetAngleLimit_S(systemIndex, channelIndex, ct.byref(minAngle), ct.byref(minRevolution), ct.byref(maxAngle), ct.byref(maxRevolution))
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetChannelProperty_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int key, signed int *value);
def SA_GetChannelProperty_S(systemIndex, channelIndex, key, value):
	SA_STATUS = MCS_lib.SA_GetChannelProperty_S(systemIndex, channelIndex, key, ct.byref(value))
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetClosedLoopMoveAcceleration_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int *acceleration);
def SA_GetClosedLoopMoveAcceleration_S(systemIndex, channelIndex, acceleration):
	SA_STATUS = MCS_lib.SA_GetClosedLoopMoveAcceleration_S(systemIndex, channelIndex, ct.byref(acceleration))
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetClosedLoopMoveSpeed_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int *speed);
def SA_GetClosedLoopMoveSpeed_S(systemIndex, channelIndex, speed):
	SA_STATUS = MCS_lib.SA_GetClosedLoopMoveSpeed_S(systemIndex, channelIndex, ct.byref(speed))
	return SA_STATUS

# MCSCONTROL_API // End effector
# SA_STATUS MCSCONTROL_CC SA_GetEndEffectorType_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int *type, signed int *param1, signed int *param2);
def SA_GetEndEffectorType_S(systemIndex, channelIndex, typ, param1, param2):
	SA_STATUS = MCS_lib.SA_GetEndEffectorType_S(systemIndex, channelIndex, ct.byref(typ), ct.byref(param1), ct.byref(param2))
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetPositionLimit_S(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int *minPosition, signed int *maxPosition);
def SA_GetPositionLimit_S(systemIndex, channelIndex, minPosition, maxPosition):
	SA_STATUS = MCS_lib.SA_GetPositionLimit_S(systemIndex, channelIndex, ct.byref(minPosition), ct.byref(maxPosition))
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetSafeDirection_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int *direction);
def SA_GetSafeDirection_S(systemIndex, channelIndex, direction):
	SA_STATUS = MCS_lib.SA_GetSafeDirection_S(systemIndex, channelIndex, ct.byref(direction))
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetScale_S(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int *scale, unsigned int *inverted);
def SA_GetScale_S(systemIndex, channelIndex, scale, inverted):
	SA_STATUS = MCS_lib.SA_GetScale_S(systemIndex, channelIndex, ct.byref(scale), ct.byref(inverted))
	return SA_STATUS

# MCSCONTROL_API // Global
# SA_STATUS MCSCONTROL_CC SA_GetSensorEnabled_S(SA_INDEX systemIndex, unsigned int *enabled);
def SA_GetSensorEnabled_S(systemIndex, enabled):
	SA_STATUS = MCS_lib.SA_GetSensorEnabled_S(systemIndex, ct.byref(enabled))
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetSensorType_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int *type);
def SA_GetSensorType_S(systemIndex, channelIndex, typ):
	SA_STATUS = MCS_lib.SA_GetSensorType_S(systemIndex, channelIndex, ct.byref(typ))
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetAccumulateRelativePositions_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int accumulate);
def SA_SetAccumulateRelativePositions_S(systemIndex, channelIndex, accumulate):
	SA_STATUS = MCS_lib.SA_SetAccumulateRelativePositions_S(systemIndex, channelIndex, accumulate)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetAngleLimit_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int minAngle, signed int minRevolution, unsigned int maxAngle, signed int maxRevolution);
def SA_SetAngleLimit_S(systemIndex, channelIndex, minAngle, minRevolution, maxAngle, maxRevolution):
	SA_STATUS = MCS_lib.SA_SetAngleLimit_S(systemIndex, channelIndex, minAngle, minRevolution, maxAngle, maxRevolution)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetChannelProperty_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int key, signed int value);
def SA_SetChannelProperty_S(systemIndex, channelIndex, key, value):
	SA_STATUS = MCS_lib.SA_SetChannelProperty_S(systemIndex, channelIndex, key, value)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetClosedLoopMaxFrequency_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int frequency);
def SA_SetClosedLoopMaxFrequency_S(systemIndex, channelIndex, frequency):
	SA_STATUS = MCS_lib.SA_SetClosedLoopMaxFrequency_S(systemIndex, channelIndex, frequency)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetClosedLoopMoveAcceleration_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int acceleration);
def SA_SetClosedLoopMoveAcceleration_S(systemIndex, channelIndex, acceleration):
	SA_STATUS = MCS_lib.SA_SetClosedLoopMoveAcceleration_S(systemIndex, channelIndex, acceleration)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetClosedLoopMoveSpeed_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int speed);
def SA_SetClosedLoopMoveSpeed_S(systemIndex, channelIndex, speed):
	SA_STATUS = MCS_lib.SA_SetClosedLoopMoveSpeed_S(systemIndex, channelIndex, speed)
	return SA_STATUS

# MCSCONTROL_API // End effector
# SA_STATUS MCSCONTROL_CC SA_SetEndEffectorType_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int type, signed int param1, signed int param2);
def SA_SetEndEffectorType_S(systemIndex, channelIndex, typ, param1, param2):
	SA_STATUS = MCS_lib.SA_SetEndEffectorType_S(systemIndex, channelIndex, typ, param1, param2)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetPosition_S(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int position);
def SA_SetPosition_S(systemIndex, channelIndex, position):
	SA_STATUS = MCS_lib.SA_SetPosition_S(systemIndex, channelIndex, position)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetPositionLimit_S(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int minPosition, signed int maxPosition);
def SA_SetPositionLimit_S(systemIndex, channelIndex, minPosition, maxPosition):
	SA_STATUS = MCS_lib.SA_SetPositionLimit_S(systemIndex, channelIndex, minPosition, maxPosition)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetSafeDirection_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int direction);
def SA_SetSafeDirection_S(systemIndex, channelIndex, direction):
	SA_STATUS = MCS_lib.SA_SetSafeDirection_S(systemIndex, channelIndex, direction)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetScale_S(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int scale, unsigned int inverted);
def SA_SetScale_S(systemIndex, channelIndex, scale, inverted):
	SA_STATUS = MCS_lib.SA_SetScale_S(systemIndex, channelIndex, scale, inverted)
	return SA_STATUS

# MCSCONTROL_API // Global
# SA_STATUS MCSCONTROL_CC SA_SetSensorEnabled_S(SA_INDEX systemIndex, unsigned int enabled);
def SA_SetSensorEnabled_S(systemIndex, enabled):
	SA_STATUS = MCS_lib.SA_SetSensorEnabled_S(systemIndex, enabled)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetSensorType_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int type);
def SA_SetSensorType_S(systemIndex, channelIndex, typ):
	SA_STATUS = MCS_lib.SA_SetSensorType_S(systemIndex, channelIndex, typ)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetStepWhileScan_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int step);
def SA_SetStepWhileScan_S(systemIndex, channelIndex, step):
	SA_STATUS = MCS_lib.SA_SetStepWhileScan_S(systemIndex, channelIndex, step)
	return SA_STATUS

# MCSCONTROL_API // End effector
# SA_STATUS MCSCONTROL_CC SA_SetZeroForce_S(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_SetZeroForce_S(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_SetZeroForce_S(systemIndex, channelIndex)
	return SA_STATUS

# /*************************************************
# **************************************************
# **  Section IIa.2: Movement Control Functions   **
# **************************************************
# *************************************************/

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_CalibrateSensor_S(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_CalibrateSensor_S(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_CalibrateSensor_S(systemIndex, channelIndex)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_FindReferenceMark_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int direction, unsigned int holdTime, unsigned int autoZero);
def SA_FindReferenceMark_S(systemIndex, channelIndex, direction, holdTime, autoZero):
	SA_STATUS = MCS_lib.SA_FindReferenceMark_S(systemIndex, channelIndex, direction, holdTime, autoZero)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GotoAngleAbsolute_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int angle, signed int revolution, unsigned int holdTime);
def SA_GotoAngleAbsolute_S(systemIndex, channelIndex, angle, revolution, holdTime):
	SA_STATUS = MCS_lib.SA_GotoAngleAbsolute_S(systemIndex, channelIndex, angle, revolution, holdTime)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GotoAngleRelative_S(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int angleDiff, signed int revolutionDiff, unsigned int holdTime);
def SA_GotoAngleRelative_S(systemIndex, channelIndex, angleDiff, revolutionDiff, holdTime):
	SA_STATUS = MCS_lib.SA_GotoAngleRelative_S(systemIndex, channelIndex, angleDiff, revolutionDiff, holdTime)
	return SA_STATUS

# MCSCONTROL_API // End effector
# SA_STATUS MCSCONTROL_CC SA_GotoGripperForceAbsolute_S(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int force, unsigned int speed, unsigned int holdTime);
def SA_GotoGripperForceAbsolute_S(systemIndex, channelIndex, force, speed, holdTime):
	SA_STATUS = MCS_lib.SA_GotoGripperForceAbsolute_S(systemIndex, channelIndex, force, speed, holdTime)
	return SA_STATUS

# MCSCONTROL_API // End effector
# SA_STATUS MCSCONTROL_CC SA_GotoGripperOpeningAbsolute_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int opening, unsigned int speed);
def SA_GotoGripperOpeningAbsolute_S(systemIndex, channelIndex, opening, speed):
	SA_STATUS = MCS_lib.SA_GotoGripperOpeningAbsolute_S(systemIndex, channelIndex, opening, speed)
	return SA_STATUS

# MCSCONTROL_API // End effector
# SA_STATUS MCSCONTROL_CC SA_GotoGripperOpeningRelative_S(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int diff, unsigned int speed);
def SA_GotoGripperOpeningRelative_S(systemIndex, channelIndex, diff, speed):
	SA_STATUS = MCS_lib.SA_GotoGripperOpeningRelative_S(systemIndex, channelIndex, diff, speed)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GotoPositionAbsolute_S(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int position, unsigned int holdTime);
def SA_GotoPositionAbsolute_S(systemIndex, channelIndex, position, holdTime):
	SA_STATUS = MCS_lib.SA_GotoPositionAbsolute_S(systemIndex, channelIndex, position, holdTime)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GotoPositionRelative_S(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int diff, unsigned int holdTime);
def SA_GotoPositionRelative_S(systemIndex, channelIndex, diff, holdTime):
	SA_STATUS = MCS_lib.SA_GotoPositionRelative_S(systemIndex, channelIndex, diff, holdTime)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_ScanMoveAbsolute_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int target, unsigned int scanSpeed);
def SA_ScanMoveAbsolute_S(systemIndex, channelIndex, target, scanSpeed):
	SA_STATUS = MCS_lib.SA_ScanMoveAbsolute_S(systemIndex, channelIndex, target, scanSpeed)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_ScanMoveRelative_S(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int diff, unsigned int scanSpeed);
def SA_ScanMoveRelative_S(systemIndex, channelIndex, diff, scanSpeed):
	SA_STATUS = MCS_lib.SA_ScanMoveRelative_S(systemIndex, channelIndex, diff, scanSpeed)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_StepMove_S(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int steps, unsigned int amplitude, unsigned int frequency);
def SA_StepMove_S(systemIndex, channelIndex, steps, amplitude, frequency):
	SA_STATUS = MCS_lib.SA_StepMove_S(systemIndex, channelIndex, steps, amplitude, frequency)
	return SA_STATUS

# MCSCONTROL_API // Positioner, End effector
# SA_STATUS MCSCONTROL_CC SA_Stop_S(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_Stop_S(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_Stop_S(systemIndex, channelIndex)
	return SA_STATUS

# /************************************************
# *************************************************
# **  Section IIa.3: Channel Feedback Functions  **
# *************************************************
# *************************************************/

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetAngle_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int *angle, signed int *revolution);
def SA_GetAngle_S(systemIndex, channelIndex, angle, revolution):
	SA_STATUS = MCS_lib.SA_GetAngle_S(systemIndex, channelIndex, ct.byref(angle), ct.byref(revolution))
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetCaptureBuffer_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int bufferIndex, SA_PACKET *buffer);
# use buffr = SA_packet() before function call to intialize the inheritance of the SA_packet class before pointing to it
def SA_GetCaptureBuffer_S(systemIndex, channelIndex, bufferIndex, buffr):
	MCS_lib.SA_GetCaptureBuffer_S.argtypes = [ct.c_ulong,ct.c_ulong,ct.c_ulong, ct.POINTER(SA_packet)]
	SA_STATUS = MCS_lib.SA_GetCaptureBuffer_S(systemIndex, channelIndex, bufferIndex, buffr)
	return SA_STATUS

# MCSCONTROL_API // End effector
# SA_STATUS MCSCONTROL_CC SA_GetForce_S(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int *force);
def SA_GetForce_S(systemIndex, channelIndex, force):
	SA_STATUS = MCS_lib.SA_GetForce_S(systemIndex, channelIndex, ct.byref(force))
	return SA_STATUS

# MCSCONTROL_API // End effector
# SA_STATUS MCSCONTROL_CC SA_GetGripperOpening_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int *opening);
def SA_GetGripperOpening_S(systemIndex, channelIndex, opening):
	SA_STATUS = MCS_lib.SA_GetGripperOpening_S(systemIndex, channelIndex, ct.byref(opening))
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetPhysicalPositionKnown_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int *known);
def SA_GetPhysicalPositionKnown_S(systemIndex, channelIndex, known):
	SA_STATUS = MCS_lib.SA_GetPhysicalPositionKnown_S(systemIndex, channelIndex, ct.byref(known))
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetPosition_S(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int *position);
def SA_GetPosition_S(systemIndex, channelIndex, position):
	SA_STATUS = MCS_lib.SA_GetPosition_S(systemIndex, channelIndex, ct.byref(position))
	return SA_STATUS

# MCSCONTROL_API // Positioner, End effector
# SA_STATUS MCSCONTROL_CC SA_GetStatus_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int *status);
def SA_GetStatus_S(systemIndex, channelIndex, status):
	SA_STATUS = MCS_lib.SA_GetStatus_S(systemIndex, channelIndex, ct.byref(status))
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetVoltageLevel_S(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int *level);
def SA_GetVoltageLevel_S(systemIndex, channelIndex, level):
	SA_STATUS = MCS_lib.SA_GetVoltageLevel_S(systemIndex, channelIndex, ct.byref(level))
	return SA_STATUS


# /************************************************************************
# *************************************************************************
# **       Section IIb:  Functions for ASYNCHRONOUS communication        **
# *************************************************************************
# ************************************************************************/

# /*************************************************
# **************************************************
# **    Section IIb.1: Configuration Functions    **
# **************************************************
# *************************************************/

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_AppendTriggeredCommand_A(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int triggerSource);
def SA_AppendTriggeredCommand_A(systemIndex, channelIndex, triggerSource):
	SA_STATUS = MCS_lib.SA_AppendTriggeredCommand_A(systemIndex, channelIndex, triggerSource)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_ClearTriggeredCommandQueue_A(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_ClearTriggeredCommandQueue_A(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_ClearTriggeredCommandQueue_A(systemIndex, channelIndex)
	return SA_STATUS

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_FlushOutput_A(SA_INDEX systemIndex);
def SA_FlushOutput_A(systemIndex):
	SA_STATUS = MCS_lib.SA_FlushOutput_A(systemIndex)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetAngleLimit_A(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_GetAngleLimit_A(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_GetAngleLimit_A(systemIndex, channelIndex)
	return SA_STATUS

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_GetBufferedOutput_A(SA_INDEX systemIndex, unsigned int *mode);
def SA_GetBufferedOutput_A(systemIndex, mode):
	SA_STATUS = MCS_lib.SA_GetBufferedOutput_A(systemIndex, ct.byref(mode))
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetChannelProperty_A(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int key);
def SA_GetChannelProperty_A(systemIndex, channelIndex, key):
	SA_STATUS = MCS_lib.SA_GetChannelProperty_A(systemIndex, channelIndex, key)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetClosedLoopMoveAcceleration_A(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_GetClosedLoopMoveAcceleration_A(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_GetClosedLoopMoveAcceleration_A(systemIndex, channelIndex)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetClosedLoopMoveSpeed_A(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_GetClosedLoopMoveSpeed_A(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_GetClosedLoopMoveSpeed_A(systemIndex, channelIndex)
	return SA_STATUS

# MCSCONTROL_API // End effector
# SA_STATUS MCSCONTROL_CC SA_GetEndEffectorType_A(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_GetEndEffectorType_A(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_GetEndEffectorType_A(systemIndex, channelIndex)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetPhysicalPositionKnown_A(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_GetPhysicalPositionKnown_A(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_GetPhysicalPositionKnown_A(systemIndex, channelIndex)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetPositionLimit_A(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_GetPositionLimit_A(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_GetPositionLimit_A(systemIndex, channelIndex)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetSafeDirection_A(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_GetSafeDirection_A(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_GetSafeDirection_A(systemIndex, channelIndex)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetScale_A(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_GetScale_A(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_GetScale_A(systemIndex, channelIndex)
	return SA_STATUS

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_GetSensorEnabled_A(SA_INDEX systemIndex);
def SA_GetSensorEnabled_A(systemIndex):
	SA_STATUS = MCS_lib.SA_GetSensorEnabled_A(systemIndex)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetSensorType_A(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_GetSensorType_A(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_GetSensorType_A(systemIndex, channelIndex)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetAccumulateRelativePositions_A(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int accumulate);
def SA_SetAccumulateRelativePositions_A(systemIndex, channelIndex, accumulate):
	SA_STATUS = MCS_lib.SA_SetAccumulateRelativePositions_A(systemIndex, channelIndex, accumulate)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetAngleLimit_A(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int minAngle, signed int minRevolution, unsigned int maxAngle, signed int maxRevolution);
def SA_SetAngleLimit_A(systemIndex, channelIndex, minAngle, minRevolution, maxAngle, maxRevolution):
	SA_STATUS = MCS_lib.SA_SetAngleLimit_A(systemIndex, channelIndex, minAngle, minRevolution, maxAngle, maxRevolution)
	return SA_STATUS

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_SetBufferedOutput_A(SA_INDEX systemIndex, unsigned int mode);
def SA_SetBufferedOutput_A(systemIndex, mode):
	SA_STATUS = MCS_lib.SA_SetBufferedOutput_A(systemIndex, mode)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetChannelProperty_A(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int key, signed int value);
def SA_SetChannelProperty_A(systemIndex, channelIndex, key, value):
	SA_STATUS = MCS_lib.SA_SetChannelProperty_A(systemIndex, channelIndex, key, value)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetClosedLoopMaxFrequency_A(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int frequency);
def SA_SetClosedLoopMaxFrequency_A(systemIndex, channelIndex, frequency):
	SA_STATUS = MCS_lib.SA_SetClosedLoopMaxFrequency_A(systemIndex, channelIndex, frequency)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetClosedLoopMoveAcceleration_A(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int acceleration);
def SA_SetClosedLoopMoveAcceleration_A(systemIndex, channelIndex, acceleration):
	SA_STATUS = MCS_lib.SA_SetClosedLoopMoveAcceleration_A(systemIndex, channelIndex, acceleration)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetClosedLoopMoveSpeed_A(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int speed);
def SA_SetClosedLoopMoveSpeed_A(systemIndex, channelIndex, speed):
	SA_STATUS = MCS_lib.SA_SetClosedLoopMoveSpeed_A(systemIndex, channelIndex, speed)
	return SA_STATUS

# MCSCONTROL_API // End effector
# SA_STATUS MCSCONTROL_CC SA_SetEndEffectorType_A(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int type, signed int param1, signed int param2);
def SA_SetEndEffectorType_A(systemIndex, channelIndex, typ, param1, param2):
	SA_STATUS = MCS_lib.SA_SetEndEffectorType_A(systemIndex, channelIndex, typ, param1, param2)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetPosition_A(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int position);
def SA_SetPosition_A(systemIndex, channelIndex, position):
	SA_STATUS = MCS_lib.SA_SetPosition_A(systemIndex, channelIndex, position)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetPositionLimit_A(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int minPosition, signed int maxPosition);
def SA_SetPositionLimit_A(systemIndex, channelIndex, minPosition, maxPosition):
	SA_STATUS = MCS_lib.SA_SetPositionLimit_A(systemIndex, channelIndex, minPosition, maxPosition)
	return SA_STATUS

# MCSCONTROL_API // Positioner, End effector
# SA_STATUS MCSCONTROL_CC SA_SetReportOnComplete_A(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int report);
def SA_SetReportOnComplete_A(systemIndex, channelIndex, report):
	SA_STATUS = MCS_lib.SA_SetReportOnComplete_A(systemIndex, channelIndex, report)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetReportOnTriggered_A(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int report);
def SA_SetReportOnTriggered_A(systemIndex, channelIndex, report):
	SA_STATUS = MCS_lib.SA_SetReportOnTriggered_A(systemIndex, channelIndex, report)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetSafeDirection_A(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int direction);
def SA_SetSafeDirection_A(systemIndex, channelIndex, direction):
	SA_STATUS = MCS_lib.SA_SetSafeDirection_A(systemIndex, channelIndex, direction)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetScale_A(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int scale, unsigned int inverted);
def SA_SetScale_A(systemIndex, channelIndex, scale, inverted):
	SA_STATUS = MCS_lib.SA_SetScale_A(systemIndex, channelIndex, scale, inverted)
	return SA_STATUS

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_SetSensorEnabled_A(SA_INDEX systemIndex, unsigned int enabled);
def SA_SetSensorEnabled_A(systemIndex, enabled):
	SA_STATUS = MCS_lib.SA_SetSensorEnabled_A(systemIndex, enabled)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetSensorType_A(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int type);
def SA_SetSensorType_A(systemIndex, channelIndex, typ):
	SA_STATUS = MCS_lib.SA_SetSensorType_A(systemIndex, channelIndex, typ)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_SetStepWhileScan_A(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int step);
def SA_SetStepWhileScan_A(systemIndex, channelIndex, step):
	SA_STATUS = MCS_lib.SA_SetStepWhileScan_A(systemIndex, channelIndex, step)
	return SA_STATUS

# MCSCONTROL_API // End effector
# SA_STATUS MCSCONTROL_CC SA_SetZeroForce_A(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_SetZeroForce_A(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_SetZeroForce_A(systemIndex, channelIndex)
	return SA_STATUS

# /*************************************************
# **************************************************
# **  Section IIb.2: Movement Control Functions   **
# **************************************************
# *************************************************/
# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_CalibrateSensor_A(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_CalibrateSensor_A(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_CalibrateSensor_A(systemIndex, channelIndex)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_FindReferenceMark_A(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int direction, unsigned int holdTime, unsigned int autoZero);
def SA_FindReferenceMark_A(systemIndex, channelIndex, direction, holdTime, autoZero):
	SA_STATUS = MCS_lib.SA_FindReferenceMark_A(systemIndex, channelIndex, direction, holdTime, autoZero)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GotoAngleAbsolute_A(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int angle, signed int revolution, unsigned int holdTime);
def SA_GotoAngleAbsolute_A(systemIndex, channelIndex, angle, revolution, holdTime):
	SA_STATUS = MCS_lib.SA_GotoAngleAbsolute_A(systemIndex, channelIndex, angle, revolution, holdTime)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GotoAngleRelative_A(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int angleDiff, signed int revolutionDiff, unsigned int holdTime);
def SA_GotoAngleRelative_A(systemIndex, channelIndex, angleDiff, revolutionDiff, holdTime):
	SA_STATUS = MCS_lib.SA_GotoAngleRelative_A(systemIndex, channelIndex, angleDiff, revolutionDiff, holdTime)
	return SA_STATUS

# MCSCONTROL_API // End effector
# SA_STATUS MCSCONTROL_CC SA_GotoGripperForceAbsolute_A(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int force, unsigned int speed, unsigned int holdTime);
def SA_GotoGripperForceAbsolute_A(systemIndex, channelIndex, force, speed, holdTime):
	SA_STATUS = MCS_lib.SA_GotoGripperForceAbsolute_A(systemIndex, channelIndex, force, speed, holdTime)
	return SA_STATUS

# MCSCONTROL_API // End effector
# SA_STATUS MCSCONTROL_CC SA_GotoGripperOpeningAbsolute_A(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int opening, unsigned int speed);
def SA_GotoGripperOpeningAbsolute_A(systemIndex, channelIndex, opening, speed):
	SA_STATUS = MCS_lib.SA_GotoGripperOpeningAbsolute_A(systemIndex, channelIndex, opening, speed)
	return SA_STATUS

# MCSCONTROL_API // End effector
# SA_STATUS MCSCONTROL_CC SA_GotoGripperOpeningRelative_A(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int diff, unsigned int speed);
def SA_GotoGripperOpeningRelative_A(systemIndex, channelIndex, diff, speed):
	SA_STATUS = MCS_lib.SA_GotoGripperOpeningRelative_A(systemIndex, channelIndex, diff, speed)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GotoPositionAbsolute_A(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int position, unsigned int holdTime);
def SA_GotoPositionAbsolute_A(systemIndex, channelIndex, position, holdTime):
	SA_STATUS = MCS_lib.SA_GotoPositionAbsolute_A(systemIndex, channelIndex, position, holdTime)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GotoPositionRelative_A(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int diff, unsigned int holdTime);
def SA_GotoPositionRelative_A(systemIndex, channelIndex, diff, holdTime):
	SA_STATUS = MCS_lib.SA_GotoPositionRelative_A(systemIndex, channelIndex, diff, holdTime)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_ScanMoveAbsolute_A(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int target, unsigned int scanSpeed);
def SA_ScanMoveAbsolute_A(systemIndex, channelIndex, target, scanSpeed):
	SA_STATUS = MCS_lib.SA_ScanMoveAbsolute_A(systemIndex, channelIndex, target, scanSpeed)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_ScanMoveRelative_A(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int diff, unsigned int scanSpeed);
def SA_ScanMoveRelative_A(systemIndex, channelIndex, diff, scanSpeed):
	SA_STATUS = MCS_lib.SA_ScanMoveRelative_A(systemIndex, channelIndex, diff, scanSpeed)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_StepMove_A(SA_INDEX systemIndex, SA_INDEX channelIndex, signed int steps, unsigned int amplitude, unsigned int frequency);
def SA_StepMove_A(systemIndex, channelIndex, steps, amplitude, frequency):
	SA_STATUS = MCS_lib.SA_StepMove_A(systemIndex, channelIndex, steps, amplitude, frequency)
	return SA_STATUS

# MCSCONTROL_API // Positioner, End effector
# SA_STATUS MCSCONTROL_CC SA_Stop_A(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_Stop_A(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_Stop_A(systemIndex, channelIndex)
	return SA_STATUS

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_TriggerCommand_A(SA_INDEX systemIndex, unsigned int triggerIndex);
def SA_TriggerCommand_A(systemIndex, triggerIndex):
	SA_STATUS = MCS_lib.SA_TriggerCommand_A(systemIndex, triggerIndex)
	return SA_STATUS

# /************************************************
# *************************************************
# **  Section IIb.3: Channel Feedback Functions  **
# *************************************************
# ************************************************/
# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetAngle_A(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_GetAngle_A(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_GetAngle_A(systemIndex, channelIndex)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetCaptureBuffer_A(SA_INDEX systemIndex, SA_INDEX channelIndex, unsigned int bufferIndex);
def SA_GetCaptureBuffer_A(systemIndex, channelIndex, bufferIndex):
	SA_STATUS = MCS_lib.SA_GetCaptureBuffer_A(systemIndex, channelIndex, bufferIndex)
	return SA_STATUS

# MCSCONTROL_API // End effector
# SA_STATUS MCSCONTROL_CC SA_GetForce_A(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_GetForce_A(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_GetForce_A(systemIndex, channelIndex)
	return SA_STATUS

# MCSCONTROL_API // End effector
# SA_STATUS MCSCONTROL_CC SA_GetGripperOpening_A(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_GetGripperOpening_A(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_GetGripperOpening_A(systemIndex, channelIndex)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetPosition_A(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_GetPosition_A(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_GetPosition_A(systemIndex, channelIndex)
	return SA_STATUS

# MCSCONTROL_API // Positioner, End effector
# SA_STATUS MCSCONTROL_CC SA_GetStatus_A(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_GetStatus_A(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_GetStatus_A(systemIndex, channelIndex)
	return SA_STATUS

# MCSCONTROL_API // Positioner
# SA_STATUS MCSCONTROL_CC SA_GetVoltageLevel_A(SA_INDEX systemIndex, SA_INDEX channelIndex);
def SA_GetVoltageLevel_A(systemIndex, channelIndex):
	SA_STATUS = MCS_lib.SA_GetVoltageLevel_A(systemIndex, channelIndex)
	return SA_STATUS

# /******************
# * Answer retrieval
# ******************/
# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_DiscardPacket_A(SA_INDEX systemIndex);
def SA_DiscardPacket_A(systemIndex):
	SA_STATUS = MCS_lib.SA_DiscardPacket_A(systemIndex)
	return SA_STATUS

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_LookAtNextPacket_A(SA_INDEX systemIndex, unsigned int timeout, SA_PACKET *packet);
# use packet = SA_packet() before function call to intialize the inheritance of the SA_packet class before pointing to it
def SA_LookAtNextPacket_A(systemIndex, timeout, packet):
	MCS_lib.SA_LookAtNextPacket_A.argtypes = [ct.c_ulong, ct.c_ulong, ct.POINTER(SA_packet)]
	SA_STATUS = MCS_lib.SA_LookAtNextPacket_A(systemIndex, timeout, packet)
	return SA_STATUS

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_ReceiveNextPacket_A(SA_INDEX systemIndex, unsigned int timeout, SA_PACKET *packet);
# use packet = SA_packet() before function call to intialize the inheritance of the SA_packet class before pointing to it
def SA_ReceiveNextPacket_A(systemIndex, timeout, packet):
	MCS_lib.SA_ReceiveNextPacket_A.argtypes = [ct.c_ulong, ct.c_ulong, ct.POINTER(SA_packet)]
	SA_STATUS = MCS_lib.SA_ReceiveNextPacket_A(systemIndex, timeout, packet)
	return SA_STATUS

# MCSCONTROL_API
# SA_STATUS MCSCONTROL_CC SA_CancelWaitForPacket_A(SA_INDEX systemIndex);
def SA_CancelWaitForPacket_A(systemIndex):
	SA_STATUS = MCS_lib.SA_CancelWaitForPacket_A(systemIndex)
	return SA_STATUS



