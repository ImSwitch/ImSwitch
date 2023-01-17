from ctypes import *
import os
import platform
import sys

# Load library

# use cdecl on unix and stdcall on windows
def ximc_shared_lib():
    if platform.system() == "Linux":
        return CDLL("libximc.so")
    elif platform.system() == "FreeBSD":
        return CDLL("libximc.so")
    elif platform.system() == "Darwin":
        return CDLL("libximc.framework/libximc")
    elif platform.system() == "Windows":
        if sys.version_info[0] == 3 and sys.version_info[0] >= 8:
            return WinDLL("libximc.dll", winmode=RTLD_GLOBAL)
        else:
            return WinDLL("libximc.dll")
    else:
        return None

lib = ximc_shared_lib()

# Common declarations

class Result:
    Ok = 0
    Error = -1
    NotImplemented = -2
    ValueError = -3
    NoDevice = -4


class calibration_t(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('A', c_double),
        ('MicrostepMode', c_uint)
    ]

class device_enumeration_t(LittleEndianStructure):
    pass

class device_network_information_t(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('ipv4', c_uint32),
        ('nodename', c_char * 16),
        ('axis_state', c_uint),
        ('locker_username', c_char * 16),
        ('locker_nodename', c_char * 16),
        ('locked_time', c_ulonglong),
    ]


# Clarify function types

lib.enumerate_devices.restype = POINTER(device_enumeration_t)
lib.get_device_name.restype = c_char_p



# ---------------------------
# BEGIN OF GENERATED code
# ---------------------------
class EnumerateFlags:
	ENUMERATE_PROBE      = 0x01
	ENUMERATE_ALL_COM    = 0x02
	ENUMERATE_NETWORK    = 0x04

class MoveState:
	MOVE_STATE_MOVING          = 0x01
	MOVE_STATE_TARGET_SPEED    = 0x02
	MOVE_STATE_ANTIPLAY        = 0x04

class ControllerFlags:
	EEPROM_PRECEDENCE    = 0x01

class PowerState:
	PWR_STATE_UNKNOWN    = 0x00
	PWR_STATE_OFF        = 0x01
	PWR_STATE_NORM       = 0x03
	PWR_STATE_REDUCT     = 0x04
	PWR_STATE_MAX        = 0x05

class StateFlags:
	STATE_CONTR                     = 0x000003F
	STATE_ERRC                      = 0x0000001
	STATE_ERRD                      = 0x0000002
	STATE_ERRV                      = 0x0000004
	STATE_EEPROM_CONNECTED          = 0x0000010
	STATE_IS_HOMED                  = 0x0000020
	STATE_SECUR                     = 0x1B3FFC0
	STATE_ALARM                     = 0x0000040
	STATE_CTP_ERROR                 = 0x0000080
	STATE_POWER_OVERHEAT            = 0x0000100
	STATE_CONTROLLER_OVERHEAT       = 0x0000200
	STATE_OVERLOAD_POWER_VOLTAGE    = 0x0000400
	STATE_OVERLOAD_POWER_CURRENT    = 0x0000800
	STATE_OVERLOAD_USB_VOLTAGE      = 0x0001000
	STATE_LOW_USB_VOLTAGE           = 0x0002000
	STATE_OVERLOAD_USB_CURRENT      = 0x0004000
	STATE_BORDERS_SWAP_MISSET       = 0x0008000
	STATE_LOW_POWER_VOLTAGE         = 0x0010000
	STATE_H_BRIDGE_FAULT            = 0x0020000
	STATE_WINDING_RES_MISMATCH      = 0x0100000
	STATE_ENCODER_FAULT             = 0x0200000
	STATE_ENGINE_RESPONSE_ERROR     = 0x0800000
	STATE_EXTIO_ALARM               = 0x1000000

class GPIOFlags:
	STATE_DIG_SIGNAL      = 0xFFFF
	STATE_RIGHT_EDGE      = 0x0001
	STATE_LEFT_EDGE       = 0x0002
	STATE_BUTTON_RIGHT    = 0x0004
	STATE_BUTTON_LEFT     = 0x0008
	STATE_GPIO_PINOUT     = 0x0010
	STATE_GPIO_LEVEL      = 0x0020
	STATE_BRAKE           = 0x0200
	STATE_REV_SENSOR      = 0x0400
	STATE_SYNC_INPUT      = 0x0800
	STATE_SYNC_OUTPUT     = 0x1000
	STATE_ENC_A           = 0x2000
	STATE_ENC_B           = 0x4000

