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
                                    'return_time']

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
        returnSamples = parameterDict['return_time'] * parameterDict['sample_rate']
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

        # scanInfoDict, for parameters that are important to relay to TTLCycleDesigner and/or image acquisition managers
        scanInfoDict = {
        }
        if not returnFrames:
            return sig_dict, scanInfoDict
        else:
            return sig_dict, [fast_axis_positions, middle_axis_positions, slow_axis_positions], scanInfoDict

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
                                    'TTL_start',
                                    'TTL_end',
                                    'sequence_time',
                                    'sample_rate']

    def make_signal(self, parameterDict):

        if not self.parameterCompatibility(parameterDict):
            print('TTL parameters seem incompatible, this error should not be \
                  since this should be checked at program start-up')
            return None

        targets = parameterDict['target_device']
        sampleRate = parameterDict['sample_rate']
        cycleSamples = parameterDict['sequence_time'] * sampleRate
        #print(f'DO sample rate: {sampleRate}, cycleSamples: {cycleSamples}')
        if not cycleSamples.is_integer():
            print('WARNING: Non-integer number of sequence samples, rounding up')
        cycleSamples = np.int(np.ceil(cycleSamples))
        signalDict = {}
        tmpSigArr = np.zeros(cycleSamples, dtype='bool')
        for i, target in enumerate(targets):
            tmpSigArr[:] = False
            for j, start in enumerate(parameterDict['TTL_start'][i]):
                startSamp = np.int(np.round(start * sampleRate))
                endSamp = np.int(np.round(parameterDict['TTL_end'][i][j] * sampleRate))
                tmpSigArr[startSamp:endSamp] = True

            signalDict[target] = np.copy(tmpSigArr)

        #TODO: add signal-tiling and zero-padding in here for this TTL cycle designer as well (see PointScanTTLCycleDesigner)

        return signalDict


