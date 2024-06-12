# MIT License

# Copyright (c) 2020 yaq

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from typing import Optional, Sequence
import struct


def _pack(
    msgid: int,
    dest: int,
    source: int,
    *,
    param1: int = 0,
    param2: int = 0,
    data: Optional[bytes] = None
):
    if data is not None:
        assert param1 == param2 == 0
        return struct.pack("<HHBB", msgid, len(data), dest | 0x80, source) + data
    else:
        return struct.pack("<H2b2B", msgid, param1, param2, dest, source)


def mod_identify(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x0223, dest, source, param1=chan_ident)


def mod_set_chanenablestate(
    dest: int, source: int, chan_ident: int, enable_state: int
) -> bytes:
    return _pack(0x0210, dest, source, param1=chan_ident, param2=enable_state)


def mod_req_chanenablestate(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x0211, dest, source, param1=chan_ident)


def hw_disconnect(dest: int, source: int) -> bytes:
    return _pack(0x0002, dest, source)


def hw_start_updatemsgs(dest: int, source: int) -> bytes:
    return _pack(0x0011, dest, source)


def hw_stop_updatemsgs(dest: int, source: int) -> bytes:
    return _pack(0x0012, dest, source)


def hw_req_info(dest: int, source: int) -> bytes:
    return _pack(0x0005, dest, source)


def rack_req_bayused(dest: int, source: int, bay_ident: int) -> bytes:
    return _pack(0x0060, dest, source, param1=bay_ident)


def hub_req_bayused(dest: int, source: int) -> bytes:
    return _pack(0x0065, dest, source)


def rack_req_statusbits(dest: int, source: int) -> bytes:
    # I suspect there is an error in the docs, and status_bits should be omitted
    # This reflects what I think it _should_ be
    # - KFS 2020-06-05
    return _pack(0x0226, dest, source)


def rack_set_digoutputs(dest: int, source: int, dig_outs: Sequence[bool]) -> bytes:
    dig_out_param = 0
    bit = 1
    for i in dig_outs:
        if i:
            dig_out_param |= bit
        bit <<= 1
    return _pack(0x0228, dest, source, param1=dig_out_param)


def rack_get_digoutputs(dest: int, source: int) -> bytes:
    return _pack(0x0229, dest, source)


def mod_set_digoutputs(
    dest: int, source: int, chan_ident: int, dig_outs: Sequence[bool]
) -> bytes:
    dig_out_param = 0
    bit = 1
    for i in dig_outs:
        if i:
            dig_out_param |= bit
        bit <<= 1
    return _pack(0x0213, dest, source, param1=dig_out_param)


def mod_req_digoutputs(dest: int, source: int) -> bytes:
    # I suspect there is an error in the docs, and bits should be omitted
    # This reflects what I think it _should_ be
    # - KFS 2020-06-05
    return _pack(0x0214, dest, source)


def hw_set_kcubemmilock(dest: int, source: int, mmi_lock: int) -> bytes:
    return _pack(0x0250, dest, source, param2=mmi_lock)


def hw_req_kcubemmilock(dest: int, source: int) -> bytes:
    # I suspect there is an error in the docs, and bits should be omitted
    # This reflects what I think it _should_ be
    # - KFS 2020-06-05
    return _pack(0x0251, dest, source)


def restorefactorysettings(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x0686, dest, source, param1=chan_ident)


def hw_yes_flash_programming(dest: int, source: int) -> bytes:
    return _pack(0x0017, dest, source)


def hw_no_flash_programming(dest: int, source: int) -> bytes:
    return _pack(0x0018, dest, source)


def mot_set_poscounter(dest: int, source: int, chan_ident: int, position: int) -> bytes:
    data = struct.pack("<Hl", chan_ident, position)
    return _pack(0x0410, dest, source, data=data)


def mot_req_poscounter(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x0411, dest, source, param1=chan_ident)


def mot_set_enccounter(dest: int, source: int, chan_ident: int, encoder_count) -> bytes:
    data = struct.pack("<Hl", chan_ident, encoder_count)
    return _pack(0x0409, dest, source, data=data)


def mot_req_enccounter(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x040A, dest, source, param1=chan_ident)


def mot_set_velparams(
    dest: int,
    source: int,
    chan_ident: int,
    min_velocity: int,
    acceleration: int,
    max_velocity: int,
) -> bytes:
    data = struct.pack("<H3l", chan_ident, min_velocity, acceleration, max_velocity)
    return _pack(0x0413, dest, source, data=data)


def mot_req_velparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x0414, dest, source, param1=chan_ident)


def mot_set_jogparams(
    dest: int,
    source: int,
    chan_ident: int,
    jog_mode: int,
    step_size: int,
    min_velocity: int,
    acceleration: int,
    max_velocity: int,
    stop_mode: int,
) -> bytes:
    data = struct.pack(
        "<HH4lH",
        chan_ident,
        jog_mode,
        step_size,
        min_velocity,
        acceleration,
        max_velocity,
        stop_mode,
    )
    return _pack(0x0416, dest, source, data=data)


def mot_req_jogparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x0417, dest, source, param1=chan_ident)


def mot_req_adcinputs(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x042B, dest, source, param1=chan_ident)


def mot_set_powerparams(
    dest: int, source: int, chan_ident: int, rest_factor: int, move_factor: int
) -> bytes:
    data = struct.pack("<3H", chan_ident, rest_factor, move_factor)
    return _pack(0x0426, dest, source, data=data)


def mot_req_powerparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x0427, dest, source, param1=chan_ident)


def mot_set_genmoveparams(
    dest: int, source: int, chan_ident: int, backlash_distance: int
) -> bytes:
    data = struct.pack("<Hl", chan_ident, backlash_distance)
    return _pack(0x043A, dest, source, data=data)


def mot_req_genmoveparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x043B, dest, source, param1=chan_ident)


def mot_set_moverelparams(
    dest: int, source: int, chan_ident: int, relative_distance: int
) -> bytes:
    data = struct.pack("<Hl", chan_ident, relative_distance)
    return _pack(0x0445, dest, source, data=data)


def mot_req_moverelparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x0446, dest, source, param1=chan_ident)


def mot_set_moveabsparams(
    dest: int, source: int, chan_ident: int, absolute_position: int
) -> bytes:
    data = struct.pack("<Hl", chan_ident, absolute_position)
    return _pack(0x0450, dest, source, data=data)


def mot_req_moveabsparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x0451, dest, source, param1=chan_ident)


def mot_set_homeparams(
    dest: int,
    source: int,
    chan_ident: int,
    home_dir: int,
    limit_switch: int,
    home_velocity: int,
    offset_distance: int,
) -> bytes:
    data = struct.pack(
        "<3Hll", chan_ident, home_dir, limit_switch, home_velocity, offset_distance
    )
    return _pack(0x0440, dest, source, data=data)


def mot_req_homeparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x0441, dest, source, param1=chan_ident)


def mot_set_limswitchparams(
    dest: int,
    source: int,
    chan_ident: int,
    cw_hardlimit: int,
    ccw_hardlimit: int,
    cw_softlimit: int,
    ccw_softlimit: int,
    soft_limit_mode: int,
) -> bytes:
    data = struct.pack(
        "<3HLLH",
        chan_ident,
        cw_hardlimit,
        ccw_hardlimit,
        cw_softlimit,
        ccw_softlimit,
        soft_limit_mode,
    )
    return _pack(0x0423, dest, source, data=data)


def mot_req_limswitchparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x0424, dest, source, param1=chan_ident)


def mot_move_home(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x0443, dest, source, param1=chan_ident)


def mot_move_relative(
    dest: int, source: int, chan_ident: int, distance: Optional[int] = None
):
    msgid = 0x0448
    if distance is None:
        return _pack(msgid, dest, source, param1=chan_ident)
    else:
        data = struct.pack("<Hl", chan_ident, distance)
        return _pack(msgid, dest, source, data=data)


