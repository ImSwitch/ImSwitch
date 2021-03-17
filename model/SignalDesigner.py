# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 09:20:14 2020

@author: andreas.boden
"""

import numpy as np
from scipy.interpolate import BPoly

# try:
#    from .errors import InvalidChildClassError, IncompatibilityError
# except ModuleNotFoundError:
from .errors import InvalidChildClassError


class SignalDesignerFactory:
    """Factory class for creating a SignalDesigner object. Factory checks
    that the new object is compatible with the parameters that will we 
    be sent to its make_signal method."""

    def __new__(cls, setupInfo, configKeyName):
        scanDesignerName = getattr(setupInfo.designers, configKeyName)

        #        SignalDesigner = super().__new__(cls, 'SignalDesigner.'+scanDesignerName)
        signalDesigner = globals()[scanDesignerName]()
        if signalDesigner.isValidSignalDesigner():
            return signalDesigner


class SignalDesigner:
    """Parent class for any type of SignaDesigner. Any child should define
    self._expected_parameters and its own make_signal method."""

    def __init__(self):

        self.lastSignal = None
        self.lastParameterDict = None

        self._expectedParameters = None

        # Make non-overwritable functions
        self.isValidSignalDesigner = self.__isValidSignalDesigner
        self.parameterCompatibility = self.__parameterCompatibility

    @property
    def expectedParameters(self):
        if self._expectedParameters is None:
            raise ValueError('Value "%s" is not defined')
        else:
            return self._expectedParameters

    def __isValidSignalDesigner(self):
        if self._expectedParameters is None:
            raise InvalidChildClassError('Child of SignalDesigner should define \
                                 "self.expected_parameters" in __init__.')
        else:
            return True

    def make_signal(self, parameterDict, setupInfo):
        """ Method to be defined by child. Should return a dictionary with 
        {'target': signal} pairs. """
        raise NotImplementedError("Method not implemented in child")

    def __parameterCompatibility(self, parameterDict):
        """ Method to check the compatibility of parameter 'parameterDict'
        and the expected parameters of the object. """
        expected = set(self._expectedParameters)
        incoming = set([*parameterDict])

        return expected == incoming


class BetaStageScanDesigner(SignalDesigner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._expectedParameters = ['target_device',
                                    'axis_length',
                                    'axis_step_size',
                                    'axis_startpos',
                                    'sequence_time',
                                    'sample_rate',
                                    'Return_time_seconds']

    def make_signal(self, parameterDict, setupInfo, returnFrames=False):

        if not self.parameterCompatibility(parameterDict):
            print([*parameterDict])
            print(self._expectedParameters)
            print('Stage scan parameters seem incompatible, this error should not be since this should be checked at program start-up')
            return None

        convFactors = [positioner.managerProperties['conversionFactor']
                       for positioner in setupInfo.positioners.values()]

        # Retrieve sizes
        [fast_axis_size, middle_axis_size, slow_axis_size] = \
            [(parameterDict['axis_length'][i] / convFactors[i]) for i in range(3)]

        # Retrieve step sized
        [fast_axis_step_size, middle_axis_step_size, slow_axis_step_size] = \
            [(parameterDict['axis_step_size'][i] / convFactors[i]) for i in range(3)]

        # Retrive starting position
        [fast_axis_start, middle_axis_start, slow_axis_start] = \
            [(parameterDict['axis_startpos'][i] / convFactors[i]) for i in range(3)]

        fast_axis_positions = 1 + np.int(np.ceil(fast_axis_size / fast_axis_step_size))
        middle_axis_positions = 1 + np.int(np.ceil(middle_axis_size / middle_axis_step_size))
        slow_axis_positions = 1 + np.int(np.ceil(slow_axis_size / slow_axis_step_size))

        sequenceSamples = parameterDict['sequence_time'] * parameterDict['sample_rate']
        returnSamples = parameterDict['Return_time_seconds'] * parameterDict['sample_rate']
        if not sequenceSamples.is_integer():
            print('WARNING: Non-integer number of sequence samples, rounding up')
        sequenceSamples = np.int(np.ceil(sequenceSamples))
        if not returnSamples.is_integer():
            print('WARNING: Non-integer number of return samples, rounding up')
        returnSamples = np.int(np.ceil(returnSamples))

        # Make fast axis signal
        rampSamples = fast_axis_positions * sequenceSamples
        lineSamples = rampSamples + returnSamples

        rampSignal = self.__makeRamp(fast_axis_start, fast_axis_size, rampSamples)
        returnRamp = self.__smoothRamp(fast_axis_size, fast_axis_start, returnSamples)
        fullLineSignal = np.concatenate((rampSignal, returnRamp))

        fastAxisSignal = np.tile(fullLineSignal, middle_axis_positions * slow_axis_positions)
        # Make middle axis signal
        colSamples = middle_axis_positions * lineSamples
        colValues = self.__makeRamp(middle_axis_start, middle_axis_size, middle_axis_positions)
        fullSquareSignal = np.zeros(colSamples)
        for s in range(middle_axis_positions):
            fullSquareSignal[s * lineSamples: s * lineSamples + rampSamples] = colValues[s]

            try:
                fullSquareSignal[s * lineSamples + rampSamples:(s + 1) * lineSamples] = \
                    self.__smoothRamp(colValues[s], colValues[s + 1], returnSamples)
            except IndexError:
                fullSquareSignal[s * lineSamples + rampSamples:(s + 1) * lineSamples] = \
                    self.__smoothRamp(colValues[s], middle_axis_start, returnSamples)

        middleAxisSignal = np.tile(fullSquareSignal, slow_axis_positions)

        # Make slow axis signal
        sliceSamples = slow_axis_positions * colSamples
        sliceValues = self.__makeRamp(slow_axis_start, slow_axis_size, slow_axis_positions)
        fullCubeSignal = np.zeros(sliceSamples)
        for s in range(slow_axis_positions):
            fullCubeSignal[s * colSamples:(s + 1) * colSamples - returnSamples] = sliceValues[s]

            try:
                fullCubeSignal[(s + 1) * colSamples - returnSamples:(s + 1) * colSamples] = \
                    self.__smoothRamp(sliceValues[s], sliceValues[s + 1], returnSamples)
            except IndexError:
                fullCubeSignal[(s + 1) * colSamples - returnSamples:(s + 1) * colSamples] = \
                    self.__smoothRamp(sliceValues[s], slow_axis_start, returnSamples)
        slowAxisSignal = fullCubeSignal

        sig_dict = {parameterDict['target_device'][0]: fastAxisSignal,
                    parameterDict['target_device'][1]: middleAxisSignal,
                    parameterDict['target_device'][2]: slowAxisSignal}

        if not returnFrames:
            return sig_dict, {}
        else:
            return sig_dict, [fast_axis_positions, middle_axis_positions, slow_axis_positions], {}

    def __makeRamp(self, start, end, samples):
        return np.linspace(start, end, num=samples)

    def __smoothRamp(self, start, end, samples):
        curve_half = 0.6
        n = np.int(np.floor(curve_half * samples))
        x = np.linspace(0, np.pi / 2, num=n, endpoint=True)
        signal = start + (end - start) * np.sin(x)
        signal = np.append(signal, end * np.ones(int(np.ceil((1 - curve_half) * samples))))
        return signal


class BetaTTLCycleDesigner(SignalDesigner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._expectedParameters = ['target_device',
                                    'TTLStarts[x,y]',
                                    'TTLEnds[x,y]',
                                    'sequence_time',
                                    'sample_rate']

    def make_signal(self, parameterDict, setupInfo):

        if not self.parameterCompatibility(parameterDict):
            print('TTL parameters seem incompatible, this error should not be \
                  since this should be checked at program start-up')
            return None

        targets = parameterDict['target_device']
        sampleRate = parameterDict['sample_rate']
        cycleSamples = parameterDict['sequence_time'] * sampleRate
        if not cycleSamples.is_integer():
            print('WARNING: Non-integer number of sequence samples, rounding up')
        cycleSamples = np.int(np.ceil(cycleSamples))
        signalDict = {}
        tmpSigArr = np.zeros(cycleSamples, dtype='bool')
        for i, target in enumerate(targets):
            tmpSigArr[:] = False
            for j, start in enumerate(parameterDict['TTLStarts[x,y]'][i]):
                startSamp = np.int(np.round(start * sampleRate))
                endSamp = np.int(np.round(parameterDict['TTLEnds[x,y]'][i][j] * sampleRate))
                tmpSigArr[startSamp:endSamp] = True

            signalDict[target] = np.copy(tmpSigArr)
        return signalDict


class GalvoScanDesigner(SignalDesigner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._expectedParameters = ['target_device',
                                    'axis_length',
                                    'axis_step_size',
                                    'axis_centerpos',
                                    'axis_startpos',
                                    'sequence_time',
                                    'sample_rate',
                                    'Return_time_seconds']

        self.__settlingtime = 20e3  # arbitrary for now  µs
        self.__paddingtime = 20e3  # arbitrary for now  µs
        self.__timestep = 10  # here for now, solve nicer later  µs

    def make_signal(self, parameterDict, setupInfo, returnFrames=False):
        print(parameterDict)
        print('Generating scanning curves...')
        axis_count = len([positioner for positioner in setupInfo.positioners.values() if positioner.managerProperties['scanner']])
        #print(axis_count)
        vel_max = [positioner.managerProperties['vel_max']
                for positioner in setupInfo.positioners.values() if positioner.managerProperties['scanner']]
        acc_max = [positioner.managerProperties['acc_max']
                for positioner in setupInfo.positioners.values() if positioner.managerProperties['scanner']]
        
        # get list of positions for each axis
        convFactors = [positioner.managerProperties['conversionFactor']
                       for positioner in setupInfo.positioners.values() if positioner.managerProperties['scanner']]

        # retrieve axis lengths
        axis_lengths = [(parameterDict['axis_length'][i] / convFactors[i]) for i in range(axis_count)]

        # retrieve axis step sizes
        axis_step_sizes = [(parameterDict['axis_step_size'][i] / convFactors[i]) for i in range(axis_count)]

        # retrieve axis center positions
        axis_centerpos = [(parameterDict['axis_centerpos'][i] / convFactors[i]) for i in range(axis_count)]

        axis_positions = []
        for i in range(axis_count):
            axis_positions.append(1 + np.int(np.ceil(axis_lengths[i] / axis_step_sizes[i])))

        # TODO: make this more modular to the number of scanners used?
        # fast axis signal
        #print('main-1')
        fast_pos, samples_period, n_lines = self.__generate_smooth_scan(parameterDict, vel_max, acc_max)
        #print('main-2')
        # slow (middle) axis signal
        axis_reps = self.__get_axis_reps(fast_pos, samples_period, n_lines)
        #print('main-3')
        slow_pos = self.__generate_step_scan(parameterDict, axis_reps)
        #print('main-4')

        # TODO: add
        # slow axis signal
        #####

        # TODO: update to inlcude as many signals as scanners
        # pad all signals
        fast_axis_signal, slow_axis_signal = self.__zero_padding(parameterDict, fast_pos, slow_pos)
        #print('main-5')

        sig_dict = {parameterDict['target_device'][0]: fast_axis_signal,
                    parameterDict['target_device'][1]: slow_axis_signal}

        pixels_line = int(parameterDict['axis_length'][0]/parameterDict['axis_step_size'][0])
        scanInfoDict = {
                'n_lines': int(parameterDict['axis_length'][1]/parameterDict['axis_step_size'][1]),
                'pixels_line': pixels_line,
                'samples_line': int(pixels_line * parameterDict['sequence_time'] * 1e6 / self.__timestep),
                'samples_period': samples_period-1,
                'samples_total': len(fast_axis_signal),
                'throw_startzero': int(self.__paddingtime / self.__timestep),
                'throw_settling': self._samples_settling,
                'throw_startacc': self._samples_startacc,
                'time_step': self.__timestep
        }

        #print('main-6')
        print('Scanning curves done!')
        if not returnFrames:
            return sig_dict, scanInfoDict
        else:
            return sig_dict, axis_positions, scanInfoDict

    def __generate_smooth_scan(self, parameterDict, vel_max, acc_max):
        """ Generate a smooth scanning curve with spline interpolation """ 
        #print('sm-1')
        n_lines = int(parameterDict['axis_length'][1]/parameterDict['axis_step_size'][1])  # number of lines
        v_max = vel_max[0]
        a_max = acc_max[0]
        # generate 1 period of curve
        #print('sm-2')
        curve_poly, time_fix, pos_fix = self.__linescan_poly(parameterDict, v_max, a_max)
        #print('sm-3')
        # calculate number of evaluation points for a line for decided timestep
        n_eval = int(time_fix[-1]/self.__timestep)
        # generate multiline curve for the whole scan
        #print(curve_poly)
        pos = self.__generate_smooth_multiline(curve_poly, time_fix, pos_fix, n_eval, n_lines)
        #print('sm-4')
        #print(pos)
        # add missing start and end piece
        pos_ret = self.__add_start_end(pos, pos_fix)
        #print('sm-5')
        return pos_ret, n_eval, n_lines

    def __generate_step_scan(self, parameterDict, axis_reps):
        """ Generate a step-function scanning curve """
        #print('stsc-1')
        l_scan = parameterDict['axis_length'][1]
        c_scan = parameterDict['axis_centerpos'][1]
        n_lines = int(parameterDict['axis_length'][1]/parameterDict['axis_step_size'][1])
        # create linspace for positions of interest
        positions = np.linspace(l_scan/n_lines, l_scan, n_lines) - l_scan/(n_lines*2) - l_scan/2 + c_scan
        #print('stsc-2')
        # repeat each middle element a number of times equal to the length of that between the faster axis repetitions
        #print(positions)
        #print(np.diff(axis_steps))
        pos_ret = np.repeat(positions, axis_reps)
        #print('stsc-3')
        # shift center of axis to center of image
        #pos = pos - l_scan/2
        # add y_center to all values  
        #pos_ret = pos + c_scan
        return pos_ret

    def __get_axis_reps(self, pos, samples_period, n_lines):
        """ Much faster to get reps for each slow-axis position than get_axis_steps """
        #print('ar-1')
        # get length of first line
        first_line = [np.argmax(pos)]
        #print('ar-2')
        # get length of all other lines
        mid_lines = np.repeat(samples_period-1, n_lines-2)
        #print('ar-3')
        # get length of last line
        last_line = [len(pos)-(first_line[0]+(samples_period-1)*(n_lines-2))]
        #print('ar-4')
        # concatenate all repetition lengths
        axis_reps = np.concatenate((first_line, mid_lines, last_line))
        #print('ar-5')
        return axis_reps

    #def __get_axis_reps(self, pos):
    #    """ Get the time of the steps taken on the axis provided (fast axis) """
    #    # get the positions of the velocity sign changes
    #    print('ar-1')
    #    possign = np.sign(np.diff(pos))
    #    print('ar-2')
    #    signchangevel = ((np.roll(possign, 1) - possign) != 0).astype(int)
    #    print('ar-3')
    #    # get all velocity signchanges
    #    signchanges = np.where(signchangevel == 1)[0]
    #    print('ar-4')
    #    # get the negative velocity sign changes for the start of the lines
    #    axis_reps = signchanges[::2]
    #    # append the last position, to calculate the length of the last step
    #    axis_reps = np.append(axis_reps, len(pos))
    #    print('ar-5')
    #    return axis_reps

    def __linescan_poly(self, parameterDict, v_max, a_max):
        """ Generate a Bernstein piecewise polynomial for a smooth one-line scanning curve,
        from the acquisition parameter settings, using piecewise spline interpolation """
        #print('lp-1')
        sequence_time = parameterDict['sequence_time'] * 1e6  # s --> µs
        #print(f'Dwell time: {sequence_time} µs')
        l_scan = parameterDict['axis_length'][0]  # µm
        c_scan = parameterDict['axis_centerpos'][0]  # µm
        v_scan = parameterDict['axis_step_size'][0]/sequence_time  # µm/µs
        dt_fix = 1e-2  # time between two fix points where the acceleration changes (infinite jerk)  # µs
        #print('lp-2')
        #print(f'Scan velocity: {v_scan} µm/µs')
        #print(f'Max velocity: {v_max} µm/µs')
        #print(f'Max acc: {a_max} µm/µs^2')
        #print('lp-3')        
        # positions at fixed points
        p1 = c_scan
        p2 = p2p = p1 + l_scan/2
        t_deacc = (v_scan+v_max)/a_max
        #print(f'Deacc time: {t_deacc}')
        d_deacc = v_scan*t_deacc + 0.5*(-a_max)*t_deacc**2
        #print(f'Deacc distance: {d_deacc}')
        p3 = p3p = p2 + d_deacc
        p4 = p4p = c_scan - (p3 - c_scan)
        p5 = p5p = p1 - l_scan/2
        p6 = p1
        pos = [p1, p2, p2p, p3, p3p, p4, p4p, p5, p5p, p6]
        
        # time at fixed points
        t1 = 0
        t_scanline = l_scan/v_scan
        #print(f'Scanline time: {t_scanline}')
        t2 = t1 + t_scanline/2
        t2p = t2 + dt_fix
        t3 = t2 + t_deacc
        t3p = t3 + dt_fix
        t4 = t3 + abs(p4 - p3)/v_max
        t4p = t4 + dt_fix
        t_acc = t_deacc
        t5 = t4 + t_acc
        t5p = t5 + dt_fix
        t6 = t5 + t_scanline/2
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
        #print('lp-4')        
        # if p3 is already past the center of the scan it means that the max_velocity was never reached
        # in this case, remove two fixed points, and change the values to the curr. vel and time in the
        # middle of the flyback
        if p3 <= c_scan:
            t_mid = np.roots([-a_max/2, v_scan, p2-c_scan])[0]
            v_mid = -a_max*t_mid + v_scan
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
            time[7] = time[5] + t_scanline/2
        #print('lp-5')        
        # generate Bernstein polynomial with piecewise spline interpolation with the fixed points
        # give positions, velocity, acceleration, and time of fixed points
        yder = np.array([pos, vel, acc]).T.tolist()
        #print(time), print(yder)
        bpoly = BPoly.from_derivatives(time, yder) # bpoly time unit: µs
        #print('lp-6')        
        # return polynomial, that can be evaluated at any timepoints you want
        # return fixed points position and time
        return bpoly, time, pos

    def __generate_smooth_multiline(self, pos_bpoly, time_fix, pos_fix, n_eval, n_lines):
        """ Generate a smooth multiline curve by evaluating the polynomial with the clock frequency used and copying it """ 
        # get evaluation times for one line
        #print(time_fix)
        #print('smml-1')
        #print(f'Number of evaluation points, one period: {n_eval}')
        x_eval = np.linspace(0, time_fix[-1], n_eval)
        #print('smml-2')
        #print(x_eval)
        # evaluate polynomial
        x_bpoly = pos_bpoly(x_eval)
        #print('smml-3')
        #print(x_bpoly)
        pos_ret = []
        # concatenate for number of lines in scan
        pos_ret = np.tile(x_bpoly[:-1], n_lines-1)
        #print('smml-4')
        return pos_ret

    def __add_start_end(self, pos, pos_fix):
        """ Add start and end half-lines to smooth scanning curve """
        # generate three pieces, two before and one after, to be concatenated to the given positions array
        #print(pos)
        #print(t_settling)
        #print('se-1')
        settlinglen = int(self.__settlingtime / self.__timestep)  # initial settling time before first line
        pos_pre1 = np.repeat(np.min(pos),settlinglen)
        self._samples_settling = len(pos_pre1)
        #print('se-2')
        pos_pre2 = pos[np.where(pos==np.min(pos))[0][-1]:]
        #print('se-3')
        pos_post1 = pos[:np.argmin(abs(pos[:np.where(pos==np.max(pos))[0][0]]-pos_fix[2]))]
        #print('se-4')
        pos_ret = np.concatenate((pos_pre1, pos_pre2, pos, pos_post1))
        self._samples_startacc = len(pos_pre2) - len(pos_post1)
        #print('se-5')
        return pos_ret

    def __zero_padding(self, parameterDict, pos1, pos2):
        """ Pad zeros to the end of two scanning curves, for initial and final settling of galvos """
        #print('zp-1')
        padlen = int(self.__paddingtime / self.__timestep)
        # check that the length of pos1 and pos2 are identical
        padlen1 = np.array([padlen,padlen])
        padlen2 = np.array([padlen,padlen])
        lendiff = abs(len(pos1)-len(pos2))
        #print('zp-2')
        # if not equal, add to the correct padding length to make them equal
        if lendiff != 0:
            if lendiff > 0:
                padlen2 = padlen2 + np.array([0,lendiff])
                #print(padlen2)
            elif lendiff < 0:
                padlen1 = padlen1 + np.array([0,lendiff])
                #print(padlen1)
        #print('zp-3')
        # pad position arrays
        pos_ret1 = np.pad(pos1, padlen1, 'constant', constant_values=0)
        #print('zp-4')
        pos_ret2 = np.pad(pos2, padlen2, 'constant', constant_values=0)
        #print('zp-5')
        return pos_ret1, pos_ret2