class EncodeStatus:
	ENC_STATE_ABSENT     = 0x00
	ENC_STATE_UNKNOWN    = 0x01
	ENC_STATE_MALFUNC    = 0x02
	ENC_STATE_REVERS     = 0x03
	ENC_STATE_OK         = 0x04

class WindStatus:
	WIND_A_STATE_ABSENT     = 0x00
	WIND_A_STATE_UNKNOWN    = 0x01
	WIND_A_STATE_MALFUNC    = 0x02
	WIND_A_STATE_OK         = 0x03
	WIND_B_STATE_ABSENT     = 0x00
	WIND_B_STATE_UNKNOWN    = 0x10
	WIND_B_STATE_MALFUNC    = 0x20
	WIND_B_STATE_OK         = 0x30

class MvcmdStatus:
	MVCMD_NAME_BITS    = 0x3F
	MVCMD_UKNWN        = 0x00
	MVCMD_MOVE         = 0x01
	MVCMD_MOVR         = 0x02
	MVCMD_LEFT         = 0x03
	MVCMD_RIGHT        = 0x04
	MVCMD_STOP         = 0x05
	MVCMD_HOME         = 0x06
	MVCMD_LOFT         = 0x07
	MVCMD_SSTP         = 0x08
	MVCMD_ERROR        = 0x40
	MVCMD_RUNNING      = 0x80

class MoveFlags:
	RPM_DIV_1000    = 0x01

class EngineFlags:
	ENGINE_REVERSE           = 0x01
	ENGINE_CURRENT_AS_RMS    = 0x02
	ENGINE_MAX_SPEED         = 0x04
	ENGINE_ANTIPLAY          = 0x08
	ENGINE_ACCEL_ON          = 0x10
	ENGINE_LIMIT_VOLT        = 0x20
	ENGINE_LIMIT_CURR        = 0x40
	ENGINE_LIMIT_RPM         = 0x80

class MicrostepMode:
	MICROSTEP_MODE_FULL        = 0x01
	MICROSTEP_MODE_FRAC_2      = 0x02
	MICROSTEP_MODE_FRAC_4      = 0x03
	MICROSTEP_MODE_FRAC_8      = 0x04
	MICROSTEP_MODE_FRAC_16     = 0x05
	MICROSTEP_MODE_FRAC_32     = 0x06
	MICROSTEP_MODE_FRAC_64     = 0x07
	MICROSTEP_MODE_FRAC_128    = 0x08
	MICROSTEP_MODE_FRAC_256    = 0x09

class EngineType:
	ENGINE_TYPE_NONE         = 0x00
	ENGINE_TYPE_DC           = 0x01
	ENGINE_TYPE_2DC          = 0x02
	ENGINE_TYPE_STEP         = 0x03
	ENGINE_TYPE_TEST         = 0x04
	ENGINE_TYPE_BRUSHLESS    = 0x05

class DriverType:
	DRIVER_TYPE_DISCRETE_FET    = 0x01
	DRIVER_TYPE_INTEGRATE       = 0x02
	DRIVER_TYPE_EXTERNAL        = 0x03

class PowerFlags:
	POWER_REDUCT_ENABLED    = 0x01
	POWER_OFF_ENABLED       = 0x02
	POWER_SMOOTH_CURRENT    = 0x04

class SecureFlags:
	ALARM_ON_DRIVER_OVERHEATING     = 0x01
	LOW_UPWR_PROTECTION             = 0x02
	H_BRIDGE_ALERT                  = 0x04
	ALARM_ON_BORDERS_SWAP_MISSET    = 0x08
	ALARM_FLAGS_STICKING            = 0x10
	USB_BREAK_RECONNECT             = 0x20
	ALARM_WINDING_MISMATCH          = 0x40
	ALARM_ENGINE_RESPONSE           = 0x80

class PositionFlags:
	SETPOS_IGNORE_POSITION    = 0x01
	SETPOS_IGNORE_ENCODER     = 0x02

class FeedbackType:
	FEEDBACK_ENCODER             = 0x01
	FEEDBACK_EMF                 = 0x04
	FEEDBACK_NONE                = 0x05
	FEEDBACK_ENCODER_MEDIATED    = 0x06

