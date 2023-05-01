#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tools for setting up and using the data recorder of a PI device."""

from __future__ import print_function

__signature__ = 0xb8574d8e314a3fd418662458a974325c


# Invalid class attribute name pylint: disable=C0103
# Too few public methods pylint: disable=R0903
# Class inherits from object, can be safely removed from bases in python3 pylint: disable=R0205
class RecordOptions(object):
    """Defines for the kind of data to be recorded."""
    NOTHING_0 = 0
    COMMANDED_POSITION_1 = 1
    ACTUAL_POSITION_2 = 2
    POSITION_ERROR_3 = 3
    PIO_VALUE_4 = 4
    DIO_VALUE_5 = 5
    COMEDI_VALUE_6 = 6
    PIEZO_VOLTAGE_7 = 7
    TIMESTAMP_8 = 8
    INDEX_9 = 9
    TICKS_10 = 10
    DDL_OUTPUT_13 = 13
    OPENLOOP_INPUT_14 = 14
    PID_OUTPUT_15 = 15
    ANALOG_OUTPUT_16 = 16
    SENSOR_NORMALIZED_17 = 17
    SENSOR_FILTERED_18 = 18
    SENSOR_ELEC_LIN_19 = 19
    SENSOR_MECH_LIN_20 = 20
    TARGET_SLEWRATE_LIM_22 = 22
    TARGET_VELOCITY_23 = 23
    TARGET_ACCELERATION_24 = 24
    TARGET_JERK_25 = 25
    DI_VALUE_26 = 26
    DO_VALUE_27 = 27
    CTV_TARGET_VALUE_28 = 28
    CCV_CONTROL_VALUE_29 = 29
    CAV_ACTUAL_VALUE_30 = 30
    CCV_CURRENT_VALUE_31 = 31
    DRIFT_COMP_OFFSET_32 = 32
    HYBRID_MOTOR_VOLTAGE_33 = 33
    HYBRID_PIEZO_VOLTAGE_34 = 34
    SYSTEM_TIME_44 = 44
    COMMANDED_VELOCITY_70 = 70
    COMMANDED_ACCELERATION_71 = 71
    ACTUAL_VELOCITY_72 = 72
    MOTOR_OUTPUT_73 = 73
    KP_OF_AXIS_74 = 74
    KI_OF_AXIS_75 = 75
    KD_OF_AXIS_76 = 76
    SIGNAL_STATUS_REGISTER_80 = 80
    ANALOG_INPUT_81 = 81
    ACTIVE_PARAMETERSET_90 = 90
    ACTUAL_FREQUENCY_91 = 91
    P0_92 = 92
    DIA_93 = 93
    CURRENT_PHASE_A_100 = 100
    CURRENT_PHASE_B_101 = 101
    CURRENT_PHASE_C_102 = 102
    CURRENT_PHASE_D_103 = 103
    FIELD_ORIENTED_CONTROL_UD_105 = 105
    FIELD_ORIENTED_CONTROL_UQ_106 = 106
    FIELD_ORIENTED_CONTROL_ID_107 = 107
    FIELD_ORIENTED_CONTROL_IQ_108 = 108
    FIELD_ORIENTED_CONTROL_U_ALPHA_109 = 109
    FIELD_ORIENTED_CONTROL_U_BETA_110 = 110
    FIELD_ORIENTED_CONTROL_V_PHASE_111 = 111
    FIELD_ORIENTED_CONTROL_ANGLE_112 = 112
    FIELD_ORIENTED_CONTROL_ANGLE_FROM_POS_113 = 113
    FIELD_ORIENTED_CONTROL_ERROR_D_114 = 114
    FIELD_ORIENTED_CONTROL_ERROR_Q_115 = 115
    POSITION_CONTROL_OUT_120 = 120
    VELOCITY_CONTROL_OUT_121 = 121
    PILOT_CONTROL_OUT_122 = 122
    ACCELERATION_CONTROL_OUT_123 = 123
    LOW_PASS_FILTERED_VELOCITY_140 = 140
    ANALOG_IN_VALUE_141 = 141
    LOW_PASS_FILTERED_VELOCITY_ERROR_142 = 142
    ACTUAL_ACCELERATION_143 = 143
    LOW_PASS_FILTERED_ACCELERATION_ERROR_144 = 144
    TW8_SINE_REGISTER_145 = 145
    TW8_COSINE_REGISTER_146 = 146
    FAST_ALIGNMENT_INPUT_CHANNEL_150 = 150
    FAST_ALIGNMENT_PROCESS_REGISTER_151 = 151
    FAST_ALIGNMENT_GS_RESULT_ROUTINE_152 = 152
    FAST_ALIGNMENT_GS_WEIGHT_ROUTINE_153 = 153
    FAST_ALIGNMENT_GS_AMPLITUDE_ROUTINE_154 = 154
    FAST_ALIGNMENT_FINISHED_FLAG_155 = 155
    FAST_ALIGNMENT_GRADIENT_SCAN_PHASE_ROUTINE_156 = 156


# Class inherits from object, can be safely removed from bases in python3 pylint: disable=R0205
class TriggerSources(object):  # Too few public methods pylint: disable=R0903
    """Defines for sources that can trigger data recording."""
    DEFAULT_0 = 0
    POSITION_CHANGING_COMMAND_1 = 1
    NEXT_COMMAND_WITH_RESET_2 = 2
    EXTERNAL_TRIGGER_3 = 3
    TRIGGER_IMMEDIATELY_4 = 4
    DIO_CHANNEL_5 = 5
    POS_CHANGING_WITH_RESET_6 = 6
    SMO_COMMAND_WITH_RESET_7 = 7
    COMEDI_CHANNEL_8 = 8
    WAVE_GENERATOR_9 = 9


def __getopt(name, enumclass):
    """Return item of 'enumclass' which name parts start with 'name'.
     @param name : Short name of item, e.g. "CUR_POS". Case insensitive, separated by "_".
     @param enumclass : Class name that contains enums.
     @return : According enum value as integer.
     """
    for item in dir(enumclass):
        match = []
        for i, itempart in enumerate(item.split('_')):
            if itempart.isdigit():
                continue
            try:
                namepart = name.split('_')[i]
            except IndexError:
                continue
            match.append(__isabbreviation(namepart.upper(), itempart.upper()))
        if all(match):
            return getattr(enumclass, item)
    raise KeyError('invalid name %r' % enumclass)


def __isabbreviation(abbrev, item):
    """Return True if first char of 'abbrev' and 'item' match and all chars of 'abbrev' occur in 'item' in this order.
    @param abbrev : Case sensitive string.
    @param item : Case sensitive string.
    @return : True if 'abbrev' is an abbreviation of 'item'.
    """
    if not abbrev:
        return True
    if not item:
        return False
    if abbrev[0] != item[0]:
        return False
    return any(__isabbreviation(abbrev[1:], item[i + 1:]) for i in range(len(item)))


def getrecopt(name):
    """Return record option value according to 'name'.
    @param name: Short name of item, e.g. "CUR_POS". Case insensitive, separated by "_".
    @return : According enum value as integer.
    """
    return __getopt(name, RecordOptions)


def gettrigsources(name):
    """Return trigger option value according to 'name'.
    @param name: Short name of item, e.g. "CUR_POS". Case insensitive, separated by "_".
    @return : According enum value as integer.
    """
    return __getopt(name, TriggerSources)
