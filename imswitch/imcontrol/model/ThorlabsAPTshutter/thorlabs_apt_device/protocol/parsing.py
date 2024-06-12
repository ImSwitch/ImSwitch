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

import struct
import functools
from typing import Dict, Any

id_to_func = {}
HEADER_SIZE = 6


def parser(msgid):
    def wrapper(func):
        @functools.wraps(func)
        def inner(data: bytes) -> Dict[str, Any]:
            msgid_read, _, dest, source = struct.unpack_from("<HHBB", data)
            dest = dest & ~0x80
            assert msgid == msgid_read
            ret = {"msg": func.__name__, "msgid": msgid, "dest": dest, "source": source}
            ret.update(func(data))
            return ret

        if msgid in id_to_func:
            raise ValueError(f"Duplicate msgid: {hex(msgid)}")
        id_to_func[msgid] = inner
        return inner

    return wrapper


def _parse_dcstatus(data: bytes) -> Dict[str, Any]:
    # I believe the documentation is wrong and velocity is encoded as a "short" and not a "word"
    # (A stage moving in reverse should return a negative velocity, not a very large positive one!)
    chan_ident, position, velocity, _, status_bits = struct.unpack_from(
        "<HlhHL", data, HEADER_SIZE
    )
    ret = {
        "chan_ident": chan_ident,
        "position": position,
        "velocity": velocity,
    }
    ret.update(_parse_status_bits(status_bits))
    return ret


def _parse_status(data: bytes) -> Dict[str, Any]:
    chan_ident, position, enc_count, status_bits = struct.unpack_from(
        "<HllL", data, HEADER_SIZE
    )
    ret = {
        "chan_ident": chan_ident,
        "position": position,
        "enc_count": enc_count,
    }
    ret.update(_parse_status_bits(status_bits))
    return ret


def _parse_status_bits(status_bits: int) -> Dict[str, Any]:
    # Bitfield
    return {
        "forward_limit_switch": bool(status_bits & 0x1),
        "reverse_limit_switch": bool(status_bits & 0x2),
        "forward_limit_soft": bool(status_bits & 0x4),
        "reverse_limit_soft": bool(status_bits & 0x8),
        "moving_forward": bool(status_bits & 0x10),
        "moving_reverse": bool(status_bits & 0x20),
        "jogging_forward": bool(status_bits & 0x40),
        "jogging_reverse": bool(status_bits & 0x80),
        "motor_connected": bool(status_bits & 0x100),
        "homing": bool(status_bits & 0x200),
        "homed": bool(status_bits & 0x400),
        "initializing": bool(status_bits & 0x800),
        "tracking": bool(status_bits & 0x1000),
        "settled": bool(status_bits & 0x2000),
        "motion_error": bool(status_bits & 0x4000),
        "instrument_error": bool(status_bits & 0x8000),
        "interlock": bool(status_bits & 0x10000),
        "overtemp": bool(status_bits & 0x20000),
        "voltage_fault": bool(status_bits & 0x40000),
        "commutation_error": bool(status_bits & 0x80000),
        "digital_in_1": bool(status_bits & 0x100000),
        "digital_in_2": bool(status_bits & 0x200000),
        "digital_in_3": bool(status_bits & 0x300000),
        "digital_in_4": bool(status_bits & 0x400000),
        "motor_current_limit_reached": bool(status_bits & 0x1000000),
        "encoder_fault": bool(status_bits & 0x2000000),
        "overcurrent": bool(status_bits & 0x4000000),
        "current_fault": bool(status_bits & 0x8000000),
        "power_ok": bool(status_bits & 0x10000000),
        "active": bool(status_bits & 0x20000000),
        "error": bool(status_bits & 0x40000000),
        "channel_enabled": bool(status_bits & 0x80000000),
    }


def _parse_pz_status_bits(status_bits: int) -> Dict[str, Any]:
    # Bitfield
    return {
        "connected": bool(status_bits & 0x1),
        "zeroed": bool(status_bits & 0x10),
        "zeroing": bool(status_bits & 0x20),
        "strain_gauge_connected": bool(status_bits & 0x100),
        "control_mode": bool(status_bits & 0x400),
        "max_75V": bool(status_bits & 0x1000),
        "max_100V": bool(status_bits & 0x2000),
        "max_150V": bool(status_bits & 0x4000),
        "dig_ins": [bool(status_bits & (1 << (21 + i))) for i in range(8)],
        "active": bool(status_bits & 0x20000000),
        "enabled": bool(status_bits & 0x80000000),
    }


def _parse_nt_status_bits(status_bits: int) -> Dict[str, Any]:
    # Bitfield
    return {
        "tracking": bool(status_bits & 0x1),
        "tracking_with_signal": bool(status_bits & 0x2),
        "tracking_channel_a": bool(status_bits & 0x4),
        "tracking_channel_b": bool(status_bits & 0x8),
        "auto_ranging": bool(status_bits & 0x10),
        "under_read": bool(status_bits & 0x20),
        "over_read": bool(status_bits & 0x40),
        "channel_a_connected": bool(status_bits & 0x10000),
        "channel_b_connected": bool(status_bits & 0x20000),
        "channel_a_enabled": bool(status_bits & 0x40000),
        "channel_b_enabled": bool(status_bits & 0x80000),
        "channel_a_ctrl_mode": bool(status_bits & 0x100000),
        "channel_b_ctrl_mode": bool(status_bits & 0x200000),
    }


def _parse_la_status_bits(status_bits: int) -> Dict[str, Any]:
    # Bitfield
    # Note, the adc on the kls101 is ignored for now
    # KFS 2021-02-19
    units = "mA" if bool(status_bits & 0x10) else ""
    units = "mW" if bool(status_bits & 0x20) else ""
    units = "dBm" if bool(status_bits & 0x40) else ""
    return {
        "output_enabled": bool(status_bits & 0x1),
        "keyswitch_enabled": bool(status_bits & 0x2),
        "control_mode": bool(status_bits & 0x4),
        "safety_interlock": bool(status_bits & 0x8),
        "units": units,
        "dig_ins": [bool(status_bits & 1 << i) for i in range(20, 22)],
        "error": bool(status_bits & 1 << 30),
    }


def _parse_ld_status_bits(status_bits: int) -> Dict[str, Any]:
    # Bitfield
    tia_range = "9uA" if bool(status_bits & 0x10) else ""
    tia_range = "100uA" if bool(status_bits & 0x20) else ""
    tia_range = "0.9mA" if bool(status_bits & 0x40) else ""
    tia_range = "10mA" if bool(status_bits & 0x80) else ""
    return {
        "output_enabled": bool(status_bits & 0x1),
        "keyswitch_enabled": bool(status_bits & 0x2),
        "control_mode": bool(status_bits & 0x4),
        "safety_interlock": bool(status_bits & 0x8),
        "tia_range": tia_range,
        "diode_polarity": bool(status_bits & 0x100),
        "external_sma_enabled": bool(status_bits & 0x200),
        "open_circuit": bool(status_bits & 0x800),
        "psu_voltages_ok": bool(status_bits & 0x1000),
        "tia_range_overlimit": bool(status_bits & 0x2000),
        "tia_range_underlimit": bool(status_bits & 0x4000),
        "signal_generator": bool(status_bits & 0x80000),
        "dig_ins": [bool(status_bits & 1 << i) for i in range(20, 22)],
        "error": bool(status_bits & 1 << 30),
        "high_stability": bool(status_bits & 1 << 31),
    }


def _parse_quad_status_bits(status_bits: int) -> Dict[str, Any]:
    # Bitfield
    return {
        "position_monitoring": bool(status_bits & 0x1),
        "open_loop": bool(status_bits & 0x2),
        "closed_loop": bool(status_bits & 0x4),
    }


