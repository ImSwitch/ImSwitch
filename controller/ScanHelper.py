# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 17:00:05 2020

@author: andreas.boden
"""

from controller.SignalDesigner import SignalDesignerFactory
    
from controller.TempestaErrors import IncompatibilityError
import numpy as np

class ScanHelperFactory():
    """Factory class for creating a ScanHelper object. Factory checks
    that the new object is a valid ScanHelper."""
    def __new__(cls , className, *args):

        scanHelper = eval(className+'(*args)')
        if scanHelper.isValidChild():
            return scanHelper

class SuperScanHelper():
    def __init__(self):
        self.isValidScanHelper = self.__isValidScanHelper
        self.isValidChild = self.isValidScanHelper
        
    def __isValidScanHelper(self): #For future possivle implementation
        return True

    def _parameterCompatibility(self, parameterDict=None):
        raise NotImplementedError("Method not implemented in child")
    



class ScanHelper(SuperScanHelper):
    def __init__(self):
        super().__init__()
        self.__stageScanDesigner = SignalDesignerFactory('stageScanDesigner')
        self.__TTLCycleDesigner = SignalDesignerFactory('TTLCycleDesigner')
        
        self._expectedSyncParameters = []

        
    def _parameterCompatibility(self, parameterDict):
        
        stageExpected = set(self.__stageScanDesigner.expectedParameters)
        stageIncoming = set(parameterDict['stageParameterList'])
         
        if not stageExpected == stageIncoming:
            raise IncompatibilityError('Incompatible stage scan parameters')

        TTLExpected = set(self.__TTLCycleDesigner.expectedParameters)
        TTLIncoming = set(parameterDict['TTLParameterList'])
 
        if not TTLExpected == TTLIncoming:
            raise IncompatibilityError('Incompatible TTL parameters')

        # syncExpected = set(self.expectedSyncParameters)
        # syncIncoming = set(stageParameterList)
        
        # if not syncExpected == syncIncoming:
        #     raise IncompatibilityError('Incompatible sync parameters')
    
    def make_full_scan(self, stageScanParameters, TTLParameters):
        
        stageScanSignalsDict, positions = \
        self.__stageScanDesigner.make_signal(stageScanParameters, \
                                             returnFrames=True)

        TTLCycleSignalsDict = \
        self.__TTLCycleDesigner.make_signal(TTLParameters)
        #Calculate samples to zero pad TTL signals with
        TTLZeroPadSamples = stageScanParameters['Return_time_seconds'] * \
        TTLParameters['Sample_rate']
        if not TTLZeroPadSamples.is_integer():
            print('WARNING: Non-integer number of return sampels, rounding up')
        TTLZeroPadSamples = np.int(np.ceil(TTLZeroPadSamples))
        #Tile and pad TTL signals according to sync parameters
        for target, signal in TTLCycleSignalsDict.items():
            signal = np.tile(signal, positions[0])
            signal = np.append(signal, np.zeros(TTLZeroPadSamples))
            signal = np.tile(signal, positions[1]*positions[2])

            TTLCycleSignalsDict[target] = signal

        return {'stageScanSignalsDict': stageScanSignalsDict, \
                'TTLCycleSignalsDict': TTLCycleSignalsDict}




""" Developement testing """            
if __name__ == '__main__':
    print('Running main')
    import matplotlib.pyplot as plt
    
    Stageparameters = {'Targets[3]': ['StageX', 'StageY', 'StageZ'], \
                  'Sizes[3]':[5,5,5], \
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
    sh = ScanHelperFactory('ScanHelper')
    fullsig = sh.make_full_scan(Stageparameters, TTLparameters)
    plt.plot(fullsig['stageScanSignalsDict']['StageX'])
    plt.plot(fullsig['stageScanSignalsDict']['StageY'])
    plt.plot(fullsig['stageScanSignalsDict']['StageZ'])
    
    plt.figure()
    plt.plot(fullsig['TTLCycleSignalsDict']['405'])

    

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
        
        
    