def mot_move_absolute(
    dest: int, source: int, chan_ident: int, position: Optional[int] = None
):
    msgid = 0x0453
    if position is None:
        return _pack(msgid, dest, source, param1=chan_ident)
    else:
        data = struct.pack("<Hl", chan_ident, position)
        return _pack(msgid, dest, source, data=data)


def mot_move_jog(dest: int, source: int, chan_ident: int, direction) -> bytes:
    return _pack(0x046A, dest, source, param1=chan_ident, param2=direction)


def mot_move_velocity(dest: int, source: int, chan_ident: int, direction) -> bytes:
    return _pack(0x0457, dest, source, param1=chan_ident, param2=direction)


def mot_move_stop(dest: int, source: int, chan_ident: int, stop_mode: int) -> bytes:
    return _pack(0x0465, dest, source, param1=chan_ident, param2=stop_mode)


def mot_set_bowindex(dest: int, source: int, chan_ident: int, bow_index: int) -> bytes:
    data = struct.pack("<HH", chan_ident, bow_index)
    return _pack(0x04F4, dest, source, data=data)


def mot_req_bowindex(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x04F5, dest, source, param1=chan_ident)


def mot_set_dcpidparams(
    dest: int,
    source: int,
    chan_ident: int,
    proportional: Optional[int] = None,
    integral: Optional[int] = None,
    differential: Optional[int] = None,
    integral_limit: Optional[int] = None,
) -> bytes:
    filter_control = 0
    if proportional is not None:
        filter_control |= 1
    else:
        proportional = 0
    if integral is not None:
        filter_control |= 2
    else:
        integral = 0
    if differential is not None:
        filter_control |= 4
    else:
        differential = 0
    if integral_limit is not None:
        filter_control |= 8
    else:
        integral_limit = 0
    data = struct.pack(
        "<H4LH",
        chan_ident,
        proportional,
        integral,
        differential,
        integral_limit,
        filter_control,
    )
    return _pack(0x04A0, dest, source, data=data)


def mot_req_dcpidparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x04A1, dest, source, param1=chan_ident)


def mot_set_avmodes(dest: int, source: int, chan_ident: int, mode_bits: int) -> bytes:
    data = struct.pack("<HH", chan_ident, mode_bits)
    return _pack(0x04B3, dest, source, data=data)


def mot_req_avmodes(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x04B4, dest, source, param1=chan_ident)


def mot_set_potparams(
    dest: int,
    source: int,
    chan_ident: int,
    zero_wnd: int,
    vel1: int,
    wnd1: int,
    vel2: int,
    wnd2: int,
    vel3: int,
    wnd3: int,
    vel4: int,
) -> bytes:
    data = struct.pack(
        "<HHlHlHlHl", chan_ident, zero_wnd, vel1, wnd1, vel2, wnd2, vel3, wnd3, vel4
    )
    return _pack(0x04B0, dest, source, data=data)


def mot_req_potparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x04B1, dest, source, param1=chan_ident)


def mot_set_buttonparams(
    dest: int,
    source: int,
    chan_ident: int,
    mode: int,
    position1: int,
    position2: int,
    time_out1: int,
    time_out2: int,
) -> bytes:
    data = struct.pack(
        "<HHllHH", chan_ident, mode, position1, position2, time_out1, time_out2
    )
    return _pack(0x04B6, dest, source, data=data)


def mot_req_buttonparams(
    dest: int, source: int, chan_ident: int, msgid_param: int
) -> bytes:
    data = struct.pack("<HH", chan_ident, msgid_param)
    return _pack(0x04B9, dest, source, data=data)


def mot_set_eepromparams(
    dest: int, source: int, chan_ident: int, msgid_param: int
) -> bytes:
    data = struct.pack("<HH", chan_ident, msgid_param)
    return _pack(0x04B9, dest, source, data=data)


def mot_set_positionloopparams(
    dest: int,
    source: int,
    chan_ident: int,
    kp_pos: int,
    integral: int,
    i_lim_pos: int,
    differential: int,
    kd_time_pos: int,
    kout_pos: int,
    kaff_pos: int,
    pos_err_lim: int,
) -> bytes:
    data = struct.pack(
        "<3HL5HL2H",
        chan_ident,
        kp_pos,
        integral,
        i_lim_pos,
        differential,
        kd_time_pos,
        kout_pos,
        kaff_pos,
        pos_err_lim,
        0,
        0,
    )
    return _pack(0x04D7, dest, source, data=data)


def mot_req_positionloopparams(dest: int, source: int, chan_ident: int):
    return _pack(0x04D8, dest, source, param1=chan_ident)


def mot_set_motoroutputparams(
    dest: int,
    source: int,
    chan_ident: int,
    cont_current_lim: int,
    energy_lim: int,
    motor_lim: int,
    motor_bias: int,
) -> bytes:
    data = struct.pack(
        "<7H", chan_ident, cont_current_lim, energy_lim, motor_lim, motor_bias, 0, 0
    )
    return _pack(0x04DA, dest, source, data=data)


def mot_req_motoroutputparams(dest: int, source: int, chan_ident: int):
    return _pack(0x04DB, dest, source, param1=chan_ident)


def mot_set_tracksettleparams(
    dest: int,
    source: int,
    chan_ident: int,
    time: int,
    settle_window: int,
    track_window: int,
) -> bytes:
    data = struct.pack("<6H", chan_ident, time, settle_window, track_window, 0, 0)
    return _pack(0x04E0, dest, source, data=data)


def mot_req_tracksettleparams(dest: int, source: int, chan_ident: int):
    return _pack(0x04E1, dest, source, param1=chan_ident)


def mot_set_profilemodeparams(
    dest: int, source: int, chan_ident: int, mode: int, jerk: int
) -> bytes:
    data = struct.pack("<HHLHH", chan_ident, mode, jerk, 0, 0)
    return _pack(0x04E3, dest, source, data=data)


def mot_req_profilemodeparams(dest: int, source: int, chan_ident: int):
    return _pack(0x04E4, dest, source, param1=chan_ident)


def mot_set_joystickparams(
    dest: int,
    source: int,
    chan_ident: int,
    gear_high_max_vel: int,
    gear_low_accn: int,
    gear_high_accn: int,
    dir_sense: int,
) -> bytes:
    data = struct.pack(
        "<H4LH", chan_ident, gear_high_max_vel, gear_low_accn, gear_high_accn, dir_sense
    )
    return _pack(0x04E6, dest, source, data=data)


def mot_req_joystickparams(dest: int, source: int, chan_ident: int):
    return _pack(0x04E7, dest, source, param1=chan_ident)


def mot_set_currentloopoarams(
    dest: int,
    source: int,
    chan_ident: int,
    phase: int,
    kp_current: int,
    ki_current: int,
    i_lim_current: int,
    i_dead_band: int,
    kff: int,
) -> bytes:
    data = struct.pack(
        "<9H",
        chan_ident,
        phase,
        kp_current,
        ki_current,
        i_lim_current,
        i_dead_band,
        kff,
        0,
        0,
    )
    return _pack(0x04D4, dest, source, data=data)


def mot_req_currentloopoarams(dest: int, source: int, chan_ident: int):
    return _pack(0x04D5, dest, source, param1=chan_ident)


def mot_set_settledcurrentloopparams(
    dest: int,
    source: int,
    chan_ident: int,
    phase: int,
    kp_settled: int,
    ki_settled: int,
    i_lim_settled: int,
    i_dead_band_settled: int,
    kff_settled: int,
) -> bytes:
    data = struct.pack(
        "<9H",
        chan_ident,
        phase,
        kp_settled,
        ki_settled,
        i_lim_settled,
        i_dead_band_settled,
        kff_settled,
        0,
        0,
    )
    return _pack(0x04E9, dest, source, data=data)


