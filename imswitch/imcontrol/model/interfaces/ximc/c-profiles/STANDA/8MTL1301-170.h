#ifndef __8MTL1301_170
#define __8MTL1301_170

#include <string.h>

#if defined(__APPLE__) && !defined(NOFRAMEWORK)
#include <libximc/ximc.h>
#else
#include <ximc.h>
#endif


#define 8MTL1301_170_BUILDER_VERSION_MAJOR  0
#define 8MTL1301_170_BUILDER_VERSION_MINOR  9
#define 8MTL1301_170_BUILDER_VERSION_BUGFIX 10
#define 8MTL1301_170_BUILDER_VERSION_SUFFIX ""
#define 8MTL1301_170_BUILDER_VERSION        "0.9.10"


#if defined(_MSC_VER)
#define inline __inline
#endif

static inline result_t set_profile_8MTL1301_170(device_t id)
{
  result_t worst_result = result_ok;
  result_t result = result_ok;

  feedback_settings_t feedback_settings;
  memset((void*)&feedback_settings, 0, sizeof(feedback_settings_t));
  feedback_settings.IPS = 0;
  feedback_settings.FeedbackType = FEEDBACK_ENCODER;
  feedback_settings.FeedbackFlags = FEEDBACK_ENC_TYPE_DIFFERENTIAL | FEEDBACK_ENC_REVERSE | FEEDBACK_ENC_TYPE_AUTO;
  feedback_settings.CountsPerTurn = 160000;
  result = set_feedback_settings(id, &feedback_settings);

  if (result != result_ok)
  {
    if (worst_result == result_ok || worst_result == result_value_error)
    {
      worst_result = result;
    }
  }

  home_settings_t home_settings;
  memset((void*)&home_settings, 0, sizeof(home_settings_t));
  home_settings.FastHome = 120;
  home_settings.uFastHome = 0;
  home_settings.SlowHome = 15;
  home_settings.uSlowHome = 0;
  home_settings.HomeDelta = -10000;
  home_settings.uHomeDelta = 0;
  home_settings.HomeFlags = HOME_STOP_SECOND_REV | HOME_STOP_FIRST_BITS | HOME_MV_SEC_EN | HOME_DIR_SECOND;
  result = set_home_settings(id, &home_settings);

  if (result != result_ok)
  {
    if (worst_result == result_ok || worst_result == result_value_error)
    {
      worst_result = result;
    }
  }

  move_settings_t move_settings;
  memset((void*)&move_settings, 0, sizeof(move_settings_t));
  move_settings.Speed = 375;
  move_settings.uSpeed = 0;
  move_settings.Accel = 9375;
  move_settings.Decel = 10312;
  move_settings.AntiplaySpeed = 375;
  move_settings.uAntiplaySpeed = 0;
  result = set_move_settings(id, &move_settings);

  if (result != result_ok)
  {
    if (worst_result == result_ok || worst_result == result_value_error)
    {
      worst_result = result;
    }
  }

  engine_settings_t engine_settings;
  memset((void*)&engine_settings, 0, sizeof(engine_settings_t));
  engine_settings.NomVoltage = 1200;
  engine_settings.NomCurrent = 3000;
  engine_settings.NomSpeed = 750;
  engine_settings.uNomSpeed = 0;
  engine_settings.EngineFlags = ENGINE_LIMIT_RPM | ENGINE_LIMIT_CURR | ENGINE_ACCEL_ON;
  engine_settings.Antiplay = -23963;
  engine_settings.MicrostepMode = MICROSTEP_MODE_FRAC_256;
  engine_settings.StepsPerRev = 2;
  result = set_engine_settings(id, &engine_settings);

  if (result != result_ok)
  {
    if (worst_result == result_ok || worst_result == result_value_error)
    {
      worst_result = result;
    }
  }

  entype_settings_t entype_settings;
  memset((void*)&entype_settings, 0, sizeof(entype_settings_t));
  entype_settings.EngineType = ENGINE_TYPE_BRUSHLESS | ENGINE_TYPE_NONE;
  result = set_entype_settings(id, &entype_settings);

  if (result != result_ok)
  {
    if (worst_result == result_ok || worst_result == result_value_error)
    {
      worst_result = result;
    }
  }

  power_settings_t power_settings;
  memset((void*)&power_settings, 0, sizeof(power_settings_t));
  power_settings.HoldCurrent = 60;
  power_settings.CurrReductDelay = 1500;
  power_settings.PowerOffDelay = 3600;
  power_settings.CurrentSetTime = 500;
  power_settings.PowerFlags = POWER_SMOOTH_CURRENT;
  result = set_power_settings(id, &power_settings);

  if (result != result_ok)
  {
    if (worst_result == result_ok || worst_result == result_value_error)
    {
      worst_result = result;
    }
  }

  secure_settings_t secure_settings;
  memset((void*)&secure_settings, 0, sizeof(secure_settings_t));
  secure_settings.LowUpwrOff = 800;
  secure_settings.CriticalUpwr = 5500;
  secure_settings.Flags = ALARM_ENGINE_RESPONSE | ALARM_FLAGS_STICKING | ALARM_ON_BORDERS_SWAP_MISSET | H_BRIDGE_ALERT | ALARM_ON_DRIVER_OVERHEATING;
  result = set_secure_settings(id, &secure_settings);

  if (result != result_ok)
  {
    if (worst_result == result_ok || worst_result == result_value_error)
    {
      worst_result = result;
    }
  }

  edges_settings_t edges_settings;
  memset((void*)&edges_settings, 0, sizeof(edges_settings_t));
  edges_settings.BorderFlags = BORDER_STOP_RIGHT | BORDER_STOP_LEFT;
  edges_settings.EnderFlags = ENDER_SW2_ACTIVE_LOW | ENDER_SW1_ACTIVE_LOW;
  edges_settings.LeftBorder = -403750;
  edges_settings.uLeftBorder = 0;
  edges_settings.RightBorder = 403750;
  edges_settings.uRightBorder = 0;
  result = set_edges_settings(id, &edges_settings);

  if (result != result_ok)
  {
    if (worst_result == result_ok || worst_result == result_value_error)
    {
      worst_result = result;
    }
  }

  pid_settings_t pid_settings;
  memset((void*)&pid_settings, 0, sizeof(pid_settings_t));
  pid_settings.KpU = 0;
  pid_settings.KiU = 0;
  pid_settings.KdU = 0;
  pid_settings.Kpf = 200;
  pid_settings.Kif = 0.25;
  pid_settings.Kdf = 0.625;
  result = set_pid_settings(id, &pid_settings);

  if (result != result_ok)
  {
    if (worst_result == result_ok || worst_result == result_value_error)
    {
      worst_result = result;
    }
  }

  ctp_settings_t ctp_settings;
  memset((void*)&ctp_settings, 0, sizeof(ctp_settings_t));
  ctp_settings.CTPMinError = 3;
  ctp_settings.CTPFlags = CTP_ERROR_CORRECTION | REV_SENS_INV;
  result = set_ctp_settings(id, &ctp_settings);

  if (result != result_ok)
  {
    if (worst_result == result_ok || worst_result == result_value_error)
    {
      worst_result = result;
    }
  }

  controller_name_t controller_name;
  memset((void*)&controller_name, 0, sizeof(controller_name_t));
  const int8_t controller_name_ControllerName_temp[16] = {0, 113, -4, 118, 5, 0, -29, 0, 6, 0, 0, 0, 104, 101, 34, 0};
  memcpy(controller_name.ControllerName, controller_name_ControllerName_temp, sizeof(int8_t) * 16);
  controller_name.CtrlFlags = 0;
  result = set_controller_name(id, &controller_name);

  if (result != result_ok)
  {
    if (worst_result == result_ok || worst_result == result_value_error)
    {
      worst_result = result;
    }
  }

  return worst_result;
}

#endif
