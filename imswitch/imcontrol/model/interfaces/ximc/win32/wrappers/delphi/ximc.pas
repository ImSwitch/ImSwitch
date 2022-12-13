unit ximc;

interface

uses Windows, Sysutils;

const
	XimcDll = 'libximc.dll';

type
	Device = integer;

type
	XimcResult = integer;

type
	StringArray = array of string;

const
	DeviceUndefined = -1;

const
	ResultOk = 0;
	ResultError = -1;
	ResultNotImplemented = -2;
	ResultValueError = -3;
	ResultNoDevice = -4;

type
	PPAnsiChar = ^PAnsiChar;

type calibration_t = record
	A: double;
	MicrostepMode: integer;
end;


{
 ------------------------------------------
   BEGIN OF GENERATED struct declarations
 ------------------------------------------
}

const
	LIBXIMC_VERSION = '2.13.5';

const
	ENUMERATE_PROBE      = $01;
	ENUMERATE_ALL_COM    = $02;
	ENUMERATE_NETWORK    = $04;

	MOVE_STATE_MOVING          = $01;
	MOVE_STATE_TARGET_SPEED    = $02;
	MOVE_STATE_ANTIPLAY        = $04;

	EEPROM_PRECEDENCE    = $01;

	PWR_STATE_UNKNOWN    = $00;
	PWR_STATE_OFF        = $01;
	PWR_STATE_NORM       = $03;
	PWR_STATE_REDUCT     = $04;
	PWR_STATE_MAX        = $05;

	STATE_CONTR                     = $000003F;
	STATE_ERRC                      = $0000001;
	STATE_ERRD                      = $0000002;
	STATE_ERRV                      = $0000004;
	STATE_EEPROM_CONNECTED          = $0000010;
	STATE_IS_HOMED                  = $0000020;
	STATE_SECUR                     = $1B3FFC0;
	STATE_ALARM                     = $0000040;
	STATE_CTP_ERROR                 = $0000080;
	STATE_POWER_OVERHEAT            = $0000100;
	STATE_CONTROLLER_OVERHEAT       = $0000200;
	STATE_OVERLOAD_POWER_VOLTAGE    = $0000400;
	STATE_OVERLOAD_POWER_CURRENT    = $0000800;
	STATE_OVERLOAD_USB_VOLTAGE      = $0001000;
	STATE_LOW_USB_VOLTAGE           = $0002000;
	STATE_OVERLOAD_USB_CURRENT      = $0004000;
	STATE_BORDERS_SWAP_MISSET       = $0008000;
	STATE_LOW_POWER_VOLTAGE         = $0010000;
	STATE_H_BRIDGE_FAULT            = $0020000;
	STATE_WINDING_RES_MISMATCH      = $0100000;
	STATE_ENCODER_FAULT             = $0200000;
	STATE_ENGINE_RESPONSE_ERROR     = $0800000;
	STATE_EXTIO_ALARM               = $1000000;

	STATE_DIG_SIGNAL      = $FFFF;
	STATE_RIGHT_EDGE      = $0001;
	STATE_LEFT_EDGE       = $0002;
	STATE_BUTTON_RIGHT    = $0004;
	STATE_BUTTON_LEFT     = $0008;
	STATE_GPIO_PINOUT     = $0010;
	STATE_GPIO_LEVEL      = $0020;
	STATE_BRAKE           = $0200;
	STATE_REV_SENSOR      = $0400;
	STATE_SYNC_INPUT      = $0800;
	STATE_SYNC_OUTPUT     = $1000;
	STATE_ENC_A           = $2000;
	STATE_ENC_B           = $4000;

	ENC_STATE_ABSENT     = $00;
	ENC_STATE_UNKNOWN    = $01;
	ENC_STATE_MALFUNC    = $02;
	ENC_STATE_REVERS     = $03;
	ENC_STATE_OK         = $04;

	WIND_A_STATE_ABSENT     = $00;
	WIND_A_STATE_UNKNOWN    = $01;
	WIND_A_STATE_MALFUNC    = $02;
	WIND_A_STATE_OK         = $03;
	WIND_B_STATE_ABSENT     = $00;
	WIND_B_STATE_UNKNOWN    = $10;
	WIND_B_STATE_MALFUNC    = $20;
	WIND_B_STATE_OK         = $30;

	MVCMD_NAME_BITS    = $3F;
	MVCMD_UKNWN        = $00;
	MVCMD_MOVE         = $01;
	MVCMD_MOVR         = $02;
	MVCMD_LEFT         = $03;
	MVCMD_RIGHT        = $04;
	MVCMD_STOP         = $05;
	MVCMD_HOME         = $06;
	MVCMD_LOFT         = $07;
	MVCMD_SSTP         = $08;
	MVCMD_ERROR        = $40;
	MVCMD_RUNNING      = $80;

	RPM_DIV_1000    = $01;

	ENGINE_REVERSE           = $01;
	ENGINE_CURRENT_AS_RMS    = $02;
	ENGINE_MAX_SPEED         = $04;
	ENGINE_ANTIPLAY          = $08;
	ENGINE_ACCEL_ON          = $10;
	ENGINE_LIMIT_VOLT        = $20;
	ENGINE_LIMIT_CURR        = $40;
	ENGINE_LIMIT_RPM         = $80;

	MICROSTEP_MODE_FULL        = $01;
	MICROSTEP_MODE_FRAC_2      = $02;
	MICROSTEP_MODE_FRAC_4      = $03;
	MICROSTEP_MODE_FRAC_8      = $04;
	MICROSTEP_MODE_FRAC_16     = $05;
	MICROSTEP_MODE_FRAC_32     = $06;
	MICROSTEP_MODE_FRAC_64     = $07;
	MICROSTEP_MODE_FRAC_128    = $08;
	MICROSTEP_MODE_FRAC_256    = $09;

	ENGINE_TYPE_NONE         = $00;
	ENGINE_TYPE_DC           = $01;
	ENGINE_TYPE_2DC          = $02;
	ENGINE_TYPE_STEP         = $03;
	ENGINE_TYPE_TEST         = $04;
	ENGINE_TYPE_BRUSHLESS    = $05;

	DRIVER_TYPE_DISCRETE_FET    = $01;
	DRIVER_TYPE_INTEGRATE       = $02;
	DRIVER_TYPE_EXTERNAL        = $03;

	POWER_REDUCT_ENABLED    = $01;
	POWER_OFF_ENABLED       = $02;
	POWER_SMOOTH_CURRENT    = $04;

	ALARM_ON_DRIVER_OVERHEATING     = $01;
	LOW_UPWR_PROTECTION             = $02;
	H_BRIDGE_ALERT                  = $04;
	ALARM_ON_BORDERS_SWAP_MISSET    = $08;
	ALARM_FLAGS_STICKING            = $10;
	USB_BREAK_RECONNECT             = $20;
	ALARM_WINDING_MISMATCH          = $40;
	ALARM_ENGINE_RESPONSE           = $80;

	SETPOS_IGNORE_POSITION    = $01;
	SETPOS_IGNORE_ENCODER     = $02;

	FEEDBACK_ENCODER             = $01;
	FEEDBACK_EMF                 = $04;
	FEEDBACK_NONE                = $05;
	FEEDBACK_ENCODER_MEDIATED    = $06;

	FEEDBACK_ENC_REVERSE              = $01;
	FEEDBACK_ENC_TYPE_BITS            = $C0;
	FEEDBACK_ENC_TYPE_AUTO            = $00;
	FEEDBACK_ENC_TYPE_SINGLE_ENDED    = $40;
	FEEDBACK_ENC_TYPE_DIFFERENTIAL    = $80;

	SYNCIN_ENABLED         = $01;
	SYNCIN_INVERT          = $02;
	SYNCIN_GOTOPOSITION    = $04;

	SYNCOUT_ENABLED     = $01;
	SYNCOUT_STATE       = $02;
	SYNCOUT_INVERT      = $04;
	SYNCOUT_IN_STEPS    = $08;
	SYNCOUT_ONSTART     = $10;
	SYNCOUT_ONSTOP      = $20;
	SYNCOUT_ONPERIOD    = $40;

	EXTIO_SETUP_OUTPUT    = $01;
	EXTIO_SETUP_INVERT    = $02;

	EXTIO_SETUP_MODE_IN_BITS         = $0F;
	EXTIO_SETUP_MODE_IN_NOP          = $00;
	EXTIO_SETUP_MODE_IN_STOP         = $01;
	EXTIO_SETUP_MODE_IN_PWOF         = $02;
	EXTIO_SETUP_MODE_IN_MOVR         = $03;
	EXTIO_SETUP_MODE_IN_HOME         = $04;
	EXTIO_SETUP_MODE_IN_ALARM        = $05;
	EXTIO_SETUP_MODE_OUT_BITS        = $F0;
	EXTIO_SETUP_MODE_OUT_OFF         = $00;
	EXTIO_SETUP_MODE_OUT_ON          = $10;
	EXTIO_SETUP_MODE_OUT_MOVING      = $20;
	EXTIO_SETUP_MODE_OUT_ALARM       = $30;
	EXTIO_SETUP_MODE_OUT_MOTOR_ON    = $40;

	BORDER_IS_ENCODER                = $01;
	BORDER_STOP_LEFT                 = $02;
	BORDER_STOP_RIGHT                = $04;
	BORDERS_SWAP_MISSET_DETECTION    = $08;

	ENDER_SWAP              = $01;
	ENDER_SW1_ACTIVE_LOW    = $02;
	ENDER_SW2_ACTIVE_LOW    = $04;

	BRAKE_ENABLED       = $01;
	BRAKE_ENG_PWROFF    = $02;

	CONTROL_MODE_BITS                = $03;
	CONTROL_MODE_OFF                 = $00;
	CONTROL_MODE_JOY                 = $01;
	CONTROL_MODE_LR                  = $02;
	CONTROL_BTN_LEFT_PUSHED_OPEN     = $04;
	CONTROL_BTN_RIGHT_PUSHED_OPEN    = $08;

	JOY_REVERSE    = $01;

	CTP_ENABLED             = $01;
	CTP_BASE                = $02;
	CTP_ALARM_ON_ERROR      = $04;
	REV_SENS_INV            = $08;
	CTP_ERROR_CORRECTION    = $10;

	HOME_DIR_FIRST           = $001;
	HOME_DIR_SECOND          = $002;
	HOME_MV_SEC_EN           = $004;
	HOME_HALF_MV             = $008;
	HOME_STOP_FIRST_BITS     = $030;
	HOME_STOP_FIRST_REV      = $010;
	HOME_STOP_FIRST_SYN      = $020;
	HOME_STOP_FIRST_LIM      = $030;
	HOME_STOP_SECOND_BITS    = $0C0;
	HOME_STOP_SECOND_REV     = $040;
	HOME_STOP_SECOND_SYN     = $080;
	HOME_STOP_SECOND_LIM     = $0C0;
	HOME_USE_FAST            = $100;

	UART_PARITY_BITS         = $03;
	UART_PARITY_BIT_EVEN     = $00;
	UART_PARITY_BIT_ODD      = $01;
	UART_PARITY_BIT_SPACE    = $02;
	UART_PARITY_BIT_MARK     = $03;
	UART_PARITY_BIT_USE      = $04;
	UART_STOP_BIT            = $08;

	MOTOR_TYPE_UNKNOWN    = $00;
	MOTOR_TYPE_STEP       = $01;
	MOTOR_TYPE_DC         = $02;
	MOTOR_TYPE_BLDC       = $03;

	ENCSET_DIFFERENTIAL_OUTPUT             = $001;
	ENCSET_PUSHPULL_OUTPUT                 = $004;
	ENCSET_INDEXCHANNEL_PRESENT            = $010;
	ENCSET_REVOLUTIONSENSOR_PRESENT        = $040;
	ENCSET_REVOLUTIONSENSOR_ACTIVE_HIGH    = $100;

	MB_AVAILABLE       = $01;
	MB_POWERED_HOLD    = $02;

	TS_TYPE_BITS             = $07;
	TS_TYPE_UNKNOWN          = $00;
	TS_TYPE_THERMOCOUPLE     = $01;
	TS_TYPE_SEMICONDUCTOR    = $02;
	TS_AVAILABLE             = $08;

	LS_ON_SW1_AVAILABLE    = $01;
	LS_ON_SW2_AVAILABLE    = $02;
	LS_SW1_ACTIVE_LOW      = $04;
	LS_SW2_ACTIVE_LOW      = $08;
	LS_SHORTED             = $10;

	BACK_EMF_INDUCTANCE_AUTO    = $01;
	BACK_EMF_RESISTANCE_AUTO    = $02;
	BACK_EMF_KM_AUTO            = $04;


