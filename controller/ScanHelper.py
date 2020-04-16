# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 17:00:05 2020

@author: andreas.boden
"""

import controller.SignalDesigner as SignalDesigner
import numpy as np

class ScanHelper():
    def __init__(self, stageScaneParameters, TTLCycleParameters, syncParameters):
        self.__stageScanDesigner = SignalDesigner.SignalDesignerFactory('stageScanDesigner', stageScaneParameters)
        self.__ttlCycleDesigner = SignalDesigner.SignalDesignerFactory('TTLCycleDesigner', TTLCycleParameters)
        
        self._expectedSyncParameters = ['TTLRepetitions', 'TTLZeroPad_seconds', 'Sample_rate']
        
        if not self._sync_parameter_compatibility(syncParameters):
            print('WARNING: Incompatible sync parameters')
        
    def _sync_parameter_compatibility(self, parameter_dict):
        expected = set(self._expectedSyncParameters)
        incoming = set([*parameter_dict])
        
        return expected == incoming
        
    def make_full_scan(self, stageScanParameters, TTLParameters, SyncParameters):
        
        stageScanSignalsDict = \
        self.__stageScanDesigner.make_signal(stageScanParameters)
        
        TTLCycleSignalsDict = \
        self.__ttlCycleDesigner.make_signal(TTLParameters)
        
        #Calculate samples to zero pad TTL signals with
        TTLZeroPadSamples = SyncParameters['TTLZeroPad_seconds'] * \
        SyncParameters['Sample_rate']
        if not TTLZeroPadSamples.is_integer():
            print('WARNIGN: Non-integer number of return sampels, rounding up')
            TTLZeroPadSamples = np.ceil(TTLZeroPadSamples)
        #Tile and pad TTL signals according to sync parameters
        for target, signal in TTLCycleSignalsDict.items():
            signal = np.tile(signal, SyncParameters['TTLRepetitions'])
            signal = np.append(signal, np.zeros(TTLZeroPadSamples))
            TTLCycleSignalsDict[target] = signal
            
        return [stageScanSignalsDict, TTLCycleSignalsDict]




""" Developement testing """            
if __name__ == '__main__':
    print('Running main')

    Stageparameters = {'Targets[3]': ['StageX', 'StageY', 'StageZ'], \
                  'Sizes[3]':[5,5,0], \
                  'Step_sizes[3]': [1,1,1], \
                  'Sequence_time_seconds': 0.005, \
                  'Sample_rate': 100000, \
                  'Return_time_seconds': 0.001}
    TTLparameters = {'Targets[x]': ['405', '488'], \
                  'TTLStarts[x,y]': [[0.0012, 0.002], [0, 0]], \
                  'TTLEnds[x,y]': [[0.0015, 0.0025], [0, 0]], \
                  'Sequence_time_seconds': 0.005, \
                  'Sample_rate': 100000}
    
    SyncParameters = {'TTLRepetitions': 6, 'TTLZeroPad_seconds': 0.001, 'Sample_rate': 100000}
    sh = ScanHelper(Stageparameters, TTLparameters, SyncParameters)
    ttlsig = sh.make_full_scan(Stageparameters, TTLparameters, SyncParameters)

    """
    parameters = {'Targets[3]': ['StageX', 'StageY', 'StageZ'], \
                  'Sizes[3]':[5,5,5], \
                  'Step_sizes[3]': [1,1,1], \
                  'Sequence_time_seconds': 0.005, \
                  'Sample_rate': 100000, \
                  'Return_time_seconds': 0.001}
    ssd = SignalDesignerFactory('stageScanDesigner', parameters)        
    sig_dict = ssd.make_signal(parameters)
    
    parameters = {'Targets[x]': ['405', '488'], \
                  'TTLStarts[x,y]': [[0.0012, 0.002], [0, 0]], \
                  'TTLEnds[x,y]': [[0.0015, 0.0025], [0, 0]], \
                  'Sequence_time_seconds': 0.005, \
                  'Sample_rate': 100000}
    ttldesigner = SignalDesignerFactory('TTLCycleDesigner', parameters)
    ttlDict = ttldesigner.make_signal(parameters)
    """
    """
    d = {'hej': 1, 'då': 2}
    
    for key, value in d.items():
        print(key)
        value = 3
        print(value)
   """ 
        
        
    