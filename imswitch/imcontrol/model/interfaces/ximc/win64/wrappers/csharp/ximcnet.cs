using System;
using System.Runtime.InteropServices;
using System.Text;

namespace ximc
{
	public enum Result { ok = 0, error = -1, not_implemented = -2, value_error = -3, no_device = -4 };

	[StructLayout(LayoutKind.Sequential)]
	public struct calibration_t
	{
		public double A;
		public uint MicrostepMode;
	};
	

	public static class Version
	{
		public const String version = "2.13.5";
	};

/*
 ------------------------------------------
   BEGIN OF GENERATED struct declarations
 ------------------------------------------
*/
	public static class Flags
	{

		public const uint ENUMERATE_PROBE      = 0x01;
		public const uint ENUMERATE_ALL_COM    = 0x02;
		public const uint ENUMERATE_NETWORK    = 0x04;

		public const uint MOVE_STATE_MOVING          = 0x01;
		public const uint MOVE_STATE_TARGET_SPEED    = 0x02;
		public const uint MOVE_STATE_ANTIPLAY        = 0x04;

		public const uint EEPROM_PRECEDENCE    = 0x01;

		public const uint PWR_STATE_UNKNOWN    = 0x00;
		public const uint PWR_STATE_OFF        = 0x01;
		public const uint PWR_STATE_NORM       = 0x03;
		public const uint PWR_STATE_REDUCT     = 0x04;
		public const uint PWR_STATE_MAX        = 0x05;

		public const uint STATE_CONTR                     = 0x000003F;
		public const uint STATE_ERRC                      = 0x0000001;
		public const uint STATE_ERRD                      = 0x0000002;
		public const uint STATE_ERRV                      = 0x0000004;
		public const uint STATE_EEPROM_CONNECTED          = 0x0000010;
		public const uint STATE_IS_HOMED                  = 0x0000020;
		public const uint STATE_SECUR                     = 0x1B3FFC0;
		public const uint STATE_ALARM                     = 0x0000040;
		public const uint STATE_CTP_ERROR                 = 0x0000080;
		public const uint STATE_POWER_OVERHEAT            = 0x0000100;
		public const uint STATE_CONTROLLER_OVERHEAT       = 0x0000200;
		public const uint STATE_OVERLOAD_POWER_VOLTAGE    = 0x0000400;
		public const uint STATE_OVERLOAD_POWER_CURRENT    = 0x0000800;
		public const uint STATE_OVERLOAD_USB_VOLTAGE      = 0x0001000;
		public const uint STATE_LOW_USB_VOLTAGE           = 0x0002000;
		public const uint STATE_OVERLOAD_USB_CURRENT      = 0x0004000;
		public const uint STATE_BORDERS_SWAP_MISSET       = 0x0008000;
		public const uint STATE_LOW_POWER_VOLTAGE         = 0x0010000;
		public const uint STATE_H_BRIDGE_FAULT            = 0x0020000;
		public const uint STATE_WINDING_RES_MISMATCH      = 0x0100000;
		public const uint STATE_ENCODER_FAULT             = 0x0200000;
		public const uint STATE_ENGINE_RESPONSE_ERROR     = 0x0800000;
		public const uint STATE_EXTIO_ALARM               = 0x1000000;

		public const uint STATE_DIG_SIGNAL      = 0xFFFF;
		public const uint STATE_RIGHT_EDGE      = 0x0001;
		public const uint STATE_LEFT_EDGE       = 0x0002;
		public const uint STATE_BUTTON_RIGHT    = 0x0004;
		public const uint STATE_BUTTON_LEFT     = 0x0008;
		public const uint STATE_GPIO_PINOUT     = 0x0010;
		public const uint STATE_GPIO_LEVEL      = 0x0020;
		public const uint STATE_BRAKE           = 0x0200;
		public const uint STATE_REV_SENSOR      = 0x0400;
		public const uint STATE_SYNC_INPUT      = 0x0800;
		public const uint STATE_SYNC_OUTPUT     = 0x1000;
		public const uint STATE_ENC_A           = 0x2000;
		public const uint STATE_ENC_B           = 0x4000;

		public const uint ENC_STATE_ABSENT     = 0x00;
		public const uint ENC_STATE_UNKNOWN    = 0x01;
		public const uint ENC_STATE_MALFUNC    = 0x02;
		public const uint ENC_STATE_REVERS     = 0x03;
		public const uint ENC_STATE_OK         = 0x04;

		public const uint WIND_A_STATE_ABSENT     = 0x00;
		public const uint WIND_A_STATE_UNKNOWN    = 0x01;
		public const uint WIND_A_STATE_MALFUNC    = 0x02;
		public const uint WIND_A_STATE_OK         = 0x03;
		public const uint WIND_B_STATE_ABSENT     = 0x00;
		public const uint WIND_B_STATE_UNKNOWN    = 0x10;
		public const uint WIND_B_STATE_MALFUNC    = 0x20;
		public const uint WIND_B_STATE_OK         = 0x30;

		public const uint MVCMD_NAME_BITS    = 0x3F;
		public const uint MVCMD_UKNWN        = 0x00;
		public const uint MVCMD_MOVE         = 0x01;
		public const uint MVCMD_MOVR         = 0x02;
		public const uint MVCMD_LEFT         = 0x03;
		public const uint MVCMD_RIGHT        = 0x04;
		public const uint MVCMD_STOP         = 0x05;
		public const uint MVCMD_HOME         = 0x06;
		public const uint MVCMD_LOFT         = 0x07;
		public const uint MVCMD_SSTP         = 0x08;
		public const uint MVCMD_ERROR        = 0x40;
		public const uint MVCMD_RUNNING      = 0x80;