type feedback_settings_t = record
		IPS: cardinal;
		FeedbackType: cardinal;
		FeedbackFlags: cardinal;
		CountsPerTurn: cardinal;
end;

type home_settings_t = record
		FastHome: cardinal;
		uFastHome: cardinal;
		SlowHome: cardinal;
		uSlowHome: cardinal;
		HomeDelta: integer;
		uHomeDelta: integer;
		HomeFlags: cardinal;
end;

type home_settings_calb_t = record
		FastHome: single;
		SlowHome: single;
		HomeDelta: single;
		HomeFlags: cardinal;
end;

type move_settings_t = record
		Speed: cardinal;
		uSpeed: cardinal;
		Accel: cardinal;
		Decel: cardinal;
		AntiplaySpeed: cardinal;
		uAntiplaySpeed: cardinal;
		MoveFlags: cardinal;
end;

type move_settings_calb_t = record
		Speed: single;
		Accel: single;
		Decel: single;
		AntiplaySpeed: single;
		MoveFlags: cardinal;
end;

type engine_settings_t = record
		NomVoltage: cardinal;
		NomCurrent: cardinal;
		NomSpeed: cardinal;
		uNomSpeed: cardinal;
		EngineFlags: cardinal;
		Antiplay: integer;
		MicrostepMode: cardinal;
		StepsPerRev: cardinal;