def mot_req_settledcurrentloopparams(dest: int, source: int, chan_ident: int):
    return _pack(0x04EA, dest, source, param1=chan_ident)


def mot_set_stageaxisparams(
    dest: int,
    source: int,
    chan_ident: int,
    stage_id: int,
    axis_id: int,
    part_no_axis: int,
    serial_num: int,
    counts_per_unit: int,
    min_pos: int,
    max_pos: int,
    max_accn: int,
    max_dec: int,
    max_vel: int,
) -> bytes:
    data = struct.pack(
        "<HHH16sLL5l4H4L",
        chan_ident,
        stage_id,
        axis_id,
        part_no_axis,
        serial_num,
        counts_per_unit,
        min_pos,
        max_pos,
        max_accn,
        max_dec,
        max_vel,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    return _pack(0x04F0, dest, source, data=data)


def mot_req_stageaxisparams(dest: int, source: int, chan_ident: int):
    return _pack(0x04F1, dest, source, param1=chan_ident)


def mot_set_tssactuatortype(dest: int, source: int, actuator_ident: int):
    return _pack(0x04FE, dest, source, param1=actuator_ident)


def mot_ack_dcstatusupdate(dest: int, source: int) -> bytes:
    return _pack(0x0492, dest, source)


def mot_req_statusupdate(dest: int, source: int, chan_ident: int):
    return _pack(0x0480, dest, source, param1=chan_ident)


def mot_req_dcstatusupdate(dest: int, source: int, chan_ident: int):
    return _pack(0x0490, dest, source, param1=chan_ident)


def mot_suspend_endofmovemsges(dest: int, source: int):
    return _pack(0x046B, dest, source)


def mot_resume_endofmovemsges(dest: int, source: int):
    return _pack(0x046C, dest, source)


def mot_set_trigger(dest: int, source: int, chan_ident: int, mode: int) -> bytes:
    # Mode parameter is a bitfield, built as an (unsigned) int, but _pack expects a signed char
    # Convert the python int to equivalent signed 1-byte value
    mode &= 0xff
    if mode >= 2**7:
        mode -= 2**8
    return _pack(0x0500, dest, source, param1=chan_ident, param2=mode)


def mot_req_trigger(dest: int, source: int, chan_ident: int):
    return _pack(0x0501, dest, source, param1=chan_ident)


def mot_set_kcubemmiparams(
    dest: int,
    source: int,
    chan_ident: int,
    mode: int,
    max_vel: int,
    accn: int,
    dir_sense: int,
    pre_set_pos1: int,
    pre_set_pos2: int,
    disp_brightness: int,
    disp_timeout: int,
    disp_dim_level: int,
) -> bytes:
    data = struct.pack(
        "<HHllHll3H",
        chan_ident,
        mode,
        max_vel,
        accn,
        dir_sense,
        pre_set_pos1,
        pre_set_pos2,
        disp_brightness,
        disp_timeout,
        disp_dim_level,
    )
    return _pack(0x0520, dest, source, data=data)


def mot_req_kcubemmiparams(dest: int, source: int, chan_ident: int):
    return _pack(0x0521, dest, source, param1=chan_ident)


def mot_set_kcubetrigioconfig(
    dest: int,
    source: int,
    chan_ident: int,
    trig1_mode: int,
    trig1_polarity: int,
    trig2_mode: int,
    trig2_polarity: int,
) -> bytes:
    data = struct.pack(
        "<6H", chan_ident, trig1_mode, trig1_polarity, trig2_mode, trig2_polarity, 0
    )
    return _pack(0x0523, dest, source, data=data)


def mot_req_kcubetrigconfig(dest: int, source: int, chan_ident: int):
    return _pack(0x0524, dest, source, param1=chan_ident)


def mot_set_kcubeposttrigparams(
    dest: int,
    source: int,
    chan_ident: int,
    start_pos_fwd: int,
    interval_fwd: int,
    num_pulses_fwd: int,
    start_pos_rev: int,
    interval_rev: int,
    num_pulses_rev: int,
    pulse_width: int,
    num_cycles: int,
) -> bytes:
    data = struct.pack(
        "<H8l",
        chan_ident,
        start_pos_fwd,
        interval_fwd,
        num_pulses_fwd,
        start_pos_rev,
        interval_rev,
        num_pulses_rev,
        pulse_width,
        num_cycles,
    )
    return _pack(0x0526, dest, source, data=data)


def mot_req_kcubeposttrigparams(dest: int, source: int, chan_ident: int):
    return _pack(0x0527, dest, source, param1=chan_ident)


def mot_set_kcubekstloopparams(
    dest: int,
    source: int,
    chan_ident: int,
    loop_mode: int,
    prop: int,
    int: int,
    diff: int,
    pid_clip: int,
    pid_tol: int,
    encoder_const: int,
) -> bytes:
    data = struct.pack(
        "<HH5lL",
        chan_ident,
        loop_mode,
        prop,
        int,
        diff,
        pid_clip,
        pid_tol,
        encoder_const,
    )
    return _pack(0x0529, dest, source, data=data)


def mot_req_kcubekstloopparams(dest: int, source: int, chan_ident: int):
    return _pack(0x052A, dest, source, param1=chan_ident)


def mot_set_mmf_operparams(
    dest: int,
    source: int,
    chan_ident: int,
    i_tranit_time: int,
    i_transit_time_adc: int,
    oper_mode1: int,
    sig_mode1: int,
    pulse_width1: int,
    oper_mode2: int,
    sig_mode2: int,
    pulse_width2: int,
) -> bytes:
    data = struct.pack(
        "<HllHHlHHllL",
        chan_ident,
        i_tranit_time,
        i_transit_time_adc,
        oper_mode1,
        sig_mode1,
        pulse_width1,
        oper_mode2,
        sig_mode2,
        pulse_width2,
        0,
        0,
    )
    return _pack(0x0510, dest, source, data=data)


def mot_req_mmf_operparams(dest: int, source: int, chan_ident: int):
    return _pack(0x0511, dest, source, param1=chan_ident)


def mot_set_sol_operatingmode(
    dest: int, source: int, chan_ident: int, mode: int
) -> bytes:

    return _pack(0x04C0, dest, source, param1=chan_ident, param2=mode)


def mot_req_sol_operatingmode(dest: int, source: int, chan_ident: int) -> bytes:

    return _pack(0x04C1, dest, source, param1=chan_ident)


def mot_set_sol_cycleparams(
    dest: int, source: int, chan_ident: int, off_time: int, num_cycles: int
) -> bytes:
    data = struct.pack("<H3l", chan_ident, off_time, num_cycles)
    return _pack(0x04C3, dest, source, data=data)


def mot_req_sol_cycleparams(dest: int, source: int, chan_ident: int):
    return _pack(0x04C4, dest, source, param1=chan_ident)


def mot_set_sol_interlockmode(
    dest: int, source: int, chan_ident: int, mode: bool
) -> bytes:
    return _pack(0x04C6, dest, source, param1=chan_ident, param2=1 if mode else 2)


def mot_req_sol_interlockmode(dest: int, source: int, chan_ident: int):
    return _pack(0x04C7, dest, source, param1=chan_ident)


def mot_set_sol_state(dest: int, source: int, chan_ident: int, state: bool) -> bytes:
    return _pack(0x04CB, dest, source, param1=chan_ident, param2=1 if state else 2)


def mot_req_sol_state(dest: int, source: int, chan_ident: int):
    return _pack(0x04CC, dest, source, param1=chan_ident)


def pz_set_positioncontrolmode(
    dest: int, source: int, chan_ident: int, mode: int
) -> bytes:
    return _pack(0x0640, dest, source, param1=chan_ident, param2=mode)


def pz_req_positioncontrolmode(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x0641, dest, source, param1=chan_ident)


def pz_set_outputvolts(dest: int, source: int, chan_ident: int, voltage: int) -> bytes:
    data = struct.pack("Hh", chan_ident, voltage)
    return _pack(0x0643, dest, source, data=data)


def pz_req_outputvolts(dest: int, source: int, chan_ident: int):
    return _pack(0x0644, dest, source, param1=chan_ident)


def pz_set_outputpos(dest: int, source: int, chan_ident: int, position: int) -> bytes:
    data = struct.pack("HH", chan_ident, position)
    return _pack(0x0646, dest, source, data=data)


def pz_req_outputpos(dest: int, source: int, chan_ident: int):
    return _pack(0x0647, dest, source, param1=chan_ident)


def pz_set_inputvoltssrc(
    dest: int, source: int, chan_ident: int, volt_src: int
) -> bytes:
    data = struct.pack("HH", chan_ident, volt_src)
    return _pack(0x0652, dest, source, data=data)


def pz_req_inputvoltssrc(dest: int, source: int, chan_ident: int):
    return _pack(0x0653, dest, source, param1=chan_ident)


def pz_set_piconsts(
    dest: int, source: int, chan_ident: int, PropConst: int, IntConst: int
) -> bytes:
    data = struct.pack("HHH", chan_ident, PropConst, IntConst)
    return _pack(0x0655, dest, source, data=data)


def pz_req_piconsts(dest: int, source: int, chan_ident: int):
    return _pack(0x0656, dest, source, param1=chan_ident)


def pz_req_pzstatusbits(dest: int, source: int, chan_ident: int):
    return _pack(0x065B, dest, source, param1=chan_ident)


def pz_req_pzstatusupdate(dest: int, source: int, chan_ident: int):
    return _pack(0x0660, dest, source, param1=chan_ident)


def pz_ack_pzstatusupdate(dest: int, source: int) -> bytes:
    return _pack(0x0662, dest, source)


def pz_set_ppc_pidconsts(
    dest: int,
    source: int,
    chan_ident: int,
    pid_p: int,
    pid_i: int,
    pid_d: int,
    pid_d_filter_cut: int,
    pid_d_filter_on: int,
) -> bytes:
    data = struct.pack(
        "<HHHHHH", chan_ident, pid_p, pid_i, pid_d, pid_d_filter_cut, pid_d_filter_on
    )
    return _pack(0x0690, dest, source, data=data)


def pz_req_ppc_pidconsts(dest: int, source: int, chan_ident: int):
    return _pack(0x0691, dest, source, param1=chan_ident)


def pz_set_ppc_notchparams(
    dest: int,
    source: int,
    chan_ident: int,
    filter_no: int,
    filter1_center: int,
    filter1_q: int,
    notch_filter_1_on: int,
    filter2_center: int,
    filter2_q: int,
    notch_filter_2_on: int,
) -> bytes:
    data = struct.pack(
        "<HHHHHHHH",
        chan_ident,
        filter_no,
        filter1_center,
        filter1_q,
        notch_filter_1_on,
        filter2_center,
        filter2_q,
        notch_filter_2_on,
    )
    return _pack(0x0693, dest, source, data=data)


def pz_req_ppc_notchparams(dest: int, source: int, chan_ident: int):
    return _pack(0x0694, dest, source, param1=chan_ident)


def pz_set_ppc_iosettings(
    dest: int,
    source: int,
    chan_ident: int,
    control_src: int,
    monitor_out_sig: int,
    monitor_out_bandwidth: int,
    feedback_src: int,
    fp_brightness: int,
) -> bytes:
    data = struct.pack(
        "<HHHHHHH",
        chan_ident,
        control_src,
        monitor_out_sig,
        monitor_out_bandwidth,
        feedback_src,
        fp_brightness,
        0,
    )
    return _pack(0x0696, dest, source, data=data)


def pz_req_ppc_iosettings(dest: int, source: int, chan_ident: int):
    return _pack(0x0697, dest, source, param1=chan_ident)


def pz_set_outputlut(
    dest: int, source: int, chan_ident: int, index: int, output: int
) -> bytes:
    data = struct.pack("<HHh", chan_ident, index, output)
    return _pack(0x0700, dest, source, data=data)


def pz_req_outputlut(dest: int, source: int, chan_ident: int):
    return _pack(0x0701, dest, source, param1=chan_ident)


def pz_set_outputlutparams(
    dest: int,
    source: int,
    chan_ident: int,
    mode: int,
    cycle_length: int,
    num_cycles: int,
    delay_time: int,
    pre_cycle_rest: int,
    post_cycle_rest: int,
    output_trig_start: int,
    output_trig_width: int,
    trig_rep_cycle: int,
) -> bytes:
    data = struct.pack(
        "<HHHLLLLHLH",
        chan_ident,
        mode,
        cycle_length,
        num_cycles,
        delay_time,
        pre_cycle_rest,
        post_cycle_rest,
        output_trig_start,
        output_trig_width,
        trig_rep_cycle,
    )
    return _pack(0x0703, dest, source, data=data)


def pz_req_outputlutparams(dest: int, source: int, chan_ident: int):
    return _pack(0x0704, dest, source, param1=chan_ident)


def pz_start_lutoutput(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x0706, dest, source, param1=chan_ident)


def pz_stop_lutoutput(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x707, dest, source, param1=chan_ident)


def pz_set_eepromparams(dest: int, source: int, chan_ident: int, msg_id: int) -> bytes:
    data = struct.pack("<HH", chan_ident, msg_id)
    return _pack(0x07D0, dest, source, data=data)


def pz_set_tpz_dispsettings(dest: int, source: int, disp_intensity: int) -> bytes:
    data = struct.pack("<H", disp_intensity)
    return _pack(0x07D1, dest, source, data=data)


def pz_req_tpz_dispsettings(dest: int, source: int):
    return _pack(0x07D2, dest, source)


def pz_set_tpz_iosettings(
    dest: int, source: int, chan_ident: int, voltage_limit: int, hub_analog_input: int
) -> bytes:
    data = struct.pack("<HHHHH", chan_ident, voltage_limit, hub_analog_input, 0, 0)
    return _pack(0x07D4, dest, source, data=data)


def pz_req_tpz_iosettings(dest: int, source: int, chan_ident: int):
    return _pack(0x07D5, dest, source, param1=chan_ident)


def pz_set_zero(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x0658, dest, source, param1=chan_ident)


def pz_req_maxtravel(dest: int, source: int, chan_ident: int):
    return _pack(0x0650, dest, source, param1=chan_ident)


def pz_set_iosettings(
    dest: int,
    source: int,
    chan_ident: int,
    amp_current_limit: int,
    amp_lowpass_filter: int,
    feedback_sig: int,
    bnc_trig_or_lv_output: int,
) -> bytes:
    data = struct.pack(
        "<HHHHH",
        chan_ident,
        amp_current_limit,
        amp_lowpass_filter,
        feedback_sig,
        bnc_trig_or_lv_output,
    )
    return _pack(0x0670, dest, source, data=data)


def pz_req_iosettings(dest: int, source: int, chan_ident: int):
    return _pack(0x0671, dest, source, param1=chan_ident)


def pz_set_outputmaxvolts(
    dest: int, source: int, chan_ident: int, voltage: int
) -> bytes:
    data = struct.pack("<HHH", chan_ident, voltage, 0)
    return _pack(0x0680, dest, source, data=data)


def pz_req_outputmaxvolts(dest: int, source: int, chan_ident: int):
    return _pack(0x0681, dest, source, param1=chan_ident)


def pz_set_tpz_slewrates(
    dest: int, source: int, chan_ident: int, slew_open: int, slew_closed: int
) -> bytes:
    data = struct.pack("<HHH", chan_ident, slew_open, slew_closed)
    return _pack(0x0683, dest, source, data=data)


def pz_req_tpz_slewrates(dest: int, source: int, chan_ident: int):
    return _pack(0x0684, dest, source, param1=chan_ident)


def pz_set_lutvaluetype(dest: int, source: int, lut_type: int) -> bytes:
    return _pack(0x0708, dest, source, param1=lut_type)


def kpz_set_kcubemmiparams(
    dest: int,
    source: int,
    js_mode: int,
    js_volt_gearbox: int,
    js_volt_step: int,
    dir_sense: int,
    preset_volt1: int,
    preset_volt2: int,
    disp_brightness: int,
    disp_timeout: int,
    disp_dim_level: int,
) -> bytes:
    data = struct.pack(
        "<HHHLHLLHHH",
        1,
        js_mode,
        js_volt_gearbox,
        js_volt_step,
        dir_sense,
        preset_volt1,
        preset_volt2,
        disp_brightness,
        disp_timeout,
        disp_dim_level,
        0,
        0,
        0,
        0,
    )
    return _pack(0x07F0, dest, source, data=data)


def kpz_req_kcubemmiparams(dest: int, source: int):
    return _pack(0x07F1, dest, source)


def pz_set_tsg_iosettings(
    dest: int,
    source: int,
    hub_analog_output: int,
    display_mode: int,
    force_calibration: int,
) -> bytes:
    data = struct.pack(
        "<HHHHHH", 1, hub_analog_output, display_mode, force_calibration, 0, 0
    )
    return _pack(0x07DA, dest, source, data=data)


def pz_req_tsg_iosettings(dest: int, source: int):
    return _pack(0x07DB, dest, source)


def kpz_set_kcubetrigioconfig(
    dest: int,
    source: int,
    trig1_mode: int,
    trig1_polarity: int,
    trig2_mode: int,
    trig2_polarity: int,
) -> bytes:
    data = struct.pack(
        "<HHHHHH", 1, trig1_mode, trig1_polarity, trig2_mode, trig2_polarity, 0
    )
    return _pack(0x07F3, dest, source, data=data)


def kpz_req_kcubetrigioconfig(dest: int, source: int):
    return _pack(0x07F4, dest, source)


def pz_set_tsg_reading(
    dest: int, source: int, chan_ident: int, reading: int, smoothed: int
) -> bytes:
    data = struct.pack("<Hhh", chan_ident, reading, smoothed)
    return _pack(0x07DD, dest, source, data=data)


def pz_req_tsg_reading(dest: int, source: int, chan_ident: int):
    return _pack(0x07DE, dest, source, param1=chan_ident)


def ksg_set_kcubemmiparams(
    dest: int,
    source: int,
    chan_ident: int,
    disp_intensity: int,
    disp_timeout: int,
    disp_dim_level: int,
) -> bytes:
    data = struct.pack(
        "<HHHH", chan_ident, disp_intensity, disp_timeout, disp_dim_level
    )
    return _pack(0x07F6, dest, source, data=data)


def ksg_req_kcubemmiparams(dest: int, source: int, chan_ident: int):
    return _pack(0x07F7, dest, source, param1=chan_ident)


def ksg_set_kcubetrigioconfig(
    dest: int,
    source: int,
    trig1_mode: int,
    trig1_polarity: int,
    trig2_mode: int,
    trig2_polarity: int,
    lower_lim: int,
    upper_lim: int,
    smoothing_samples: int,
) -> bytes:
    data = struct.pack(
        "<HHHHHllHH",
        1,
        trig1_mode,
        trig1_polarity,
        trig2_mode,
        trig2_polarity,
        lower_lim,
        upper_lim,
        smoothing_samples,
        0,
    )
    return _pack(0x07F9, dest, source, data=data)


def ksg_req_kcubetrigioconfig(dest: int, source: int):
    return _pack(0x07FA, dest, source)


def pz_set_ntmode(dest: int, source: int, state: int) -> bytes:
    return _pack(0x0603, dest, source, param1=state)


def pz_req_ntmode(dest: int, source: int):
    return _pack(0x0604, dest, source)


def pz_set_nttrackthreshold(
    dest: int, source: int, threshold_abs_reading: int
) -> bytes:
    data = struct.pack("<f", threshold_abs_reading)
    return _pack(0x0606, dest, source, data=data)


def pz_req_nttrackthreshold(dest: int, source: int):
    return _pack(0x0607, dest, source)


def pz_set_ntcirchomepos(
    dest: int, source: int, circ_home_pos_a: int, circ_home_pos_b: int
) -> bytes:
    data = struct.pack("<HH", circ_home_pos_a, circ_home_pos_b)
    return _pack(0x0609, dest, source, data=data)


def pz_req_ntcirchomepos(dest: int, source: int):
    return _pack(0x0610, dest, source)


def pz_move_ntcirctohomepos(dest: int, source: int):
    return _pack(0x0612, dest, source)


def pz_req_ntcirccentrepos(dest: int, source: int):
    return _pack(0x0613, dest, source)


def pz_set_ntcircparams(
    dest: int,
    source: int,
    circ_dia_mode: int,
    circ_dia_sw: int,
    circ_osc_freq: int,
    abs_pwr_min_circ_dia: int,
    abs_pwr_max_circ_dia: int,
    abs_pwr_adjust_type: int,
) -> bytes:
    data = struct.pack(
        "<HHHHHH",
        circ_dia_mode,
        circ_dia_sw,
        circ_osc_freq,
        abs_pwr_min_circ_dia,
        abs_pwr_max_circ_dia,
        abs_pwr_adjust_type,
    )
    return _pack(0x0618, dest, source, data=data)


def pz_req_ntcircparams(dest: int, source: int):
    return _pack(0x0619, dest, source)


def pz_set_ntcircdia(dest: int, source: int, circ_dia: int) -> bytes:
    return _pack(0x061A, dest, source, param1=circ_dia)


def pz_set_ntcircdialut(dest: int, source: int, lut_val: Sequence[int]) -> bytes:
    data = struct.pack("<16H", lut_val)
    return _pack(0x0621, dest, source, data=data)


def pz_req_ntcircdialut(dest: int, source: int):
    return _pack(0x0622, dest, source)


def pz_set_ntphasecompparams(
    dest: int,
    source: int,
    phase_comp_mode: int,
    phase_comp_asw: int,
    phase_comp_bsw: int,
) -> bytes:
    data = struct.pack("<Hhh", phase_comp_mode, phase_comp_asw, phase_comp_bsw)
    return _pack(0x0626, dest, source, data=data)


def pz_req_ntphasecompparams(dest: int, source: int):
    return _pack(0x0627, dest, source)


def pz_set_nttiarangeparams(
    dest: int,
    source: int,
    range_mode: int,
    range_up_limit: int,
    range_down_limit: int,
    settle_sample: int,
    range_change_type: int,
    range_sw: int,
) -> bytes:
    data = struct.pack(
        "<HhhhHH",
        range_mode,
        range_up_limit,
        range_down_limit,
        settle_sample,
        range_change_type,
        range_sw,
    )
    return _pack(0x0630, dest, source, data=data)


def pz_req_nttiarangeparams(dest: int, source: int):
    return _pack(0x0631, dest, source)


def pz_set_ntgainparams(
    dest: int, source: int, gain_ctrl_mode: int, nt_gain_sw: int
) -> bytes:
    data = struct.pack("<Hh", gain_ctrl_mode, nt_gain_sw)
    return _pack(0x0633, dest, source, data=data)


def pz_req_ntgainparams(dest: int, source: int):
    return _pack(0x0634, dest, source)


def pz_set_nttiapfilterparams(dest: int, source: int, param_1: int) -> bytes:
    data = struct.pack("<5l", param_1, 0, 0, 0, 0)
    return _pack(0x0636, dest, source, data=data)


def pz_req_nttiapfilterparams(dest: int, source: int):
    return _pack(0x0637, dest, source)


def pz_req_nttiareading(dest: int, source: int):
    return _pack(0x0639, dest, source)


def pz_set_ntfeedbacksrc(dest: int, source: int, feedback_src: int) -> bytes:
    return _pack(0x063B, dest, source, param1=feedback_src)


def pz_req_ntfeedbacksrc(dest: int, source: int):
    return _pack(0x063C, dest, source)


def pz_req_ntstatusbits(dest: int, source: int):
    return _pack(0x063E, dest, source)


def pz_req_ntstatusupdate(dest: int, source: int):
    return _pack(0x0664, dest, source)


def pz_ack_ntstatusbits(dest: int, source: int):
    return _pack(0x0666, dest, source)


def kna_set_nttialpfiltercoeefs(dest: int, source: int, param_1: int) -> bytes:
    data = struct.pack("<5l", param_1, 0, 0, 0, 0)
    return _pack(0x0687, dest, source, data=data)


def kna_req_nttialpfiltercoeefs(dest: int, source: int):
    return _pack(0x0688, dest, source)


def kna_set_kcubemmiparams(
    dest: int, source: int, wheel_step: int, disp_brightness: int
) -> bytes:
    data = struct.pack("<HH6H", wheel_step, disp_brightness, 0, 0, 0, 0, 0, 0)
    return _pack(0x068A, dest, source, data=data)


def kna_req_kcubemmiparams(dest: int, source: int):
    return _pack(0x068B, dest, source)


def kna_set_kcubetrigioconfig(
    dest: int,
    source: int,
    t1_mode: int,
    t1_polarity: int,
    t2_mode: int,
    t2_polarity: int,
) -> bytes:
    data = struct.pack(
        "<10H", t1_mode, t1_polarity, 0, t2_mode, t2_polarity, 0, 0, 0, 0, 0
    )
    return _pack(0x068D, dest, source, data=data)


def kna_req_kcubetrigioconfig(dest: int, source: int):
    return _pack(0x068E, dest, source)


def kna_req_xyscan(dest: int, source: int):
    return _pack(0x06A0, dest, source)


def kna_stop_xyscan(dest: int, source: int):
    return _pack(0x06A2, dest, source)


def nt_set_eepromparams(dest: int, source: int, chan_ident: int, msg_id: int) -> bytes:
    data = struct.pack("<HH", chan_ident, msg_id)
    return _pack(0x07E7, dest, source, data=data)


def nt_set_tna_dispsettings(dest: int, source: int, disp_intensity: int) -> bytes:
    data = struct.pack("<H", disp_intensity)
    return _pack(0x07E8, dest, source, data=data)


def nt_req_tna_dispsettings(dest: int, source: int):
    return _pack(0x07E9, dest, source)


def nt_set_tnaiosettings(
    dest: int,
    source: int,
    lv_out_range: int,
    lv_out_route: int,
    hv_out_range: int,
    sign_io_route: int,
) -> bytes:
    data = struct.pack("<HHHH", lv_out_range, lv_out_route, hv_out_range, sign_io_route)
    return _pack(0x07EB, dest, source, data=data)


def nt_req_tnaiosettings(dest: int, source: int):
    return _pack(0x07EC, dest, source)


def la_set_power_setpoint(dest: int, source: int, setpoint: int) -> bytes:
    data = struct.pack("<HH", 1, setpoint)
    return _pack(0x0800, dest, source, data=data)


def la_req_power_setpoint(dest: int, source: int):
    return _pack(0x0801, dest, source, param1=1)


def la_req_laser_current_and_power(dest: int, source: int):
    return _pack(0x0801, dest, source, param1=3)


def la_req_laser_current_and_power_tld110(dest: int, source: int):
    return _pack(0x0801, dest, source, param1=4)


def la_set_laser_control_source(dest: int, source: int, laser_source: int) -> bytes:
    data = struct.pack("<HH", 5, laser_source)
    return _pack(0x0800, dest, source, data=data)


def la_req_laser_control_source(dest: int, source: int):
    return _pack(0x0801, dest, source, param1=5)


def la_req_lastatusbits(dest: int, source: int):
    return _pack(0x0801, dest, source, param1=7)


def la_req_max_limits(dest: int, source: int):
    return _pack(0x0801, dest, source, param1=9)


def la_req_max_diode_current(dest: int, source: int):
    return _pack(0x0801, dest, source, param1=10)


def la_set_display_settings(
    dest: int, source: int, intensity: int, units: int
) -> bytes:
    data = struct.pack("<HHHH", 11, intensity, units, 0)
    return _pack(0x0800, dest, source, data=data)


def la_req_display_settings(dest: int, source: int):
    return _pack(0x0801, dest, source, param1=11)


def la_set_misc_params(
    dest: int, source: int, calib_factor: float, polarity: int, ramp_up: int
) -> bytes:
    data = struct.pack("<HfHH", 13, calib_factor, polarity, ramp_up)
    return _pack(0x0800, dest, source, data=data)


def la_req_misc_params(dest: int, source: int):
    return _pack(0x0801, dest, source, param1=13)


def la_set_mmi_params(dest: int, source: int, disp_intensity: int) -> bytes:
    data = struct.pack("<HHHHH", 14, disp_intensity, 0, 0, 0, 0)
    return _pack(0x0800, dest, source, data=data)


def la_req_mmi_params(dest: int, source: int):
    return _pack(0x0801, dest, source, param1=14)


def la_set_klddigoutputs(dest: int, source: int, dig_outputs: int) -> bytes:
    data = struct.pack("<HHH", 14, dig_outputs, 0)
    return _pack(0x0800, dest, source, data=data)


def la_req_klddigoutputs(dest: int, source: int):
    return _pack(0x0801, dest, source, param1=17)


def la_set_eepromparams(dest: int, source: int, msgid: int) -> bytes:
    data = struct.pack("<H", msgid)
    return _pack(0x0810, dest, source, data=data)


def la_enableoutput(dest: int, source: int):
    return _pack(0x0811, dest, source)


def la_disableoutput(dest: int, source: int):
    return _pack(0x0812, dest, source)


def la_openloop(dest: int, source: int):
    return _pack(0x0813, dest, source)


def la_closedloop(dest: int, source: int):
    return _pack(0x0814, dest, source)


def ld_maxcurrentadjust(
    dest: int, source: int, enable_adjustment: int, allow_with_diode: int
):
    return _pack(
        0x0816, dest, source, param1=enable_adjustment, param2=allow_with_diode
    )


def ld_set_maxcurrentdigpot(dest: int, source: int, max_current: int) -> bytes:
    return _pack(0x0817, dest, source, param1=max_current)


def ld_req_maxcurrentdigpot(dest: int, source: int):
    return _pack(0x0818, dest, source)


def ld_findtiaagain(dest: int, source: int):
    return _pack(0x081A, dest, source)


def ld_tiagainadjust(dest: int, source: int, enable: int) -> bytes:
    return _pack(0x081B, dest, source, param1=enable)


def la_req_statusupdate(dest: int, source: int):
    return _pack(0x0820, dest, source)


def la_ack_statusupdate(dest: int, source: int):
    return _pack(0x0822, dest, source)


def ld_ack_statusupdate(dest: int, source: int):
    return _pack(0x0827, dest, source)


def la_set_kcubetrigconfig(
    dest: int,
    source: int,
    trig1_mode: int,
    trig1_polarity: int,
    trig2_mode: int,
    trig2_polarity: int,
) -> bytes:
    data = struct.pack(
        "<HHHHHHH", 1, trig1_mode, trig1_polarity, 0, trig2_mode, trig2_polarity, 0
    )
    return _pack(0x082A, dest, source, data=data)


def la_req_kcubetrigconfig(dest: int, source: int):
    return _pack(0x082B, dest, source)


def quad_set_loopparams(
    dest: int, source: int, pGain: int, iGain: int, dGain: int
) -> bytes:
    data = struct.pack("<HHHH", 1, pGain, iGain, dGain)
    return _pack(0x0870, dest, source, data=data)


def quad_req_loopparams(dest: int, source: int):
    return _pack(0x0871, dest, source, param1=1)


def quad_req_readings(dest: int, source: int):
    return _pack(0x0871, dest, source, param1=3)


def quad_set_posdemandparams(
    dest: int,
    source: int,
    x_pos_dem_min: int,
    y_pos_dem_min: int,
    x_pos_dem_max: int,
    y_pos_dem_max: int,
    lv_out_route: int,
    ol_pos_dem: int,
    x_pos_fb_sense: int,
    y_pos_fb_sense: int,
) -> bytes:
    data = struct.pack(
        "<HhhhhHHhh",
        5,
        x_pos_dem_min,
        y_pos_dem_min,
        x_pos_dem_max,
        y_pos_dem_max,
        lv_out_route,
        ol_pos_dem,
        x_pos_fb_sense,
        y_pos_fb_sense,
    )
    return _pack(0x0870, dest, source, data=data)


def quad_req_posdemandparams(dest: int, source: int):
    return _pack(0x0871, dest, source, param1=5)


def quad_set_opermode(dest: int, source: int, mode: int) -> bytes:
    data = struct.pack("<HH", 7, mode)
    return _pack(0x0870, dest, source, data=data)


def quad_req_opermode(dest: int, source: int):
    return _pack(0x0871, dest, source, param1=7)


def quad_set_dispsettings(
    dest: int, source: int, disp_intensity: int, disp_mode: int, disp_dim_timeout: int
) -> bytes:
    data = struct.pack("<HHHH", 8, disp_intensity, disp_mode, disp_dim_timeout)
    return _pack(0x0870, dest, source, data=data)


def quad_req_dispsettings(dest: int, source: int):
    return _pack(0x0871, dest, source, param1=8)


def quad_set_positionoutputs(dest: int, source: int, x_pos: int, y_pos: int) -> bytes:
    data = struct.pack("<Hhh", 0xD, x_pos, y_pos)
    return _pack(0x0870, dest, source, data=data)


def quad_req_positionoutputs(dest: int, source: int):
    return _pack(0x0871, dest, source, param1=0xD)


def quad_set_loopparams2(
    dest: int,
    source: int,
    p: int,
    i: int,
    d: int,
    low_pass_cutoff: int,
    notch_center: int,
    filter_q: int,
    notch_filter_on: int,
    deriv_filter_on: int,
) -> bytes:
    data = struct.pack(
        "<HffffffHH",
        0xE,
        p,
        i,
        d,
        low_pass_cutoff,
        notch_center,
        filter_q,
        notch_filter_on,
        deriv_filter_on,
    )
    return _pack(0x0870, dest, source, data=data)


def quad_req_loopparams2(dest: int, source: int):
    return _pack(0x0871, dest, source, param1=0xE)


def quad_set_kpatrigioconfig(
    dest: int,
    source: int,
    trig1_mode: int,
    trig1_polarity: int,
    trig1_sum_min: int,
    trig1_sum_max: int,
    trig1_diff_threshold: int,
    trig2_mode: int,
    trig2_polarity: int,
    trig2_sum_min: int,
    trig2_sum_max: int,
    trig2_diff_threshold: int,
) -> bytes:
    data = struct.pack(
        "<12H",
        0xF,
        trig1_mode,
        trig1_polarity,
        trig1_sum_min,
        trig1_sum_max,
        trig1_diff_threshold,
        trig2_mode,
        trig2_polarity,
        trig2_sum_min,
        trig2_sum_max,
        trig2_diff_threshold,
        0,
    )
    return _pack(0x0870, dest, source, data=data)


def quad_req_kpatrigioconfig(dest: int, source: int):
    return _pack(0x0871, dest, source, param1=0xF)


def quad_set_kpadigoutputs(dest: int, source: int, dig_outs: int) -> bytes:
    data = struct.pack("<HHH", 0xA, dig_outs, 0)
    return _pack(0x0870, dest, source, data=data)


def quad_req_kpadigoutputs(dest: int, source: int):
    return _pack(0x0871, dest, source, param1=0xA)


def quad_req_statusupdate(dest: int, source: int):
    return _pack(0x0880, dest, source)


def quad_ack_statusupdate(dest: int, source: int):
    return _pack(0x0882, dest, source)


def quad_set_eepromparams(dest: int, source: int, msgid: int) -> bytes:
    data = struct.pack("<H", msgid)
    return _pack(0x0875, dest, source, data=data)


def tec_set_tempsetpoint(dest: int, source: int, temp_set: int) -> bytes:
    data = struct.pack("<HH", 1, temp_set)
    return _pack(0x0840, dest, source, data=data)


def tec_req_tempsetpoint(dest: int, source: int):
    return _pack(0x0841, dest, source, param1=1)


def tec_req_readings(dest: int, source: int):
    return _pack(0x0841, dest, source, param1=3)


def tec_set_iosettings(
    dest: int, source: int, sensor: int, current_limit: int
) -> bytes:
    data = struct.pack("<HHh", 5, sensor, current_limit)
    return _pack(0x0840, dest, source, data=data)


def tec_req_iosettings(dest: int, source: int):
    return _pack(0x0841, dest, source, param1=5)


def tec_req_statusbits(dest: int, source: int):
    return _pack(0x0841, dest, source, param1=7)


def tec_set_loopparams(dest: int, source: int, p: int, i: int, d: int) -> bytes:
    data = struct.pack("<HHHH", 9, p, i, d)
    return _pack(0x0840, dest, source, data=data)


def tec_req_loopparams(dest: int, source: int):
    return _pack(0x0841, dest, source, param1=9)


def tec_set_disp_settings(
    dest: int, source: int, disp_intensity: int, disp_mode: int
) -> bytes:
    data = struct.pack("<HHHH", 0xB, disp_intensity, disp_mode, 0)
    return _pack(0x0840, dest, source, data=data)


def tec_req_disp_settings(dest: int, source: int):
    return _pack(0x0841, dest, source, param1=0xB)


def tec_set_eepromparams(
    dest: int,
    source: int,
) -> bytes:
    data = struct.pack("<H", 0)
    return _pack(0x0850, dest, source, data=data)


def tec_req_statusupdate(dest: int, source: int):
    return _pack(0x0860, dest, source)


def tec_ack_statusupdate(dest: int, source: int):
    return _pack(0x0862, dest, source)


def pzmot_set_poscounts(
    dest: int, source: int, chan_ident: int, position: int
) -> bytes:
    data = struct.pack("<HHll", 5, chan_ident, position, 0)
    return _pack(0x0850, dest, source, data=data)


def pzmot_req_poscounts(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x0851, dest, source, param1=5, param2=chan_ident)


def pzmot_set_driveopparams(
    dest: int,
    source: int,
    chan_ident: int,
    max_voltage: int,
    step_rate: int,
    step_accn: int,
) -> bytes:
    data = struct.pack("<HHHll", 7, chan_ident, max_voltage, step_rate, step_accn)
    return _pack(0x08C0, dest, source, data=data)


def pzmot_req_driveopparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x08C1, dest, source, param1=7, param2=chan_ident)