		public const uint RPM_DIV_1000    = 0x01;

		public const uint ENGINE_REVERSE           = 0x01;
		public const uint ENGINE_CURRENT_AS_RMS    = 0x02;
		public const uint ENGINE_MAX_SPEED         = 0x04;
		public const uint ENGINE_ANTIPLAY          = 0x08;
		public const uint ENGINE_ACCEL_ON          = 0x10;
		public const uint ENGINE_LIMIT_VOLT        = 0x20;
		public const uint ENGINE_LIMIT_CURR        = 0x40;
		public const uint ENGINE_LIMIT_RPM         = 0x80;

		public const uint MICROSTEP_MODE_FULL        = 0x01;
		public const uint MICROSTEP_MODE_FRAC_2      = 0x02;
		public const uint MICROSTEP_MODE_FRAC_4      = 0x03;
		public const uint MICROSTEP_MODE_FRAC_8      = 0x04;
		public const uint MICROSTEP_MODE_FRAC_16     = 0x05;
		public const uint MICROSTEP_MODE_FRAC_32     = 0x06;
		public const uint MICROSTEP_MODE_FRAC_64     = 0x07;
		public const uint MICROSTEP_MODE_FRAC_128    = 0x08;
		public const uint MICROSTEP_MODE_FRAC_256    = 0x09;

		public const uint ENGINE_TYPE_NONE         = 0x00;
		public const uint ENGINE_TYPE_DC           = 0x01;
		public const uint ENGINE_TYPE_2DC          = 0x02;
		public const uint ENGINE_TYPE_STEP         = 0x03;
		public const uint ENGINE_TYPE_TEST         = 0x04;
		public const uint ENGINE_TYPE_BRUSHLESS    = 0x05;

		public const uint DRIVER_TYPE_DISCRETE_FET    = 0x01;
		public const uint DRIVER_TYPE_INTEGRATE       = 0x02;
		public const uint DRIVER_TYPE_EXTERNAL        = 0x03;

		public const uint POWER_REDUCT_ENABLED    = 0x01;
		public const uint POWER_OFF_ENABLED       = 0x02;
		public const uint POWER_SMOOTH_CURRENT    = 0x04;

		public const uint ALARM_ON_DRIVER_OVERHEATING     = 0x01;
		public const uint LOW_UPWR_PROTECTION             = 0x02;
		public const uint H_BRIDGE_ALERT                  = 0x04;
		public const uint ALARM_ON_BORDERS_SWAP_MISSET    = 0x08;
		public const uint ALARM_FLAGS_STICKING            = 0x10;
		public const uint USB_BREAK_RECONNECT             = 0x20;
		public const uint ALARM_WINDING_MISMATCH          = 0x40;
		public const uint ALARM_ENGINE_RESPONSE           = 0x80;

		public const uint SETPOS_IGNORE_POSITION    = 0x01;
		public const uint SETPOS_IGNORE_ENCODER     = 0x02;

		public const uint FEEDBACK_ENCODER             = 0x01;
		public const uint FEEDBACK_EMF                 = 0x04;
		public const uint FEEDBACK_NONE                = 0x05;
		public const uint FEEDBACK_ENCODER_MEDIATED    = 0x06;

		public const uint FEEDBACK_ENC_REVERSE              = 0x01;
		public const uint FEEDBACK_ENC_TYPE_BITS            = 0xC0;
		public const uint FEEDBACK_ENC_TYPE_AUTO            = 0x00;
		public const uint FEEDBACK_ENC_TYPE_SINGLE_ENDED    = 0x40;
		public const uint FEEDBACK_ENC_TYPE_DIFFERENTIAL    = 0x80;

		public const uint SYNCIN_ENABLED         = 0x01;
		public const uint SYNCIN_INVERT          = 0x02;
		public const uint SYNCIN_GOTOPOSITION    = 0x04;

		public const uint SYNCOUT_ENABLED     = 0x01;
		public const uint SYNCOUT_STATE       = 0x02;
		public const uint SYNCOUT_INVERT      = 0x04;
		public const uint SYNCOUT_IN_STEPS    = 0x08;
		public const uint SYNCOUT_ONSTART     = 0x10;
		public const uint SYNCOUT_ONSTOP      = 0x20;
		public const uint SYNCOUT_ONPERIOD    = 0x40;

		public const uint EXTIO_SETUP_OUTPUT    = 0x01;
		public const uint EXTIO_SETUP_INVERT    = 0x02;

		public const uint EXTIO_SETUP_MODE_IN_BITS         = 0x0F;
		public const uint EXTIO_SETUP_MODE_IN_NOP          = 0x00;
		public const uint EXTIO_SETUP_MODE_IN_STOP         = 0x01;
		public const uint EXTIO_SETUP_MODE_IN_PWOF         = 0x02;
		public const uint EXTIO_SETUP_MODE_IN_MOVR         = 0x03;
		public const uint EXTIO_SETUP_MODE_IN_HOME         = 0x04;
		public const uint EXTIO_SETUP_MODE_IN_ALARM        = 0x05;
		public const uint EXTIO_SETUP_MODE_OUT_BITS        = 0xF0;
		public const uint EXTIO_SETUP_MODE_OUT_OFF         = 0x00;
		public const uint EXTIO_SETUP_MODE_OUT_ON          = 0x10;
		public const uint EXTIO_SETUP_MODE_OUT_MOVING      = 0x20;
		public const uint EXTIO_SETUP_MODE_OUT_ALARM       = 0x30;
		public const uint EXTIO_SETUP_MODE_OUT_MOTOR_ON    = 0x40;