def _parse_tec_status_bits(status_bits: int) -> Dict[str, Any]:
    # Bitfield
    display_mode = "temp_actual" if bool(status_bits & 0x10) else ""
    display_mode = "temp_set" if bool(status_bits & 0x20) else ""
    display_mode = "temp_delta" if bool(status_bits & 0x40) else ""
    display_mode = "current" if bool(status_bits & 0x80) else ""
    return {
        "output_enabled": bool(status_bits & 0x1),
        "display_mode": display_mode,
        "error": bool(status_bits & (0x1 << 30)),
    }


def _parse_pzmot_status_bits(status_bits: int) -> Dict[str, Any]:
    # Bitfield
    # Tracking and interlock are the same bit?
    return {
        "forward_limit_switch": bool(status_bits & 0x1),
        "reverse_limit_switch": bool(status_bits & 0x2),
        "moving_forward": bool(status_bits & 0x10),
        "moving_reverse": bool(status_bits & 0x20),
        "jogging_forward": bool(status_bits & 0x40),
        "jogging_reverse": bool(status_bits & 0x80),
        "motor_connected": bool(status_bits & 0x100),
        "homing": bool(status_bits & 0x200),
        "homed": bool(status_bits & 0x400),
        "dig_in1": bool(status_bits & 0x100000),
        "power_ok": bool(status_bits & 0x10000000),
        "active": bool(status_bits & 0x20000000),
        "error": bool(status_bits & 0x40000000),
        "channel_enabled": bool(status_bits & 0x80000000),
    }


@parser(0x0212)
def mod_get_chanenablestate(data: bytes) -> Dict[str, Any]:
    return {"chan_ident": data[2], "enabled": data[3] == 0x01}


@parser(0x0002)
def hw_disconnect(data: bytes) -> Dict[str, Any]:
    return {}


@parser(0x0080)
def hw_response(data: bytes) -> Dict[str, Any]:
    return {}


@parser(0x0081)
def hw_richresponse(data: bytes) -> Dict[str, Any]:
    msg_ident, code, notes = struct.unpack_from("<HH64s", data, HEADER_SIZE)
    return {"msg_ident": msg_ident, "code": code, "notes": notes}


@parser(0x0006)
def hw_get_info(data: bytes) -> Dict[str, Any]:
    (
        serial_number,
        model_number,
        type_,
        *firmware_version,
        _,
        _,
        hw_version,
        mod_state,
        nchs,
    ) = struct.unpack_from("<l8sH4B60sHHH", data, HEADER_SIZE)
    return {
        "serial_number": serial_number,
        "model_number": model_number,
        "type": type_,
        "firmware_version": firmware_version[::-1],
        "hw_version": hw_version,
        "mod_state": mod_state,
        "nchs": nchs,
    }


@parser(0x0061)
def rack_get_bayused(data: bytes) -> Dict[str, Any]:
    return {"bay_ident": data[2], "occupied": data[3] == 0x01}


@parser(0x0066)
def hub_get_bayused(data: bytes) -> Dict[str, Any]:
    bay_ident = data[2]
    if bay_ident == 0xFF:
        bay_ident = -1
    return {"bay_ident": bay_ident}


@parser(0x0226)
def rack_get_statusbits(data: bytes) -> Dict[str, Any]:
    # Bitfield
    (status_bits,) = struct.unpack_from("<L", data, HEADER_SIZE)
    return {
        "dig_outs": [
            bool(status_bits & 0x1),
            bool(status_bits & 0x2),
            bool(status_bits & 0x3),
            bool(status_bits & 0x4),
        ]
    }


@parser(0x0230)
def rack_get_digoutputs(data: bytes) -> Dict[str, Any]:
    # Bitfield
    return {
        "dig_outs": [
            bool(data[2] & 0x1),
            bool(data[2] & 0x2),
            bool(data[2] & 0x3),
            bool(data[2] & 0x4),
        ]
    }


@parser(0x0215)
def mod_get_digoutputs(data: bytes) -> Dict[str, Any]:
    # This differs from 0x0225 and 0x0230, as the number of outputs is not known
    # Bitfield
    return {"bits": data[2]}


@parser(0x0252)
def hw_get_kcubemmilock(data: bytes) -> Dict[str, Any]:
    return {"locked": data[3] == 0x01}


@parser(0x0412)
def mot_get_poscounter(data: bytes) -> Dict[str, Any]:
    chan_ident, position = struct.unpack_from("<Hl", data, HEADER_SIZE)
    return {"chan_ident": chan_ident, "position": position}


@parser(0x040B)
def mot_get_enccounter(data: bytes) -> Dict[str, Any]:
    chan_ident, encoder_count = struct.unpack_from("<Hl", data, HEADER_SIZE)
    return {"chan_ident": chan_ident, "encoder_count": encoder_count}


@parser(0x0415)
def mot_get_velparams(data: bytes) -> Dict[str, Any]:
    chan_ident, min_velocity, acceleration, max_velocity = struct.unpack_from(
        "<H3l", data, HEADER_SIZE
    )
    return {
        "chan_ident": chan_ident,
        "min_velocity": min_velocity,
        "acceleration": acceleration,
        "max_velocity": max_velocity,
    }


@parser(0x0418)
def mot_get_jogparams(data: bytes) -> Dict[str, Any]:
    (
        chan_ident,
        jog_mode,
        step_size,
        min_velocity,
        acceleration,
        max_velocity,
        stop_mode,
    ) = struct.unpack_from("<HH4lH", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "jog_mode": jog_mode,
        "step_size": step_size,
        "min_velocity": min_velocity,
        "acceleration": acceleration,
        "max_velocity": max_velocity,
        "stop_mode": stop_mode,
    }


@parser(0x042C)
def mot_get_adcinputs(data: bytes) -> Dict[str, Any]:
    adc_input1, adc_input2 = struct.unpack_from("<HH", data, HEADER_SIZE)
    return {
        "adc_input1": adc_input1 * 5 / 2 ** 15,
        "adc_input2": adc_input2 * 5 / 2 ** 15,
    }


@parser(0x0428)
def mot_get_powerparams(data: bytes) -> Dict[str, Any]:
    chan_ident, rest_factor, move_factor = struct.unpack_from("<3H", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "rest_factor": rest_factor,
        "move_factor": move_factor,
    }


@parser(0x043C)
def mot_get_genmoveparams(data: bytes) -> Dict[str, Any]:
    chan_ident, backlash_distance = struct.unpack_from("<Hl", data, HEADER_SIZE)
    return {"chan_ident": chan_ident, "backlash_distance": backlash_distance}


@parser(0x0447)
def mot_get_moverelparams(data: bytes) -> Dict[str, Any]:
    chan_ident, relative_distance = struct.unpack_from("<Hl", data, HEADER_SIZE)
    return {"chan_ident": chan_ident, "relative_distance": relative_distance}


@parser(0x0452)
def mot_get_moveabsparams(data: bytes) -> Dict[str, Any]:
    chan_ident, absolute_position = struct.unpack_from("<Hl", data, HEADER_SIZE)
    return {"chan_ident": chan_ident, "absolute_position": absolute_position}


@parser(0x0442)
def mot_get_homeparams(data: bytes) -> Dict[str, Any]:
    (
        chan_ident,
        home_dir,
        limit_switch,
        home_velocity,
        offset_distance,
    ) = struct.unpack_from("<3Hll", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "home_dir": home_dir,
        "limit_switch": limit_switch,
        "home_velocity": home_velocity,
        "offset_distance": offset_distance,
    }