class FeedbackFlags:
	FEEDBACK_ENC_REVERSE              = 0x01
	FEEDBACK_ENC_TYPE_BITS            = 0xC0
	FEEDBACK_ENC_TYPE_AUTO            = 0x00
	FEEDBACK_ENC_TYPE_SINGLE_ENDED    = 0x40
	FEEDBACK_ENC_TYPE_DIFFERENTIAL    = 0x80

class SyncInFlags:
	SYNCIN_ENABLED         = 0x01
	SYNCIN_INVERT          = 0x02
	SYNCIN_GOTOPOSITION    = 0x04

class SyncOutFlags:
	SYNCOUT_ENABLED     = 0x01
	SYNCOUT_STATE       = 0x02
	SYNCOUT_INVERT      = 0x04
	SYNCOUT_IN_STEPS    = 0x08
	SYNCOUT_ONSTART     = 0x10
	SYNCOUT_ONSTOP      = 0x20
	SYNCOUT_ONPERIOD    = 0x40

class ExtioSetupFlags:
	EXTIO_SETUP_OUTPUT    = 0x01
	EXTIO_SETUP_INVERT    = 0x02

class ExtioModeFlags:
	EXTIO_SETUP_MODE_IN_BITS         = 0x0F
	EXTIO_SETUP_MODE_IN_NOP          = 0x00
	EXTIO_SETUP_MODE_IN_STOP         = 0x01
	EXTIO_SETUP_MODE_IN_PWOF         = 0x02
	EXTIO_SETUP_MODE_IN_MOVR         = 0x03
	EXTIO_SETUP_MODE_IN_HOME         = 0x04
	EXTIO_SETUP_MODE_IN_ALARM        = 0x05
	EXTIO_SETUP_MODE_OUT_BITS        = 0xF0
	EXTIO_SETUP_MODE_OUT_OFF         = 0x00
	EXTIO_SETUP_MODE_OUT_ON          = 0x10
	EXTIO_SETUP_MODE_OUT_MOVING      = 0x20
	EXTIO_SETUP_MODE_OUT_ALARM       = 0x30
	EXTIO_SETUP_MODE_OUT_MOTOR_ON    = 0x40

class BorderFlags:
	BORDER_IS_ENCODER                = 0x01
	BORDER_STOP_LEFT                 = 0x02
	BORDER_STOP_RIGHT                = 0x04
	BORDERS_SWAP_MISSET_DETECTION    = 0x08

class EnderFlags:
	ENDER_SWAP              = 0x01
	ENDER_SW1_ACTIVE_LOW    = 0x02
	ENDER_SW2_ACTIVE_LOW    = 0x04

class BrakeFlags:
	BRAKE_ENABLED       = 0x01
	BRAKE_ENG_PWROFF    = 0x02

class ControlFlags:
	CONTROL_MODE_BITS                = 0x03
	CONTROL_MODE_OFF                 = 0x00
	CONTROL_MODE_JOY                 = 0x01
	CONTROL_MODE_LR                  = 0x02
	CONTROL_BTN_LEFT_PUSHED_OPEN     = 0x04
	CONTROL_BTN_RIGHT_PUSHED_OPEN    = 0x08

class JoyFlags:
	JOY_REVERSE    = 0x01

class CtpFlags:
	CTP_ENABLED             = 0x01
	CTP_BASE                = 0x02
	CTP_ALARM_ON_ERROR      = 0x04
	REV_SENS_INV            = 0x08
	CTP_ERROR_CORRECTION    = 0x10

class HomeFlags:
	HOME_DIR_FIRST           = 0x001
	HOME_DIR_SECOND          = 0x002
	HOME_MV_SEC_EN           = 0x004
	HOME_HALF_MV             = 0x008
	HOME_STOP_FIRST_BITS     = 0x030
	HOME_STOP_FIRST_REV      = 0x010
	HOME_STOP_FIRST_SYN      = 0x020
	HOME_STOP_FIRST_LIM      = 0x030
	HOME_STOP_SECOND_BITS    = 0x0C0
	HOME_STOP_SECOND_REV     = 0x040
	HOME_STOP_SECOND_SYN     = 0x080
	HOME_STOP_SECOND_LIM     = 0x0C0
	HOME_USE_FAST            = 0x100