end;

type engine_settings_calb_t = record
		NomVoltage: cardinal;
		NomCurrent: cardinal;
		NomSpeed: single;
		EngineFlags: cardinal;
		Antiplay: single;
		MicrostepMode: cardinal;
		StepsPerRev: cardinal;
end;

type entype_settings_t = record
		EngineType: cardinal;
		DriverType: cardinal;
end;

type power_settings_t = record
		HoldCurrent: cardinal;
		CurrReductDelay: cardinal;
		PowerOffDelay: cardinal;
		CurrentSetTime: cardinal;
		PowerFlags: cardinal;
end;

type secure_settings_t = record
		LowUpwrOff: cardinal;
		CriticalIpwr: cardinal;
		CriticalUpwr: cardinal;
		CriticalT: cardinal;
		CriticalIusb: cardinal;
		CriticalUusb: cardinal;
		MinimumUusb: cardinal;
		Flags: cardinal;
end;

type edges_settings_t = record
		BorderFlags: cardinal;
		EnderFlags: cardinal;
		LeftBorder: integer;
		uLeftBorder: integer;
		RightBorder: integer;
		uRightBorder: integer;
end;

type edges_settings_calb_t = record
		BorderFlags: cardinal;
		EnderFlags: cardinal;
		LeftBorder: single;
		RightBorder: single;
end;

type pid_settings_t = record
		KpU: cardinal;
		KiU: cardinal;
		KdU: cardinal;
		Kpf: single;
		Kif: single;
		Kdf: single;
end;

type sync_in_settings_t = record
		SyncInFlags: cardinal;
		ClutterTime: cardinal;
		Distance: integer;
		uPosition: integer;
		Speed: cardinal;
		uSpeed: cardinal;
end;

type sync_in_settings_calb_t = record
		SyncInFlags: cardinal;
		ClutterTime: cardinal;
		Distance: single;
		Speed: single;
end;