		public const uint BORDER_IS_ENCODER                = 0x01;
		public const uint BORDER_STOP_LEFT                 = 0x02;
		public const uint BORDER_STOP_RIGHT                = 0x04;
		public const uint BORDERS_SWAP_MISSET_DETECTION    = 0x08;

		public const uint ENDER_SWAP              = 0x01;
		public const uint ENDER_SW1_ACTIVE_LOW    = 0x02;
		public const uint ENDER_SW2_ACTIVE_LOW    = 0x04;

		public const uint BRAKE_ENABLED       = 0x01;
		public const uint BRAKE_ENG_PWROFF    = 0x02;

		public const uint CONTROL_MODE_BITS                = 0x03;
		public const uint CONTROL_MODE_OFF                 = 0x00;
		public const uint CONTROL_MODE_JOY                 = 0x01;
		public const uint CONTROL_MODE_LR                  = 0x02;
		public const uint CONTROL_BTN_LEFT_PUSHED_OPEN     = 0x04;
		public const uint CONTROL_BTN_RIGHT_PUSHED_OPEN    = 0x08;

		public const uint JOY_REVERSE    = 0x01;

		public const uint CTP_ENABLED             = 0x01;
		public const uint CTP_BASE                = 0x02;
		public const uint CTP_ALARM_ON_ERROR      = 0x04;
		public const uint REV_SENS_INV            = 0x08;
		public const uint CTP_ERROR_CORRECTION    = 0x10;

		public const uint HOME_DIR_FIRST           = 0x001;
		public const uint HOME_DIR_SECOND          = 0x002;
		public const uint HOME_MV_SEC_EN           = 0x004;
		public const uint HOME_HALF_MV             = 0x008;
		public const uint HOME_STOP_FIRST_BITS     = 0x030;
		public const uint HOME_STOP_FIRST_REV      = 0x010;
		public const uint HOME_STOP_FIRST_SYN      = 0x020;
		public const uint HOME_STOP_FIRST_LIM      = 0x030;
		public const uint HOME_STOP_SECOND_BITS    = 0x0C0;
		public const uint HOME_STOP_SECOND_REV     = 0x040;
		public const uint HOME_STOP_SECOND_SYN     = 0x080;
		public const uint HOME_STOP_SECOND_LIM     = 0x0C0;
		public const uint HOME_USE_FAST            = 0x100;

		public const uint UART_PARITY_BITS         = 0x03;
		public const uint UART_PARITY_BIT_EVEN     = 0x00;
		public const uint UART_PARITY_BIT_ODD      = 0x01;
		public const uint UART_PARITY_BIT_SPACE    = 0x02;
		public const uint UART_PARITY_BIT_MARK     = 0x03;
		public const uint UART_PARITY_BIT_USE      = 0x04;
		public const uint UART_STOP_BIT            = 0x08;

		public const uint MOTOR_TYPE_UNKNOWN    = 0x00;
		public const uint MOTOR_TYPE_STEP       = 0x01;
		public const uint MOTOR_TYPE_DC         = 0x02;
		public const uint MOTOR_TYPE_BLDC       = 0x03;

		public const uint ENCSET_DIFFERENTIAL_OUTPUT             = 0x001;
		public const uint ENCSET_PUSHPULL_OUTPUT                 = 0x004;
		public const uint ENCSET_INDEXCHANNEL_PRESENT            = 0x010;
		public const uint ENCSET_REVOLUTIONSENSOR_PRESENT        = 0x040;
		public const uint ENCSET_REVOLUTIONSENSOR_ACTIVE_HIGH    = 0x100;

		public const uint MB_AVAILABLE       = 0x01;
		public const uint MB_POWERED_HOLD    = 0x02;

		public const uint TS_TYPE_BITS             = 0x07;
		public const uint TS_TYPE_UNKNOWN          = 0x00;
		public const uint TS_TYPE_THERMOCOUPLE     = 0x01;
		public const uint TS_TYPE_SEMICONDUCTOR    = 0x02;
		public const uint TS_AVAILABLE             = 0x08;

		public const uint LS_ON_SW1_AVAILABLE    = 0x01;
		public const uint LS_ON_SW2_AVAILABLE    = 0x02;
		public const uint LS_SW1_ACTIVE_LOW      = 0x04;
		public const uint LS_SW2_ACTIVE_LOW      = 0x08;
		public const uint LS_SHORTED             = 0x10;