def tim_set_jogparams(
    dest: int,
    source: int,
    chan_ident: int,
    jog_mode: int,
    jog_step_size: int,
    jog_step_rate: int,
    jog_step_accn: int,
) -> bytes:
    data = struct.pack(
        "<HHHlll", 9, chan_ident, jog_mode, jog_step_size, jog_step_rate, jog_step_accn
    )
    return _pack(0x08C0, dest, source, data=data)


def tim_req_jogparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x08C1, dest, source, param1=9, param2=chan_ident)


def tim_set_potparams(
    dest: int, source: int, chan_ident: int, max_step_rate: int
) -> bytes:
    data = struct.pack("<HHl", 0x11, chan_ident, max_step_rate)
    return _pack(0x08C0, dest, source, data=data)


def tim_req_potparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x08C1, dest, source, param1=0x11, param2=chan_ident)


def tim_set_buttonparams(
    dest: int, source: int, chan_ident: int, mode: int, position1: int, position2: int
) -> bytes:
    data = struct.pack("<HHHllHH", 0x13, chan_ident, mode, position1, position2, 0, 0)
    return _pack(0x08C0, dest, source, data=data)


def tim_req_buttonparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x08C1, dest, source, param1=0x13, param2=chan_ident)


def pzmot_set_limswitchparams(
    dest: int, source: int, chan_ident: int, fwd_hard_limit: int, rev_hard_limit: int
) -> bytes:
    data = struct.pack("<HHHHH", 0xB, chan_ident, fwd_hard_limit, rev_hard_limit, 0)
    return _pack(0x08C0, dest, source, data=data)


