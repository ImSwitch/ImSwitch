# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 17:00:05 2020

@author: andreas.boden
"""

import numpy as np
import matplotlib.pyplot as plt


class ScanHelper():
    def __init__(self):
        self.stageScanDesigner = StageScanDesigner()
        self.ttlCycleDesigner = TTLCycleDesigner()

class SignalDesigner():
    def __init__(self):
        
        self.last_signal = None
        self.last_parameter_dict = None
        
        self._expected_parameters = None
        
    @property
    def expected_parameters(self):
        if self._expected_parameters is None:
            raise ValueError('Value "%s" is not defined')
        else:
            return self._expected_parameters
    

    def make_signal(self, parameter_dict):
        raise NotImplementedError("Method not implemented in child")
    
    def _parameter_compatibility(self, parameter_dict):
        expected = set(self._expected_parameters)
        incoming = set([*parameter_dict])
        
        return expected == incoming
    
        
class StageScanDesigner(SignalDesigner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._expected_parameters = ['Targets[3]',\
                                     'Sizes[3]', \
                                     'Step_sizes[3]', \
                                     'Sequence_time_seconds', \
                                     'Sample_rate', \
                                     'Return_time_seconds']
        
        
        
    def make_signal(self, parameter_dict):
        
        if not self._parameter_compatibility(parameter_dict):
            print('WHAT ARE YOU DOING??? THESE PARAMETERS ARE WIEEEERD!?!?!?')
            return None
        #Retrieve sizes
        [fast_axis_size, middle_axis_size, slow_axis_size] = \
        [parameter_dict['Sizes[3]'][i] for i in range(3)]
        
        #Retrieve step sized
        [fast_axis_step_size, middle_axis_step_size, slow_axis_step_size] = \
        [parameter_dict['Step_sizes[3]'][i] for i in range(3)]
        
        fast_axis_positions =  1 + np.int(np.ceil(fast_axis_size / fast_axis_step_size))
        middle_axis_positions = 1 + np.int(np.ceil(middle_axis_size / middle_axis_step_size))
        slow_axis_positions = 1 + np.int(np.ceil(slow_axis_size / slow_axis_step_size))
        
        """
        fast_axis_best_step_size = fast_axis_size / fast_axis_steps
        middle_axis_best_step_size = middle_axis_size / middle_axis_steps
        slow_axis_best_step_size = slow_axis_size / slow_axis_steps
        """
        sequenceSamples = \
        parameter_dict['Sequence_time_seconds'] * parameter_dict['Sample_rate']
        returnSamples = \
        parameter_dict['Return_time_seconds'] * parameter_dict['Sample_rate']
        if not sequenceSamples.is_integer():
            print('WARNIGN: Non-integer number of sequence sampels, rounding up')
            sequenceSamples = np.ceil(sequenceSamples)
        if not returnSamples.is_integer():
            print('WARNIGN: Non-integer number of return sampels, rounding up')
            returnSamples = np.ceil(returnSamples)
        
        
        #Make fast axis signal
        rampSamples = fast_axis_positions * sequenceSamples
        lineSamples = rampSamples + returnSamples
        rampSignal = self.makeRamp(0, fast_axis_size, rampSamples)
        returnRamp = self.smoothRamp(fast_axis_size, 0, returnSamples)
        fullLineSignal = np.concatenate((rampSignal, returnRamp))
        
        fastAxisSignal = np.tile(fullLineSignal, middle_axis_positions*slow_axis_positions)
        plt.plot(fastAxisSignal)
        
        #Make middle axis signal
        colSamples = middle_axis_positions * lineSamples
        colValues = self.makeRamp(0, middle_axis_size, middle_axis_positions)
        fullSquareSignal = np.zeros(colSamples)
        for s in range(middle_axis_positions):
            fullSquareSignal[s*lineSamples: \
                             s*lineSamples + rampSamples] = \
                             colValues[s]
                             
            try:
                fullSquareSignal[s*lineSamples + rampSamples: \
                                 (s+1)*lineSamples] = \
                                 self.smoothRamp(colValues[s], colValues[s+1], returnSamples)
            except IndexError:
                fullSquareSignal[s*lineSamples + rampSamples: \
                                 (s+1)*lineSamples] = \
                                 self.smoothRamp(colValues[s], 0, returnSamples)
        
        middleAxisSignal = np.tile(fullSquareSignal, slow_axis_positions)
        plt.plot(middleAxisSignal)
        
        #Make slow axis signal
        sliceSamples = slow_axis_positions * colSamples
        sliceValues = self.makeRamp(0, slow_axis_size, slow_axis_positions)
        fullCubeSignal = np.zeros(sliceSamples)
        for s in range(slow_axis_positions):
            fullCubeSignal[s*colSamples: \
                             (s+1)*colSamples - returnSamples] = \
                             sliceValues[s]
                             
            try:
                fullCubeSignal[(s+1)*colSamples - returnSamples: \
                                 (s+1)*colSamples] = \
                                 self.smoothRamp(sliceValues[s], sliceValues[s+1], returnSamples)
            except IndexError:
                fullCubeSignal[(s+1)*colSamples - returnSamples: \
                                 (s+1)*colSamples] = \
                                 self.smoothRamp(sliceValues[s], 0, returnSamples)
        slowAxisSignal = fullCubeSignal             
        plt.plot(slowAxisSignal)
        
        sig_dict = {parameter_dict['Targets[3]'][0]: fastAxisSignal, \
                    parameter_dict['Targets[3]'][1]: middleAxisSignal, \
                    parameter_dict['Targets[3]'][2]: slowAxisSignal}
        
        return sig_dict
        
    def makeRamp(self, start, end, samples):
        return np.linspace(start, end, num=samples)


    def smoothRamp(self, start, end, samples):
        curve_half = 0.6
        x = np.linspace(0, np.pi/2, num=np.floor(curve_half*samples), endpoint=True)
        signal = start + (end-start)*np.sin(x)
        signal = np.append(signal, end*np.ones(int(np.ceil((1-curve_half)*samples))))
        return signal
    
    
    
if __name__ == '__main__':
    print('Running main')
    ssd = StageScanDesigner()
    parameters = {'Targets[3]': ['StageX', 'StageY', 'StageZ'], \
                  'Sizes[3]':[5,5,5], \
                  'Step_sizes[3]': [1,1,1], \
                  'Sequence_time_seconds': 0.005, \
                  'Sample_rate': 100000, \
                  'Return_time_seconds': 0.001}
            
    sig_dict = ssd.make_signal(parameters)
    
    
    