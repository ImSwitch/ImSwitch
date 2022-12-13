def set_profile_8MR191E_1_28(lib, id):
    worst_result = Result.Ok
    result = Result.Ok

    feedback_settings = feedback_settings_t()

    feedback_settings.IPS = 4000
    class FeedbackType_:
        FEEDBACK_ENCODER_MEDIATED = 6
        FEEDBACK_NONE = 5
        FEEDBACK_EMF = 4
        FEEDBACK_ENCODER = 1
    feedback_settings.FeedbackType = FeedbackType_.FEEDBACK_EMF
    class FeedbackFlags_:
        FEEDBACK_ENC_TYPE_BITS = 192
        FEEDBACK_ENC_TYPE_DIFFERENTIAL = 128
        FEEDBACK_ENC_TYPE_SINGLE_ENDED = 64
        FEEDBACK_ENC_REVERSE = 1
        FEEDBACK_ENC_TYPE_AUTO = 0
    feedback_settings.FeedbackFlags = FeedbackFlags_.FEEDBACK_ENC_TYPE_SINGLE_ENDED | FeedbackFlags_.FEEDBACK_ENC_TYPE_AUTO
    feedback_settings.CountsPerTurn = 4000
    result = lib.set_feedback_settings(id, byref(feedback_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    home_settings = home_settings_t()

    home_settings.FastHome = 100
    home_settings.uFastHome = 0
    home_settings.SlowHome = 10
    home_settings.uSlowHome = 0
    home_settings.HomeDelta = -1000
    home_settings.uHomeDelta = 0
    class HomeFlags_:
        HOME_USE_FAST = 256
        HOME_STOP_SECOND_BITS = 192
        HOME_STOP_SECOND_LIM = 192
        HOME_STOP_SECOND_SYN = 128
        HOME_STOP_SECOND_REV = 64
        HOME_STOP_FIRST_BITS = 48
        HOME_STOP_FIRST_LIM = 48
        HOME_STOP_FIRST_SYN = 32
        HOME_STOP_FIRST_REV = 16
        HOME_HALF_MV = 8
        HOME_MV_SEC_EN = 4
        HOME_DIR_SECOND = 2
        HOME_DIR_FIRST = 1
    home_settings.HomeFlags = HomeFlags_.HOME_USE_FAST | HomeFlags_.HOME_STOP_SECOND_REV | HomeFlags_.HOME_STOP_FIRST_BITS | HomeFlags_.HOME_DIR_FIRST
    result = lib.set_home_settings(id, byref(home_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    move_settings = move_settings_t()

    move_settings.Speed = 2000
    move_settings.uSpeed = 0
    move_settings.Accel = 2000
    move_settings.Decel = 5000
    move_settings.AntiplaySpeed = 2000
    move_settings.uAntiplaySpeed = 0
    class MoveFlags_:
        RPM_DIV_1000 = 1

    result = lib.set_move_settings(id, byref(move_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    engine_settings = engine_settings_t()

    engine_settings.NomVoltage = 360
    engine_settings.NomCurrent = 670
    engine_settings.NomSpeed = 4800
    engine_settings.uNomSpeed = 0
    class EngineFlags_:
        ENGINE_LIMIT_RPM = 128
        ENGINE_LIMIT_CURR = 64
        ENGINE_LIMIT_VOLT = 32
        ENGINE_ACCEL_ON = 16
        ENGINE_ANTIPLAY = 8
        ENGINE_MAX_SPEED = 4
        ENGINE_CURRENT_AS_RMS = 2
        ENGINE_REVERSE = 1
    engine_settings.EngineFlags = EngineFlags_.ENGINE_LIMIT_RPM | EngineFlags_.ENGINE_ACCEL_ON
    engine_settings.Antiplay = 1800
    class MicrostepMode_:
        MICROSTEP_MODE_FRAC_256 = 9
        MICROSTEP_MODE_FRAC_128 = 8
        MICROSTEP_MODE_FRAC_64 = 7
        MICROSTEP_MODE_FRAC_32 = 6
        MICROSTEP_MODE_FRAC_16 = 5
        MICROSTEP_MODE_FRAC_8 = 4
        MICROSTEP_MODE_FRAC_4 = 3
        MICROSTEP_MODE_FRAC_2 = 2
        MICROSTEP_MODE_FULL = 1
    engine_settings.MicrostepMode = MicrostepMode_.MICROSTEP_MODE_FRAC_256
    engine_settings.StepsPerRev = 200
    result = lib.set_engine_settings(id, byref(engine_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    entype_settings = entype_settings_t()

    class EngineType_:
        ENGINE_TYPE_BRUSHLESS = 5
        ENGINE_TYPE_TEST = 4
        ENGINE_TYPE_STEP = 3
        ENGINE_TYPE_2DC = 2
        ENGINE_TYPE_DC = 1
        ENGINE_TYPE_NONE = 0
    entype_settings.EngineType = EngineType_.ENGINE_TYPE_STEP | EngineType_.ENGINE_TYPE_NONE
    class DriverType_:
        DRIVER_TYPE_EXTERNAL = 3
        DRIVER_TYPE_INTEGRATE = 2
        DRIVER_TYPE_DISCRETE_FET = 1
    entype_settings.DriverType = DriverType_.DRIVER_TYPE_INTEGRATE
    result = lib.set_entype_settings(id, byref(entype_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    power_settings = power_settings_t()

    power_settings.HoldCurrent = 50
    power_settings.CurrReductDelay = 1000
    power_settings.PowerOffDelay = 60
    power_settings.CurrentSetTime = 300
    class PowerFlags_:
        POWER_SMOOTH_CURRENT = 4
        POWER_OFF_ENABLED = 2
        POWER_REDUCT_ENABLED = 1
    power_settings.PowerFlags = PowerFlags_.POWER_SMOOTH_CURRENT | PowerFlags_.POWER_REDUCT_ENABLED
    result = lib.set_power_settings(id, byref(power_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    secure_settings = secure_settings_t()

    secure_settings.LowUpwrOff = 800
    secure_settings.CriticalIpwr = 4000
    secure_settings.CriticalUpwr = 5500
    secure_settings.CriticalT = 800
    secure_settings.CriticalIusb = 450
    secure_settings.CriticalUusb = 520
    secure_settings.MinimumUusb = 420
    class Flags_:
        ALARM_ENGINE_RESPONSE = 128
        ALARM_WINDING_MISMATCH = 64
        USB_BREAK_RECONNECT = 32
        ALARM_FLAGS_STICKING = 16
        ALARM_ON_BORDERS_SWAP_MISSET = 8
        H_BRIDGE_ALERT = 4
        LOW_UPWR_PROTECTION = 2
        ALARM_ON_DRIVER_OVERHEATING = 1
    secure_settings.Flags = Flags_.ALARM_ENGINE_RESPONSE | Flags_.ALARM_FLAGS_STICKING | Flags_.ALARM_ON_BORDERS_SWAP_MISSET | Flags_.H_BRIDGE_ALERT | Flags_.ALARM_ON_DRIVER_OVERHEATING
    result = lib.set_secure_settings(id, byref(secure_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    edges_settings = edges_settings_t()

    class BorderFlags_:
        BORDERS_SWAP_MISSET_DETECTION = 8
        BORDER_STOP_RIGHT = 4
        BORDER_STOP_LEFT = 2
        BORDER_IS_ENCODER = 1

    class EnderFlags_:
        ENDER_SW2_ACTIVE_LOW = 4
        ENDER_SW1_ACTIVE_LOW = 2
        ENDER_SWAP = 1
    edges_settings.EnderFlags = EnderFlags_.ENDER_SW2_ACTIVE_LOW | EnderFlags_.ENDER_SW1_ACTIVE_LOW | EnderFlags_.ENDER_SWAP
    edges_settings.LeftBorder = -34100
    edges_settings.uLeftBorder = 0
    edges_settings.RightBorder = 100
    edges_settings.uRightBorder = 0
    result = lib.set_edges_settings(id, byref(edges_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    pid_settings = pid_settings_t()

    pid_settings.KpU = 0
    pid_settings.KiU = 0
    pid_settings.KdU = 0
    pid_settings.Kpf = 0.006000000052154064
    pid_settings.Kif = 0.05000000074505806
    pid_settings.Kdf = 2.8000000384054147e-05
    result = lib.set_pid_settings(id, byref(pid_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    sync_in_settings = sync_in_settings_t()

    class SyncInFlags_:
        SYNCIN_GOTOPOSITION = 4
        SYNCIN_INVERT = 2
        SYNCIN_ENABLED = 1

    sync_in_settings.ClutterTime = 4
    sync_in_settings.Distance = 0
    sync_in_settings.uPosition = 0
    sync_in_settings.Speed = 0
    sync_in_settings.uSpeed = 0
    result = lib.set_sync_in_settings(id, byref(sync_in_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    sync_out_settings = sync_out_settings_t()

    class SyncOutFlags_:
        SYNCOUT_ONPERIOD = 64
        SYNCOUT_ONSTOP = 32
        SYNCOUT_ONSTART = 16
        SYNCOUT_IN_STEPS = 8
        SYNCOUT_INVERT = 4
        SYNCOUT_STATE = 2
        SYNCOUT_ENABLED = 1
    sync_out_settings.SyncOutFlags = SyncOutFlags_.SYNCOUT_ONSTOP | SyncOutFlags_.SYNCOUT_ONSTART
    sync_out_settings.SyncOutPulseSteps = 100
    sync_out_settings.SyncOutPeriod = 2000
    sync_out_settings.Accuracy = 0
    sync_out_settings.uAccuracy = 0
    result = lib.set_sync_out_settings(id, byref(sync_out_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    extio_settings = extio_settings_t()

    class EXTIOSetupFlags_:
        EXTIO_SETUP_INVERT = 2
        EXTIO_SETUP_OUTPUT = 1
    extio_settings.EXTIOSetupFlags = EXTIOSetupFlags_.EXTIO_SETUP_OUTPUT
    class EXTIOModeFlags_:
        EXTIO_SETUP_MODE_OUT_BITS = 240
        EXTIO_SETUP_MODE_OUT_MOTOR_ON = 64
        EXTIO_SETUP_MODE_OUT_ALARM = 48
        EXTIO_SETUP_MODE_OUT_MOVING = 32
        EXTIO_SETUP_MODE_OUT_ON = 16
        EXTIO_SETUP_MODE_IN_BITS = 15
        EXTIO_SETUP_MODE_IN_ALARM = 5
        EXTIO_SETUP_MODE_IN_HOME = 4
        EXTIO_SETUP_MODE_IN_MOVR = 3
        EXTIO_SETUP_MODE_IN_PWOF = 2
        EXTIO_SETUP_MODE_IN_STOP = 1
        EXTIO_SETUP_MODE_IN_NOP = 0
        EXTIO_SETUP_MODE_OUT_OFF = 0
    extio_settings.EXTIOModeFlags = EXTIOModeFlags_.EXTIO_SETUP_MODE_IN_STOP | EXTIOModeFlags_.EXTIO_SETUP_MODE_IN_NOP | EXTIOModeFlags_.EXTIO_SETUP_MODE_OUT_OFF
    result = lib.set_extio_settings(id, byref(extio_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    brake_settings = brake_settings_t()

    brake_settings.t1 = 300
    brake_settings.t2 = 500
    brake_settings.t3 = 300
    brake_settings.t4 = 400
    class BrakeFlags_:
        BRAKE_ENG_PWROFF = 2
        BRAKE_ENABLED = 1
    brake_settings.BrakeFlags = BrakeFlags_.BRAKE_ENG_PWROFF
    result = lib.set_brake_settings(id, byref(brake_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    control_settings = control_settings_t()

    control_settings.MaxSpeed[0] = 20
    control_settings.MaxSpeed[1] = 200
    control_settings.MaxSpeed[2] = 2000
    control_settings.MaxSpeed[3] = 0
    control_settings.MaxSpeed[4] = 0
    control_settings.MaxSpeed[5] = 0
    control_settings.MaxSpeed[6] = 0
    control_settings.MaxSpeed[7] = 0
    control_settings.MaxSpeed[8] = 0
    control_settings.MaxSpeed[9] = 0
    control_settings.uMaxSpeed[0] = 0
    control_settings.uMaxSpeed[1] = 0
    control_settings.uMaxSpeed[2] = 0
    control_settings.uMaxSpeed[3] = 0
    control_settings.uMaxSpeed[4] = 0
    control_settings.uMaxSpeed[5] = 0
    control_settings.uMaxSpeed[6] = 0
    control_settings.uMaxSpeed[7] = 0
    control_settings.uMaxSpeed[8] = 0
    control_settings.uMaxSpeed[9] = 0
    control_settings.Timeout[0] = 1000
    control_settings.Timeout[1] = 1000
    control_settings.Timeout[2] = 1000
    control_settings.Timeout[3] = 1000
    control_settings.Timeout[4] = 1000
    control_settings.Timeout[5] = 1000
    control_settings.Timeout[6] = 1000
    control_settings.Timeout[7] = 1000
    control_settings.Timeout[8] = 1000
    control_settings.MaxClickTime = 300
    class Flags_:
        CONTROL_BTN_RIGHT_PUSHED_OPEN = 8
        CONTROL_BTN_LEFT_PUSHED_OPEN = 4
        CONTROL_MODE_BITS = 3
        CONTROL_MODE_LR = 2
        CONTROL_MODE_JOY = 1
        CONTROL_MODE_OFF = 0
    control_settings.Flags = Flags_.CONTROL_MODE_LR | Flags_.CONTROL_MODE_OFF
    control_settings.DeltaPosition = 1
    control_settings.uDeltaPosition = 0
    result = lib.set_control_settings(id, byref(control_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    joystick_settings = joystick_settings_t()

    joystick_settings.JoyLowEnd = 0
    joystick_settings.JoyCenter = 5000
    joystick_settings.JoyHighEnd = 10000
    joystick_settings.ExpFactor = 100
    joystick_settings.DeadZone = 50
    class JoyFlags_:
        JOY_REVERSE = 1

    result = lib.set_joystick_settings(id, byref(joystick_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    ctp_settings = ctp_settings_t()

    ctp_settings.CTPMinError = 3
    class CTPFlags_:
        CTP_ERROR_CORRECTION = 16
        REV_SENS_INV = 8
        CTP_ALARM_ON_ERROR = 4
        CTP_BASE = 2
        CTP_ENABLED = 1
    ctp_settings.CTPFlags = CTPFlags_.CTP_ERROR_CORRECTION
    result = lib.set_ctp_settings(id, byref(ctp_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    uart_settings = uart_settings_t()

    uart_settings.Speed = 115200
    class UARTSetupFlags_:
        UART_STOP_BIT = 8
        UART_PARITY_BIT_USE = 4
        UART_PARITY_BITS = 3
        UART_PARITY_BIT_MARK = 3
        UART_PARITY_BIT_SPACE = 2
        UART_PARITY_BIT_ODD = 1
        UART_PARITY_BIT_EVEN = 0
    uart_settings.UARTSetupFlags = UARTSetupFlags_.UART_PARITY_BIT_EVEN
    result = lib.set_uart_settings(id, byref(uart_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    controller_name = controller_name_t()

    controller_name.ControllerName = bytes([0, 113, 15, 119, 34, 0, 82, 0, 3, 0, 0, 0, 120, 108, 70, 0])
    class CtrlFlags_:
        EEPROM_PRECEDENCE = 1

    result = lib.set_controller_name(id, byref(controller_name))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    emf_settings = emf_settings_t()

    emf_settings.L = 0.005400000140070915
    emf_settings.R = 7.400000095367432
    emf_settings.Km = 0.0024999999441206455
    class BackEMFFlags_:
        BACK_EMF_KM_AUTO = 4
        BACK_EMF_RESISTANCE_AUTO = 2
        BACK_EMF_INDUCTANCE_AUTO = 1
    emf_settings.BackEMFFlags = BackEMFFlags_.BACK_EMF_KM_AUTO | BackEMFFlags_.BACK_EMF_RESISTANCE_AUTO | BackEMFFlags_.BACK_EMF_INDUCTANCE_AUTO
    result = lib.set_emf_settings(id, byref(emf_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    engine_advansed_setup = engine_advansed_setup_t()

    engine_advansed_setup.stepcloseloop_Kw = 50
    engine_advansed_setup.stepcloseloop_Kp_low = 1000
    engine_advansed_setup.stepcloseloop_Kp_high = 33
    result = lib.set_engine_advansed_setup(id, byref(engine_advansed_setup))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    extended_settings = extended_settings_t()

    extended_settings.Param1 = 0
    result = lib.set_extended_settings(id, byref(extended_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    stage_name = stage_name_t()

    stage_name.PositionerName = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    result = lib.set_stage_name(id, byref(stage_name))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    stage_information = stage_information_t()

    stage_information.Manufacturer = bytes([0, 116, 97, 110, 100, 97, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    stage_information.PartNumber = bytes([56, 77, 82, 49, 57, 49, 69, 45, 49, 45, 50, 56, 0, 52, 51, 0, 52, 0, 49, 0, 0, 0, 0, 0])
    result = lib.set_stage_information(id, byref(stage_information))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    stage_settings = stage_settings_t()

    stage_settings.LeadScrewPitch = 2
    stage_settings.Units = bytes([0, 101, 103, 114, 101, 101, 0, 0])
    stage_settings.MaxSpeed = 48
    stage_settings.TravelRange = 360
    stage_settings.SupplyVoltageMin = 0
    stage_settings.SupplyVoltageMax = 0
    stage_settings.MaxCurrentConsumption = 0
    stage_settings.HorizontalLoadCapacity = 0
    stage_settings.VerticalLoadCapacity = 0
    result = lib.set_stage_settings(id, byref(stage_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    motor_information = motor_information_t()

    motor_information.Manufacturer = bytes([0, 111, 116, 105, 111, 110, 32, 67, 111, 110, 116, 114, 111, 108, 32, 80])
    motor_information.PartNumber = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    result = lib.set_motor_information(id, byref(motor_information))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    motor_settings = motor_settings_t()

    class MotorType_:
        MOTOR_TYPE_BLDC = 3
        MOTOR_TYPE_DC = 2
        MOTOR_TYPE_STEP = 1
        MOTOR_TYPE_UNKNOWN = 0
    motor_settings.MotorType = MotorType_.MOTOR_TYPE_STEP | MotorType_.MOTOR_TYPE_UNKNOWN
    motor_settings.ReservedField = 0
    motor_settings.Poles = 0
    motor_settings.Phases = 0
    motor_settings.NominalVoltage = 0
    motor_settings.NominalCurrent = 0
    motor_settings.NominalSpeed = 0
    motor_settings.NominalTorque = 0
    motor_settings.NominalPower = 0
    motor_settings.WindingResistance = 0
    motor_settings.WindingInductance = 0
    motor_settings.RotorInertia = 0
    motor_settings.StallTorque = 0
    motor_settings.DetentTorque = 0
    motor_settings.TorqueConstant = 0
    motor_settings.SpeedConstant = 0
    motor_settings.SpeedTorqueGradient = 0
    motor_settings.MechanicalTimeConstant = 0
    motor_settings.MaxSpeed = 5000
    motor_settings.MaxCurrent = 0
    motor_settings.MaxCurrentTime = 0
    motor_settings.NoLoadCurrent = 0
    motor_settings.NoLoadSpeed = 0
    result = lib.set_motor_settings(id, byref(motor_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    encoder_information = encoder_information_t()

    encoder_information.Manufacturer = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    encoder_information.PartNumber = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    result = lib.set_encoder_information(id, byref(encoder_information))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    encoder_settings = encoder_settings_t()

    encoder_settings.MaxOperatingFrequency = 0
    encoder_settings.SupplyVoltageMin = 0
    encoder_settings.SupplyVoltageMax = 0
    encoder_settings.MaxCurrentConsumption = 0
    encoder_settings.PPR = 1000
    class EncoderSettings_:
        ENCSET_REVOLUTIONSENSOR_ACTIVE_HIGH = 256
        ENCSET_REVOLUTIONSENSOR_PRESENT = 64
        ENCSET_INDEXCHANNEL_PRESENT = 16
        ENCSET_PUSHPULL_OUTPUT = 4
        ENCSET_DIFFERENTIAL_OUTPUT = 1

    result = lib.set_encoder_settings(id, byref(encoder_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    hallsensor_information = hallsensor_information_t()

    hallsensor_information.Manufacturer = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    hallsensor_information.PartNumber = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    result = lib.set_hallsensor_information(id, byref(hallsensor_information))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    hallsensor_settings = hallsensor_settings_t()

    hallsensor_settings.MaxOperatingFrequency = 0
    hallsensor_settings.SupplyVoltageMin = 0
    hallsensor_settings.SupplyVoltageMax = 0
    hallsensor_settings.MaxCurrentConsumption = 0
    hallsensor_settings.PPR = 0
    result = lib.set_hallsensor_settings(id, byref(hallsensor_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    gear_information = gear_information_t()

    gear_information.Manufacturer = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    gear_information.PartNumber = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    result = lib.set_gear_information(id, byref(gear_information))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    gear_settings = gear_settings_t()

    gear_settings.ReductionIn = 1
    gear_settings.ReductionOut = 1
    gear_settings.RatedInputTorque = 0
    gear_settings.RatedInputSpeed = 0
    gear_settings.MaxOutputBacklash = 0
    gear_settings.InputInertia = 0
    gear_settings.Efficiency = 0
    result = lib.set_gear_settings(id, byref(gear_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    accessories_settings = accessories_settings_t()

    accessories_settings.MagneticBrakeInfo = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    accessories_settings.MBRatedVoltage = 0
    accessories_settings.MBRatedCurrent = 0
    accessories_settings.MBTorque = 0
    class MBSettings_:
        MB_POWERED_HOLD = 2
        MB_AVAILABLE = 1

    accessories_settings.TemperatureSensorInfo = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    accessories_settings.TSMin = 0
    accessories_settings.TSMax = 0
    accessories_settings.TSGrad = 0
    class TSSettings_:
        TS_AVAILABLE = 8
        TS_TYPE_BITS = 7
        TS_TYPE_SEMICONDUCTOR = 2
        TS_TYPE_THERMOCOUPLE = 1
        TS_TYPE_UNKNOWN = 0
    accessories_settings.TSSettings = TSSettings_.TS_TYPE_THERMOCOUPLE | TSSettings_.TS_TYPE_UNKNOWN
    class LimitSwitchesSettings_:
        LS_SHORTED = 16
        LS_SW2_ACTIVE_LOW = 8
        LS_SW1_ACTIVE_LOW = 4
        LS_ON_SW2_AVAILABLE = 2
        LS_ON_SW1_AVAILABLE = 1

    result = lib.set_accessories_settings(id, byref(accessories_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    return worst_result