type sync_out_settings_t = record
		SyncOutFlags: cardinal;
		SyncOutPulseSteps: cardinal;
		SyncOutPeriod: cardinal;
		Accuracy: cardinal;
		uAccuracy: cardinal;
end;

type sync_out_settings_calb_t = record
		SyncOutFlags: cardinal;
		SyncOutPulseSteps: cardinal;
		SyncOutPeriod: cardinal;
		Accuracy: single;
end;

type extio_settings_t = record
		EXTIOSetupFlags: cardinal;
		EXTIOModeFlags: cardinal;
end;

type brake_settings_t = record
		t1: cardinal;
		t2: cardinal;
		t3: cardinal;
		t4: cardinal;
		BrakeFlags: cardinal;
end;

type control_settings_t = record
		MaxSpeed: array [0..9] of cardinal;
		uMaxSpeed: array [0..9] of cardinal;
		Timeout: array [0..8] of cardinal;
		MaxClickTime: cardinal;
		Flags: cardinal;
		DeltaPosition: integer;
		uDeltaPosition: integer;
end;

type control_settings_calb_t = record
		MaxSpeed: array [0..9] of single;
		Timeout: array [0..8] of cardinal;
		MaxClickTime: cardinal;
		Flags: cardinal;
		DeltaPosition: single;
end;

type joystick_settings_t = record
		JoyLowEnd: cardinal;
		JoyCenter: cardinal;
		JoyHighEnd: cardinal;
		ExpFactor: cardinal;
		DeadZone: cardinal;
		JoyFlags: cardinal;
end;

type ctp_settings_t = record
		CTPMinError: cardinal;
		CTPFlags: cardinal;
end;

type uart_settings_t = record
		Speed: cardinal;
		UARTSetupFlags: cardinal;
end;

type calibration_settings_t = record
		CSS1_A: single;
		CSS1_B: single;
		CSS2_A: single;
		CSS2_B: single;
		FullCurrent_A: single;
		FullCurrent_B: single;
end;

type controller_name_t = record
		ControllerName: PAnsiChar;
		CtrlFlags: cardinal;
end;

type nonvolatile_memory_t = record
		UserData: array [0..6] of cardinal;
end;

type emf_settings_t = record
		L: single;
		R: single;
		Km: single;
		BackEMFFlags: cardinal;
end;

type engine_advansed_setup_t = record
		stepcloseloop_Kw: cardinal;
		stepcloseloop_Kp_low: cardinal;
		stepcloseloop_Kp_high: cardinal;
end;

type extended_settings_t = record
		Param1: cardinal;
end;

type get_position_t = record
		Distance: integer;
		uPosition: integer;
		EncPosition: Int64;
end;

type get_position_calb_t = record
		Distance: single;
		EncPosition: Int64;
end;

type set_position_t = record
		Distance: integer;
		uPosition: integer;
		EncPosition: Int64;
		PosFlags: cardinal;
end;

type set_position_calb_t = record
		Distance: single;
		EncPosition: Int64;
		PosFlags: cardinal;
end;

type status_t = record
		MoveSts: cardinal;
		MvCmdSts: cardinal;
		PWRSts: cardinal;
		EncSts: cardinal;
		WindSts: cardinal;
		CurPosition: integer;
		uCurPosition: integer;
		EncPosition: Int64;
		CurSpeed: integer;
		uCurSpeed: integer;
		Ipwr: integer;
		Upwr: integer;
		Iusb: integer;
		Uusb: integer;
		CurT: integer;
		Flags: cardinal;
		GPIOFlags: cardinal;
		CmdBufFreeSpace: cardinal;
end;

type status_calb_t = record
		MoveSts: cardinal;
		MvCmdSts: cardinal;
		PWRSts: cardinal;
		EncSts: cardinal;
		WindSts: cardinal;
		CurPosition: single;
		EncPosition: Int64;
		CurSpeed: single;
		Ipwr: integer;
		Upwr: integer;
		Iusb: integer;
		Uusb: integer;
		CurT: integer;
		Flags: cardinal;
		GPIOFlags: cardinal;
		CmdBufFreeSpace: cardinal;
end;

type measurements_t = record
		Speed: array [0..24] of integer;
		Error: array [0..24] of integer;
		Length: cardinal;
end;

type chart_data_t = record
		WindingVoltageA: integer;
		WindingVoltageB: integer;
		WindingVoltageC: integer;
		WindingCurrentA: integer;
		WindingCurrentB: integer;
		WindingCurrentC: integer;
		Pot: cardinal;
		Joy: cardinal;
		DutyCycle: integer;
end;

type device_information_t = record
		Manufacturer: PAnsiChar;
		ManufacturerId: PAnsiChar;
		ProductDescription: PAnsiChar;
		Major: cardinal;
		Minor: cardinal;
		Release: cardinal;
end;

type serial_number_t = record
		SN: cardinal;
		Key: array [0..31] of byte;
		Major: cardinal;
		Minor: cardinal;
		Release: cardinal;
end;

