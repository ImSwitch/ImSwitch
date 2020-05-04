# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 09:20:14 2020

@author: andreas.boden
"""
#try:
#    from TempestaErrors import InvalidChildClassError, IncompatibilityError
#except ModuleNotFoundError:
from controller.TempestaErrors import InvalidChildClassError, IncompatibilityError
import numpy as np
import json
# import matplotlib.pyplot as plt

class SignalDesignerFactory():
    """Factory class for creating a SignalDesigner object. Factory checks
    that the new object is compatible with the parameters that will we 
    be sent to its make_signal method."""
    def __new__(cls , configKeyName):
        config_dict = json.load(open('../config_files/config.json'))
        scanDesignerName = config_dict[configKeyName]
        
#        SignalDesigner = super().__new__(cls, 'SignalDesigner.'+scanDesignerName)
        signalDesigner = eval(scanDesignerName+'()')
        if signalDesigner.isValidSignalDesigner():
            return signalDesigner


class SignalDesigner():
    """Parent class for any type of SignaDesigner. Any child should define
    self._expected_parameters and its own make_signal method."""
    def __init__(self):
        
        self.lastSignal = None
        self.lastParameterDict = None
        
        self._expectedParameters = None
        
        #Make non-overwritable functions
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

    def make_signal(self, parameter_dict):
        """ Method to be defined by child. Should return a dictionary with 
        {'target': signal} pairs. """
        raise NotImplementedError("Method not implemented in child")
    
    def __parameterCompatibility(self, parameterDict):
        """ Method to check the compatibility of parameter 'parameter_dict'
        and the expected parameters of the object. """
        expected = set(self._expectedParameters)
        incoming = set([*parameterDict])
        
        return expected == incoming
        
      
class BetaStageScanDesigner(SignalDesigner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.convFactors = {'X': 1.5870,'Y': 1.5907, 'Z': 10}
        
        self._expectedParameters = ['Targets[3]',\
                                     'Sizes[3]', \
                                     'Step_sizes[3]', \
                                     'Sequence_time_seconds', \
                                     'Sample_rate', \
                                     'Return_time_seconds']
        
    
    def make_signal(self, parameter_dict, returnFrames = False):
        
        if not self.parameterCompatibility(parameter_dict):
            print('Parameters seem incompatible, this error should not be \
                  since this should be checked at program start-up')
            return None
        #Retrieve sizes
        [fast_axis_size, middle_axis_size, slow_axis_size] = \
        [(parameter_dict['Sizes[3]'][i]/self.convFactors[parameter_dict['Targets[3]'][i].split('_')[1]]) for i in range(3)]

        #Retrieve step sized
        [fast_axis_step_size, middle_axis_step_size, slow_axis_step_size] = \
        [parameter_dict['Step_sizes[3]'][i] for i in range(3)]

        
        fast_axis_positions =  1 + np.int(np.ceil(fast_axis_size / fast_axis_step_size))
        middle_axis_positions = 1 + np.int(np.ceil(middle_axis_size / middle_axis_step_size))
        slow_axis_positions = 1 + np.int(np.ceil(slow_axis_size / slow_axis_step_size))

        sequenceSamples = \
        parameter_dict['Sequence_time_seconds'] * parameter_dict['Sample_rate']
        returnSamples = \
        parameter_dict['Return_time_seconds'] * parameter_dict['Sample_rate']
        if not sequenceSamples.is_integer():
            print('WARNIGN: Non-integer number of sequence sampels, rounding up')
        sequenceSamples = np.int(np.ceil(sequenceSamples))
        if not returnSamples.is_integer():
            print('WARNING: Non-integer number of return sampels, rounding up')
        returnSamples = np.int(np.ceil(returnSamples))
        
        #Make fast axis signal
        rampSamples = fast_axis_positions * sequenceSamples
        lineSamples = rampSamples + returnSamples

        rampSignal = self.__makeRamp(0, fast_axis_size, rampSamples)
        returnRamp = self.__smoothRamp(fast_axis_size, 0, returnSamples)
        fullLineSignal = np.concatenate((rampSignal, returnRamp))
        
        fastAxisSignal = np.tile(fullLineSignal, middle_axis_positions*slow_axis_positions)
        #Make middle axis signal
        colSamples = middle_axis_positions * lineSamples
        colValues = self.__makeRamp(0, middle_axis_size, middle_axis_positions)
        fullSquareSignal = np.zeros(colSamples)
        for s in range(middle_axis_positions):
            fullSquareSignal[s*lineSamples: \
                             s*lineSamples + rampSamples] = \
                             colValues[s]
                             
            try:
                fullSquareSignal[s*lineSamples + rampSamples: \
                                 (s+1)*lineSamples] = \
                                 self.__smoothRamp(colValues[s], colValues[s+1], returnSamples)
            except IndexError:
                fullSquareSignal[s*lineSamples + rampSamples: \
                                 (s+1)*lineSamples] = \
                                 self.__smoothRamp(colValues[s], 0, returnSamples)
        
        middleAxisSignal = np.tile(fullSquareSignal, slow_axis_positions)

        #Make slow axis signal
        sliceSamples = slow_axis_positions * colSamples
        sliceValues = self.__makeRamp(0, slow_axis_size, slow_axis_positions)
        fullCubeSignal = np.zeros(sliceSamples)
        for s in range(slow_axis_positions):
            fullCubeSignal[s*colSamples: \
                             (s+1)*colSamples - returnSamples] = \
                             sliceValues[s]
                             
            try:
                fullCubeSignal[(s+1)*colSamples - returnSamples: \
                                 (s+1)*colSamples] = \
                                 self.__smoothRamp(sliceValues[s], sliceValues[s+1], returnSamples)
            except IndexError:
                fullCubeSignal[(s+1)*colSamples - returnSamples: \
                                 (s+1)*colSamples] = \
                                 self.__smoothRamp(sliceValues[s], 0, returnSamples)
        slowAxisSignal = fullCubeSignal

        sig_dict = {parameter_dict['Targets[3]'][0]: fastAxisSignal, \
                    parameter_dict['Targets[3]'][1]: middleAxisSignal, \
                    parameter_dict['Targets[3]'][2]: slowAxisSignal}

        if not returnFrames:
            return sig_dict
        else:
            return sig_dict, [fast_axis_positions, middle_axis_positions, slow_axis_positions]
        
    def __makeRamp(self, start, end, samples):
        return np.linspace(start, end, num=samples)

    def __smoothRamp(self, start, end, samples):
        curve_half = 0.6
        n = np.int(np.floor(curve_half*samples))
        x = np.linspace(0, np.pi/2, num=n, endpoint=True)
        signal = start + (end-start)*np.sin(x)
        signal = np.append(signal, end*np.ones(int(np.ceil((1-curve_half)*samples))))
        return signal

    
class BetaTTLCycleDesigner(SignalDesigner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._expectedParameters = ['Targets[x]',\
                                     'TTLStarts[x,y]', \
                                     'TTLEnds[x,y]', \
                                     'Sequence_time_seconds', \
                                     'Sample_rate']
        
    def make_signal(self, parameter_dict):
        
        if not self.parameterCompatibility(parameter_dict):
            print('Parameters seem incompatible, this error should not be \
                  since this should be checked at program start-up')
            return None
        
        targets = parameter_dict['Targets[x]']
        sampleRate = parameter_dict['Sample_rate']
        cycleSamples = parameter_dict['Sequence_time_seconds'] * sampleRate
        if not cycleSamples.is_integer():
            print('WARNIGN: Non-integer number of sequence sampels, rounding up')
        cycleSamples = np.int(np.ceil(cycleSamples))
        signalDict = {}
        tmpSigArr = np.zeros(cycleSamples, dtype='bool')
        for i, target in enumerate(targets):
            tmpSigArr[:] = False
            for j, start in enumerate(parameter_dict['TTLStarts[x,y]'][i]):
                startSamp = np.int(np.round(start * sampleRate))
                endSamp = np.int(np.round(parameter_dict['TTLEnds[x,y]'][i][j] * sampleRate))
                tmpSigArr[startSamp:endSamp] = True
                
            signalDict[target] = np.copy(tmpSigArr)
        return signalDict