class UARTSetupFlags:
	UART_PARITY_BITS         = 0x03
	UART_PARITY_BIT_EVEN     = 0x00
	UART_PARITY_BIT_ODD      = 0x01
	UART_PARITY_BIT_SPACE    = 0x02
	UART_PARITY_BIT_MARK     = 0x03
	UART_PARITY_BIT_USE      = 0x04
	UART_STOP_BIT            = 0x08

class MotorTypeFlags:
	MOTOR_TYPE_UNKNOWN    = 0x00
	MOTOR_TYPE_STEP       = 0x01
	MOTOR_TYPE_DC         = 0x02
	MOTOR_TYPE_BLDC       = 0x03

class EncoderSettingsFlags:
	ENCSET_DIFFERENTIAL_OUTPUT             = 0x001
	ENCSET_PUSHPULL_OUTPUT                 = 0x004
	ENCSET_INDEXCHANNEL_PRESENT            = 0x010
	ENCSET_REVOLUTIONSENSOR_PRESENT        = 0x040
	ENCSET_REVOLUTIONSENSOR_ACTIVE_HIGH    = 0x100

class MBSettingsFlags:
	MB_AVAILABLE       = 0x01
	MB_POWERED_HOLD    = 0x02

class TSSettingsFlags:
	TS_TYPE_BITS             = 0x07
	TS_TYPE_UNKNOWN          = 0x00
	TS_TYPE_THERMOCOUPLE     = 0x01
	TS_TYPE_SEMICONDUCTOR    = 0x02
	TS_AVAILABLE             = 0x08

class LSFlags:
	LS_ON_SW1_AVAILABLE    = 0x01
	LS_ON_SW2_AVAILABLE    = 0x02
	LS_SW1_ACTIVE_LOW      = 0x04
	LS_SW2_ACTIVE_LOW      = 0x08
	LS_SHORTED             = 0x10

class BackEMFFlags:
	BACK_EMF_INDUCTANCE_AUTO    = 0x01
	BACK_EMF_RESISTANCE_AUTO    = 0x02
	BACK_EMF_KM_AUTO            = 0x04


class feedback_settings_t(Structure):
	_fields_ = [
		("IPS", c_uint),
		("FeedbackType", c_uint),
		("FeedbackFlags", c_uint),
		("CountsPerTurn", c_uint),
	]

class home_settings_t(Structure):
	_fields_ = [
		("FastHome", c_uint),
		("uFastHome", c_uint),
		("SlowHome", c_uint),
		("uSlowHome", c_uint),
		("HomeDelta", c_int),
		("uHomeDelta", c_int),
		("HomeFlags", c_uint),
	]

class home_settings_calb_t(Structure):
	_fields_ = [
		("FastHome", c_float),
		("SlowHome", c_float),
		("HomeDelta", c_float),
		("HomeFlags", c_uint),
	]

class move_settings_t(Structure):
	_fields_ = [
		("Speed", c_uint),
		("uSpeed", c_uint),
		("Accel", c_uint),
		("Decel", c_uint),
		("AntiplaySpeed", c_uint),
		("uAntiplaySpeed", c_uint),
		("MoveFlags", c_uint),
	]

class move_settings_calb_t(Structure):
	_fields_ = [
		("Speed", c_float),
		("Accel", c_float),
		("Decel", c_float),
		("AntiplaySpeed", c_float),
		("MoveFlags", c_uint),
	]

class engine_settings_t(Structure):
	_fields_ = [
		("NomVoltage", c_uint),
		("NomCurrent", c_uint),
		("NomSpeed", c_uint),
		("uNomSpeed", c_uint),
		("EngineFlags", c_uint),
		("Antiplay", c_int),
		("MicrostepMode", c_uint),
		("StepsPerRev", c_uint),
	]

class engine_settings_calb_t(Structure):
	_fields_ = [
		("NomVoltage", c_uint),
		("NomCurrent", c_uint),
		("NomSpeed", c_float),
		("EngineFlags", c_uint),
		("Antiplay", c_float),
		("MicrostepMode", c_uint),
		("StepsPerRev", c_uint),
	]

class entype_settings_t(Structure):
	_fields_ = [
		("EngineType", c_uint),
		("DriverType", c_uint),
	]

class power_settings_t(Structure):
	_fields_ = [
		("HoldCurrent", c_uint),
		("CurrReductDelay", c_uint),
		("PowerOffDelay", c_uint),
		("CurrentSetTime", c_uint),
		("PowerFlags", c_uint),
	]