type analog_data_t = record
		A1Voltage_ADC: cardinal;
		A2Voltage_ADC: cardinal;
		B1Voltage_ADC: cardinal;
		B2Voltage_ADC: cardinal;
		SupVoltage_ADC: cardinal;
		ACurrent_ADC: cardinal;
		BCurrent_ADC: cardinal;
		FullCurrent_ADC: cardinal;
		Temp_ADC: cardinal;
		Joy_ADC: cardinal;
		Pot_ADC: cardinal;
		L5_ADC: cardinal;
		H5_ADC: cardinal;
		A1Voltage: integer;
		A2Voltage: integer;
		B1Voltage: integer;
		B2Voltage: integer;
		SupVoltage: integer;
		ACurrent: integer;
		BCurrent: integer;
		FullCurrent: integer;
		Temp: integer;
		Joy: integer;
		Pot: integer;
		L5: integer;
		H5: integer;
		deprecated: cardinal;
		R: integer;
		L: integer;
end;

type debug_read_t = record
		DebugData: array [0..127] of byte;
end;

type debug_write_t = record
		DebugData: array [0..127] of byte;
end;

type stage_name_t = record
		PositionerName: PAnsiChar;
end;

type stage_information_t = record
		Manufacturer: PAnsiChar;
		PartNumber: PAnsiChar;
end;

type stage_settings_t = record
		LeadScrewPitch: single;
		Units: PAnsiChar;
		MaxSpeed: single;
		TravelRange: single;
		SupplyVoltageMin: single;
		SupplyVoltageMax: single;
		MaxCurrentConsumption: single;
		HorizontalLoadCapacity: single;
		VerticalLoadCapacity: single;
end;

type motor_information_t = record
		Manufacturer: PAnsiChar;
		PartNumber: PAnsiChar;
end;

type motor_settings_t = record
		MotorType: cardinal;
		ReservedField: cardinal;
		Poles: cardinal;
		Phases: cardinal;
		NominalVoltage: single;
		NominalCurrent: single;
		NominalSpeed: single;
		NominalTorque: single;
		NominalPower: single;
		WindingResistance: single;
		WindingInductance: single;
		RotorInertia: single;
		StallTorque: single;
		DetentTorque: single;
		TorqueConstant: single;
		SpeedConstant: single;
		SpeedTorqueGradient: single;
		MechanicalTimeConstant: single;
		MaxSpeed: single;
		MaxCurrent: single;
		MaxCurrentTime: single;
		NoLoadCurrent: single;
		NoLoadSpeed: single;
end;

type encoder_information_t = record
		Manufacturer: PAnsiChar;
		PartNumber: PAnsiChar;
end;

type encoder_settings_t = record
		MaxOperatingFrequency: single;
		SupplyVoltageMin: single;
		SupplyVoltageMax: single;
		MaxCurrentConsumption: single;
		PPR: cardinal;
		EncoderSettings: cardinal;
end;

type hallsensor_information_t = record
		Manufacturer: PAnsiChar;
		PartNumber: PAnsiChar;
end;

type hallsensor_settings_t = record
		MaxOperatingFrequency: single;
		SupplyVoltageMin: single;
		SupplyVoltageMax: single;
		MaxCurrentConsumption: single;
		PPR: cardinal;
end;

type gear_information_t = record
		Manufacturer: PAnsiChar;
		PartNumber: PAnsiChar;
end;

type gear_settings_t = record
		ReductionIn: single;
		ReductionOut: single;
		RatedInputTorque: single;
		RatedInputSpeed: single;
		MaxOutputBacklash: single;
		InputInertia: single;
		Efficiency: single;
end;

type accessories_settings_t = record
		MagneticBrakeInfo: PAnsiChar;
		MBRatedVoltage: single;
		MBRatedCurrent: single;
		MBTorque: single;
		MBSettings: cardinal;
		TemperatureSensorInfo: PAnsiChar;
		TSMin: single;
		TSMax: single;
		TSGrad: single;
		TSSettings: cardinal;
		LimitSwitchesSettings: cardinal;
end;

type init_random_t = record
		key: array [0..15] of byte;
end;

type globally_unique_identifier_t = record
		UniqueID0: cardinal;
		UniqueID1: cardinal;
		UniqueID2: cardinal;
		UniqueID3: cardinal;
end;

{
 --------------------------------------------
   BEGIN OF GENERATED function declarations
 --------------------------------------------
}

function set_feedback_settings (id: Device; var feedback_settings: feedback_settings_t) : XimcResult; stdcall; external XimcDll;

function get_feedback_settings (id: Device; out feedback_settings: feedback_settings_t) : XimcResult; stdcall; external XimcDll;

function set_home_settings (id: Device; var home_settings: home_settings_t) : XimcResult; stdcall; external XimcDll;

function set_home_settings_calb (id: Device; var home_settings_calb: home_settings_calb_t; var calibration: calibration_t) : XimcResult; stdcall; external XimcDll;

function get_home_settings (id: Device; out home_settings: home_settings_t) : XimcResult; stdcall; external XimcDll;

function get_home_settings_calb (id: Device; out home_settings_calb: home_settings_calb_t; var calibration: calibration_t) : XimcResult; stdcall; external XimcDll;

function set_move_settings (id: Device; var move_settings: move_settings_t) : XimcResult; stdcall; external XimcDll;

function set_move_settings_calb (id: Device; var move_settings_calb: move_settings_calb_t; var calibration: calibration_t) : XimcResult; stdcall; external XimcDll;

function get_move_settings (id: Device; out move_settings: move_settings_t) : XimcResult; stdcall; external XimcDll;

function get_move_settings_calb (id: Device; out move_settings_calb: move_settings_calb_t; var calibration: calibration_t) : XimcResult; stdcall; external XimcDll;