@parser(0x0425)
def mot_get_limswitchparams(data: bytes) -> Dict[str, Any]:
    (
        chan_ident,
        cw_hardlimit,
        ccw_hardlimit,
        cw_softlimit,
        ccw_softlimit,
        soft_limit_mode,
    ) = struct.unpack_from("<3HLLH", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "cw_hardlimit": cw_hardlimit,
        "ccw_hardlimit": ccw_hardlimit,
        "cw_softlimit": cw_softlimit,
        "ccw_softlimit": ccw_softlimit,
        "soft_limit_mode": soft_limit_mode,
    }


@parser(0x0444)
def mot_move_homed(data: bytes) -> Dict[str, Any]:
    return {"chan_ident": data[2]}


@parser(0x0464)
def mot_move_completed(data: bytes) -> Dict[str, Any]:
    return _parse_dcstatus(data)


@parser(0x0466)
def mot_move_stopped(data: bytes) -> Dict[str, Any]:
    return _parse_dcstatus(data)


@parser(0x04F6)
def mot_get_bowindex(data: bytes) -> Dict[str, Any]:
    chan_ident, bow_index = struct.unpack_from("<HH", data, HEADER_SIZE)
    return {"chan_ident": chan_ident, "bow_index": bow_index}


@parser(0x04A2)
def mot_get_dcpidparams(data: bytes) -> Dict[str, Any]:
    (
        chan_ident,
        proportional,
        integral,
        differential,
        integral_limits,
        filter_control,
    ) = struct.unpack_from("<H4LH", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "proportional": proportional,
        "integral": integral,
        "differential": differential,
        "integral_limits": integral_limits,
        "filter_control": filter_control
    }


@parser(0x04B5)
def mot_get_avmodes(data: bytes) -> Dict[str, Any]:
    chan_ident, mode_bits = struct.unpack_from("<HH", data, HEADER_SIZE)
    # Bitfield
    return {"chan_ident": chan_ident, "mode_bits": mode_bits}


@parser(0x04B2)
def mot_get_potparams(data: bytes) -> Dict[str, Any]:
    chan_ident, zero_wnd, vel1, wnd1, vel2, wnd2, vel3, wnd3, vel4 = struct.unpack_from(
        "<HHlHlHlHl", data, HEADER_SIZE
    )
    return {
        "chan_ident": chan_ident,
        "zero_wnd": zero_wnd,
        "vel1": vel1,
        "wnd1": wnd1,
        "vel2": vel2,
        "wnd2": wnd2,
        "vel3": vel3,
        "wnd3": wnd3,
        "vel4": vel4,
    }


@parser(0x04B8)
def mot_get_buttonparams(data: bytes) -> Dict[str, Any]:
    chan_ident, mode, position1, position2, time_out1, time_out2 = struct.unpack_from(
        "<HHllHH", data, HEADER_SIZE
    )
    return {
        "chan_ident": chan_ident,
        "mode": mode,
        "position1": position1,
        "position2": position2,
        "time_out1": time_out1,
        "time_out2": time_out2,
    }


@parser(0x0491)
def mot_get_dcstatusupdate(data: bytes) -> Dict[str, Any]:
    return _parse_dcstatus(data)


@parser(0x04D9)
def mot_get_positionloopparams(data: bytes) -> Dict[str, Any]:
    (
        chan_ident,
        kp_pos,
        integral,
        i_lim_pos,
        differential,
        kd_time_pos,
        kout_pos,
        kaff_pos,
        pos_err_lim,
        _,
        _,
    ) = struct.unpack_from("<3HL5HL2H", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "kp_pos": kp_pos,
        "integral": integral,
        "i_lim_pos": i_lim_pos,
        "differential": differential,
        "kd_time_pos": kd_time_pos,
        "kout_pos": kout_pos,
        "kaff_pos": kaff_pos,
        "pos_err_lim": pos_err_lim,
    }


@parser(0x04DC)
def mot_get_motoroutputparams(data: bytes) -> Dict[str, Any]:
    (
        chan_ident,
        cont_current_lim,
        energy_lim,
        motor_lim,
        motor_bias,
        _,
        _,
    ) = struct.unpack_from("<7H", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "cont_current_lim": cont_current_lim,
        "energy_lim": energy_lim,
        "motor_lim": motor_lim,
        "motor_bias": motor_bias,
    }


@parser(0x04E2)
def mot_get_tracksettleparams(data: bytes) -> Dict[str, Any]:
    chan_ident, time, settle_window, track_window, _, _ = struct.unpack_from(
        "<6H", data, HEADER_SIZE
    )
    return {
        "chan_ident": chan_ident,
        "time": time,
        "settle_window": settle_window,
        "track_window": track_window,
    }


@parser(0x04E5)
def mot_get_profilemodeparams(data: bytes) -> Dict[str, Any]:
    chan_ident, mode, jerk, _, _ = struct.unpack_from("<HHLHH", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "mode": mode,
        "jerk": jerk,
    }


@parser(0x04E8)
def mot_get_joystickparams(data: bytes) -> Dict[str, Any]:
    (
        chan_ident,
        gear_high_max_vel,
        gear_low_accn,
        gear_high_accn,
        dir_sense,
    ) = struct.unpack_from("<H4LH", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "gear_high_max_vel": gear_high_max_vel,
        "gear_low_accn": gear_low_accn,
        "gear_high_accn": gear_high_accn,
        "dir_sense": dir_sense,
    }


@parser(0x04D6)
def mot_get_currentloopoarams(data: bytes) -> Dict[str, Any]:
    (
        chan_ident,
        phase,
        kp_current,
        ki_current,
        i_lim_current,
        i_dead_band,
        kff,
        _,
        _,
    ) = struct.unpack_from("<9H", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "phase": phase,
        "kp_current": kp_current,
        "ki_current": ki_current,
        "i_lim_current": i_lim_current,
        "i_dead_band": i_dead_band,
        "kff": kff,
    }


@parser(0x04EB)
def mot_get_settledcurrentloopparams(data: bytes) -> Dict[str, Any]:
    (
        chan_ident,
        phase,
        kp_settled,
        ki_settled,
        i_lim_settled,
        i_dead_band_settled,
        kff_settled,
        _,
        _,
    ) = struct.unpack_from("<9H", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "phase": phase,
        "kp_settled": kp_settled,
        "ki_settled": ki_settled,
        "i_lim_settled": i_lim_settled,
        "i_dead_band_settled": i_dead_band_settled,
        "kff_settled": kff_settled,
    }