class secure_settings_t(Structure):
	_fields_ = [
		("LowUpwrOff", c_uint),
		("CriticalIpwr", c_uint),
		("CriticalUpwr", c_uint),
		("CriticalT", c_uint),
		("CriticalIusb", c_uint),
		("CriticalUusb", c_uint),
		("MinimumUusb", c_uint),
		("Flags", c_uint),
	]

class edges_settings_t(Structure):
	_fields_ = [
		("BorderFlags", c_uint),
		("EnderFlags", c_uint),
		("LeftBorder", c_int),
		("uLeftBorder", c_int),
		("RightBorder", c_int),
		("uRightBorder", c_int),
	]

class edges_settings_calb_t(Structure):
	_fields_ = [
		("BorderFlags", c_uint),
		("EnderFlags", c_uint),
		("LeftBorder", c_float),
		("RightBorder", c_float),
	]

class pid_settings_t(Structure):
	_fields_ = [
		("KpU", c_uint),
		("KiU", c_uint),
		("KdU", c_uint),
		("Kpf", c_float),
		("Kif", c_float),
		("Kdf", c_float),
	]

class sync_in_settings_t(Structure):
	_fields_ = [
		("SyncInFlags", c_uint),
		("ClutterTime", c_uint),
		("Distance", c_int),
		("uPosition", c_int),
		("Speed", c_uint),
		("uSpeed", c_uint),
	]

class sync_in_settings_calb_t(Structure):
	_fields_ = [
		("SyncInFlags", c_uint),
		("ClutterTime", c_uint),
		("Distance", c_float),
		("Speed", c_float),
	]

class sync_out_settings_t(Structure):
	_fields_ = [
		("SyncOutFlags", c_uint),
		("SyncOutPulseSteps", c_uint),
		("SyncOutPeriod", c_uint),
		("Accuracy", c_uint),
		("uAccuracy", c_uint),
	]

class sync_out_settings_calb_t(Structure):
	_fields_ = [
		("SyncOutFlags", c_uint),
		("SyncOutPulseSteps", c_uint),
		("SyncOutPeriod", c_uint),
		("Accuracy", c_float),
	]

class extio_settings_t(Structure):
	_fields_ = [
		("EXTIOSetupFlags", c_uint),
		("EXTIOModeFlags", c_uint),
	]

class brake_settings_t(Structure):
	_fields_ = [
		("t1", c_uint),
		("t2", c_uint),
		("t3", c_uint),
		("t4", c_uint),
		("BrakeFlags", c_uint),
	]

class control_settings_t(Structure):
	_fields_ = [
		("MaxSpeed", c_uint * 10),
		("uMaxSpeed", c_uint * 10),
		("Timeout", c_uint * 9),
		("MaxClickTime", c_uint),
		("Flags", c_uint),
		("DeltaPosition", c_int),
		("uDeltaPosition", c_int),
	]

class control_settings_calb_t(Structure):
	_fields_ = [
		("MaxSpeed", c_float * 10),
		("Timeout", c_uint * 9),
		("MaxClickTime", c_uint),
		("Flags", c_uint),
		("DeltaPosition", c_float),
	]

class joystick_settings_t(Structure):
	_fields_ = [
		("JoyLowEnd", c_uint),
		("JoyCenter", c_uint),
		("JoyHighEnd", c_uint),
		("ExpFactor", c_uint),
		("DeadZone", c_uint),
		("JoyFlags", c_uint),
	]

class ctp_settings_t(Structure):
	_fields_ = [
		("CTPMinError", c_uint),
		("CTPFlags", c_uint),
	]

class uart_settings_t(Structure):
	_fields_ = [
		("Speed", c_uint),
		("UARTSetupFlags", c_uint),
	]

class calibration_settings_t(Structure):
	_fields_ = [
		("CSS1_A", c_float),
		("CSS1_B", c_float),
		("CSS2_A", c_float),
		("CSS2_B", c_float),
		("FullCurrent_A", c_float),
		("FullCurrent_B", c_float),
	]

class controller_name_t(Structure):
	_fields_ = [
		("ControllerName", c_char * 17),
		("CtrlFlags", c_uint),
	]

class nonvolatile_memory_t(Structure):
	_fields_ = [
		("UserData", c_uint * 7),
	]

class emf_settings_t(Structure):
	_fields_ = [
		("L", c_float),
		("R", c_float),
		("Km", c_float),
		("BackEMFFlags", c_uint),
	]

