# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 17:00:05 2020

@author: andreas.boden
"""

import numpy as np


class signalDesigner():
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
        expected = map(self._expected_parameters)
        incoming = map([*parameter_dict])
        
        return expected == incoming
        
class stageScanDesigner(signalDesigner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._expected_parameters = ['Size[3]', \
                                     'Step_size[3]', \
                                     'Sequence_time_seconds', \
                                     'Sample_rate', \
                                     'Return_time_seconds']
        
        
        
    def make_signal(self, parameter_dict):
        
        
        
if __name__ == '__main__':
    print('Running main')
    ssd = stageScanDesigner()
    
    
    
    