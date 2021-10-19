import numpy as np
from scipy.interpolate import BPoly

from .basesignaldesigners import ScanDesigner


class GalvoScanDesigner(ScanDesigner):
    """ Scan designer for scan systems with galvanometric mirrors.

    Designer params: None
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._expectedParameters = ['target_device',
                                    'axis_length',
                                    'axis_step_size',
                                    'axis_centerpos',
                                    'axis_startpos',
                                    'sequence_time']

    def checkSignalComp(self, scanParameters, setupInfo, scanInfo):
        """ Check analog scanning signals so that they are inside the range of
        the acceptable scanner voltages."""
        fast_positioner = setupInfo.positioners[scanParameters['target_device'][0]]
        slow_positioner = setupInfo.positioners[scanParameters['target_device'][1]]

        if (scanInfo['minmax_fast_axis'][0] < fast_positioner.managerProperties['minVolt'] or
                scanInfo['minmax_fast_axis'][1] > fast_positioner.managerProperties['maxVolt']):
            return False
        if (scanInfo['minmax_slow_axis'][0] < slow_positioner.managerProperties['minVolt'] or
                scanInfo['minmax_slow_axis'][1] > slow_positioner.managerProperties['maxVolt']):
            return False
        return True

    def make_signal(self, parameterDict, setupInfo):
        # time step of evaluated scanning curves [µs]
        self.__timestep = 1e6 / setupInfo.scan.sampleRate
        # arbitrary for now - should calculate this based on the abs(biggest) axis_centerpos and the
        # max speed/acc, as that is what limits time it takes for axes to get to the right position
        self.__minsettlingtime = 1000
        # arbitrary for now  µs
        self.__paddingtime = 3000

        positioners = [positioner for positioner in setupInfo.positioners.values()
                       if positioner.forScanning]
        positionersProps = [positioner.managerProperties for positioner in positioners]

        axis_count = len(positioners)
        # convert vel_max from µm/µs to V/µs
        vel_max = [positionerProps['vel_max'] / positionerProps['conversionFactor']
                   for positionerProps in positionersProps]
        # convert acc_max from µm/µs^2 to V/µs^2
        acc_max = [positionerProps['acc_max'] / positionerProps['conversionFactor']
                   for positionerProps in positionersProps]

        # get list of positions for each axis
        convFactors = [positionerProps['conversionFactor'] for positionerProps in positionersProps]

        # TODO: this is not correct, as I take the order of conversion factors from the order in the
        #       list of scanners, but the scan info order as the scan axis order
        # retrieve axis lengths in V
        self.axis_length = [(parameterDict['axis_length'][i] / convFactors[i])
                            for i in range(axis_count)]
        # retrieve axis step sizes in V
        self.axis_step_size = [(parameterDict['axis_step_size'][i] / convFactors[i])
                               for i in range(axis_count)]
        # retrieve axis center positions in V
        self.axis_centerpos = [(parameterDict['axis_centerpos'][i] / convFactors[i])
                               for i in range(axis_count)]

        axis_positions = []
        for i in range(axis_count):
            axis_positions.append(int(np.ceil(self.axis_length[i] / self.axis_step_size[i])))

        self.__settlingtime = self.__calc_settling_time(self.axis_length, self.axis_centerpos,
                                                        vel_max, acc_max)

        # TODO: make this more modular to the number of scanners used?
        # fast axis signal
        fast_pos, samples_period, n_lines = self.__generate_smooth_scan(parameterDict, vel_max[0],
                                                                        acc_max[0])
        # slow (middle) axis signal
        axis_reps = self.__get_axis_reps(fast_pos, samples_period, n_lines)
        slow_pos = self.__generate_step_scan(parameterDict, axis_reps, vel_max[1], acc_max[1])

        # TODO: add
        # third axis signal
        #####

        # TODO: update to inlcude as many signals as scanners
        # pad all signals
        fast_axis_signal, slow_axis_signal = self.__zero_padding(parameterDict, fast_pos, slow_pos)

        sig_dict = {parameterDict['target_device'][0]: fast_axis_signal,
                    parameterDict['target_device'][1]: slow_axis_signal}

        # plt.figure()
        # plt.plot(fast_axis_signal-0.01)
        # plt.plot(slow_axis_signal)
        # plt.show()

        pixels_line = int(self.axis_length[0] / self.axis_step_size[0])
        # scanInfoDict: parameters that are important to relay to TTLCycleDesigner and/or image
        # acquisition managers
        scanInfoDict = {
            'n_lines': int(self.axis_length[1] / self.axis_step_size[1]),
            'pixels_line': pixels_line,
            'scan_samples_line': int(
                round(pixels_line * parameterDict['sequence_time'] * 1e6 / self.__timestep)
            ),
            'scan_samples_period': samples_period - 1,
            'scan_samples_total': len(fast_axis_signal),
            'scan_throw_startzero': int(round(self.__paddingtime / self.__timestep)),
            'scan_throw_initpos': self._samples_initpos,
            'scan_throw_settling': self._samples_settling,
            'scan_throw_startacc': self._samples_startacc,
            'scan_throw_finalpos': self._samples_finalpos,
            'scan_time_step': round(self.__timestep * 1e-6, ndigits=10),
            'dwell_time': parameterDict['sequence_time'],
            'pixel_size_ax1': parameterDict['axis_step_size'][0],
            'pixel_size_ax2': parameterDict['axis_step_size'][1],
            'minmax_fast_axis': [min(fast_axis_signal), max(fast_axis_signal)],
            'minmax_slow_axis': [min(slow_axis_signal), max(slow_axis_signal)]
        }

        self._logger.debug('Scanning curves generated.')
        return sig_dict, axis_positions, scanInfoDict

    def __calc_settling_time(self, axis_length, axis_centerpos, vel_max, acc_max):
        t_initpos_vc_slow = abs(axis_centerpos[1] - axis_length[1] / 2) / vel_max[1]
        t_initpos_vc_fast = abs(axis_centerpos[0] - axis_length[0] / 2) / vel_max[0]
        t_acc_slow = vel_max[1] / acc_max[1]
        t_acc_fast = vel_max[0] / acc_max[0]
        t_initpos_slow = t_initpos_vc_slow + 2 * t_acc_slow
        t_initpos_fast = t_initpos_vc_fast + 2 * t_acc_fast
        settlingtime = self.__minsettlingtime + np.max([0, t_initpos_slow - t_initpos_fast])
        return settlingtime

    def __generate_smooth_scan(self, parameterDict, v_max, a_max):
        """ Generate a smooth scanning curve with spline interpolation """
        n_lines = int(self.axis_length[1] / self.axis_step_size[1])  # number of lines

        curve_poly, time_fix, pos_fix = self.__linescan_poly(parameterDict, v_max, a_max)
        # calculate number of evaluation points for a line for decided timestep
        n_eval = int(time_fix[-1] / self.__timestep)
        # generate multiline curve for the whole scan
        pos = self.__generate_smooth_multiline(curve_poly, time_fix, pos_fix, n_eval, n_lines)
        # add missing start and end piece
        pos_ret = self.__add_start_end(pos, pos_fix, v_max, a_max)
        return pos_ret, n_eval, n_lines

    def __generate_step_scan(self, parameterDict, axis_reps, v_max, a_max):
        """ Generate a step-function scanning curve, with initial smooth
        positioning """
        l_scan = self.axis_length[1]
        c_scan = self.axis_centerpos[1]
        n_lines = int(self.axis_length[1] / self.axis_step_size[1])
        # create linspace for axis positions
        positions = (np.linspace(l_scan / n_lines, l_scan, n_lines) -
                     l_scan / (n_lines * 2) - l_scan / 2 + c_scan)
        # generate the initial smooth positioning curve
        pos_init = self.__init_positioning(positions[0], v_max, a_max)
        axis_reps[0] = axis_reps[0] - len(pos_init)
        # generate the final smooth positioning curve
        pos_final = self.__final_positioning(positions[-1], v_max, a_max)
        # repeat each middle element a number of times equal to the length of that between the
        # faster axis repetitions
        pos_steps = np.repeat(positions, axis_reps)
        # add initial positioning
        pos_ret = np.concatenate((pos_init, pos_steps, pos_final))
        return pos_ret

    def __get_axis_reps(self, pos, samples_period, n_lines):
        """ Get reps for each step on slow axis, by looking at the maximum and
        periods of the fast axis """
        start_skip = self._samples_initpos + self._samples_settling + self._samples_startacc
        end_skip = self._samples_finalpos
        # get length of first line
        first_line = [np.argmax(pos[start_skip:-end_skip]) + start_skip]
        # get length of all other lines
        rest_lines = np.repeat(samples_period - 1, n_lines - 1)
        # concatenate all repetition lengths
        axis_reps = np.concatenate((first_line, rest_lines))
        return axis_reps

    def __linescan_poly(self, parameterDict, v_max, a_max):
        """ Generate a Bernstein piecewise polynomial for a smooth one-line
        scanning curve, from the acquisition parameter settings, using
        piecewise spline interpolation """
        sequence_time = parameterDict['sequence_time'] * 1e6  # s --> µs
        l_scan = self.axis_length[0]  # µm
        c_scan = self.axis_centerpos[0]  # µm
        v_scan = self.axis_step_size[0] / sequence_time  # µm/µs

        # time between two fix points where the acceleration changes (infinite jerk) - µs
        dt_fix = 1e-2

        # positions at fixed points
        p1 = c_scan
        p2 = p2p = p1 + l_scan / 2
        t_deacc = (v_scan + v_max) / a_max
        d_deacc = v_scan * t_deacc + 0.5 * (-a_max) * t_deacc ** 2
        p3 = p3p = p2 + d_deacc
        p4 = p4p = c_scan - (p3 - c_scan)
        p5 = p5p = p1 - l_scan / 2
        p6 = p1
        pos = [p1, p2, p2p, p3, p3p, p4, p4p, p5, p5p, p6]

        # time at fixed points
        t1 = 0
        t_scanline = l_scan / v_scan
        t2 = t1 + t_scanline / 2
        t2p = t2 + dt_fix
        t3 = t2 + t_deacc
        t3p = t3 + dt_fix
        t4 = t3 + abs(p4 - p3) / v_max
        t4p = t4 + dt_fix
        t_acc = t_deacc
        t5 = t4 + t_acc
        t5p = t5 + dt_fix
        t6 = t5 + t_scanline / 2
        time = [t1, t2, t2p, t3, t3p, t4, t4p, t5, t5p, t6]

        # velocity at fixed points
        v1 = v_scan
        v2 = v2p = v_scan
        v3 = v3p = v4 = v4p = -v_max
        v5 = v5p = v6 = v_scan
        vel = [v1, v2, v2p, v3, v3p, v4, v4p, v5, v5p, v6]

        # acceleration at fixed points
        a1 = a2 = 0
        a2p = a3 = -a_max
        a3p = a4 = 0
        a4p = a5 = a_max
        a5p = a6 = 0
        acc = [a1, a2, a2p, a3, a3p, a4, a4p, a5, a5p, a6]
        # if p3 is already past the center of the scan it means that the max_velocity was never
        # reached in this case, remove two fixed points, and change the values to the curr. vel and
        # time in the middle of the flyback
        if p3 <= c_scan:
            t_mid = np.roots([-a_max / 2, v_scan, p2 - c_scan])[0]
            v_mid = -a_max * t_mid + v_scan
            del pos[5:7]
            del vel[5:7]
            del acc[5:7]
            del time[5:7]
            pos[3:5] = [c_scan, c_scan]
            vel[3:5] = [v_mid, v_mid]
            acc[3:5] = [-a_max, a_max]
            time[3] = time[2] + t_mid
            time[4] = time[3] + dt_fix
            time[5] = time[3] + t_mid
            time[6] = time[5] + dt_fix
            time[7] = time[5] + t_scanline / 2
        # generate Bernstein polynomial with piecewise spline interpolation with the fixed points
        # give positions, velocity, acceleration, and time of fixed points
        yder = np.array([pos, vel, acc]).T.tolist()

        bpoly = BPoly.from_derivatives(time, yder)  # bpoly time unit: µs
        # return polynomial, that can be evaluated at any timepoints you want
        # return fixed points position and time
        return bpoly, time, pos

    def __generate_smooth_multiline(self, pos_bpoly, time_fix, pos_fix, n_eval, n_lines):
        """ Generate a smooth multiline curve by evaluating the polynomial with
        the clock frequency used and copying it """
        # get evaluation times for one line
        x_eval = np.linspace(0, time_fix[-1], n_eval)
        # evaluate polynomial
        x_bpoly = pos_bpoly(x_eval)
        pos_ret = []
        # concatenate for number of lines in scan
        pos_ret = np.tile(x_bpoly[:-1], n_lines - 1)
        return pos_ret

    def __init_positioning(self, initpos, v_max, a_max):
        v_max = np.sign(initpos) * v_max
        a_max = np.sign(initpos) * a_max

        # time between two fix points where the acceleration changes (infinite jerk)  # µs
        dt_fix = 1e-2

        # positions at fixed points
        p1 = p1p = 0
        t_deacc = v_max / a_max
        d_deacc = 0.5 * a_max * t_deacc ** 2
        p2 = p2p = d_deacc
        p3 = p3p = initpos - d_deacc
        p4 = initpos
        pos = [p1, p1p, p2, p2p, p3, p3p, p4]

        # time at fixed points
        t1 = 0
        t1p = dt_fix
        t2 = t_deacc
        t2p = t2 + dt_fix
        t3 = t2 + abs(abs(p3 - p2) / v_max)
        t3p = t3 + dt_fix
        t4 = t3 + t_deacc
        time = [t1, t1p, t2, t2p, t3, t3p, t4]

        # velocity at fixed points
        v1 = v1p = 0
        v2 = v2p = v3 = v3p = v_max
        v4 = 0
        vel = [v1, v1p, v2, v2p, v3, v3p, v4]

        # acceleration at fixed points
        a1 = 0
        a1p = a2 = a_max
        a2p = a3 = 0
        a3p = a4 = -a_max
        acc = [a1, a1p, a2, a2p, a3, a3p, a4]

        # if p2 is already past the center of the scan it means that the max_velocity was never
        # reached in this case, remove two fixed points, and change the values to the curr. vel and
        # time in the middle of the flyback
        if abs(p2 - p1) >= abs(initpos / 2):
            t_mid = np.sqrt(abs(initpos / a_max))
            v_mid = a_max * t_mid
            del pos[4:6]
            del vel[4:6]
            del acc[4:6]
            del time[4:6]
            pos[2:4] = [initpos / 2, initpos / 2]
            vel[2:4] = [v_mid, v_mid]
            acc[2:4] = [a_max, -a_max]
            time[2] = t_mid
            time[3] = t_mid + dt_fix
            time[4] = 2 * t_mid

        # generate Bernstein polynomial with piecewise spline interpolation with the fixed points
        # give positions, velocity, acceleration, and time of fixed points
        yder = np.array([pos, vel, acc]).T.tolist()
        bpoly = BPoly.from_derivatives(time, yder)  # bpoly time unit: µs

        # get number of evaluation points
        n_eval = int(time[-1] / self.__timestep)
        # get evaluation times for one line
        t_eval = np.linspace(0, time[-1], n_eval)
        # evaluate polynomial
        poly_eval = bpoly(t_eval)
        # return evaluated polynomial at the timestep I want
        return poly_eval

    def __final_positioning(self, initpos, v_max, a_max):
        """ Generate a polynomial for a smooth final positioning scanning
        curve, from the acquisition parameter settings """
        v_max = -np.sign(initpos) * v_max
        a_max = -np.sign(initpos) * a_max

        # time between two fix points where the acceleration changes (infinite jerk)  # µs
        dt_fix = 1e-2

        # positions at fixed points
        p1 = p1p = initpos
        t_deacc = (v_max) / a_max
        d_deacc = 0.5 * a_max * t_deacc ** 2
        p2 = p2p = initpos + d_deacc
        p3 = p3p = -d_deacc
        p4 = 0
        pos = [p1, p1p, p2, p2p, p3, p3p, p4]

        # time at fixed points
        t1 = 0
        t1p = dt_fix
        t2 = t_deacc
        t2p = t2 + dt_fix
        t3 = t2 + abs(abs(p3 - p2) / v_max)
        t3p = t3 + dt_fix
        t4 = t3 + t_deacc
        time = [t1, t1p, t2, t2p, t3, t3p, t4]

        # velocity at fixed points
        v1 = v1p = 0
        v2 = v2p = v3 = v3p = v_max
        v4 = 0
        vel = [v1, v1p, v2, v2p, v3, v3p, v4]

        # acceleration at fixed points
        a1 = 0
        a1p = a2 = a_max
        a2p = a3 = 0
        a3p = a4 = -a_max
        acc = [a1, a1p, a2, a2p, a3, a3p, a4]

        # if p2 is already past the center of the scan it means that the max_velocity was never
        # reached in this case, remove two fixed points, and change the values to the curr. vel and
        # time in the middle of the flyback
        if abs(p2 - p1) >= abs(initpos / 2):
            t_mid = np.sqrt(abs(initpos / a_max))
            v_mid = a_max * t_mid
            del pos[4:6]
            del vel[4:6]
            del acc[4:6]
            del time[4:6]
            pos[2:4] = [initpos / 2, initpos / 2]
            vel[2:4] = [v_mid, v_mid]
            acc[2:4] = [a_max, -a_max]
            time[2] = t_mid
            time[3] = t_mid + dt_fix
            time[4] = 2 * t_mid

        # generate Bernstein polynomial with piecewise spline interpolation with the fixed points
        # give positions, velocity, acceleration, and time of fixed points
        yder = np.array([pos, vel, acc]).T.tolist()
        bpoly = BPoly.from_derivatives(time, yder)  # bpoly time unit: µs

        # get number of evaluation points
        n_eval = int(time[-1] / self.__timestep)
        # get evaluation times for one line
        t_eval = np.linspace(0, time[-1], n_eval)
        # evaluate polynomial
        poly_eval = bpoly(t_eval)
        # return evaluated polynomial at the timestep I want
        return poly_eval

    def __add_start_end(self, pos, pos_fix, v_max, a_max):
        """ Add start and end half-lines to smooth scanning curve """

        # generate five pieces, three before and two after, to be concatenated to the given
        # positions array

        # initial smooth acceleration piece from 0
        pos_pre1 = self.__init_positioning(initpos=np.min(pos), v_max=v_max, a_max=a_max)
        self._samples_initpos = len(pos_pre1)
        # initial settling time before first line
        settlinglen = int(round(self.__settlingtime / self.__timestep))
        pos_pre2 = np.repeat(np.min(pos), settlinglen)  # settling positions
        self._samples_settling = len(pos_pre2)
        pos_pre3 = pos[np.where(pos == np.min(pos))[0][-1]:]  # first half scan curve
        # alt: last half scan curve to last peak after last line
        pos_post1 = pos[:np.where(pos == np.max(pos))[0][0]]
        # final smooth acceleration piece from max to 0
        pos_post2 = self.__final_positioning(initpos=pos_post1[-1], v_max=v_max, a_max=a_max)
        pos_ret = np.concatenate((pos_pre1, pos_pre2, pos_pre3, pos, pos_post1, pos_post2))
        # half scan line
        pos_halfscanline =\
            pos[:np.argmin(abs(pos[:np.where(pos == np.max(pos))[0][0]] - pos_fix[2]))]
        self._samples_startacc = len(pos_pre3) - len(pos_halfscanline)
        self._samples_finalpos = len(pos_post2)
        return pos_ret

    def __zero_padding(self, parameterDict, pos1, pos2):
        """ Pad zeros to the end of two scanning curves, for initial and final
        settling of galvos """
        padlen = int(round(self.__paddingtime / self.__timestep))
        # check that the length of pos1 and pos2 are identical
        padlen1 = np.array([padlen, padlen])
        padlen2 = np.array([padlen, padlen])
        lendiff = len(pos1) - len(pos2)
        # if not equal, add to the correct padding length to make them equal
        if lendiff != 0:
            if lendiff > 0:
                padlen2 = padlen2 + np.array([0, abs(lendiff)])
            elif lendiff < 0:
                padlen1 = padlen1 + np.array([0, abs(lendiff)])
        # pad position arrays
        pos_ret1 = np.pad(pos1, padlen1, 'constant', constant_values=0)
        pos_ret2 = np.pad(pos2, padlen2, 'constant', constant_values=0)
        return pos_ret1, pos_ret2

# def __initial_positioning(self, initpos, v_max, a_max):
#    """ Generate a polynomial for a smooth initial positioning scanning
#    curve, from the acquisition parameter settings and initial position """
#    v_max = np.sign(initpos)*acq_param['v1_max']
#    a_max = np.sign(initpos)*acq_param['a1_max']
#    # time between two fix points where the acceleration changes (infinite jerk)  # µs
#    dt_fix = 1e-2
#
#    # positions at fixed points
#    p1 = p1p = 0
#    t_deacc = (v_max)/a_max
#    d_deacc = 0.5*a_max*t_deacc**2
#    p2 = p2p = d_deacc
#    p3 = p3p = initpos - d_deacc
#    p4 = initpos
#    pos = [p1, p1p, p2, p2p, p3, p3p, p4]
#
#    # time at fixed points
#    t1 = 0
#    t1p = dt_fix
#    t2 = t_deacc
#    t2p = t2 + dt_fix
#    t3 = t2 + abs(abs(p3 - p2)/v_max)
#    t3p = t3 + dt_fix
#    t4 = t3 + t_deacc
#    time = [t1, t1p, t2, t2p, t3, t3p, t4]
#
#    # velocity at fixed points
#    v1 = v1p = 0
#    v2 = v2p = v3 = v3p = v_max
#    v4 = 0
#    vel = [v1, v1p, v2, v2p, v3, v3p, v4]
#
#    # acceleration at fixed points
#    a1 = 0
#    a1p = a2 = a_max
#    a2p = a3 = 0
#    a3p = a4 = -a_max
#    acc = [a1, a1p, a2, a2p, a3, a3p, a4]
#
#    # if p2 is already past the center of the scan it means that the max_velocity was never
#    # reached in this case, remove two fixed points, and change the values to the curr. vel and
#    # time in the middle of the flyback
#    if abs(p2) >= abs(initpos/2):
#        t_mid = np.sqrt(abs(initpos/a_max))
#        v_mid = a_max*t_mid
#        del pos[4:6]
#        del vel[4:6]
#        del acc[4:6]
#        del time[4:6]
#        pos[2:4] = [initpos/2, initpos/2]
#        vel[2:4] = [v_mid, v_mid]
#        acc[2:4] = [a_max, -a_max]
#        time[2] = t_mid
#        time[3] = t_mid + dt_fix
#        time[4] = 2*t_mid
#
#    # generate Bernstein polynomial with piecewise spline interpolation with the fixed points
#    # give positions, velocity, acceleration, and time of fixed points
#    yder = np.array([pos, vel, acc]).T.tolist()
#    bpoly = BPoly.from_derivatives(time, yder) # bpoly time unit: µs
#
#    # get number of evaluation points
#    n_eval = int(time[-1]/acq_param['timestep'])
#    # get evaluation times for one line
#    t_eval = np.linspace(0, time[-1], n_eval)
#    # evaluate polynomial
#    poly_eval = bpoly(t_eval)
#    # return evaluated polynomial at the timestep I want
#    return poly_eval


# Copyright (C) 2020, 2021 TestaLab
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
