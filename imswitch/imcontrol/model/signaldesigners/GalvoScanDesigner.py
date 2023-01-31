import numpy as np
from scipy.interpolate import BPoly

from .basesignaldesigners import ScanDesigner

from imswitch.imcommon.model import initLogger


class GalvoScanDesigner(ScanDesigner):
    """ Scan designer for scan systems with galvanometric mirrors.

    Designer params: None
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        self._expectedParameters = ['target_device',
                                    'axis_length',
                                    'axis_step_size',
                                    'axis_centerpos',
                                    'axis_startpos',
                                    'sequence_time']

    def checkSignalComp(self, scanParameters, setupInfo, scanInfo):
        """ Check analog scanning signals so that they are inside the range of
        the acceptable scanner voltages."""
        for i in range(len(scanParameters['target_device'])):
            if scanParameters['target_device'][i] != 'None':
                if np.ceil(scanParameters['axis_length'][i]/scanParameters['axis_step_size'][i]) > 1:
                    positioner = setupInfo.positioners[scanParameters['target_device'][i]]
                    minv = positioner.managerProperties['minVolt']
                    maxv = positioner.managerProperties['maxVolt']
                    if (scanInfo['minmaxes'][i][0] < minv or scanInfo['minmaxes'][i][1] > maxv):
                        return False
        return True

    def checkSignalLength(self, scanParameters, setupInfo):
        """ Check that the signal would not be too large (to be stored in
        the RAM and to be generated and run inside a reasonable time). """
        #TODO: change limits below later, to be more representative of what we want. Also think about changing the
        # way >d3 steps are generated and sent to the nidaq - probably should run those scans as simple d2 scans and
        # repeat them, with steps on the axes that needs steps between. Keep track of that in ScanController for
        # example, alternatively directly in NidaqController.runScan?
        device_count = len([positioner for positioner in setupInfo.positioners.values() if positioner.forScanning])
        # retrieve axis lengths in um of active axes
        axis_length = [scanParameters['axis_length'][i] for i in range(device_count)
                            if np.ceil(scanParameters['axis_length'][i]/scanParameters['axis_step_size'][i]) > 1]
        axis_count_scan = len(axis_length)
        # retrieve axis step sizes in um of active axes
        axis_step_size = [scanParameters['axis_step_size'][i] for i in range(device_count)
                            if np.ceil(scanParameters['axis_length'][i]/scanParameters['axis_step_size'][i]) > 1]
        # get list of number of axis steps
        n_steps_dx = [int(axis_length[i] / axis_step_size[i]) for i in range(axis_count_scan)]
        # get list of number of axis scan samples, for first two axes initially
        scan_steps = np.prod(n_steps_dx)
        scan_time = scan_steps * scanParameters['sequence_time']
        if scan_time > 60*10:  # 10 minutes
            return False
        elif scan_steps > 1e7:
            return False
        return True

    def make_signal(self, parameterDict, setupInfo):
        # time step of evaluated scanning curves [µs]
        self.__timestep = 1e6 / setupInfo.scan.sampleRate
        # arbitrary for now - should calculate this based on the abs(biggest) axis_centerpos and the
        # max speed/acc, as that is what limits time it takes for axes to get to the right position
        self.__minsettlingtime = 1000
        # arbitrary for now  µs
        self.__paddingtime = 1000

        positioners = [positioner for positioner in setupInfo.positioners.values()
                       if positioner.forScanning]
        positionerNames = [positioner for positioner in setupInfo.positioners
                           if setupInfo.positioners[positioner].forScanning]
        positionersProps = [positioner.managerProperties for positioner in positioners]

        device_count = len(positioners)
        # convert vel_max from µm/µs to V/µs
        vel_max = [positionerProps['vel_max'] / positionerProps['conversionFactor']
                   if 'vel_max' in positionerProps else 1e6
                   for positionerProps in positionersProps]
        # convert acc_max from µm/µs^2 to V/µs^2
        acc_max = [positionerProps['acc_max'] / positionerProps['conversionFactor']
                   if 'acc_max' in positionerProps else 1e6
                   for positionerProps in positionersProps]

        # get conversion factors for scanning axes
        convFactors = [positionerProps['conversionFactor'] 
                       if 'conversionFactor' in positionerProps else 1
                       for positionerProps in positionersProps]

        # retrieve axis order of active axes, to compare with the positionerNames
        self.axis_devs_order = [parameterDict['target_device'][i] for i in range(device_count)
                                if np.ceil(parameterDict['axis_length'][i]/parameterDict['axis_step_size'][i]) > 1]
        # retrieve axis lengths in V of active axes
        self.axis_length = [(parameterDict['axis_length'][i] / convFactors[positionerNames.index(self.axis_devs_order[i])])
                            for i in range(device_count)
                            if np.ceil(parameterDict['axis_length'][i]/parameterDict['axis_step_size'][i]) > 1]
        # retrieve axis step sizes in V of active axes
        self.axis_step_size = [(parameterDict['axis_step_size'][i] / convFactors[positionerNames.index(self.axis_devs_order[i])])
                               for i in range(device_count)
                               if np.ceil(parameterDict['axis_length'][i]/parameterDict['axis_step_size'][i]) > 1]
        # retrieve axis center positions in V of active axes
        self.axis_centerpos = [(parameterDict['axis_centerpos'][i] / convFactors[positionerNames.index(self.axis_devs_order[i])])
                               for i in range(device_count)
                               if np.ceil(parameterDict['axis_length'][i]/parameterDict['axis_step_size'][i]) > 1]
        # retrieve axis velocity max of active axes
        self.axis_vel_max = [vel_max[positionerNames.index(self.axis_devs_order[i])]
                               for i in range(device_count)
                               if np.ceil(parameterDict['axis_length'][i]/parameterDict['axis_step_size'][i]) > 1]
        # retrieve axis acceleration max of active axes
        self.axis_acc_max = [acc_max[positionerNames.index(self.axis_devs_order[i])]
                               for i in range(device_count)
                               if np.ceil(parameterDict['axis_length'][i]/parameterDict['axis_step_size'][i]) > 1]

        axis_count_scan = len(self.axis_devs_order)

        # get list of number of axis steps
        n_steps_dx = [int(self.axis_length[i] / self.axis_step_size[i]) for i in range(axis_count_scan)]
        # get list of number of axis scan samples, for first two axes initially
        n_scan_samples_dx = [int(round(n_steps_dx[i] * parameterDict['sequence_time'] * 1e6 / self.__timestep)) for i in range(1)]
        n_scan_samples_dx.insert(0, 1)
        pixel_sizes = [parameterDict['axis_step_size'][i] for i in range(axis_count_scan)]

        # get list of d1 positions for each active axis
        axis_positions = []
        for i in range(axis_count_scan):
            axis_positions.append(int(np.ceil(self.axis_length[i] / self.axis_step_size[i])))

        self.__settlingtime = self.__calc_settling_time(self.axis_length, self.axis_centerpos,
                                                        self.axis_vel_max, self.axis_acc_max)

        # generate axis signals for all d axes
        pos = []  # list with all axis positions lists
        # d1 axis signal
        axis = 0
        pos_temp, samples_d2_period = self.__generate_smooth_scan(parameterDict, self.axis_vel_max[0], self.axis_acc_max[0], n_steps_dx[1])
        pos.append(pos_temp)

        # initiate pad length list
        pad_maxes = [0,0]

        # d2 axis signal
        if axis_count_scan > 1:
            axis = 1
            axis_reps = self.__get_axis_reps(pos[0], samples_d2_period, n_steps_dx[1])
            smooth = False if 'mock' in self.axis_devs_order[axis].lower() else True
            pos_temp = self.__generate_step_scan(axis, n_scan_samples_dx[axis], n_steps_dx[axis], self.axis_devs_order[axis], smooth, v_max=self.axis_vel_max[axis], a_max=self.axis_acc_max[axis], axis_reps=axis_reps)
            pos.append(pos_temp)
            n_scan_samples_dx.append(len(pos[0]))

        # d>2 axes signals - all generated as pure step signals
        if axis_count_scan > 2:
            for axis in range(2, axis_count_scan):
                pos, pad_max = self.__zero_padding(pos, padlen_base=0)
                pad_maxes.append(pad_max)
                pos = self.__repeat_dlower(pos, n_steps_dx[axis])
                smooth = False if 'mock' in self.axis_devs_order[axis].lower() else True
                pos_temp = self.__generate_step_scan(axis, n_scan_samples_dx[axis], n_steps_dx[axis], self.axis_devs_order[axis], smooth, v_max=self.axis_vel_max[axis], a_max=self.axis_acc_max[axis])
                pos.append(pos_temp)
                n_scan_samples_dx.append(len(pos[0]))

        # pad all signals with zeros, for initial and final settling of galvos and safety start and end
        axis_signals, pad_max = self.__zero_padding(pos, padlen_base=int(round(self.__paddingtime / self.__timestep)))
        pad_maxes.append(pad_max)

        # add all signals to a signal dictionary
        sig_dict = {parameterDict['target_device'][i]: axis_signals[i] for i in range(axis_count_scan)}

        # create scan information dictionary scanInfoDict
        # with parameters that are important to relay to TTLCycleDesigner
        # and/or image acquisition managers (such as APDManager)
        scanInfoDict = {
            'axis_names': self.axis_devs_order,
            'img_dims': n_steps_dx,
            'scan_samples': n_scan_samples_dx,
            'pixel_sizes': pixel_sizes,
            'minmaxes': [[min(axis_signals[i]), max(axis_signals[i])] for i in range(axis_count_scan)],
            'scan_samples_total': len(axis_signals[0]),
            'scan_throw_startzero': int(round(self.__paddingtime / self.__timestep)),
            'scan_throw_initpos': self._samples_initpos,
            'scan_throw_settling': self._samples_settling,
            'scan_throw_startacc': self._samples_startacc,
            'scan_throw_finalpos': self._samples_finalpos,
            'scan_time_step': round(self.__timestep * 1e-6, ndigits=10),
            'dwell_time': parameterDict['sequence_time'],
            'phase_delay': parameterDict['phase_delay'],
            'scan_samples_d2_period': samples_d2_period - 1,
            'padlens': pad_maxes
        }
        #'extra_laser_on': parameterDict['extra_laser_on']
        #self._logger.debug(scanInfoDict)

        self.__plot_curves(plot=False, signals=axis_signals)  # for debugging

        self._logger.info(f'Scanning curves generated, third dimension step time: {round(self.__timestep * 1e-6 * n_scan_samples_dx[2], ndigits=5)} s.')
        return sig_dict, axis_positions, scanInfoDict

    def __calc_settling_time(self, axis_length, axis_centerpos, vel_max, acc_max):
        """ Calculate settling time based on first two axis parameters.
        TODO: fix this to include all axes, as smooth axes can be in other positions?
        """
        t_initpos_vc_d2 = abs(axis_centerpos[1] - axis_length[1] / 2) / vel_max[1]
        t_initpos_vc_d1 = abs(axis_centerpos[0] - axis_length[0] / 2) / vel_max[0]
        t_acc_d2 = vel_max[1] / acc_max[1]
        t_acc_d1 = vel_max[0] / acc_max[0]
        t_initpos_d2 = t_initpos_vc_d2 + 2 * t_acc_d2
        t_initpos_d1 = t_initpos_vc_d1 + 2 * t_acc_d1
        settlingtime = self.__minsettlingtime + np.max([0, t_initpos_d2 - t_initpos_d1])
        return settlingtime

    def __generate_smooth_scan(self, parameterDict, v_max, a_max, n_d2):
        """ Generate a smooth scanning curve with spline interpolation """
        curve_poly, time_fix, pos_fix = self.__d2scan_poly(parameterDict, v_max, a_max)
        # calculate number of evaluation points for a d2 step for decided timestep
        n_eval = int(time_fix[-1] / self.__timestep)
        # generate multi-d2-step curve for the whole d3 step
        pos = self.__generate_smooth_multid2(curve_poly, time_fix, pos_fix, n_eval, n_d2)
        # add missing start and end piece
        pos_ret = self.__add_start_end(pos, pos_fix, v_max, a_max)
        return pos_ret, n_eval

    def __generate_step_scan(self, dim, len_axis, n_axis, axis_name, smooth, v_max=0, a_max=0, axis_reps=[0,0]):
        """ Generate a step-function scanning curve, with smooth initial positioning or not. """
        l_scan = self.axis_length[dim]
        c_scan = self.axis_centerpos[dim]
        # create linspace for axis positions
        positions = (np.linspace(l_scan / n_axis, l_scan, n_axis) -
                     l_scan / (n_axis * 2) - l_scan / 2 + c_scan)
        if 'mock' in axis_name.lower():
            positions = positions - positions[0]
        if smooth:
            # generate the initial smooth positioning curve
            pos_init = self.__init_positioning(positions[0], v_max, a_max)
            # generate the final smooth positioning curve
            pos_final = self.__final_positioning(positions[-1], v_max, a_max)
        if dim==1: # and 'mock' not in axis_name.lower():
            if 'mock' not in axis_name.lower():
                axis_reps[0] = axis_reps[0] - len(pos_init)
            pos_ret = np.repeat(positions, axis_reps)
        else:
            pos_ret = np.repeat(positions, len_axis)
        if smooth:
            pos_ret = np.concatenate((pos_init, pos_ret, pos_final))
        return pos_ret

    def __repeat_dlower(self, pos, n_steps_axis):
        """ Repeat the current positions, for all dimensions,
        for the number of steps on the new axis. """
        pos_ret = [np.tile(pos_dim, n_steps_axis) for pos_dim in pos]
        return pos_ret

    def __get_axis_reps(self, pos, samples_period, n_d2):
        """ Get reps for each step on d2 axis, by looking at the maximum and
        periods of the d1 axis """
        start_skip = self._samples_initpos + self._samples_settling + self._samples_startacc
        end_skip = self._samples_finalpos
        # get length of first d2 step
        first_d2 = [np.argmax(pos[start_skip:-end_skip]) + start_skip]
        # get length of all other d2 steps
        rest_d2s = np.repeat(samples_period - 1, n_d2 - 1)
        # concatenate all repetition lengths
        return np.concatenate((first_d2, rest_d2s))

    def __d2scan_poly(self, parameterDict, v_max, a_max):
        """ Generate a Bernstein piecewise polynomial for a smooth one-d2-step
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
        t_scand2 = l_scan / v_scan
        t2 = t1 + t_scand2 / 2
        t2p = t2 + dt_fix
        t3 = t2 + t_deacc
        t3p = t3 + dt_fix
        t4 = t3 + abs(p4 - p3) / v_max
        t4p = t4 + dt_fix
        t_acc = t_deacc
        t5 = t4 + t_acc
        t5p = t5 + dt_fix
        t6 = t5 + t_scand2 / 2
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
            time[7] = time[5] + t_scand2 / 2
        # generate Bernstein polynomial with piecewise spline interpolation with the fixed points
        # give positions, velocity, acceleration, and time of fixed points
        yder = np.array([pos, vel, acc]).T.tolist()

        bpoly = BPoly.from_derivatives(time, yder)  # bpoly time unit: µs
        # return polynomial, that can be evaluated at any timepoints you want
        # return fixed points position and time
        return bpoly, time, pos

    def __generate_smooth_multid2(self, pos_bpoly, time_fix, pos_fix, n_eval, n_d2):
        """ Generate a smooth multi-d2-step curve by evaluating the polynomial with
        the clock frequency used and copying it """
        # get evaluation times for one d2 step
        x_eval = np.linspace(0, time_fix[-1], n_eval)
        # evaluate polynomial
        x_bpoly = pos_bpoly(x_eval)
        pos_ret = []
        # concatenate for number of d2 steps in scan
        pos_ret = np.tile(x_bpoly[:-1], n_d2 - 1)
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
        # get evaluation times for one d2 step
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
        # get evaluation times for one d2 step
        t_eval = np.linspace(0, time[-1], n_eval)
        # evaluate polynomial
        poly_eval = bpoly(t_eval)
        # return evaluated polynomial at the timestep I want
        return poly_eval

    def __add_start_end(self, pos, pos_fix, v_max, a_max):
        """ Add start and end half-d2-steps to smooth scanning curve """
        # generate five pieces, three before and two after, to be concatenated to the given positions array
        # initial smooth acceleration piece from 0
        pos_pre1 = self.__init_positioning(initpos=np.min(pos), v_max=v_max, a_max=a_max)
        self._samples_initpos = len(pos_pre1)
        # initial settling time before first d2 step
        settlinglen = int(round(self.__settlingtime / self.__timestep))
        pos_pre2 = np.repeat(np.min(pos), settlinglen)  # settling positions
        self._samples_settling = len(pos_pre2)
        pos_pre3 = pos[np.where(pos == np.min(pos))[0][-1]:]  # first half scan curve
        # alt: last half scan curve to last peak after last d2 step
        pos_post1 = pos[:np.where(pos == np.max(pos))[0][0]]
        # final smooth acceleration piece from max to 0
        pos_post2 = self.__final_positioning(initpos=pos_post1[-1], v_max=v_max, a_max=a_max)
        pos_ret = np.concatenate((pos_pre1, pos_pre2, pos_pre3, pos, pos_post1, pos_post2))
        # half scan d2 step
        pos_halfscand2step =\
            pos[:np.argmin(abs(pos[:np.where(pos == np.max(pos))[0][0]] - pos_fix[2]))]
        self._samples_startacc = len(pos_pre3) - len(pos_halfscand2step)
        self._samples_finalpos = len(pos_post2)
        return pos_ret

    def __zero_padding(self, pos, padlen_base):
        """ Pad zeros to the beginning and end of all scanning curves. """
        pos_ret = []  # return array of padded axis signals
        n_axes = len(pos)  # number of axes
        padlens = [np.array([padlen_base, padlen_base]) for i in range(n_axes)]  # basic padding length added to arrays for all axes
        # calculate padding lengths for all axes
        # get longest axis index
        pos_lens = [len(pos_i) for pos_i in pos]
        pos_max_len = np.argmax(pos_lens)
        # get difference in length between longest and all other axes
        pos_len_diffs = [pos_lens[pos_max_len] - pos_len for pos_len in pos_lens]
        # add length differences to padlens for each axis, if differences sum != 0
        if np.sum(pos_len_diffs) != 0:
            padlens = [padlen_i + np.array([0, pos_len_diffs[i]]) for i, padlen_i in enumerate(padlens)]
        # pad arrays
        for axis, pos_axis in enumerate(pos):
            pos_temp = np.pad(pos_axis, padlens[axis], 'constant', constant_values=0)
            pos_ret.append(pos_temp)
        ## get maximum pad length
        #pad_max = 0
        #for padlen in padlens:
        #    if padlen[1] > pad_max:
        #        pad_max = padlen[1]
        return pos_ret, padlens[0][1]

    def __plot_curves(self, plot, signals):
        """ Plot all scan curves, for debugging. """
        if plot:
            import matplotlib.pyplot as plt
            plt.figure(1)
            plt.clf()
            for i, signal in enumerate(signals):
                plt.plot(signal - 0.01 * i)
                target = self.axis_devs_order[i]
                self._logger.debug(f'Signal length {target}: {len(signal)}')
            plt.show()

# Copyright (C) 2020-2021 ImSwitch developers
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