def pzmot_req_limswitchparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x08C1, dest, source, param1=0xB, param2=chan_ident)


def pzmot_set_homeparams(
    dest: int,
    source: int,
    chan_ident: int,
    home_direction: int,
    home_lim_switch: int,
    home_step_rate: int,
    home_offset_dist: int,
) -> bytes:
    data = struct.pack(
        "<HHHHLl",
        0xF,
        chan_ident,
        home_direction,
        home_lim_switch,
        home_step_rate,
        home_offset_dist,
    )
    return _pack(0x08C0, dest, source, data=data)


def pzmot_req_homeparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x08C1, dest, source, param1=0xF, param2=chan_ident)


def pzmot_set_kcubemmiparams(
    dest: int,
    source: int,
    chan_ident: int,
    js_mode: int,
    js_max_step_rate: int,
    js_dir_sense: int,
    preset_pos1: int,
    preset_pos2: int,
    disp_brightness: int,
) -> bytes:
    data = struct.pack(
        "<HHHlHllHH",
        0x15,
        chan_ident,
        js_mode,
        js_max_step_rate,
        js_dir_sense,
        preset_pos1,
        preset_pos2,
        disp_brightness,
        0,
    )
    return _pack(0x08C0, dest, source, data=data)


def pzmot_req_kcubemmiparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x08C1, dest, source, param1=0x15, param2=chan_ident)


