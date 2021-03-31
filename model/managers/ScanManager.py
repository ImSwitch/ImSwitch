# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 17:00:05 2020

@author: andreas.boden
"""

import numpy as np

from model.SignalDesigner import SignalDesignerFactory
from model.errors import IncompatibilityError


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
        self.__scanDesigner = SignalDesignerFactory(setupInfo, 'scanDesigner')
        self.__TTLCycleDesigner = SignalDesignerFactory(setupInfo, 'TTLCycleDesigner')

        self._expectedSyncParameters = []

    def _parameterCompatibility(self, parameterDict):
        stageExpected = set(self.__scanDesigner.expectedParameters)
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

    def makeFullScan(self, scanParameters, TTLParameters, setupInfo, staticPositioner=False):

        if not staticPositioner:
            scanSignalsDict, positions, scanInfoDict = self.__scanDesigner.make_signal(
                scanParameters, setupInfo, returnFrames=True
            )
            TTLCycleSignalsDict = self.__TTLCycleDesigner.make_signal(TTLParameters, setupInfo, scanInfoDict)
        else:
            TTLCycleSignalsDict = self.__TTLCycleDesigner.make_signal(TTLParameters, setupInfo)
            scanSignalsDict = {}
            scanInfoDict = {}

        return {'scanSignalsDict': scanSignalsDict,
                'TTLCycleSignalsDict': TTLCycleSignalsDict}, scanInfoDict


""" Developement testing """
if __name__ == '__main__':
    print('Running main')
    import matplotlib.pyplot as plt

    Stageparameters = {'target_device': ['Stage_X', 'Stage_Y', 'Stage_Z'],
                       'axis_length': [5, 5, 5],
                       'axis_step_size': [1, 1, 1],
                       'axis_startpos': [0, 0, 0],
                       'sequence_time': 0.005,
                       'sample_rate': 100000,
                       'return_time': 0.001}
    TTLparameters = {'target_device': ['405', '488'],
                     'TTL_start': [[0.0001, 0.004], [0, 0]],
                     'TTL_end': [[0.0015, 0.005], [0, 0]],
                     'sequence_time': 0.005,
                     'sample_rate': 100000}

    SyncParameters = {'TTLRepetitions': 6, 'TTLZeroPad_seconds': 0.001, 'sample_rate': 100000}
    sh = ScanManagerFactory('ScanManager')
    fullsig = sh.makeFullScan(Stageparameters, TTLparameters)
    plt.plot(fullsig['scanSignalsDict']['Stage_X'])
    plt.plot(fullsig['scanSignalsDict']['Stage_Y'])
    plt.plot(fullsig['scanSignalsDict']['Stage_Z'])

    plt.figure()
    plt.plot(fullsig['TTLCycleSignalsDict']['405'])

    """
    parameters = {'target_device': ['StageX', 'StageY', 'StageZ'], \
                  'axis_length':[5,5,5], \
                  'axis_step_size': [1,1,1], \
                  'sequence_time': 0.005, \
                  'sample_rate': 100000, \
                  'return_time': 0.001}
    ssd = SignalDesignerFactory('scanDesigner', parameters)        
    sig_dict = ssd.make_signal(parameters)
    
    parameters = {'target_device': ['405', '488'], \
                  'TTL_start': [[0.0012, 0.002], [0, 0]], \
                  'TTL_end': [[0.0015, 0.0025], [0, 0]], \
                  'sequence_time': 0.005, \
                  'sample_rate': 100000}
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
