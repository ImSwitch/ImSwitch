def set_profile_8MTL1301_170_LEN_100(lib, id):
    worst_result = Result.Ok
    result = Result.Ok

    feedback_settings = feedback_settings_t()

    feedback_settings.IPS = 0
    class FeedbackType_:
        FEEDBACK_ENCODER_MEDIATED = 6
        FEEDBACK_NONE = 5
        FEEDBACK_EMF = 4
        FEEDBACK_ENCODER = 1
    feedback_settings.FeedbackType = FeedbackType_.FEEDBACK_ENCODER
    class FeedbackFlags_:
        FEEDBACK_ENC_TYPE_BITS = 192
        FEEDBACK_ENC_TYPE_DIFFERENTIAL = 128
        FEEDBACK_ENC_TYPE_SINGLE_ENDED = 64
        FEEDBACK_ENC_REVERSE = 1
        FEEDBACK_ENC_TYPE_AUTO = 0
    feedback_settings.FeedbackFlags = FeedbackFlags_.FEEDBACK_ENC_TYPE_DIFFERENTIAL | FeedbackFlags_.FEEDBACK_ENC_REVERSE | FeedbackFlags_.FEEDBACK_ENC_TYPE_AUTO
    feedback_settings.CountsPerTurn = 320000
    result = lib.set_feedback_settings(id, byref(feedback_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    home_settings = home_settings_t()

    home_settings.FastHome = 120
    home_settings.uFastHome = 0
    home_settings.SlowHome = 15
    home_settings.uSlowHome = 0
    home_settings.HomeDelta = -10000
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
    home_settings.HomeFlags = HomeFlags_.HOME_STOP_SECOND_REV | HomeFlags_.HOME_STOP_FIRST_BITS | HomeFlags_.HOME_MV_SEC_EN | HomeFlags_.HOME_DIR_SECOND
    result = lib.set_home_settings(id, byref(home_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    move_settings = move_settings_t()

    move_settings.Speed = 375
    move_settings.uSpeed = 0
    move_settings.Accel = 9375
    move_settings.Decel = 10312
    move_settings.AntiplaySpeed = 375
    move_settings.uAntiplaySpeed = 0
    result = lib.set_move_settings(id, byref(move_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    engine_settings = engine_settings_t()

    engine_settings.NomVoltage = 1200
    engine_settings.NomCurrent = 3000
    engine_settings.NomSpeed = 750
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
    engine_settings.EngineFlags = EngineFlags_.ENGINE_LIMIT_RPM | EngineFlags_.ENGINE_LIMIT_CURR | EngineFlags_.ENGINE_ACCEL_ON
    engine_settings.Antiplay = 17611
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
    engine_settings.StepsPerRev = 2
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
    entype_settings.EngineType = EngineType_.ENGINE_TYPE_BRUSHLESS | EngineType_.ENGINE_TYPE_NONE
    result = lib.set_entype_settings(id, byref(entype_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    power_settings = power_settings_t()

    power_settings.HoldCurrent = 60
    power_settings.CurrReductDelay = 1500
    power_settings.PowerOffDelay = 3600
    power_settings.CurrentSetTime = 500
    class PowerFlags_:
        POWER_SMOOTH_CURRENT = 4
        POWER_OFF_ENABLED = 2
        POWER_REDUCT_ENABLED = 1
    power_settings.PowerFlags = PowerFlags_.POWER_SMOOTH_CURRENT
    result = lib.set_power_settings(id, byref(power_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    secure_settings = secure_settings_t()

    secure_settings.LowUpwrOff = 800
    secure_settings.CriticalUpwr = 5500
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
    edges_settings.BorderFlags = BorderFlags_.BORDER_STOP_RIGHT | BorderFlags_.BORDER_STOP_LEFT
    class EnderFlags_:
        ENDER_SW2_ACTIVE_LOW = 4
        ENDER_SW1_ACTIVE_LOW = 2
        ENDER_SWAP = 1
    edges_settings.EnderFlags = EnderFlags_.ENDER_SW2_ACTIVE_LOW | EnderFlags_.ENDER_SW1_ACTIVE_LOW | EnderFlags_.ENDER_SWAP
    edges_settings.LeftBorder = -807500
    edges_settings.uLeftBorder = 0
    edges_settings.RightBorder = 807500
    edges_settings.uRightBorder = 0
    result = lib.set_edges_settings(id, byref(edges_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    pid_settings = pid_settings_t()

    pid_settings.KpU = 0
    pid_settings.KiU = 0
    pid_settings.KdU = 0
    pid_settings.Kpf = 200
    pid_settings.Kif = 0.25
    pid_settings.Kdf = 0.625
    result = lib.set_pid_settings(id, byref(pid_settings))

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
    ctp_settings.CTPFlags = CTPFlags_.CTP_ERROR_CORRECTION | CTPFlags_.REV_SENS_INV
    result = lib.set_ctp_settings(id, byref(ctp_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    controller_name = controller_name_t()

    controller_name.ControllerName = bytes([0, 113, 252, 118, 5, 0, 227, 0, 6, 0, 0, 0, 104, 101, 34, 0])
    class CtrlFlags_:
        EEPROM_PRECEDENCE = 1

    result = lib.set_controller_name(id, byref(controller_name))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    return worst_result