class PointScanTTLCycleDesigner(SignalDesigner):
    """ Line-based TTL cycle designer, for point-scanning applications. 
    Treat input ms as lines. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._expectedParameters = ['target_device',
                                    'TTL_start',
                                    'TTL_end',
                                    'sequence_time',
                                    'sample_rate']

    def make_signal(self, parameterDict, scanInfoDict=None):
        if not self.parameterCompatibility(parameterDict):
            print('TTL parameters seem incompatible, this error should not be \
                  since this should be checked at program start-up')
            return None
        
        if not scanInfoDict:
            return self.__make_signal_stationary(parameterDict)
        else:
            signal_dict = {}

            targets = parameterDict['target_device']
            sample_rate = parameterDict['sample_rate']
            samples_pixel = parameterDict['sequence_time'] * sample_rate
            pixels_line = scanInfoDict['pixels_line']
            samples_line = scanInfoDict['scan_samples_line']
            samples_total = scanInfoDict['scan_samples_total']

            zeropad_syncdelay = 0
            zeropad_lineflyback = scanInfoDict['scan_samples_period'] - scanInfoDict['scan_samples_line']
            zeropad_initpos = scanInfoDict['scan_throw_initpos']
            zeropad_settling = scanInfoDict['scan_throw_settling']
            zeropad_start = scanInfoDict['scan_throw_startzero']
            zeropad_startacc = scanInfoDict['scan_throw_startacc']
            zeropad_finalpos = scanInfoDict['scan_throw_finalpos']
            # Tile and pad TTL signals according to fast axis scan parameters
            for i, target in enumerate(targets):
                signal_line = np.zeros(samples_line, dtype='bool')
                for j, start, end in enumerate(zip(parameterDict['TTL_start'][i], parameterDict['TTL_end'][i])):
                    start_on = np.min(np.int(np.round(start * samples_line)), samples_line)
                    end_on =  np.min(np.int(np.round(end * samples_line)), samples_line)
                    signal_line[start_on:end:on] = True
                
                signal_period = np.append(signal_line, np.zeros(zeropad_lineflyback, dtype='bool'))
                #TODO: # only do 2D-scan for now, fix for 3D-scan
                signal = np.tile(signal_period, scanInfoDict['n_lines'] - 1)  # all lines except last
                signal = np.append(signal, signal_line)  # add last line (does without flyback)

                signal = np.append(np.zeros(zeropad_syncdelay, dtype='bool'), signal)  # pad a delay for synchronizing scan position with TTL
                signal = np.append(np.zeros(zeropad_startacc, dtype='bool'), signal)  # pad first line acceleration
                signal = np.append(np.zeros(zeropad_settling, dtype='bool'), signal)  # pad start settling
                signal = np.append(np.zeros(zeropad_initpos, dtype='bool'), signal)  # pad initpos
                signal = np.append(np.zeros(zeropad_start, dtype='bool'), signal)  # pad start zeros
                zeropad_end = samples_total - len(signal)
                signal = np.append(signal, np.zeros(zeropad_end, dtype='bool'))  # pad end zeros to same length as analog scanning

                signal_dict[target] = signal
            
            # return signal_dict, which contains bool arrays for each target
            return signal_dict

    def __make_signal_stationary(self, parameterDict):
        signal_dict_pixel = self.__pixel_stationary(parameterDict)
        return signal_dict_pixel

    def __pixel_stationary(self, parameterDict)
        targets = parameterDict['target_device']
        sample_rate = parameterDict['sample_rate']
        samples_cycle = parameterDict['sequence_time'] * sample_rate
        if not samples_cycle.is_integer():
            print('WARNING: Non-integer number of sequence samples, rounding up')
        samples_cycle = np.int(np.ceil(samples_cycle))
        signalDict = {}
        tmpSigArr = np.zeros(samples_cycle, dtype='bool')
        for i, target in enumerate(targets):
            tmpSigArr[:] = False
            for j, start in enumerate(parameterDict['TTL_start'][i]):
                startSamp = np.int(np.round(start * sample_rate))
                endSamp = np.int(np.round(parameterDict['TTL_end'][i][j] * sample_rate))
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
                                    'return_time']


    def make_signal(self, parameterDict, setupInfo, returnFrames=False):
        self.__timestep = 1e6 / parameterDict['sample_rate']  # time step of evaluated scanning curves [µs]
        self.__settlingtime = 300  # arbitrary for now  µs
        self.__paddingtime = 300  # arbitrary for now  µs
        #print(parameterDict)
        #print('Generating scanning curves...')
        axis_count = len([positioner for positioner in setupInfo.positioners.values() if positioner.managerProperties['scanner']])
        #print(axis_count)
        vel_max = [positioner.managerProperties['vel_max']
                for positioner in setupInfo.positioners.values() if positioner.managerProperties['scanner']]
        acc_max = [positioner.managerProperties['acc_max']
                for positioner in setupInfo.positioners.values() if positioner.managerProperties['scanner']]
        
        # get list of positions for each axis
        convFactors = [positioner.managerProperties['conversionFactor']
                       for positioner in setupInfo.positioners.values() if positioner.managerProperties['scanner']]

        # retrieve axis lengths in V
        self.axis_length = [(parameterDict['axis_length'][i] / convFactors[i]) for i in range(axis_count)]
        #print(self.axis_length)
        # retrieve axis step sizes in V
        self.axis_step_size = [(parameterDict['axis_step_size'][i] / convFactors[i]) for i in range(axis_count)]
        #print(self.axis_step_size)
        # retrieve axis center positions in V
        self.axis_centerpos = [(parameterDict['axis_centerpos'][i] / convFactors[i]) for i in range(axis_count)]
        #print(self.axis_centerpos)

        axis_positions = []
        for i in range(axis_count):
            axis_positions.append(np.int(np.ceil(self.axis_length[i] / self.axis_step_size[i])))

        # TODO: make this more modular to the number of scanners used?
        # fast axis signal
        #print('main-1')
        fast_pos, samples_period, n_lines = self.__generate_smooth_scan(parameterDict, vel_max[0], acc_max[0])
        #print('main-2')
        # slow (middle) axis signal
        axis_reps = self.__get_axis_reps(fast_pos, samples_period, n_lines)
        #print('main-3')
        slow_pos = self.__generate_step_scan(parameterDict, axis_reps, vel_max[1], acc_max[1])
        #print('main-4')

        # TODO: add
        # slow axis signal
        #####

        # TODO: update to inlcude as many signals as scanners
        # pad all signals
        #print(np.shape(fast_pos))
        fast_axis_signal, slow_axis_signal = self.__zero_padding(parameterDict, fast_pos, slow_pos)
        #print(np.shape(fast_axis_signal))
        #print('main-5')

        sig_dict = {parameterDict['target_device'][0]: fast_axis_signal,
                    parameterDict['target_device'][1]: slow_axis_signal}

        pixels_line = int(self.axis_length[0]/self.axis_step_size[0])
        # scanInfoDict, for parameters that are important to relay to TTLCycleDesigner and/or image acquisition managers
        scanInfoDict = {
                'n_lines': int(self.axis_length[1]/self.axis_step_size[1]),
                'pixels_line': pixels_line,
                'scan_samples_line': int(pixels_line * parameterDict['sequence_time'] * 1e6 / self.__timestep),
                'scan_samples_period': samples_period-1,
                'scan_samples_total': len(fast_axis_signal),
                'scan_throw_startzero': int(self.__paddingtime / self.__timestep),
                'scan_throw_initpos': self._samples_initpos,
                'scan_throw_settling': self._samples_settling,
                'scan_throw_startacc': self._samples_startacc,
                'scan_throw_finalpos': self._samples_finalpos,
                'scan_time_step': round(self.__timestep * 1e-6, ndigits=10),
                'dwell_time': parameterDict['sequence_time']
        }

        #print('main-6')
        print('Scanning curves generated.')
        if not returnFrames:
            return sig_dict, scanInfoDict
        else:
            return sig_dict, axis_positions, scanInfoDict

    def __generate_smooth_scan(self, parameterDict, v_max, a_max):
        """ Generate a smooth scanning curve with spline interpolation """ 
        #print('sm-1')
        n_lines = int(self.axis_length[1]/self.axis_step_size[1])  # number of lines
        #v_max = vel_max[0]
        #a_max = acc_max[0]
        # generate 1 period of curve
        #print('sm-2')
        curve_poly, time_fix, pos_fix = self.__linescan_poly(parameterDict, v_max, a_max)
        #print('sm-3')
        # calculate number of evaluation points for a line for decided timestep
        n_eval = int(time_fix[-1]/self.__timestep)
        # generate multiline curve for the whole scan
        #print(curve_poly)
        pos = self.__generate_smooth_multiline(curve_poly, time_fix, pos_fix, n_eval, n_lines)
        #print(np.shape(pos))
        #print('sm-4')
        #print(pos)
        # add missing start and end piece
        pos_ret = self.__add_start_end(pos, pos_fix, v_max, a_max)
        #print('sm-5')
        return pos_ret, n_eval, n_lines

    def __generate_step_scan(self, parameterDict, axis_reps, v_max, a_max):
        """ Generate a step-function scanning curve, with initial smooth positioning """
        #print('stsc-1')
        l_scan = self.axis_length[1]
        c_scan = self.axis_centerpos[1]
        n_lines = int(self.axis_length[1]/self.axis_step_size[1])
        # create linspace for axis positions
        positions = np.linspace(l_scan/n_lines, l_scan, n_lines) - l_scan/(n_lines*2) - l_scan/2 + c_scan
        #print('stsc-2')
        # generate the initial smooth positioning curve
        pos_init = self.__init_positioning(positions[0], v_max, a_max)
        axis_reps[0] = axis_reps[0]-len(pos_init)
        # generate the final smooth positioning curve
        pos_final = self.__final_positioning(positions[-1], v_max, a_max)
        axis_reps[-1] = axis_reps[-1]-len(pos_final)
        # repeat each middle element a number of times equal to the length of that between the faster axis repetitions
        #print(positions)
        #print(np.diff(axis_steps))
        pos_steps = np.repeat(positions, axis_reps)
        #print('stsc-3')
        # shift center of axis to center of image
        #pos = pos - l_scan/2
        # add y_center to all values  
        #pos_ret = pos + c_scan
        # add initial positioning
        pos_ret = np.concatenate((pos_init, pos_steps, pos_final))
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

    def __linescan_poly(self, parameterDict, v_max, a_max):
        """ Generate a Bernstein piecewise polynomial for a smooth one-line scanning curve,
        from the acquisition parameter settings, using piecewise spline interpolation """
        #print('lp-1')
        sequence_time = parameterDict['sequence_time'] * 1e6  # s --> µs
        #print(f'Dwell time: {sequence_time} µs')
        l_scan = self.axis_length[0]  # µm
        c_scan = self.axis_centerpos[0]  # µm
        v_scan = self.axis_step_size[0]/sequence_time  # µm/µs
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

    def __init_positioning(self, initpos, v_max, a_max):
        v_max = np.sign(initpos)*v_max
        a_max = np.sign(initpos)*a_max
        dt_fix = 1e-2  # time between two fix points where the acceleration changes (infinite jerk)  # µs
        
        # positions at fixed points
        p1 = p1p = 0
        t_deacc = (v_max)/a_max
        #print(f'Deacc time: {t_deacc}')
        d_deacc = 0.5*a_max*t_deacc**2
        #print(f'Deacc distance: {d_deacc}')
        p2 = p2p = d_deacc
        p3 = p3p = initpos - d_deacc
        p4 = initpos
        pos = [p1, p1p, p2, p2p, p3, p3p, p4]
        
        # time at fixed points
        t1 = 0
        t1p = dt_fix
        t2 = t_deacc
        t2p = t2 + dt_fix
        t3 = t2 + abs(abs(p3 - p2)/v_max)
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
        
        # if p2 is already past the center of the scan it means that the max_velocity was never reached
        # in this case, remove two fixed points, and change the values to the curr. vel and time in the
        # middle of the flyback
        if abs(p2) >= abs(initpos/2):
            t_mid = np.sqrt(abs(initpos/a_max))
            v_mid = a_max*t_mid
            del pos[4:6]
            del vel[4:6]
            del acc[4:6]
            del time[4:6]
            pos[2:4] = [initpos/2, initpos/2]
            vel[2:4] = [v_mid, v_mid]
            acc[2:4] = [a_max, -a_max]
            time[2] = t_mid
            time[3] = t_mid + dt_fix
            time[4] = 2*t_mid
        
        # generate Bernstein polynomial with piecewise spline interpolation with the fixed points
        # give positions, velocity, acceleration, and time of fixed points        
        yder = np.array([pos, vel, acc]).T.tolist()
        bpoly = BPoly.from_derivatives(time, yder) # bpoly time unit: µs

        # get number of evaluation points
        n_eval = int(time[-1]/self.__timestep)
        # get evaluation times for one line
        t_eval = np.linspace(0, time[-1], n_eval)
        # evaluate polynomial
        poly_eval = bpoly(t_eval)
        # return evaluated polynomial at the timestep I want
        return poly_eval

    def __final_positioning(self, initpos, v_max, a_max):
        """ Generate a polynomial for a smooth final positioning scanning curve, from the acquisition parameter settings """
        v_max = -np.sign(initpos)*v_max
        a_max = -np.sign(initpos)*a_max
        dt_fix = 1e-2  # time between two fix points where the acceleration changes (infinite jerk)  # µs
            
        # positions at fixed points
        p1 = p1p = initpos
        t_deacc = (v_max)/a_max
        d_deacc = 0.5*a_max*t_deacc**2
        p2 = p2p = initpos + d_deacc
        p3 = p3p = -d_deacc
        p4 = 0
        pos = [p1, p1p, p2, p2p, p3, p3p, p4]
        
        # time at fixed points
        t1 = 0
        t1p = dt_fix
        t2 = t_deacc
        t2p = t2 + dt_fix
        t3 = t2 + abs(abs(p3 - p2)/v_max)
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
        
        # if p2 is already past the center of the scan it means that the max_velocity was never reached
        # in this case, remove two fixed points, and change the values to the curr. vel and time in the
        # middle of the flyback
        if abs(p2) <= abs(initpos/2) or abs(p2) > abs(initpos):
            t_mid = np.sqrt(abs(initpos/a_max))
            v_mid = a_max*t_mid
            del pos[4:6]
            del vel[4:6]
            del acc[4:6]
            del time[4:6]
            pos[2:4] = [initpos/2, initpos/2]
            vel[2:4] = [v_mid, v_mid]
            acc[2:4] = [a_max, -a_max]
            time[2] = t_mid
            time[3] = t_mid + dt_fix
            time[4] = 2*t_mid
        
        # generate Bernstein polynomial with piecewise spline interpolation with the fixed points
        # give positions, velocity, acceleration, and time of fixed points
        yder = np.array([pos, vel, acc]).T.tolist()
        bpoly = BPoly.from_derivatives(time, yder) # bpoly time unit: µs
        
        # get number of evaluation points
        n_eval = int(time[-1]/self.__timestep)
        # get evaluation times for one line
        t_eval = np.linspace(0, time[-1], n_eval)
        # evaluate polynomial
        poly_eval = bpoly(t_eval)
        # return evaluated polynomial at the timestep I want
        return poly_eval

    def __add_start_end(self, pos, pos_fix, v_max, a_max):
        """ Add start and end half-lines to smooth scanning curve """
        # generate five pieces, three before and two after, to be concatenated to the given positions array
        pos_pre1 = self.__init_positioning(initpos=np.min(pos), v_max=v_max, a_max=a_max)  # initial smooth acceleration piece from 0
        self._samples_initpos = len(pos_pre1)
        settlinglen = int(self.__settlingtime / self.__timestep)  # initial settling time before first line
        pos_pre2 = np.repeat(np.min(pos),settlinglen)  # settling positions
        self._samples_settling = len(pos_pre2)
        #print('se-2')
        pos_pre3 = pos[np.where(pos==np.min(pos))[0][-1]:]  # first half scan curve
        #print('se-3')
        pos_post1 = pos[:np.where(pos==np.max(pos))[0][0]]  # alt: last half scan curve to last peak after last line
        #print('se-4')
        pos_post2 = self.__final_positioning(initpos=pos_post1[-1], v_max=v_max, a_max=a_max)  # final smooth acceleration piece from max to 0
        pos_ret = np.concatenate((pos_pre1, pos_pre2, pos_pre3, pos, pos_post1, pos_post2))
        pos_halfscanline = pos[:np.argmin(abs(pos[:np.where(pos==np.max(pos))[0][0]]-pos_fix[2]))]  # half scan line
        self._samples_startacc = len(pos_pre3) - len(pos_halfscanline)
        self._samples_finalpos = len(pos_post2)
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


    def __initial_positioning(initpos, v_max, a_max):
        """ Generate a polynomial for a smooth initial positioning scanning curve, from the acquisition parameter settings and initial position """
        v_max = np.sign(initpos)*acq_param['v1_max']
        a_max = np.sign(initpos)*acq_param['a1_max']
        dt_fix = 1e-2  # time between two fix points where the acceleration changes (infinite jerk)  # µs
            
        # positions at fixed points
        p1 = p1p = 0
        t_deacc = (v_max)/a_max
        d_deacc = 0.5*a_max*t_deacc**2
        p2 = p2p = d_deacc
        p3 = p3p = initpos - d_deacc
        p4 = initpos
        pos = [p1, p1p, p2, p2p, p3, p3p, p4]
        
        # time at fixed points
        t1 = 0
        t1p = dt_fix
        t2 = t_deacc
        t2p = t2 + dt_fix
        t3 = t2 + abs(abs(p3 - p2)/v_max)
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
        
        # if p2 is already past the center of the scan it means that the max_velocity was never reached
        # in this case, remove two fixed points, and change the values to the curr. vel and time in the
        # middle of the flyback
        if abs(p2) >= abs(initpos/2):
            t_mid = np.sqrt(abs(initpos/a_max))
            v_mid = a_max*t_mid
            del pos[4:6]
            del vel[4:6]
            del acc[4:6]
            del time[4:6]
            pos[2:4] = [initpos/2, initpos/2]
            vel[2:4] = [v_mid, v_mid]
            acc[2:4] = [a_max, -a_max]
            time[2] = t_mid
            time[3] = t_mid + dt_fix
            time[4] = 2*t_mid
        
        # generate Bernstein polynomial with piecewise spline interpolation with the fixed points
        # give positions, velocity, acceleration, and time of fixed points
        yder = np.array([pos, vel, acc]).T.tolist()
        bpoly = BPoly.from_derivatives(time, yder) # bpoly time unit: µs
        
        # get number of evaluation points
        n_eval = int(time[-1]/acq_param['timestep'])
        # get evaluation times for one line
        t_eval = linspace(0, time[-1], n_eval)
        # evaluate polynomial
        poly_eval = bpoly(t_eval)
        # return evaluated polynomial at the timestep I want
        return poly_eval