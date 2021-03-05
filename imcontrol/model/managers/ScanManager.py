# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 17:00:05 2020

@author: andreas.boden
"""

import numpy as np

from imcontrol.model.SignalDesigner import SignalDesignerFactory
from imcontrol.model import IncompatibilityError


class ScanManagerFactory:
    """Factory class for creating a ScanManager object. Factory checks
    that the new object is a valid ScanManager."""

    def __new__(cls, className, *args):
        scanManager = globals()[className](*args)
        if scanManager.isValidChild():
            return scanManager


class SuperScanManager:
    def __init__(self):
        self.isValidScanManager = self.__isValidScanManager
        self.isValidChild = self.isValidScanManager

    def __isValidScanManager(self):  # For future possivle implementation
        return True

    def _parameterCompatibility(self, parameterDict=None):
        raise NotImplementedError("Method not implemented in child")


class ScanManager(SuperScanManager):
    def __init__(self, setupInfo):
        super().__init__()
        self.__stageScanDesigner = SignalDesignerFactory(setupInfo, 'stageScanDesigner')
        self.__TTLCycleDesigner = SignalDesignerFactory(setupInfo, 'TTLCycleDesigner')

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

    def getTTLCycleSignalsDict(self, TTLParameters, setupInfo):
        return self.__TTLCycleDesigner.make_signal(TTLParameters, setupInfo)

    def makeFullScan(self, stageScanParameters, TTLParameters, setupInfo, staticPositioner=False):
        TTLCycleSignalsDict = self.getTTLCycleSignalsDict(TTLParameters, setupInfo)

        # Calculate samples to zero pad TTL signals with
        TTLZeroPadSamples = stageScanParameters['Return_time_seconds'] * TTLParameters['Sample_rate']
        if not TTLZeroPadSamples.is_integer():
            print('WARNING: Non-integer number of return samples, rounding up')
        TTLZeroPadSamples = np.int(np.ceil(TTLZeroPadSamples))

        if not staticPositioner:
            stageScanSignalsDict, positions = self.__stageScanDesigner.make_signal(
                stageScanParameters, setupInfo, returnFrames=True
            )

            # Tile and pad TTL signals according to sync parameters
            for target, signal in TTLCycleSignalsDict.items():
                signal = np.tile(signal, positions[0])
                signal = np.append(signal, np.zeros(TTLZeroPadSamples, dtype='bool'))
                signal = np.tile(signal, positions[1] * positions[2])

                TTLCycleSignalsDict[target] = signal
        else:
            stageScanSignalsDict = {}

        return {'stageScanSignalsDict': stageScanSignalsDict,
                'TTLCycleSignalsDict': TTLCycleSignalsDict}


""" Developement testing """
if __name__ == '__main__':
    print('Running main')
    import matplotlib.pyplot as plt

    Stageparameters = {'Targets[x]': ['Stage_X', 'Stage_Y', 'Stage_Z'],
                       'Sizes[x]': [5, 5, 5],
                       'Step_sizes[x]': [1, 1, 1],
                       'Start[x]': [0, 0, 0],
                       'Sequence_time_seconds': 0.005,
                       'Sample_rate': 100000,
                       'Return_time_seconds': 0.001}
    TTLparameters = {'Targets[x]': ['405', '488'],
                     'TTLStarts[x,y]': [[0.0001, 0.004], [0, 0]],
                     'TTLEnds[x,y]': [[0.0015, 0.005], [0, 0]],
                     'Sequence_time_seconds': 0.005,
                     'Sample_rate': 100000}

    SyncParameters = {'TTLRepetitions': 6, 'TTLZeroPad_seconds': 0.001, 'Sample_rate': 100000}
    sh = ScanManagerFactory('ScanManager')
    fullsig = sh.makeFullScan(Stageparameters, TTLparameters)
    plt.plot(fullsig['stageScanSignalsDict']['Stage_X'])
    plt.plot(fullsig['stageScanSignalsDict']['Stage_Y'])
    plt.plot(fullsig['stageScanSignalsDict']['Stage_Z'])

    plt.figure()
    plt.plot(fullsig['TTLCycleSignalsDict']['405'])

    """
    parameters = {'Targets[x]': ['StageX', 'StageY', 'StageZ'], \
                  'Sizes[x]':[5,5,5], \
                  'Step_sizes[x]': [1,1,1], \
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