def pzmot_set_kcubetrigioconfig(
    dest: int,
    source: int,
    trig_channel1: int,
    trig_channel2: int,
    trig1_mode: int,
    trig1_polarity: int,
    trig2_mode: int,
    trig2_polarity: int,
) -> bytes:
    data = struct.pack(
        "<13H",
        0x17,
        trig_channel1,
        trig_channel2,
        trig1_mode,
        trig1_polarity,
        trig2_mode,
        trig2_polarity,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    return _pack(0x08C0, dest, source, data=data)


def pzmot_req_kcubetrigioconfig(dest: int, source: int):
    return _pack(0x08C1, dest, source, param1=0x17)


def pzmot_set_kcubetrigparams(
    dest: int,
    source: int,
    chan_ident: int,
    start_pos_fwd: int,
    interval_fwd: int,
    num_pulses_fwd: int,
    start_pos_reverse: int,
    interval_rev: int,
    num_pulses_rev: int,
    pulse_width: int,
    num_cycles: int,
) -> bytes:
    data = struct.pack(
        "<HHllllllll",
        0x19,
        chan_ident,
        start_pos_fwd,
        interval_fwd,
        num_pulses_fwd,
        start_pos_reverse,
        interval_rev,
        num_pulses_rev,
        pulse_width,
        num_cycles,
    )
    return _pack(0x08C0, dest, source, data=data)


def pzmot_req_kcubetrigparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x08C1, dest, source, param1=0x19, param2=chan_ident)