function set_engine_settings (id: Device; var engine_settings: engine_settings_t) : XimcResult; stdcall; external XimcDll;

function set_engine_settings_calb (id: Device; var engine_settings_calb: engine_settings_calb_t; var calibration: calibration_t) : XimcResult; stdcall; external XimcDll;

function get_engine_settings (id: Device; out engine_settings: engine_settings_t) : XimcResult; stdcall; external XimcDll;

function get_engine_settings_calb (id: Device; out engine_settings_calb: engine_settings_calb_t; var calibration: calibration_t) : XimcResult; stdcall; external XimcDll;

function set_entype_settings (id: Device; var entype_settings: entype_settings_t) : XimcResult; stdcall; external XimcDll;

function get_entype_settings (id: Device; out entype_settings: entype_settings_t) : XimcResult; stdcall; external XimcDll;

function set_power_settings (id: Device; var power_settings: power_settings_t) : XimcResult; stdcall; external XimcDll;

function get_power_settings (id: Device; out power_settings: power_settings_t) : XimcResult; stdcall; external XimcDll;

function set_secure_settings (id: Device; var secure_settings: secure_settings_t) : XimcResult; stdcall; external XimcDll;

function get_secure_settings (id: Device; out secure_settings: secure_settings_t) : XimcResult; stdcall; external XimcDll;

function set_edges_settings (id: Device; var edges_settings: edges_settings_t) : XimcResult; stdcall; external XimcDll;

function set_edges_settings_calb (id: Device; var edges_settings_calb: edges_settings_calb_t; var calibration: calibration_t) : XimcResult; stdcall; external XimcDll;

function get_edges_settings (id: Device; out edges_settings: edges_settings_t) : XimcResult; stdcall; external XimcDll;

function get_edges_settings_calb (id: Device; out edges_settings_calb: edges_settings_calb_t; var calibration: calibration_t) : XimcResult; stdcall; external XimcDll;

function set_pid_settings (id: Device; var pid_settings: pid_settings_t) : XimcResult; stdcall; external XimcDll;

function get_pid_settings (id: Device; out pid_settings: pid_settings_t) : XimcResult; stdcall; external XimcDll;

function set_sync_in_settings (id: Device; var sync_in_settings: sync_in_settings_t) : XimcResult; stdcall; external XimcDll;

function set_sync_in_settings_calb (id: Device; var sync_in_settings_calb: sync_in_settings_calb_t; var calibration: calibration_t) : XimcResult; stdcall; external XimcDll;

function get_sync_in_settings (id: Device; out sync_in_settings: sync_in_settings_t) : XimcResult; stdcall; external XimcDll;

function get_sync_in_settings_calb (id: Device; out sync_in_settings_calb: sync_in_settings_calb_t; var calibration: calibration_t) : XimcResult; stdcall; external XimcDll;

function set_sync_out_settings (id: Device; var sync_out_settings: sync_out_settings_t) : XimcResult; stdcall; external XimcDll;

function set_sync_out_settings_calb (id: Device; var sync_out_settings_calb: sync_out_settings_calb_t; var calibration: calibration_t) : XimcResult; stdcall; external XimcDll;

function get_sync_out_settings (id: Device; out sync_out_settings: sync_out_settings_t) : XimcResult; stdcall; external XimcDll;

function get_sync_out_settings_calb (id: Device; out sync_out_settings_calb: sync_out_settings_calb_t; var calibration: calibration_t) : XimcResult; stdcall; external XimcDll;

function set_extio_settings (id: Device; var extio_settings: extio_settings_t) : XimcResult; stdcall; external XimcDll;

function get_extio_settings (id: Device; out extio_settings: extio_settings_t) : XimcResult; stdcall; external XimcDll;

function set_brake_settings (id: Device; var brake_settings: brake_settings_t) : XimcResult; stdcall; external XimcDll;

function get_brake_settings (id: Device; out brake_settings: brake_settings_t) : XimcResult; stdcall; external XimcDll;

function set_control_settings (id: Device; var control_settings: control_settings_t) : XimcResult; stdcall; external XimcDll;

function set_control_settings_calb (id: Device; var control_settings_calb: control_settings_calb_t; var calibration: calibration_t) : XimcResult; stdcall; external XimcDll;

function get_control_settings (id: Device; out control_settings: control_settings_t) : XimcResult; stdcall; external XimcDll;

function get_control_settings_calb (id: Device; out control_settings_calb: control_settings_calb_t; var calibration: calibration_t) : XimcResult; stdcall; external XimcDll;

function set_joystick_settings (id: Device; var joystick_settings: joystick_settings_t) : XimcResult; stdcall; external XimcDll;

function get_joystick_settings (id: Device; out joystick_settings: joystick_settings_t) : XimcResult; stdcall; external XimcDll;

function set_ctp_settings (id: Device; var ctp_settings: ctp_settings_t) : XimcResult; stdcall; external XimcDll;

function get_ctp_settings (id: Device; out ctp_settings: ctp_settings_t) : XimcResult; stdcall; external XimcDll;

function set_uart_settings (id: Device; var uart_settings: uart_settings_t) : XimcResult; stdcall; external XimcDll;

function get_uart_settings (id: Device; out uart_settings: uart_settings_t) : XimcResult; stdcall; external XimcDll;

function set_calibration_settings (id: Device; var calibration_settings: calibration_settings_t) : XimcResult; stdcall; external XimcDll;