class engine_advansed_setup_t(Structure):
	_fields_ = [
		("stepcloseloop_Kw", c_uint),
		("stepcloseloop_Kp_low", c_uint),
		("stepcloseloop_Kp_high", c_uint),
	]

class extended_settings_t(Structure):
	_fields_ = [
		("Param1", c_uint),
	]

class get_position_t(Structure):
	_fields_ = [
		("Distance", c_int),
		("uPosition", c_int),
		("EncPosition", c_longlong),
	]

class get_position_calb_t(Structure):
	_fields_ = [
		("Distance", c_float),
		("EncPosition", c_longlong),
	]

class set_position_t(Structure):
	_fields_ = [
		("Distance", c_int),
		("uPosition", c_int),
		("EncPosition", c_longlong),
		("PosFlags", c_uint),
	]

class set_position_calb_t(Structure):
	_fields_ = [
		("Distance", c_float),
		("EncPosition", c_longlong),
		("PosFlags", c_uint),
	]

class status_t(Structure):
	_fields_ = [
		("MoveSts", c_uint),
		("MvCmdSts", c_uint),
		("PWRSts", c_uint),
		("EncSts", c_uint),
		("WindSts", c_uint),
		("CurPosition", c_int),
		("uCurPosition", c_int),
		("EncPosition", c_longlong),
		("CurSpeed", c_int),
		("uCurSpeed", c_int),
		("Ipwr", c_int),
		("Upwr", c_int),
		("Iusb", c_int),
		("Uusb", c_int),
		("CurT", c_int),
		("Flags", c_uint),
		("GPIOFlags", c_uint),
		("CmdBufFreeSpace", c_uint),
	]

class status_calb_t(Structure):
	_fields_ = [
		("MoveSts", c_uint),
		("MvCmdSts", c_uint),
		("PWRSts", c_uint),
		("EncSts", c_uint),
		("WindSts", c_uint),
		("CurPosition", c_float),
		("EncPosition", c_longlong),
		("CurSpeed", c_float),
		("Ipwr", c_int),
		("Upwr", c_int),
		("Iusb", c_int),
		("Uusb", c_int),
		("CurT", c_int),
		("Flags", c_uint),
		("GPIOFlags", c_uint),
		("CmdBufFreeSpace", c_uint),
	]

class measurements_t(Structure):
	_fields_ = [
		("Speed", c_int * 25),
		("Error", c_int * 25),
		("Length", c_uint),
	]

class chart_data_t(Structure):
	_fields_ = [
		("WindingVoltageA", c_int),
		("WindingVoltageB", c_int),
		("WindingVoltageC", c_int),
		("WindingCurrentA", c_int),
		("WindingCurrentB", c_int),
		("WindingCurrentC", c_int),
		("Pot", c_uint),
		("Joy", c_uint),
		("DutyCycle", c_int),
	]

class device_information_t(Structure):
	_fields_ = [
		("Manufacturer", c_char * 5),
		("ManufacturerId", c_char * 3),
		("ProductDescription", c_char * 9),
		("Major", c_uint),
		("Minor", c_uint),
		("Release", c_uint),
	]

class serial_number_t(Structure):
	_fields_ = [
		("SN", c_uint),
		("Key", c_ubyte * 32),
		("Major", c_uint),
		("Minor", c_uint),
		("Release", c_uint),
	]

class analog_data_t(Structure):
	_fields_ = [
		("A1Voltage_ADC", c_uint),
		("A2Voltage_ADC", c_uint),
		("B1Voltage_ADC", c_uint),
		("B2Voltage_ADC", c_uint),
		("SupVoltage_ADC", c_uint),
		("ACurrent_ADC", c_uint),
		("BCurrent_ADC", c_uint),
		("FullCurrent_ADC", c_uint),
		("Temp_ADC", c_uint),
		("Joy_ADC", c_uint),
		("Pot_ADC", c_uint),
		("L5_ADC", c_uint),
		("H5_ADC", c_uint),
		("A1Voltage", c_int),
		("A2Voltage", c_int),
		("B1Voltage", c_int),
		("B2Voltage", c_int),
		("SupVoltage", c_int),
		("ACurrent", c_int),
		("BCurrent", c_int),
		("FullCurrent", c_int),
		("Temp", c_int),
		("Joy", c_int),
		("Pot", c_int),
		("L5", c_int),
		("H5", c_int),
		("deprecated", c_uint),
		("R", c_int),
		("L", c_int),
	]