def pzmot_set_kcubechanenablemode(dest: int, source: int, mode: int) -> bytes:
    data = struct.pack("<HH", 0x2B, mode)
    return _pack(0x08C0, dest, source, data=data)


def pzmot_req_kcubechanenablemode(dest: int, source: int):
    return _pack(0x08C1, dest, source, param1=0x2B)


def pzmot_set_kcubejogparams(
    dest: int,
    source: int,
    chan_ident: int,
    jog_mode: int,
    jog_step_size_fwd: int,
    jog_step_size_rev: int,
    jog_step_rate: int,
    jog_step_accn: int,
) -> bytes:
    data = struct.pack(
        "<HHHllll",
        0x2D,
        chan_ident,
        jog_mode,
        jog_step_size_fwd,
        jog_step_size_rev,
        jog_step_rate,
        jog_step_accn,
    )
    return _pack(0x08C0, dest, source, data=data)


def pzmot_req_kcubejogparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x08C1, dest, source, param1=0x2D, param2=chan_ident)


def pzmot_set_kcubefeedbacksigparams(
    dest: int, source: int, chan_ident: int, fb_signal_mode: int, encoder_const: int
) -> bytes:
    data = struct.pack("<HHHl", 0x30, chan_ident, fb_signal_mode, encoder_const)
    return _pack(0x08C0, dest, source, data=data)