		public const uint BACK_EMF_INDUCTANCE_AUTO    = 0x01;
		public const uint BACK_EMF_RESISTANCE_AUTO    = 0x02;
		public const uint BACK_EMF_KM_AUTO            = 0x04;

	}; // flags


	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct feedback_settings_t
	{
		public uint IPS;
		public uint FeedbackType;
		public uint FeedbackFlags;
		public uint CountsPerTurn;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct home_settings_t
	{
		public uint FastHome;
		public uint uFastHome;
		public uint SlowHome;
		public uint uSlowHome;
		public int HomeDelta;
		public int uHomeDelta;
		public uint HomeFlags;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct home_settings_calb_t
	{
		public float FastHome;
		public float SlowHome;
		public float HomeDelta;
		public uint HomeFlags;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct move_settings_t
	{
		public uint Speed;
		public uint uSpeed;
		public uint Accel;
		public uint Decel;
		public uint AntiplaySpeed;
		public uint uAntiplaySpeed;
		public uint MoveFlags;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct move_settings_calb_t
	{
		public float Speed;
		public float Accel;
		public float Decel;
		public float AntiplaySpeed;
		public uint MoveFlags;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct engine_settings_t
	{
		public uint NomVoltage;
		public uint NomCurrent;
		public uint NomSpeed;
		public uint uNomSpeed;
		public uint EngineFlags;
		public int Antiplay;
		public uint MicrostepMode;
		public uint StepsPerRev;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct engine_settings_calb_t
	{
		public uint NomVoltage;
		public uint NomCurrent;
		public float NomSpeed;
		public uint EngineFlags;
		public float Antiplay;
		public uint MicrostepMode;
		public uint StepsPerRev;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct entype_settings_t
	{
		public uint EngineType;
		public uint DriverType;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct power_settings_t
	{
		public uint HoldCurrent;
		public uint CurrReductDelay;
		public uint PowerOffDelay;
		public uint CurrentSetTime;
		public uint PowerFlags;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct secure_settings_t
	{
		public uint LowUpwrOff;
		public uint CriticalIpwr;
		public uint CriticalUpwr;
		public uint CriticalT;
		public uint CriticalIusb;
		public uint CriticalUusb;
		public uint MinimumUusb;
		public uint Flags;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct edges_settings_t
	{
		public uint BorderFlags;
		public uint EnderFlags;
		public int LeftBorder;
		public int uLeftBorder;
		public int RightBorder;
		public int uRightBorder;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct edges_settings_calb_t
	{
		public uint BorderFlags;
		public uint EnderFlags;
		public float LeftBorder;
		public float RightBorder;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct pid_settings_t
	{
		public uint KpU;
		public uint KiU;
		public uint KdU;
		public float Kpf;
		public float Kif;
		public float Kdf;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct sync_in_settings_t
	{
		public uint SyncInFlags;
		public uint ClutterTime;
		public int Position;
		public int uPosition;
		public uint Speed;
		public uint uSpeed;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct sync_in_settings_calb_t
	{
		public uint SyncInFlags;
		public uint ClutterTime;
		public float Position;
		public float Speed;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct sync_out_settings_t
	{
		public uint SyncOutFlags;
		public uint SyncOutPulseSteps;
		public uint SyncOutPeriod;
		public uint Accuracy;
		public uint uAccuracy;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct sync_out_settings_calb_t
	{
		public uint SyncOutFlags;
		public uint SyncOutPulseSteps;
		public uint SyncOutPeriod;
		public float Accuracy;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct extio_settings_t
	{
		public uint EXTIOSetupFlags;
		public uint EXTIOModeFlags;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct brake_settings_t
	{
		public uint t1;
		public uint t2;
		public uint t3;
		public uint t4;
		public uint BrakeFlags;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct control_settings_t
	{
		[MarshalAs(UnmanagedType.ByValArray, SizeConst = 10)]
		public uint[] MaxSpeed;
		[MarshalAs(UnmanagedType.ByValArray, SizeConst = 10)]
		public uint[] uMaxSpeed;
		[MarshalAs(UnmanagedType.ByValArray, SizeConst = 9)]
		public uint[] Timeout;
		public uint MaxClickTime;
		public uint Flags;
		public int DeltaPosition;
		public int uDeltaPosition;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct control_settings_calb_t
	{
		[MarshalAs(UnmanagedType.ByValArray, SizeConst = 10)]
		public float[] MaxSpeed;
		[MarshalAs(UnmanagedType.ByValArray, SizeConst = 9)]
		public uint[] Timeout;
		public uint MaxClickTime;
		public uint Flags;
		public float DeltaPosition;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct joystick_settings_t
	{
		public uint JoyLowEnd;
		public uint JoyCenter;
		public uint JoyHighEnd;
		public uint ExpFactor;
		public uint DeadZone;
		public uint JoyFlags;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct ctp_settings_t
	{
		public uint CTPMinError;
		public uint CTPFlags;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct uart_settings_t
	{
		public uint Speed;
		public uint UARTSetupFlags;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct calibration_settings_t
	{
		public float CSS1_A;
		public float CSS1_B;
		public float CSS2_A;
		public float CSS2_B;
		public float FullCurrent_A;
		public float FullCurrent_B;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct controller_name_t
	{
		[MarshalAs(UnmanagedType.ByValTStr, SizeConst = 17)]
		public string ControllerName;
		public uint CtrlFlags;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct nonvolatile_memory_t
	{
		[MarshalAs(UnmanagedType.ByValArray, SizeConst = 7)]
		public uint[] UserData;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct emf_settings_t
	{
		public float L;
		public float R;
		public float Km;
		public uint BackEMFFlags;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct engine_advansed_setup_t
	{
		public uint stepcloseloop_Kw;
		public uint stepcloseloop_Kp_low;
		public uint stepcloseloop_Kp_high;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct extended_settings_t
	{
		public uint Param1;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct get_position_t
	{
		public int Position;
		public int uPosition;
		public long EncPosition;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct get_position_calb_t
	{
		public float Position;
		public long EncPosition;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct set_position_t
	{
		public int Position;
		public int uPosition;
		public long EncPosition;
		public uint PosFlags;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct set_position_calb_t
	{
		public float Position;
		public long EncPosition;
		public uint PosFlags;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct status_t
	{
		public uint MoveSts;
		public uint MvCmdSts;
		public uint PWRSts;
		public uint EncSts;
		public uint WindSts;
		public int CurPosition;
		public int uCurPosition;
		public long EncPosition;
		public int CurSpeed;
		public int uCurSpeed;
		public int Ipwr;
		public int Upwr;
		public int Iusb;
		public int Uusb;
		public int CurT;
		public uint Flags;
		public uint GPIOFlags;
		public uint CmdBufFreeSpace;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct status_calb_t
	{
		public uint MoveSts;
		public uint MvCmdSts;
		public uint PWRSts;
		public uint EncSts;
		public uint WindSts;
		public float CurPosition;
		public long EncPosition;
		public float CurSpeed;
		public int Ipwr;
		public int Upwr;
		public int Iusb;
		public int Uusb;
		public int CurT;
		public uint Flags;
		public uint GPIOFlags;
		public uint CmdBufFreeSpace;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct measurements_t
	{
		[MarshalAs(UnmanagedType.ByValArray, SizeConst = 25)]
		public int[] Speed;
		[MarshalAs(UnmanagedType.ByValArray, SizeConst = 25)]
		public int[] Error;
		public uint Length;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct chart_data_t
	{
		public int WindingVoltageA;
		public int WindingVoltageB;
		public int WindingVoltageC;
		public int WindingCurrentA;
		public int WindingCurrentB;
		public int WindingCurrentC;
		public uint Pot;
		public uint Joy;
		public int DutyCycle;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct device_information_t
	{
		[MarshalAs(UnmanagedType.ByValTStr, SizeConst = 5)]
		public string Manufacturer;
		[MarshalAs(UnmanagedType.ByValTStr, SizeConst = 3)]
		public string ManufacturerId;
		[MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
		public string ProductDescription;
		public uint Major;
		public uint Minor;
		public uint Release;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct serial_number_t
	{
		public uint SN;
		[MarshalAs(UnmanagedType.ByValArray, SizeConst = 32)]
		public byte[] Key;
		public uint Major;
		public uint Minor;
		public uint Release;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct analog_data_t
	{
		public uint A1Voltage_ADC;
		public uint A2Voltage_ADC;
		public uint B1Voltage_ADC;
		public uint B2Voltage_ADC;
		public uint SupVoltage_ADC;
		public uint ACurrent_ADC;
		public uint BCurrent_ADC;
		public uint FullCurrent_ADC;
		public uint Temp_ADC;
		public uint Joy_ADC;
		public uint Pot_ADC;
		public uint L5_ADC;
		public uint H5_ADC;
		public int A1Voltage;
		public int A2Voltage;
		public int B1Voltage;
		public int B2Voltage;
		public int SupVoltage;
		public int ACurrent;
		public int BCurrent;
		public int FullCurrent;
		public int Temp;
		public int Joy;
		public int Pot;
		public int L5;
		public int H5;
		public uint deprecated;
		public int R;
		public int L;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct debug_read_t
	{
		[MarshalAs(UnmanagedType.ByValArray, SizeConst = 128)]
		public byte[] DebugData;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct debug_write_t
	{
		[MarshalAs(UnmanagedType.ByValArray, SizeConst = 128)]
		public byte[] DebugData;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct stage_name_t
	{
		[MarshalAs(UnmanagedType.ByValTStr, SizeConst = 17)]
		public string PositionerName;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct stage_information_t
	{
		[MarshalAs(UnmanagedType.ByValTStr, SizeConst = 17)]
		public string Manufacturer;
		[MarshalAs(UnmanagedType.ByValTStr, SizeConst = 25)]
		public string PartNumber;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct stage_settings_t
	{
		public float LeadScrewPitch;
		[MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
		public string Units;
		public float MaxSpeed;
		public float TravelRange;
		public float SupplyVoltageMin;
		public float SupplyVoltageMax;
		public float MaxCurrentConsumption;
		public float HorizontalLoadCapacity;
		public float VerticalLoadCapacity;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct motor_information_t
	{
		[MarshalAs(UnmanagedType.ByValTStr, SizeConst = 17)]
		public string Manufacturer;
		[MarshalAs(UnmanagedType.ByValTStr, SizeConst = 25)]
		public string PartNumber;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct motor_settings_t
	{
		public uint MotorType;
		public uint ReservedField;
		public uint Poles;
		public uint Phases;
		public float NominalVoltage;
		public float NominalCurrent;
		public float NominalSpeed;
		public float NominalTorque;
		public float NominalPower;
		public float WindingResistance;
		public float WindingInductance;
		public float RotorInertia;
		public float StallTorque;
		public float DetentTorque;
		public float TorqueConstant;
		public float SpeedConstant;
		public float SpeedTorqueGradient;
		public float MechanicalTimeConstant;
		public float MaxSpeed;
		public float MaxCurrent;
		public float MaxCurrentTime;
		public float NoLoadCurrent;
		public float NoLoadSpeed;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct encoder_information_t
	{
		[MarshalAs(UnmanagedType.ByValTStr, SizeConst = 17)]
		public string Manufacturer;
		[MarshalAs(UnmanagedType.ByValTStr, SizeConst = 25)]
		public string PartNumber;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct encoder_settings_t
	{
		public float MaxOperatingFrequency;
		public float SupplyVoltageMin;
		public float SupplyVoltageMax;
		public float MaxCurrentConsumption;
		public uint PPR;
		public uint EncoderSettings;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct hallsensor_information_t
	{
		[MarshalAs(UnmanagedType.ByValTStr, SizeConst = 17)]
		public string Manufacturer;
		[MarshalAs(UnmanagedType.ByValTStr, SizeConst = 25)]
		public string PartNumber;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct hallsensor_settings_t
	{
		public float MaxOperatingFrequency;
		public float SupplyVoltageMin;
		public float SupplyVoltageMax;
		public float MaxCurrentConsumption;
		public uint PPR;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct gear_information_t
	{
		[MarshalAs(UnmanagedType.ByValTStr, SizeConst = 17)]
		public string Manufacturer;
		[MarshalAs(UnmanagedType.ByValTStr, SizeConst = 25)]
		public string PartNumber;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct gear_settings_t
	{
		public float ReductionIn;
		public float ReductionOut;
		public float RatedInputTorque;
		public float RatedInputSpeed;
		public float MaxOutputBacklash;
		public float InputInertia;
		public float Efficiency;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct accessories_settings_t
	{
		[MarshalAs(UnmanagedType.ByValTStr, SizeConst = 25)]
		public string MagneticBrakeInfo;
		public float MBRatedVoltage;
		public float MBRatedCurrent;
		public float MBTorque;
		public uint MBSettings;
		[MarshalAs(UnmanagedType.ByValTStr, SizeConst = 25)]
		public string TemperatureSensorInfo;
		public float TSMin;
		public float TSMax;
		public float TSGrad;
		public uint TSSettings;
		public uint LimitSwitchesSettings;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct init_random_t
	{
		[MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
		public byte[] key;
	};

	[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
	public struct globally_unique_identifier_t
	{
		public uint UniqueID0;
		public uint UniqueID1;
		public uint UniqueID2;
		public uint UniqueID3;
	};

/*
 --------------------------------------------
   BEGIN OF GENERATED function declarations
 --------------------------------------------
*/

	public partial class API
	{
		[DllImport("libximc.dll")]
		public static extern Result set_feedback_settings (int id, ref feedback_settings_t feedback_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_feedback_settings (int id, out feedback_settings_t feedback_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_home_settings (int id, ref home_settings_t home_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_home_settings_calb (int id, ref home_settings_calb_t home_settings_calb, ref calibration_t calibration);

		[DllImport("libximc.dll")]
		public static extern Result get_home_settings (int id, out home_settings_t home_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_home_settings_calb (int id, out home_settings_calb_t home_settings_calb, ref calibration_t calibration);

		[DllImport("libximc.dll")]
		public static extern Result set_move_settings (int id, ref move_settings_t move_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_move_settings_calb (int id, ref move_settings_calb_t move_settings_calb, ref calibration_t calibration);

		[DllImport("libximc.dll")]
		public static extern Result get_move_settings (int id, out move_settings_t move_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_move_settings_calb (int id, out move_settings_calb_t move_settings_calb, ref calibration_t calibration);

		[DllImport("libximc.dll")]
		public static extern Result set_engine_settings (int id, ref engine_settings_t engine_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_engine_settings_calb (int id, ref engine_settings_calb_t engine_settings_calb, ref calibration_t calibration);

		[DllImport("libximc.dll")]
		public static extern Result get_engine_settings (int id, out engine_settings_t engine_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_engine_settings_calb (int id, out engine_settings_calb_t engine_settings_calb, ref calibration_t calibration);

		[DllImport("libximc.dll")]
		public static extern Result set_entype_settings (int id, ref entype_settings_t entype_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_entype_settings (int id, out entype_settings_t entype_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_power_settings (int id, ref power_settings_t power_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_power_settings (int id, out power_settings_t power_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_secure_settings (int id, ref secure_settings_t secure_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_secure_settings (int id, out secure_settings_t secure_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_edges_settings (int id, ref edges_settings_t edges_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_edges_settings_calb (int id, ref edges_settings_calb_t edges_settings_calb, ref calibration_t calibration);

		[DllImport("libximc.dll")]
		public static extern Result get_edges_settings (int id, out edges_settings_t edges_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_edges_settings_calb (int id, out edges_settings_calb_t edges_settings_calb, ref calibration_t calibration);

		[DllImport("libximc.dll")]
		public static extern Result set_pid_settings (int id, ref pid_settings_t pid_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_pid_settings (int id, out pid_settings_t pid_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_sync_in_settings (int id, ref sync_in_settings_t sync_in_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_sync_in_settings_calb (int id, ref sync_in_settings_calb_t sync_in_settings_calb, ref calibration_t calibration);

		[DllImport("libximc.dll")]
		public static extern Result get_sync_in_settings (int id, out sync_in_settings_t sync_in_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_sync_in_settings_calb (int id, out sync_in_settings_calb_t sync_in_settings_calb, ref calibration_t calibration);

		[DllImport("libximc.dll")]
		public static extern Result set_sync_out_settings (int id, ref sync_out_settings_t sync_out_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_sync_out_settings_calb (int id, ref sync_out_settings_calb_t sync_out_settings_calb, ref calibration_t calibration);

		[DllImport("libximc.dll")]
		public static extern Result get_sync_out_settings (int id, out sync_out_settings_t sync_out_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_sync_out_settings_calb (int id, out sync_out_settings_calb_t sync_out_settings_calb, ref calibration_t calibration);

		[DllImport("libximc.dll")]
		public static extern Result set_extio_settings (int id, ref extio_settings_t extio_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_extio_settings (int id, out extio_settings_t extio_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_brake_settings (int id, ref brake_settings_t brake_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_brake_settings (int id, out brake_settings_t brake_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_control_settings (int id, ref control_settings_t control_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_control_settings_calb (int id, ref control_settings_calb_t control_settings_calb, ref calibration_t calibration);

		[DllImport("libximc.dll")]
		public static extern Result get_control_settings (int id, out control_settings_t control_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_control_settings_calb (int id, out control_settings_calb_t control_settings_calb, ref calibration_t calibration);

		[DllImport("libximc.dll")]
		public static extern Result set_joystick_settings (int id, ref joystick_settings_t joystick_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_joystick_settings (int id, out joystick_settings_t joystick_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_ctp_settings (int id, ref ctp_settings_t ctp_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_ctp_settings (int id, out ctp_settings_t ctp_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_uart_settings (int id, ref uart_settings_t uart_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_uart_settings (int id, out uart_settings_t uart_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_calibration_settings (int id, ref calibration_settings_t calibration_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_calibration_settings (int id, out calibration_settings_t calibration_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_controller_name (int id, ref controller_name_t controller_name);

		[DllImport("libximc.dll")]
		public static extern Result get_controller_name (int id, out controller_name_t controller_name);

		[DllImport("libximc.dll")]
		public static extern Result set_nonvolatile_memory (int id, ref nonvolatile_memory_t nonvolatile_memory);

		[DllImport("libximc.dll")]
		public static extern Result get_nonvolatile_memory (int id, out nonvolatile_memory_t nonvolatile_memory);

		[DllImport("libximc.dll")]
		public static extern Result set_emf_settings (int id, ref emf_settings_t emf_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_emf_settings (int id, out emf_settings_t emf_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_engine_advansed_setup (int id, ref engine_advansed_setup_t engine_advansed_setup);

		[DllImport("libximc.dll")]
		public static extern Result get_engine_advansed_setup (int id, out engine_advansed_setup_t engine_advansed_setup);

		[DllImport("libximc.dll")]
		public static extern Result set_extended_settings (int id, ref extended_settings_t extended_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_extended_settings (int id, out extended_settings_t extended_settings);

		[DllImport("libximc.dll")]
		public static extern Result command_stop (int id);

		[DllImport("libximc.dll")]
		public static extern Result command_power_off (int id);

		[DllImport("libximc.dll")]
		public static extern Result command_move (int id, int Position, int uPosition);

		[DllImport("libximc.dll")]
		public static extern Result command_move_calb (int id, float Position, ref calibration_t calibration);

		[DllImport("libximc.dll")]
		public static extern Result command_movr (int id, int DeltaPosition, int uDeltaPosition);

		[DllImport("libximc.dll")]
		public static extern Result command_movr_calb (int id, float DeltaPosition, ref calibration_t calibration);

		[DllImport("libximc.dll")]
		public static extern Result command_home (int id);

		[DllImport("libximc.dll")]
		public static extern Result command_left (int id);

		[DllImport("libximc.dll")]
		public static extern Result command_right (int id);

		[DllImport("libximc.dll")]
		public static extern Result command_loft (int id);

		[DllImport("libximc.dll")]
		public static extern Result command_sstp (int id);

		[DllImport("libximc.dll")]
		public static extern Result get_position (int id, out get_position_t the_get_position);

		[DllImport("libximc.dll")]
		public static extern Result get_position_calb (int id, out get_position_calb_t the_get_position_calb, ref calibration_t calibration);

		[DllImport("libximc.dll")]
		public static extern Result set_position (int id, ref set_position_t the_set_position);

		[DllImport("libximc.dll")]
		public static extern Result set_position_calb (int id, ref set_position_calb_t the_set_position_calb, ref calibration_t calibration);

		[DllImport("libximc.dll")]
		public static extern Result command_zero (int id);

		[DllImport("libximc.dll")]
		public static extern Result command_save_settings (int id);

		[DllImport("libximc.dll")]
		public static extern Result command_read_settings (int id);

		[DllImport("libximc.dll")]
		public static extern Result command_save_robust_settings (int id);

		[DllImport("libximc.dll")]
		public static extern Result command_read_robust_settings (int id);

		[DllImport("libximc.dll")]
		public static extern Result command_eesave_settings (int id);

		[DllImport("libximc.dll")]
		public static extern Result command_eeread_settings (int id);

		[DllImport("libximc.dll")]
		public static extern Result command_start_measurements (int id);

		[DllImport("libximc.dll")]
		public static extern Result get_measurements (int id, out measurements_t measurements);

		[DllImport("libximc.dll")]
		public static extern Result get_chart_data (int id, out chart_data_t chart_data);

		[DllImport("libximc.dll")]
		public static extern Result get_serial_number (int id, out uint SerialNumber);

		[DllImport("libximc.dll")]
		public static extern Result get_firmware_version (int id, out uint Major, out uint Minor, out uint Release);

		[DllImport("libximc.dll")]
		public static extern Result service_command_updf (int id);

		[DllImport("libximc.dll")]
		public static extern Result set_serial_number (int id, ref serial_number_t serial_number);

		[DllImport("libximc.dll")]
		public static extern Result get_analog_data (int id, out analog_data_t analog_data);

		[DllImport("libximc.dll")]
		public static extern Result get_debug_read (int id, out debug_read_t debug_read);

		[DllImport("libximc.dll")]
		public static extern Result set_debug_write (int id, ref debug_write_t debug_write);

		[DllImport("libximc.dll")]
		public static extern Result set_stage_name (int id, ref stage_name_t stage_name);

		[DllImport("libximc.dll")]
		public static extern Result get_stage_name (int id, out stage_name_t stage_name);

		[DllImport("libximc.dll")]
		public static extern Result set_stage_information (int id, ref stage_information_t stage_information);

		[DllImport("libximc.dll")]
		public static extern Result get_stage_information (int id, out stage_information_t stage_information);

		[DllImport("libximc.dll")]
		public static extern Result set_stage_settings (int id, ref stage_settings_t stage_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_stage_settings (int id, out stage_settings_t stage_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_motor_information (int id, ref motor_information_t motor_information);

		[DllImport("libximc.dll")]
		public static extern Result get_motor_information (int id, out motor_information_t motor_information);

		[DllImport("libximc.dll")]
		public static extern Result set_motor_settings (int id, ref motor_settings_t motor_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_motor_settings (int id, out motor_settings_t motor_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_encoder_information (int id, ref encoder_information_t encoder_information);

		[DllImport("libximc.dll")]
		public static extern Result get_encoder_information (int id, out encoder_information_t encoder_information);

		[DllImport("libximc.dll")]
		public static extern Result set_encoder_settings (int id, ref encoder_settings_t encoder_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_encoder_settings (int id, out encoder_settings_t encoder_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_hallsensor_information (int id, ref hallsensor_information_t hallsensor_information);

		[DllImport("libximc.dll")]
		public static extern Result get_hallsensor_information (int id, out hallsensor_information_t hallsensor_information);

		[DllImport("libximc.dll")]
		public static extern Result set_hallsensor_settings (int id, ref hallsensor_settings_t hallsensor_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_hallsensor_settings (int id, out hallsensor_settings_t hallsensor_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_gear_information (int id, ref gear_information_t gear_information);

		[DllImport("libximc.dll")]
		public static extern Result get_gear_information (int id, out gear_information_t gear_information);

		[DllImport("libximc.dll")]
		public static extern Result set_gear_settings (int id, ref gear_settings_t gear_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_gear_settings (int id, out gear_settings_t gear_settings);

		[DllImport("libximc.dll")]
		public static extern Result set_accessories_settings (int id, ref accessories_settings_t accessories_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_accessories_settings (int id, out accessories_settings_t accessories_settings);

		[DllImport("libximc.dll")]
		public static extern Result get_bootloader_version (int id, out uint Major, out uint Minor, out uint Release);

		[DllImport("libximc.dll")]
		public static extern Result get_init_random (int id, out init_random_t init_random);

		[DllImport("libximc.dll")]
		public static extern Result get_globally_unique_identifier (int id, out globally_unique_identifier_t globally_unique_identifier);
	};

/*
 -------------------------
   END OF GENERATED CODE
 -------------------------
*/


	public partial class API
	{   
		private class Impl
		{
			[DllImport("libximc.dll")]
			public static extern IntPtr get_device_name(IntPtr device_enumeration, int device_index);
		};

		[DllImport("libximc.dll", CharSet = CharSet.Ansi)]
		public static extern int open_device ([MarshalAs(UnmanagedType.LPStr)] String name);
		[DllImport("libximc.dll")]
		public static extern Result close_device (ref int id);
		[DllImport("libximc.dll", CharSet = CharSet.Ansi)]
		public static extern Result probe_device ([MarshalAs(UnmanagedType.LPStr)] String name);
		
		[DllImport("libximc.dll")]
		public static extern Result reset_locks ();
		[DllImport("libximc.dll", CharSet = CharSet.Ansi)]
		public static extern Result ximc_fix_usbser_sys ([MarshalAs(UnmanagedType.LPStr)] String name);
		[DllImport("libximc.dll")]
		public static extern Result get_device_information (int id, out device_information_t device_information);
		[DllImport("libximc.dll")]
		public static extern Result get_status (int id, out status_t status);
		[DllImport("libximc.dll")]
		public static extern Result get_status_calb (int id, out status_calb_t status, ref calibration_t calibration);
		[DllImport("libximc.dll")]
		public static extern Result goto_firmware(int id, out byte ret);
		[DllImport("libximc.dll", CharSet = CharSet.Ansi)]
		public static extern Result has_firmware([MarshalAs(UnmanagedType.LPStr)] String name, out byte ret);
		[DllImport("libximc.dll", CharSet = CharSet.Ansi)]
		public static extern Result write_key([MarshalAs(UnmanagedType.LPStr)] String name, byte[] key);
		[DllImport("libximc.dll")]
		public static extern Result command_reset(int id);
		[DllImport("libximc.dll", CharSet = CharSet.Ansi)]
		public static extern Result command_update_firmware([MarshalAs(UnmanagedType.LPStr)] String name, byte[] data, uint data_size);
		[DllImport("libximc.dll")]
		public static extern void msec_sleep(int id);
		[DllImport("libximc.dll", CharSet = CharSet.Ansi)]
		public static extern void ximc_version(StringBuilder version);
		
		[DllImport("libximc.dll", CharSet = CharSet.Ansi)]
		public static extern IntPtr enumerate_devices(int enumerate_flags, [MarshalAs(UnmanagedType.LPStr)] String hints);
		[DllImport("libximc.dll")]
		public static extern Result enumerate_devices(IntPtr device_enumeration);
		[DllImport("libximc.dll")]
		public static extern Result free_enumerate_devices(IntPtr device_enumeration);
		[DllImport("libximc.dll")]
		public static extern int get_device_count(IntPtr device_enumeration);

		public static String get_device_name(IntPtr device_enumeration, int device_index)
		{
			return System.Runtime.InteropServices.Marshal.PtrToStringAnsi(
					Impl.get_device_name(device_enumeration, device_index));
		}


		[DllImport("libximc.dll")]
		public static extern Result get_enumerate_device_information(IntPtr device_enumeration, int device_index, 
				out device_information_t device_information);
		[DllImport("libximc.dll")]
		public static extern Result get_enumerate_device_serial(IntPtr device_enumeration, int device_index,
				out UInt32 serial);

		public enum LogLevel { error = 0x01, warning = 0x02, info = 0x03, debug = 0x04 };

		[UnmanagedFunctionPointer(CallingConvention.StdCall)]
		public delegate void LoggingCallback ([MarshalAs(UnmanagedType.I4)] LogLevel loglevel,
				[MarshalAs(UnmanagedType.LPWStr)] string message, IntPtr user_data);
		
		[DllImport("libximc.dll")]
		public static extern void set_logging_callback([MarshalAs(UnmanagedType.FunctionPtr)] LoggingCallback logging_callback, IntPtr user_data);
	
		[DllImport("libximc.dll")]
		public static extern Result command_wait_for_stop(int id, int wait_interval_ms);

		[DllImport("libximc.dll")]
		public static extern Result set_bindy_key([MarshalAs(UnmanagedType.LPStr)] String keyfilepath);
	};

};