class debug_read_t(Structure):
	_fields_ = [
		("DebugData", c_ubyte * 128),
	]

class debug_write_t(Structure):
	_fields_ = [
		("DebugData", c_ubyte * 128),
	]

class stage_name_t(Structure):
	_fields_ = [
		("PositionerName", c_char * 17),
	]

class stage_information_t(Structure):
	_fields_ = [
		("Manufacturer", c_char * 17),
		("PartNumber", c_char * 25),
	]

class stage_settings_t(Structure):
	_fields_ = [
		("LeadScrewPitch", c_float),
		("Units", c_char * 9),
		("MaxSpeed", c_float),
		("TravelRange", c_float),
		("SupplyVoltageMin", c_float),
		("SupplyVoltageMax", c_float),
		("MaxCurrentConsumption", c_float),
		("HorizontalLoadCapacity", c_float),
		("VerticalLoadCapacity", c_float),
	]

class motor_information_t(Structure):
	_fields_ = [
		("Manufacturer", c_char * 17),
		("PartNumber", c_char * 25),
	]

class motor_settings_t(Structure):
	_fields_ = [
		("MotorType", c_uint),
		("ReservedField", c_uint),
		("Poles", c_uint),
		("Phases", c_uint),
		("NominalVoltage", c_float),
		("NominalCurrent", c_float),
		("NominalSpeed", c_float),
		("NominalTorque", c_float),
		("NominalPower", c_float),
		("WindingResistance", c_float),
		("WindingInductance", c_float),
		("RotorInertia", c_float),
		("StallTorque", c_float),
		("DetentTorque", c_float),
		("TorqueConstant", c_float),
		("SpeedConstant", c_float),
		("SpeedTorqueGradient", c_float),
		("MechanicalTimeConstant", c_float),
		("MaxSpeed", c_float),
		("MaxCurrent", c_float),
		("MaxCurrentTime", c_float),
		("NoLoadCurrent", c_float),
		("NoLoadSpeed", c_float),
	]

class encoder_information_t(Structure):
	_fields_ = [
		("Manufacturer", c_char * 17),
		("PartNumber", c_char * 25),
	]

class encoder_settings_t(Structure):
	_fields_ = [
		("MaxOperatingFrequency", c_float),
		("SupplyVoltageMin", c_float),
		("SupplyVoltageMax", c_float),
		("MaxCurrentConsumption", c_float),
		("PPR", c_uint),
		("EncoderSettings", c_uint),
	]

class hallsensor_information_t(Structure):
	_fields_ = [
		("Manufacturer", c_char * 17),
		("PartNumber", c_char * 25),
	]

class hallsensor_settings_t(Structure):
	_fields_ = [
		("MaxOperatingFrequency", c_float),
		("SupplyVoltageMin", c_float),
		("SupplyVoltageMax", c_float),
		("MaxCurrentConsumption", c_float),
		("PPR", c_uint),
	]

class gear_information_t(Structure):
	_fields_ = [
		("Manufacturer", c_char * 17),
		("PartNumber", c_char * 25),
	]

class gear_settings_t(Structure):
	_fields_ = [
		("ReductionIn", c_float),
		("ReductionOut", c_float),
		("RatedInputTorque", c_float),
		("RatedInputSpeed", c_float),
		("MaxOutputBacklash", c_float),
		("InputInertia", c_float),
		("Efficiency", c_float),
	]

class accessories_settings_t(Structure):
	_fields_ = [
		("MagneticBrakeInfo", c_char * 25),
		("MBRatedVoltage", c_float),
		("MBRatedCurrent", c_float),
		("MBTorque", c_float),
		("MBSettings", c_uint),
		("TemperatureSensorInfo", c_char * 25),
		("TSMin", c_float),
		("TSMax", c_float),
		("TSGrad", c_float),
		("TSSettings", c_uint),
		("LimitSwitchesSettings", c_uint),
	]

class init_random_t(Structure):
	_fields_ = [
		("key", c_ubyte * 16),
	]

class globally_unique_identifier_t(Structure):
	_fields_ = [
		("UniqueID0", c_uint),
		("UniqueID1", c_uint),
		("UniqueID2", c_uint),
		("UniqueID3", c_uint),
	]

# -------------------------
# END OF GENERATED code
# -------------------------



# vim: set ft=python