@parser(0x04F2)
def mot_get_stageaxisparams(data: bytes) -> Dict[str, Any]:
    (
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
        _,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = struct.unpack_from("<HHH16sLL5l4H4L", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "stage_id": stage_id,
        "axis_id": axis_id,
        "part_no_axis": part_no_axis,
        "serial_num": serial_num,
        "counts_per_unit": counts_per_unit,
        "min_pos": min_pos,
        "max_pos": max_pos,
        "max_accn": max_accn,
        "max_dec": max_dec,
        "max_vel": max_vel,
    }


@parser(0x0481)
def mot_get_statusupdate(data: bytes) -> Dict[str, Any]:
    return _parse_status(data)


@parser(0x042A)
def mot_get_statusbits(data: bytes) -> Dict[str, Any]:
    chan_ident, status_bits = struct.unpack_from("<HL", data, HEADER_SIZE)
    ret = {
        "chan_ident": chan_ident,
    }
    ret.update(_parse_status_bits(status_bits))
    # Bitfield
    return ret


@parser(0x0502)
def mot_get_trigger(data: bytes) -> Dict[str, Any]:
    return {
        "chan_ident": data[2],
        "mode": data[3],
    }


@parser(0x0522)
def mot_get_kcubemmiparams(data: bytes) -> Dict[str, Any]:
    (
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
    ) = struct.unpack_from("<HHllHll3H", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "mode": mode,
        "max_vel": max_vel,
        "accn": accn,
        "dir_sense": dir_sense,
        "pre_set_pos1": pre_set_pos1,
        "pre_set_pos2": pre_set_pos2,
        "disp_brightness": disp_brightness,
        "disp_timeout": disp_timeout,
        "disp_dim_level": disp_dim_level,
    }


@parser(0x0525)
def mot_get_kcubetrigconfig(data: bytes) -> Dict[str, Any]:
    (
        chan_ident,
        trig1_mode,
        trig1_polarity,
        trig2_mode,
        trig2_polarity,
    ) = struct.unpack_from("<5H", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "trig1_mode": trig1_mode,
        "trig1_polarity": trig1_polarity,
        "trig2_mode": trig2_mode,
        "trig2_polarity": trig2_polarity,
    }


@parser(0x0528)
def mot_get_kcubeposttrigparams(data: bytes) -> Dict[str, Any]:
    (
        chan_ident,
        start_pos_fwd,
        interval_fwd,
        num_pulses_fwd,
        start_pos_rev,
        interval_rev,
        num_pulses_rev,
        pulse_width,
        num_cycles,
    ) = struct.unpack_from("<H8l", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "start_pos_fwd": start_pos_fwd,
        "interval_fwd": interval_fwd,
        "num_pulses_fwd": num_pulses_fwd,
        "start_pos_rev": start_pos_rev,
        "interval_rev": interval_rev,
        "num_pulses_rev": num_pulses_rev,
        "pulse_width": pulse_width,
        "num_cycles": num_cycles,
    }


@parser(0x052B)
def mot_get_kcubekstloopparams(data: bytes) -> Dict[str, Any]:
    (
        chan_ident,
        loop_mode,
        prop,
        int,
        diff,
        pid_clip,
        pid_tol,
        encoder_const,
    ) = struct.unpack_from("<HH5lL", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "loop_mode": loop_mode,
        "prop": prop,
        "int": int,
        "diff": diff,
        "pid_clip": pid_clip,
        "pid_tol": pid_tol,
        "encoder_const": encoder_const,
    }


@parser(0x0512)
def mot_get_mmf_operparams(data: bytes) -> Dict[str, Any]:
    (
        chan_ident,
        i_tranit_time,
        i_transit_time_adc,
        oper_mode1,
        sig_mode1,
        pulse_width1,
        oper_mode2,
        sig_mode2,
        pulse_width2,
        _,
        _,
    ) = struct.unpack_from("<HllHHlHHllL", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "i_tranit_time": i_tranit_time,
        "i_transit_time_adc": i_transit_time_adc,
        "oper_mode1": oper_mode1,
        "sig_mode1": sig_mode1,
        "pulse_width1": pulse_width1,
        "oper_mode2": oper_mode2,
        "sig_mode2": sig_mode2,
        "pulse_width2": pulse_width2,
    }


@parser(0x04C2)
def mot_get_sol_operatingmode(data: bytes) -> Dict[str, Any]:
    return {"chan_ident": data[2], "mode": data[3]}


@parser(0x04C5)
def mot_get_sol_cycleparams(data: bytes) -> Dict[str, Any]:
    chan_ident, off_time, num_cycles = struct.unpack_from("<H3l", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "off_time": off_time,
        "num_cycles": num_cycles,
    }


@parser(0x04C8)
def mot_get_sol_interlockmode(data: bytes) -> Dict[str, Any]:
    return {"chan_ident": data[2], "mode": data[3] == 0x01}


@parser(0x04CD)
def mot_get_sol_state(data: bytes) -> Dict[str, Any]:
    return {"chan_ident": data[2], "state": data[3] == 0x01}


@parser(0x0642)
def pz_get_positioncontrolmode(data: bytes) -> Dict[str, Any]:
    return {"chan_ident": data[2], "mode": data[3]}


@parser(0x0645)
def pz_get_outputvolts(data: bytes) -> Dict[str, Any]:
    chan_ident, voltage = struct.unpack_from("<Hh", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "voltage": voltage,
    }


@parser(0x0648)
def pz_get_outputpos(data: bytes) -> Dict[str, Any]:
    chan_ident, position = struct.unpack_from("<HH", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "position": position,
    }


@parser(0x0654)
def pz_get_inputvoltssrc(data: bytes) -> Dict[str, Any]:
    chan_ident, volt_src = struct.unpack_from("<HH", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "volt_src": volt_src,
    }


@parser(0x0657)
def pz_get_piconsts(data: bytes) -> Dict[str, Any]:
    chan_ident, PropConst, IntConst = struct.unpack_from("<HHH", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "PropConst": PropConst,
        "IntConst": IntConst,
    }


@parser(0x065C)
def pz_get_pzstatusbits(data: bytes) -> Dict[str, Any]:
    chan_ident, status_bits = struct.unpack_from("<HL", data, HEADER_SIZE)
    ret = {"chan_ident": chan_ident}
    ret.update(_parse_pz_status_bits(status_bits))
    return ret


@parser(0x0661)
def pz_get_pzstatusupdate(data: bytes) -> Dict[str, Any]:
    chan_ident, output_voltage, position, status_bits = struct.unpack_from(
        "<HhhL", data, HEADER_SIZE
    )
    ret = {
        "chan_ident": chan_ident,
        "output_voltage": output_voltage,
        "position": position,
    }
    ret.update(_parse_pz_status_bits(status_bits))
    return ret


@parser(0x0692)
def pz_get_ppc_pidconsts(data: bytes) -> Dict[str, Any]:
    (
        chan_ident,
        pid_p,
        pid_i,
        pid_d,
        pid_d_filter_cut,
        pid_d_filter_on,
    ) = struct.unpack_from("<HHHHHH", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "pid_p": pid_p,
        "pid_i": pid_i,
        "pid_d": pid_d,
        "pid_d_filter_cut": pid_d_filter_cut,
        "pid_d_filter_on": pid_d_filter_on,
    }


@parser(0x0695)
def pz_get_ppc_notchparams(data: bytes) -> Dict[str, Any]:
    (
        chan_ident,
        filter_no,
        filter1_center,
        filter1_q,
        notch_filter_1_on,
        filter2_center,
        filter2_q,
        notch_filter_2_on,
    ) = struct.unpack_from("<HHHHHHHH", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "filter_no": filter_no,
        "filter1_center": filter1_center,
        "filter1_q": filter1_q,
        "notch_filter_1_on": notch_filter_1_on,
        "filter2_center": filter2_center,
        "filter2_q": filter2_q,
        "notch_filter_2_on": notch_filter_2_on,
    }


@parser(0x0698)
def pz_get_ppc_iosettings(data: bytes) -> Dict[str, Any]:
    (
        chan_ident,
        control_src,
        monitor_out_sig,
        monitor_out_bandwidth,
        feedback_src,
        fp_brightness,
        _,
    ) = struct.unpack_from("<HHHHHHH", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "control_src": control_src,
        "monitor_out_sig": monitor_out_sig,
        "monitor_out_bandwidth": monitor_out_bandwidth,
        "feedback_src": feedback_src,
        "fp_brightness": fp_brightness,
    }


@parser(0x0702)
def pz_get_outputlut(data: bytes) -> Dict[str, Any]:
    chan_ident, index, output = struct.unpack_from("<HHh", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "index": index,
        "output": output,
    }


@parser(0x0705)
def pz_get_outputlutparams(data: bytes) -> Dict[str, Any]:
    (
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
    ) = struct.unpack_from("<HHHLLLLHLH", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "mode": mode,
        "cycle_length": cycle_length,
        "num_cycles": num_cycles,
        "delay_time": delay_time,
        "pre_cycle_rest": pre_cycle_rest,
        "post_cycle_rest": post_cycle_rest,
        "output_trig_start": output_trig_start,
        "output_trig_width": output_trig_width,
        "trig_rep_cycle": trig_rep_cycle,
    }


@parser(0x07D3)
def pz_get_tpz_dispsettings(data: bytes) -> Dict[str, Any]:
    disp_intensity = struct.unpack_from("<H", data, HEADER_SIZE)
    return {
        "disp_intensity": disp_intensity,
    }


@parser(0x07D6)
def pz_get_tpz_iosettings(data: bytes) -> Dict[str, Any]:
    chan_ident, voltage_limit, hub_analog_input, _, _ = struct.unpack_from(
        "<HHHHH", data, HEADER_SIZE
    )
    return {
        "chan_ident": chan_ident,
        "voltage_limit": voltage_limit,
        "hub_analog_input": hub_analog_input,
    }


@parser(0x0651)
def pz_get_maxtravel(data: bytes) -> Dict[str, Any]:
    chan_ident, travel = struct.unpack_from("<HH", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "travel": travel,
    }


@parser(0x0672)
def pz_get_iosettings(data: bytes) -> Dict[str, Any]:
    (
        chan_ident,
        amp_current_limit,
        amp_lowpass_filter,
        feedback_sig,
        bnc_trig_or_lv_output,
    ) = struct.unpack_from("<HHHHH", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "amp_current_limit": amp_current_limit,
        "amp_lowpass_filter": amp_lowpass_filter,
        "feedback_sig": feedback_sig,
        "bnc_trig_or_lv_output": bnc_trig_or_lv_output,
    }


@parser(0x0682)
def pz_get_outputmaxvolts(data: bytes) -> Dict[str, Any]:
    chan_ident, voltage, flags = struct.unpack_from("<HHH", data, HEADER_SIZE)
    ret = {
        "chan_ident": chan_ident,
        "voltage": voltage,
    }
    ret.update(
        {
            "max_75V": bool(flags & 0x2),
            "max_100V": bool(flags & 0x4),
            "max_150V": bool(flags & 0x8),
        }
    )
    return ret


@parser(0x0685)
def pz_get_tpz_slewrates(data: bytes) -> Dict[str, Any]:
    chan_ident, slew_open, slew_closed = struct.unpack_from("<HHH", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "slew_open": slew_open,
        "slew_closed": slew_closed,
    }


@parser(0x07F2)
def kpz_get_kcubemmiparams(data: bytes) -> Dict[str, Any]:
    (
        _,
        js_mode,
        js_volt_gearbox,
        js_volt_step,
        dir_sense,
        preset_volt1,
        preset_volt2,
        disp_brightness,
        disp_timeout,
        disp_dim_level,
        _,
        _,
        _,
        _,
    ) = struct.unpack_from("<HHHLHLLHHH", data, HEADER_SIZE)
    return {
        "js_mode": js_mode,
        "js_volt_gearbox": js_volt_gearbox,
        "js_volt_step": js_volt_step,
        "dir_sense": dir_sense,
        "preset_volt1": preset_volt1,
        "preset_volt2": preset_volt2,
        "disp_brightness": disp_brightness,
        "disp_timeout": disp_timeout,
        "disp_dim_level": disp_dim_level,
    }


@parser(0x07F5)
def kpz_get_kcubetrigioconfig(data: bytes) -> Dict[str, Any]:
    _, trig1_mode, trig1_polarity, trig2_mode, trig2_polarity, _ = struct.unpack_from(
        "<HHHHHH", data, HEADER_SIZE
    )
    return {
        "trig1_mode": trig1_mode,
        "trig1_polarity": trig1_polarity,
        "trig2_mode": trig2_mode,
        "trig2_polarity": trig2_polarity,
    }


@parser(0x07DC)
def pz_get_tsg_iosettings(data: bytes) -> Dict[str, Any]:
    _, hub_analog_output, display_mode, force_calibration, _, _ = struct.unpack_from(
        "<HHHHHH", data, HEADER_SIZE
    )
    return {
        "hub_analog_output": hub_analog_output,
        "display_mode": display_mode,
        "force_calibration": force_calibration,
    }


@parser(0x07DF)
def pz_get_tsg_reading(data: bytes) -> Dict[str, Any]:
    chan_ident, reading, smoothed = struct.unpack_from("<Hhh", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "reading": reading,
        "smoothed": smoothed,
    }


@parser(0x07F8)
def ksg_get_kcubemmiparams(data: bytes) -> Dict[str, Any]:
    chan_ident, disp_intensity, disp_timeout, disp_dim_level = struct.unpack_from(
        "<HHHH", data, HEADER_SIZE
    )
    return {
        "chan_ident": chan_ident,
        "disp_intensity": disp_intensity,
        "disp_timeout": disp_timeout,
        "disp_dim_level": disp_dim_level,
    }


@parser(0x07FB)
def ksg_get_kcubetrigioconfig(data: bytes) -> Dict[str, Any]:
    (
        _,
        trig1_mode,
        trig1_polarity,
        trig2_mode,
        trig2_polarity,
        lower_lim,
        upper_lim,
        smoothing_samples,
        _,
    ) = struct.unpack_from("<HHHHHllHH", data, HEADER_SIZE)
    return {
        "trig1_mode": trig1_mode,
        "trig1_polarity": trig1_polarity,
        "trig2_mode": trig2_mode,
        "trig2_polarity": trig2_polarity,
        "lower_lim": lower_lim,
        "upper_lim": upper_lim,
        "smoothing_samples": smoothing_samples,
    }


@parser(0x0605)
def pz_get_ntmode(data: bytes) -> Dict[str, Any]:
    return {"state": data[2], "mode": data[3]}


@parser(0x0608)
def pz_get_nttrackthreshold(data: bytes) -> Dict[str, Any]:
    threshold_abs_reading = struct.unpack_from("<f", data, HEADER_SIZE)
    return {
        "threshold_abs_reading": threshold_abs_reading,
    }


@parser(0x0611)
def pz_get_ntcirchomepos(data: bytes) -> Dict[str, Any]:
    circ_home_pos_a, circ_home_pos_b = struct.unpack_from("<HH", data, HEADER_SIZE)
    return {
        "circ_home_pos_a": circ_home_pos_a,
        "circ_home_pos_b": circ_home_pos_b,
    }


@parser(0x061A)
def pz_get_ntcircparams(data: bytes) -> Dict[str, Any]:
    (
        circ_dia_mode,
        circ_dia_sw,
        circ_osc_freq,
        abs_pwr_min_circ_dia,
        abs_pwr_max_circ_dia,
        abs_pwr_adjust_type,
    ) = struct.unpack_from("<HHHHHH", data, HEADER_SIZE)
    return {
        "circ_dia_mode": circ_dia_mode,
        "circ_dia_sw": circ_dia_sw,
        "circ_osc_freq": circ_osc_freq,
        "abs_pwr_min_circ_dia": abs_pwr_min_circ_dia,
        "abs_pwr_max_circ_dia": abs_pwr_max_circ_dia,
        "abs_pwr_adjust_type": abs_pwr_adjust_type,
    }


@parser(0x0623)
def pz_get_ntcircdialut(data: bytes) -> Dict[str, Any]:
    lut_val = struct.unpack_from("<16H", data, HEADER_SIZE)
    return {
        "lut_val": lut_val,
    }


@parser(0x0628)
def pz_get_ntphasecompparams(data: bytes) -> Dict[str, Any]:
    phase_comp_mode, phase_comp_asw, phase_comp_bsw = struct.unpack_from(
        "<Hhh", data, HEADER_SIZE
    )
    return {
        "phase_comp_mode": phase_comp_mode,
        "phase_comp_asw": phase_comp_asw,
        "phase_comp_bsw": phase_comp_bsw,
    }


@parser(0x0632)
def pz_get_nttiarangeparams(data: bytes) -> Dict[str, Any]:
    (
        range_mode,
        range_up_limit,
        range_down_limit,
        settle_sample,
        range_change_type,
        range_sw,
    ) = struct.unpack_from("<HhhhHH", data, HEADER_SIZE)
    return {
        "range_mode": range_mode,
        "range_up_limit": range_up_limit,
        "range_down_limit": range_down_limit,
        "settle_sample": settle_sample,
        "range_change_type": range_change_type,
        "range_sw": range_sw,
    }


@parser(0x0635)
def pz_get_ntgainparams(data: bytes) -> Dict[str, Any]:
    gain_ctrl_mode, nt_gain_sw = struct.unpack_from("<Hh", data, HEADER_SIZE)
    return {
        "gain_ctrl_mode": gain_ctrl_mode,
        "nt_gain_sw": nt_gain_sw,
    }


@parser(0x0638)
def pz_get_nttiapfilterparams(data: bytes) -> Dict[str, Any]:
    param_1, _, _, _, _ = struct.unpack_from("<5l", data, HEADER_SIZE)
    return {
        "param_1": param_1,
    }


@parser(0x063A)
def pz_get_nttiareading(data: bytes) -> Dict[str, Any]:
    abs_reading, rel_reading, range, under_over_read = struct.unpack_from(
        "<fHHH", data, HEADER_SIZE
    )
    return {
        "abs_reading": abs_reading,
        "rel_reading": rel_reading,
        "range": range,
        "under_over_read": under_over_read,
    }


@parser(0x063D)
def pz_get_ntfeedbacksrc(data: bytes) -> Dict[str, Any]:
    return {
        "feedback_src": data[2],
    }


@parser(0x063F)
def pz_get_ntstatusbits(data: bytes) -> Dict[str, Any]:
    (status_bits,) = struct.unpack_from("<l", data, HEADER_SIZE)
    return _parse_nt_status_bits(status_bits)


@parser(0x0665)
def pz_get_ntstatusupdate(data: bytes) -> Dict[str, Any]:
    (
        circ_pos_a,
        circ_pos_b,
        circ_dia,
        abs_reading,
        rel_reading,
        range,
        under_over_read,
        status_bits,
        nt_gain,
        phase_comp_a,
        phase_comp_b,
    ) = struct.unpack_from("<HHfHHHlhhh", data, HEADER_SIZE)
    ret = {
        "circ_pos_a": circ_pos_a,
        "circ_pos_b": circ_pos_b,
        "circ_dia": circ_dia,
        "abs_reading": abs_reading,
        "rel_reading": rel_reading,
        "range": range,
        "under_over_read": under_over_read,
        "nt_gain": nt_gain,
        "phase_comp_a": phase_comp_a,
        "phase_comp_b": phase_comp_b,
    }
    ret.update(_parse_nt_status_bits(status_bits))
    return ret


@parser(0x0689)
def kna_get_nttialpfiltercoeefs(data: bytes) -> Dict[str, Any]:
    param_1, _, _, _, _ = struct.unpack_from("<5l", data, HEADER_SIZE)
    return {
        "param_1": param_1,
    }


@parser(0x068C)
def kna_get_kcubemmiparams(data: bytes) -> Dict[str, Any]:
    wheel_step, disp_brightness, _, _, _, _, _, _ = struct.unpack_from(
        "<HH6H", data, HEADER_SIZE
    )
    return {
        "wheel_step": wheel_step,
        "disp_brightness": disp_brightness,
    }


@parser(0x068F)
def kna_get_kcubetrigioconfig(data: bytes) -> Dict[str, Any]:
    t1_mode, t1_polarity, _, t2_mode, t2_polarity, _, _, _, _, _ = struct.unpack_from(
        "<10H", data, HEADER_SIZE
    )
    return {
        "t1_mode": t1_mode,
        "t1_polarity": t1_polarity,
        "t2_mode": t2_mode,
        "t2_polarity": t2_polarity,
    }


@parser(0x06A1)
def kna_get_xyscan(data: bytes) -> Dict[str, Any]:
    line_number, range, *intensity_map = struct.unpack_from("<HH96B", data, HEADER_SIZE)
    return {
        "line_number": line_number,
        "range": range,
        "intensity_map": intensity_map,
    }


@parser(0x07EA)
def nt_get_tna_dispsettings(data: bytes) -> Dict[str, Any]:
    disp_intensity = struct.unpack_from("<H", data, HEADER_SIZE)
    return {
        "disp_intensity": disp_intensity,
    }


@parser(0x07ED)
def nt_get_tnaiosettings(data: bytes) -> Dict[str, Any]:
    lv_out_range, lv_out_route, hv_out_range, sign_io_route = struct.unpack_from(
        "<HHHH", data, HEADER_SIZE
    )
    return {
        "lv_out_range": lv_out_range,
        "lv_out_route": lv_out_route,
        "hv_out_range": hv_out_range,
        "sign_io_route": sign_io_route,
    }


@parser(0x0800)
def la_get_params(data: bytes) -> Dict[str, Any]:
    (submsgid,) = struct.unpack_from("<H", data, HEADER_SIZE)
    ret = {"submsgid": submsgid}
    if submsgid == 1:
        setpoint = struct.unpack_from("<H", data, HEADER_SIZE + 2)
        ret.update({"setpoint": setpoint})
    elif submsgid == 3:
        current, power = struct.unpack_from("<HH", data, HEADER_SIZE + 2)
        ret.update({"current": current, "power": power})
    elif submsgid == 4:
        current, power, voltage = struct.unpack_from("<Hhh", data, HEADER_SIZE + 2)
        ret.update({"current": current, "power": power, "voltage": voltage})
    elif submsgid == 5:
        (laser_source,) = struct.unpack_from("<H", data, HEADER_SIZE + 2)
        ret.update({"laser_source": laser_source})
    elif submsgid == 5:
        (laser_source,) = struct.unpack_from("<H", data, HEADER_SIZE + 2)
        ret.update({"laser_source": laser_source})
    elif submsgid == 7:
        (statusbits,) = struct.unpack_from("<L", data, HEADER_SIZE + 2)
        ret.update(_parse_la_status_bits(statusbits))
    elif submsgid == 9:
        max_current, max_power, wavelength = struct.unpack_from(
            "<HHH", data, HEADER_SIZE + 2
        )
        ret.update(
            {
                "max_current": max_current,
                "max_power": max_power,
                "wavelength": wavelength,
            }
        )
    elif submsgid == 10:
        (max_current,) = struct.unpack_from("<h", data, HEADER_SIZE + 2)
        ret.update({"max_current": max_current})
    elif submsgid == 11:
        intensity, units, _ = struct.unpack_from("<HHH", data, HEADER_SIZE + 2)
        ret.update({"intensity": intensity, "units": units})
    elif submsgid == 13:
        calib_factor, polarity, ramp_up = struct.unpack_from(
            "<fHH", data, HEADER_SIZE + 2
        )
        ret.update(
            {"calib_factor": calib_factor, "polarity": polarity, "ramp_up": ramp_up}
        )
    elif submsgid == 14:
        disp_intensity, _, _, _ = struct.unpack_from("<HHHH", data, HEADER_SIZE + 2)
        ret.update({"disp_intensity": disp_intensity})
    elif submsgid == 17:
        (
            dig_outs,
            _,
        ) = struct.unpack_from("<HH", data, HEADER_SIZE + 2)
        ret.update({"dig_outs": dig_outs})

    return ret


@parser(0x815)
def ld_potrotating(data: bytes):
    return {"degrees": struct.unpack_from("<h", data, 2)}


@parser(0x0819)
def ld_get_maxcurrentdigpot(data: bytes) -> Dict[str, Any]:
    return {
        "max_current": data[2],
    }


@parser(0x0821)
def la_get_statusupdate(data: bytes) -> Dict[str, Any]:
    laser_current, laser_power, statusbits = struct.unpack_from(
        "<HHL", data, HEADER_SIZE
    )
    ret = {
        "laser_current": laser_current,
        "laser_power": laser_power,
    }

    ret.update(_parse_la_status_bits(statusbits))
    return ret


@parser(0x0826)
def ld_get_statusupdate(data: bytes) -> Dict[str, Any]:
    laser_current, photo_current, laser_voltage, _, statusbits = struct.unpack_from(
        "<hHhLL", data, HEADER_SIZE
    )
    ret = {
        "laser_current": laser_current,
        "photo_current": photo_current,
        "laser_voltage": laser_voltage,
    }
    ret.update(_parse_ld_status_bits(statusbits))
    return ret


@parser(0x082C)
def la_get_kcubetrigconfig(data: bytes) -> Dict[str, Any]:
    (
        _,
        trig1_mode,
        trig1_polarity,
        _,
        trig2_mode,
        trig2_polarity,
        _,
    ) = struct.unpack_from("<HHHHHHH", data, HEADER_SIZE)
    return {
        "trig1_mode": trig1_mode,
        "trig1_polarity": trig1_polarity,
        "trig2_mode": trig2_mode,
        "trig2_polarity": trig2_polarity,
    }


@parser(0x0870)
def quad_get_params(data: bytes) -> Dict[str, Any]:
    (submsgid,) = struct.unpack_from("<H", data, HEADER_SIZE)
    ret = {"submsgid": submsgid}
    if submsgid == 1:
        PGain, IGain, DGain = struct.unpack_from("<HHH", data, HEADER_SIZE)
        ret.update(
            {
                "PGain": PGain,
                "IGain": IGain,
                "DGain": DGain,
            }
        )
    elif submsgid == 3:
        x_diff, y_diff, sum, x_pos, y_pos = struct.unpack_from(
            "<hhHhh", data, HEADER_SIZE
        )
        ret.update(
            {
                "x_diff": x_diff,
                "y_diff": y_diff,
                "sum": sum,
                "x_pos": x_pos,
                "y_pos": y_pos,
            }
        )
    elif submsgid == 5:
        (
            x_pos_dem_min,
            y_pos_dem_min,
            x_pos_dem_max,
            y_pos_dem_max,
            lv_out_route,
            ol_pos_dem,
            x_pos_fb_sense,
            y_pos_fb_sense,
        ) = struct.unpack_from("<hhhhHHhh", data, HEADER_SIZE)
        ret.update(
            {
                "x_pos_dem_min": x_pos_dem_min,
                "y_pos_dem_min": y_pos_dem_min,
                "x_pos_dem_max": x_pos_dem_max,
                "y_pos_dem_max": y_pos_dem_max,
                "lv_out_route": lv_out_route,
                "ol_pos_dem": ol_pos_dem,
                "x_pos_fb_sense": x_pos_fb_sense,
                "y_pos_fb_sense": y_pos_fb_sense,
            }
        )
    elif submsgid == 7:
        (mode,) = struct.unpack_from("<H", data, HEADER_SIZE)
        ret.update(
            {
                "mode": mode,
            }
        )
    elif submsgid == 8:
        disp_intensity, disp_mode, disp_dim_timeout = struct.unpack_from(
            "<HHH", data, HEADER_SIZE
        )
        ret.update(
            {
                "disp_intensity": disp_intensity,
                "disp_mode": disp_mode,
                "disp_dim_timeout": disp_dim_timeout,
            }
        )
    elif submsgid == 0xD:
        x_pos, y_pos = struct.unpack_from("<hh", data, HEADER_SIZE)
        ret.update(
            {
                "x_pos": x_pos,
                "y_pos": y_pos,
            }
        )
    elif submsgid == 0xE:
        (
            p,
            i,
            d,
            low_pass_cutoff,
            notch_center,
            filter_q,
            notch_filter_on,
            deriv_filter_on,
        ) = struct.unpack_from("<ffffffHH", data, HEADER_SIZE)
        ret.update(
            {
                "p": p,
                "i": i,
                "d": d,
                "low_pass_cutoff": low_pass_cutoff,
                "notch_center": notch_center,
                "filter_q": filter_q,
                "notch_filter_on": notch_filter_on,
                "deriv_filter_on": deriv_filter_on,
            }
        )
    elif submsgid == 0xF:
        (
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
            _,
        ) = struct.unpack_from("<11H", data, HEADER_SIZE)
        ret.update(
            {
                "trig1_mode": trig1_mode,
                "trig1_polarity": trig1_polarity,
                "trig1_sum_min": trig1_sum_min,
                "trig1_sum_max": trig1_sum_max,
                "trig1_diff_threshold": trig1_diff_threshold,
                "trig2_mode": trig2_mode,
                "trig2_polarity": trig2_polarity,
                "trig2_sum_min": trig2_sum_min,
                "trig2_sum_max": trig2_sum_max,
                "trig2_diff_threshold": trig2_diff_threshold,
            }
        )
    elif submsgid == 0xA:
        dig_outs, _ = struct.unpack_from("<HH", data, HEADER_SIZE)
        ret.update(
            {
                "dig_outs": dig_outs,
            }
        )

    return ret


@parser(0x0881)
def quad_get_statusupdate(data: bytes) -> Dict[str, Any]:
    x_diff, y_diff, sum, x_pos, y_pos, statusbits = struct.unpack_from(
        "<hhHhhL", data, HEADER_SIZE
    )
    ret = {
        "x_diff": x_diff,
        "y_diff": y_diff,
        "sum": sum,
        "x_pos": x_pos,
        "y_pos": y_pos,
    }
    ret.update(_parse_quad_status_bits(statusbits))
    return ret


@parser(0x0842)
def tec_get_params(data: bytes) -> Dict[str, Any]:
    (submsgid,) = struct.unpack_from("<H", data, HEADER_SIZE)
    ret = {"submsgid": submsgid}
    if submsgid == 1:
        (temp_set,) = struct.unpack_from("<H", data, HEADER_SIZE)
        ret.update({"temp_set": temp_set})
    elif submsgid == 3:
        current, temp_actual, temp_set = struct.unpack_from("<hhH", data, HEADER_SIZE)
        ret.update(
            {
                "current": current,
                "temp_actual": temp_actual,
                "temp_set": temp_set,
            }
        )
    elif submsgid == 5:
        sensor, current_limit = struct.unpack_from("<Hh", data, HEADER_SIZE)
        ret.update(
            {
                "sensor": sensor,
                "current_limit": current_limit,
            }
        )
    elif submsgid == 7:
        (statusbits,) = struct.unpack_from("<L", data, HEADER_SIZE)
        ret.update(_parse_tec_status_bits(statusbits))
    elif submsgid == 9:
        p, i, d = struct.unpack_from("<HHH", data, HEADER_SIZE)
        ret.update(
            {
                "p": p,
                "i": i,
                "d": d,
            }
        )
    elif submsgid == 0xB:
        disp_intensity, disp_mode, _ = struct.unpack_from("<HHH", data, HEADER_SIZE)
        ret.update(
            {
                "disp_intensity": disp_intensity,
                "disp_mode": disp_mode,
            }
        )

    return ret


@parser(0x0861)
def tec_get_statusupdate(data: bytes) -> Dict[str, Any]:
    current, temp_actual, temp_set, statusbits = struct.unpack_from(
        "<hhHL", data, HEADER_SIZE
    )
    ret = {"current": current, "temp_actual": temp_actual, "temp_set": temp_set}
    ret.update(_parse_tec_status_bits(statusbits))
    return ret


@parser(0x08C2)
def pzmot_get_params(data: bytes) -> Dict[str, Any]:
    (submsgid,) = struct.unpack_from("<H", data, HEADER_SIZE)
    ret = {"submsgid": submsgid}
    if submsgid == 5:
        chan_ident, position, _ = struct.unpack_from("<Hll", data, HEADER_SIZE)
        ret.update(
            {
                "chan_ident": chan_ident,
                "position": position,
            }
        )
    elif submsgid == 7:
        chan_ident, max_voltage, step_rate, step_accn = struct.unpack_from(
            "<HHll", data, HEADER_SIZE
        )
        ret.update(
            {
                "chan_ident": chan_ident,
                "max_voltage": max_voltage,
                "step_rate": step_rate,
                "step_accn": step_accn,
            }
        )
    elif submsgid == 9:
        (
            chan_ident,
            jog_mode,
            jog_step_size,
            jog_step_rate,
            jog_step_accn,
        ) = struct.unpack_from("<HHlll", data, HEADER_SIZE)
        ret.update(
            {
                "chan_ident": chan_ident,
                "jog_mode": jog_mode,
                "jog_step_size": jog_step_size,
                "jog_step_rate": jog_step_rate,
                "jog_step_accn": jog_step_accn,
            }
        )
    elif submsgid == 0x11:
        chan_ident, max_step_rate = struct.unpack_from("<Hl", data, HEADER_SIZE)
        ret.update(
            {
                "chan_ident": chan_ident,
                "max_step_rate": max_step_rate,
            }
        )
    elif submsgid == 0x13:
        chan_ident, mode, position1, position2, _, _ = struct.unpack_from(
            "<HHllHH", data, HEADER_SIZE
        )
        ret.update(
            {
                "chan_ident": chan_ident,
                "mode": mode,
                "position1": position1,
                "position2": position2,
            }
        )
    elif submsgid == 0xB:
        chan_ident, fwd_hard_limit, rev_hard_limit, _ = struct.unpack_from(
            "<HHHH", data, HEADER_SIZE
        )
        ret.update(
            {
                "chan_ident": chan_ident,
                "fwd_hard_limit": fwd_hard_limit,
                "rev_hard_limit": rev_hard_limit,
            }
        )
    elif submsgid == 0xF:
        (
            chan_ident,
            home_direction,
            home_lim_switch,
            home_step_rate,
            home_offset_dist,
        ) = struct.unpack_from("<HHHLl", data, HEADER_SIZE)
        ret.update(
            {
                "chan_ident": chan_ident,
                "home_direction": home_direction,
                "home_lim_switch": home_lim_switch,
                "home_step_rate": home_step_rate,
                "home_offset_dist": home_offset_dist,
            }
        )
    elif submsgid == 0x15:
        (
            chan_ident,
            js_mode,
            js_max_step_rate,
            js_dir_sense,
            preset_pos1,
            preset_pos2,
            disp_brightness,
            _,
        ) = struct.unpack_from("<HHlHllHH", data, HEADER_SIZE)
        ret.update(
            {
                "chan_ident": chan_ident,
                "js_mode": js_mode,
                "js_max_step_rate": js_max_step_rate,
                "js_dir_sense": js_dir_sense,
                "preset_pos1": preset_pos1,
                "preset_pos2": preset_pos2,
                "disp_brightness": disp_brightness,
            }
        )
    elif submsgid == 0x17:
        (
            trig_channel1,
            trig_channel2,
            trig1_mode,
            trig1_polarity,
            trig2_mode,
            trig2_polarity,
            *_,
        ) = struct.unpack_from("<12H", data, HEADER_SIZE)
        ret.update(
            {
                "trig_channel1": trig_channel1,
                "trig_channel2": trig_channel2,
                "trig1_mode": trig1_mode,
                "trig1_polarity": trig1_polarity,
                "trig2_mode": trig2_mode,
                "trig2_polarity": trig2_polarity,
            }
        )
    elif submsgid == 0x19:
        (
            chan_ident,
            start_pos_fwd,
            interval_fwd,
            num_pulses_fwd,
            start_pos_reverse,
            interval_rev,
            num_pulses_rev,
            pulse_width,
            num_cycles,
        ) = struct.unpack_from("<Hllllllll", data, HEADER_SIZE)
        ret.update(
            {
                "chan_ident": chan_ident,
                "start_pos_fwd": start_pos_fwd,
                "interval_fwd": interval_fwd,
                "num_pulses_fwd": num_pulses_fwd,
                "start_pos_reverse": start_pos_reverse,
                "interval_rev": interval_rev,
                "num_pulses_rev": num_pulses_rev,
                "pulse_width": pulse_width,
                "num_cycles": num_cycles,
            }
        )
    elif submsgid == 0x2B:
        mode = struct.unpack_from("<H", data, HEADER_SIZE)
        ret.update(
            {
                "mode": mode,
            }
        )
    elif submsgid == 0x2D:
        (
            chan_ident,
            jog_mode,
            jog_step_size_fwd,
            jog_step_size_rev,
            jog_step_rate,
            jog_step_accn,
        ) = struct.unpack_from("<HHllll", data, HEADER_SIZE)
        ret.update(
            {
                "chan_ident": chan_ident,
                "jog_mode": jog_mode,
                "jog_step_size_fwd": jog_step_size_fwd,
                "jog_step_size_rev": jog_step_size_rev,
                "jog_step_rate": jog_step_rate,
                "jog_step_accn": jog_step_accn,
            }
        )
    elif submsgid == 0x30:
        chan_ident, fb_signal_mode, encoder_const = struct.unpack_from(
            "<HHl", data, HEADER_SIZE
        )
        ret.update(
            {
                "chan_ident": chan_ident,
                "fb_signal_mode": fb_signal_mode,
                "encoder_const": encoder_const,
            }
        )
    elif submsgid == 0x32:
        chan_ident, rel_distance = struct.unpack_from("<Hl", data, HEADER_SIZE)
        ret.update(
            {
                "chan_ident": chan_ident,
                "rel_distance": rel_distance,
            }
        )
    elif submsgid == 0x34:
        chan_ident, abs_distance = struct.unpack_from("<Hl", data, HEADER_SIZE)
        ret.update(
            {
                "chan_ident": chan_ident,
                "abs_distance": abs_distance,
            }
        )

    return ret


@parser(0x08D6)
def pzmot_move_completed(data: bytes) -> Dict[str, Any]:
    chan_ident, abs_position, _, _ = struct.unpack_from("<Hlll", data, HEADER_SIZE)
    return {
        "chan_ident": chan_ident,
        "abs_position": abs_position,
    }


@parser(0x08E1)
def pzmot_get_statusupdate(data: bytes) -> Dict[str, Any]:
    chan_ident, position, _, status_bits = struct.unpack_from(
        "<HllL", data, HEADER_SIZE
    )
    ret = {
        "chan_ident": chan_ident,
        "position": position,
    }
    ret.update(_parse_pzmot_status_bits(status_bits))
    return ret


@parser(0x0532)
def pol_get_params(data: bytes) -> Dict[str, Any]:
    _, velocity, home_position, jog_step1, jog_step2, jog_step3 = struct.unpack_from(
        "<HHHHHH", data, HEADER_SIZE
    )
    return {
        "velocity": velocity,
        "home_position": home_position,
        "jog_step1": jog_step1,
        "jog_step2": jog_step2,
        "jog_step3": jog_step3,
    }