def pzmot_req_kcubefeedbacksigparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x08C1, dest, source, param1=0x30, param2=chan_ident)


def pzmot_set_kcubemoverelativeparams(
    dest: int, source: int, chan_ident: int, rel_distance: int
) -> bytes:
    data = struct.pack("<HHl", 0x32, chan_ident, rel_distance)
    return _pack(0x08C0, dest, source, data=data)


def pzmot_req_kcubemoverelativeparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x08C1, dest, source, param1=0x32, param2=chan_ident)


def pzmot_req_kcubemoveabsoluteparams(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x08C1, dest, source, param1=0x34, param2=chan_ident)


def pzmot_set_kcubemoveabsoluteparams(
    dest: int, source: int, chan_ident: int, rel_distance: int
) -> bytes:
    data = struct.pack("<HHl", 0x34, chan_ident, rel_distance)
    return _pack(0x08C0, dest, source, data=data)


def pzmot_move_absolute(
    dest: int, source: int, chan_ident: int, abs_position: int
) -> bytes:
    data = struct.pack("<Hl", chan_ident, abs_position)
    return _pack(0x08D4, dest, source, data=data)


def pzmot_move_jog(dest: int, source: int, chan_ident: int, jog_dir: int) -> bytes:
    return _pack(0x08D9, dest, source, param1=chan_ident, param2=jog_dir)


def pzmot_req_statusupdate(dest: int, source: int, chan_ident: int) -> bytes:
    return _pack(0x08E0, dest, source, param1=chan_ident)


def pzmot_ack_statusupdate(dest: int, source: int) -> bytes:
    return _pack(0x08E2, dest, source)


def pol_set_params(
    dest: int,
    source: int,
    velocity: int,
    home_position: int,
    jog_step1: int,
    jog_step2: int,
    jog_step3: int,
) -> bytes:
    data = struct.pack(
        "<HHHHHH", 0, velocity, home_position, jog_step1, jog_step2, jog_step3
    )
    return _pack(0x0530, dest, source, data=data)


def pol_req_params(dest: int, source: int):
    return _pack(0x0531, dest, source)