function get_calibration_settings (id: Device; out calibration_settings: calibration_settings_t) : XimcResult; stdcall; external XimcDll;

function set_controller_name (id: Device; var controller_name: controller_name_t) : XimcResult; stdcall; external XimcDll;

function get_controller_name (id: Device; out controller_name: controller_name_t) : XimcResult; stdcall; external XimcDll;

function set_nonvolatile_memory (id: Device; var nonvolatile_memory: nonvolatile_memory_t) : XimcResult; stdcall; external XimcDll;

function get_nonvolatile_memory (id: Device; out nonvolatile_memory: nonvolatile_memory_t) : XimcResult; stdcall; external XimcDll;

function set_emf_settings (id: Device; var emf_settings: emf_settings_t) : XimcResult; stdcall; external XimcDll;

function get_emf_settings (id: Device; out emf_settings: emf_settings_t) : XimcResult; stdcall; external XimcDll;

function set_engine_advansed_setup (id: Device; var engine_advansed_setup: engine_advansed_setup_t) : XimcResult; stdcall; external XimcDll;

function get_engine_advansed_setup (id: Device; out engine_advansed_setup: engine_advansed_setup_t) : XimcResult; stdcall; external XimcDll;

function set_extended_settings (id: Device; var extended_settings: extended_settings_t) : XimcResult; stdcall; external XimcDll;

function get_extended_settings (id: Device; out extended_settings: extended_settings_t) : XimcResult; stdcall; external XimcDll;

function command_stop (id: Device) : XimcResult; stdcall; external XimcDll;

function command_power_off (id: Device) : XimcResult; stdcall; external XimcDll;

function command_move (id: Device; Distance: integer; uPosition: integer) : XimcResult; stdcall; external XimcDll;

function command_move_calb (id: Device; Distance: single; var calibration: calibration_t) : XimcResult; stdcall; external XimcDll;

function command_movr (id: Device; DeltaPosition: integer; uDeltaPosition: integer) : XimcResult; stdcall; external XimcDll;

function command_movr_calb (id: Device; DeltaPosition: single; var calibration: calibration_t) : XimcResult; stdcall; external XimcDll;

function command_home (id: Device) : XimcResult; stdcall; external XimcDll;

function command_left (id: Device) : XimcResult; stdcall; external XimcDll;

function command_right (id: Device) : XimcResult; stdcall; external XimcDll;

function command_loft (id: Device) : XimcResult; stdcall; external XimcDll;

function command_sstp (id: Device) : XimcResult; stdcall; external XimcDll;

function get_position (id: Device; out the_get_position: get_position_t) : XimcResult; stdcall; external XimcDll;

function get_position_calb (id: Device; out the_get_position_calb: get_position_calb_t; var calibration: calibration_t) : XimcResult; stdcall; external XimcDll;

function set_position (id: Device; var the_set_position: set_position_t) : XimcResult; stdcall; external XimcDll;

function set_position_calb (id: Device; var the_set_position_calb: set_position_calb_t; var calibration: calibration_t) : XimcResult; stdcall; external XimcDll;

function command_zero (id: Device) : XimcResult; stdcall; external XimcDll;

function command_save_settings (id: Device) : XimcResult; stdcall; external XimcDll;

function command_read_settings (id: Device) : XimcResult; stdcall; external XimcDll;

function command_save_robust_settings (id: Device) : XimcResult; stdcall; external XimcDll;

function command_read_robust_settings (id: Device) : XimcResult; stdcall; external XimcDll;

function command_eesave_settings (id: Device) : XimcResult; stdcall; external XimcDll;

function command_eeread_settings (id: Device) : XimcResult; stdcall; external XimcDll;

function command_start_measurements (id: Device) : XimcResult; stdcall; external XimcDll;

function get_measurements (id: Device; out measurements: measurements_t) : XimcResult; stdcall; external XimcDll;

function get_chart_data (id: Device; out chart_data: chart_data_t) : XimcResult; stdcall; external XimcDll;

function get_serial_number (id: Device; out SerialNumber: cardinal) : XimcResult; stdcall; external XimcDll;

function get_firmware_version (id: Device; out Major: cardinal; out Minor: cardinal; out Release: cardinal) : XimcResult; stdcall; external XimcDll;

function service_command_updf (id: Device) : XimcResult; stdcall; external XimcDll;

function set_serial_number (id: Device; var serial_number: serial_number_t) : XimcResult; stdcall; external XimcDll;

function get_analog_data (id: Device; out analog_data: analog_data_t) : XimcResult; stdcall; external XimcDll;

function get_debug_read (id: Device; out debug_read: debug_read_t) : XimcResult; stdcall; external XimcDll;

function set_debug_write (id: Device; var debug_write: debug_write_t) : XimcResult; stdcall; external XimcDll;

function set_stage_name (id: Device; var stage_name: stage_name_t) : XimcResult; stdcall; external XimcDll;

function get_stage_name (id: Device; out stage_name: stage_name_t) : XimcResult; stdcall; external XimcDll;

function set_stage_information (id: Device; var stage_information: stage_information_t) : XimcResult; stdcall; external XimcDll;

function get_stage_information (id: Device; out stage_information: stage_information_t) : XimcResult; stdcall; external XimcDll;

function set_stage_settings (id: Device; var stage_settings: stage_settings_t) : XimcResult; stdcall; external XimcDll;

function get_stage_settings (id: Device; out stage_settings: stage_settings_t) : XimcResult; stdcall; external XimcDll;

function set_motor_information (id: Device; var motor_information: motor_information_t) : XimcResult; stdcall; external XimcDll;

function get_motor_information (id: Device; out motor_information: motor_information_t) : XimcResult; stdcall; external XimcDll;

function set_motor_settings (id: Device; var motor_settings: motor_settings_t) : XimcResult; stdcall; external XimcDll;

function get_motor_settings (id: Device; out motor_settings: motor_settings_t) : XimcResult; stdcall; external XimcDll;

function set_encoder_information (id: Device; var encoder_information: encoder_information_t) : XimcResult; stdcall; external XimcDll;

function get_encoder_information (id: Device; out encoder_information: encoder_information_t) : XimcResult; stdcall; external XimcDll;

function set_encoder_settings (id: Device; var encoder_settings: encoder_settings_t) : XimcResult; stdcall; external XimcDll;

function get_encoder_settings (id: Device; out encoder_settings: encoder_settings_t) : XimcResult; stdcall; external XimcDll;

function set_hallsensor_information (id: Device; var hallsensor_information: hallsensor_information_t) : XimcResult; stdcall; external XimcDll;

function get_hallsensor_information (id: Device; out hallsensor_information: hallsensor_information_t) : XimcResult; stdcall; external XimcDll;

function set_hallsensor_settings (id: Device; var hallsensor_settings: hallsensor_settings_t) : XimcResult; stdcall; external XimcDll;

function get_hallsensor_settings (id: Device; out hallsensor_settings: hallsensor_settings_t) : XimcResult; stdcall; external XimcDll;

function set_gear_information (id: Device; var gear_information: gear_information_t) : XimcResult; stdcall; external XimcDll;

function get_gear_information (id: Device; out gear_information: gear_information_t) : XimcResult; stdcall; external XimcDll;

function set_gear_settings (id: Device; var gear_settings: gear_settings_t) : XimcResult; stdcall; external XimcDll;

function get_gear_settings (id: Device; out gear_settings: gear_settings_t) : XimcResult; stdcall; external XimcDll;

function set_accessories_settings (id: Device; var accessories_settings: accessories_settings_t) : XimcResult; stdcall; external XimcDll;

function get_accessories_settings (id: Device; out accessories_settings: accessories_settings_t) : XimcResult; stdcall; external XimcDll;

function get_bootloader_version (id: Device; out Major: cardinal; out Minor: cardinal; out Release: cardinal) : XimcResult; stdcall; external XimcDll;

function get_init_random (id: Device; out init_random: init_random_t) : XimcResult; stdcall; external XimcDll;

function get_globally_unique_identifier (id: Device; out globally_unique_identifier: globally_unique_identifier_t) : XimcResult; stdcall; external XimcDll;

{
 -------------------------
   END OF GENERATED CODE
 -------------------------
}

function open_device (name: PAnsiChar) : Device; stdcall; external XimcDll;
function close_device (var id: Device) : XimcResult; stdcall; external XimcDll;
function probe_device (name: PAnsiChar) : XimcResult; stdcall; external XimcDll;

function enumerate_devices(enumerate_flags: Integer; hints: PAnsiChar) : Pointer; 
				stdcall; external XimcDll;
function free_enumerate_devices(enumerate_devices: Pointer) : XimcResult; 
				stdcall; external XimcDll;
function get_device_count(device_enumeration: Pointer) : Integer;
				stdcall; external XimcDll;
function get_device_name(device_enumeration: Pointer; device_index: Integer) : PAnsiChar;
				stdcall; external XimcDll;
function get_enumerate_device_serial(device_enumeration: Pointer; device_index: Integer; 
				out serial: Cardinal) : XimcResult; stdcall; external XimcDll;
function get_enumerate_device_information(device_enumeration: Pointer; device_index: Integer; 
				out device_information: device_information_t) : XimcResult; stdcall; external XimcDll;

function reset_locks () : XimcResult; stdcall; external XimcDll;
function ximc_fix_usbser_sys (name: PAnsiChar) : XimcResult; stdcall; external XimcDll;
function get_device_information (id: Device; out device_information: device_information_t) : XimcResult; stdcall; external XimcDll;
function get_status (id: Device; out status: status_t) : XimcResult; stdcall; external XimcDll;
function get_status_calb (id: Device; out status: status_calb_t; var calibration: calibration_t) : XimcResult; stdcall; external XimcDll;

function goto_firmware(id: Device; out ret: Byte) : XimcResult; stdcall; external XimcDll;
function has_firmware(name: PAnsiChar; out ret: Byte) : XimcResult; stdcall; external XimcDll;
function write_key(name: PAnsiChar; key: Cardinal) : XimcResult; stdcall; external XimcDll;
function command_update_firmware(name: PAnsiChar; data: PByte; data_size: Cardinal) : XimcResult; stdcall; external XimcDll;
function command_reset(id: Device) : XimcResult; stdcall; external XimcDll;

procedure msec_sleep(msec: Cardinal); stdcall; external XimcDll;
procedure ximc_version(out version: PAnsiChar); stdcall; external XimcDll;

function command_wait_for_stop(id: Device; wait_interval_ms: Integer) : XimcResult; stdcall; external XimcDll;
procedure set_bindy_key(keyfilepath: PAnsiChar); stdcall; external XimcDll;

implementation

end.
