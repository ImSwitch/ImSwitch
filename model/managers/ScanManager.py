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
        TTLCycleSignalsDict = self.getTTLCycleSignalsDict(TTLParameters, setupInfo)

        # Calculate samples to zero pad TTL signals with
        #TTLZeroPadSamples = scanParameters['Return_time_seconds'] * TTLParameters['sample_rate']
        #if not TTLZeroPadSamples.is_integer():
        #    print('WARNING: Non-integer number of return samples, rounding up')
        #TTLZeroPadSamples = np.int(np.ceil(TTLZeroPadSamples))

        if not staticPositioner:
            scanSignalsDict, positions, scanInfoDict = self.__scanDesigner.make_signal(
                scanParameters, setupInfo, returnFrames=True
            )
            print(scanSignalsDict)
            print(scanInfoDict)
            #TODO: # add below into a new TTL_cycle_designer, that takes the scanInfoDict from the analog signal designer as input
            zeropad_lineflyback = scanInfoDict['scan_samples_period'] - scanInfoDict['scan_samples_line']
            #print(f'scan flyback: {zeropad_lineflyback}')
            zeropad_settling = scanInfoDict['scan_throw_settling']
            #print(f'scan settl {zeropad_settling}')
            zeropad_start = scanInfoDict['scan_throw_startzero']
            #print(f'scan startendzero: {zeropad_startend}')
            zeropad_startacc = scanInfoDict['scan_throw_startacc']
            #print(f'scan startacc: {zeropad_startacc}')
            # Tile and pad TTL signals according to fast axis scan parameters
            for target, signal in TTLCycleSignalsDict.items():
                #print(f'one pixel: {len(signal)}')
                signal_line = np.tile(signal, scanInfoDict['pixels_line'])
                #print(f'one line: {len(signal_line)}')
                signal_period = np.append(signal_line, np.zeros(zeropad_lineflyback, dtype='bool'))#*signal[0])
                #print(f'one period: {len(signal_period)}')
                #TODO: # only do 2D-scan for now, fix for 3D-scan
                signal = np.tile(signal_period, scanInfoDict['n_lines'] - 1)  # all lines except last
                #print(f'all-1 lines: {len(signal)}')
                signal = np.append(signal, signal_line)  # add last line (does without flyback)
                
                #print(f'all lines: {len(signal)}')
                signal = np.append(np.zeros(zeropad_startacc, dtype='bool'), signal)  # pad first line accelereation
                #print(f'startacc: {len(signal)}')
                signal = np.append(np.zeros(zeropad_settling, dtype='bool'), signal)  # pad start settling
                #print(f'settl: {len(signal)}')
                signal = np.append(np.zeros(zeropad_start, dtype='bool'), signal)  # pad start zero
                #print(f'zerostart: {len(signal)}')
                zeropad_end = scanInfoDict['scan_samples_total'] - len(signal)
                #onepad_end = 12
                #signal = np.append(signal, np.ones(onepad_end, dtype='bool'))  # pad end zero to same length
                #TODO: this does not seem to be correct, I have the laser off the last ~120 µs (last pixels) in the last row
                signal = np.append(signal, np.zeros(zeropad_end, dtype='bool'))  # pad end zero to same length
                #print(f'zeroend: {len(signal)}')

                TTLCycleSignalsDict[target] = signal
        else:
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
                       'Return_time_seconds': 0.001}
    TTLparameters = {'target_device': ['405', '488'],
                     'TTLStarts[x,y]': [[0.0001, 0.004], [0, 0]],
                     'TTLEnds[x,y]': [[0.0015, 0.005], [0, 0]],
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
                  'Return_time_seconds': 0.001}
    ssd = SignalDesignerFactory('scanDesigner', parameters)        
    sig_dict = ssd.make_signal(parameters)
    
    parameters = {'target_device': ['405', '488'], \
                  'TTLStarts[x,y]': [[0.0012, 0.002], [0, 0]], \
                  'TTLEnds[x,y]': [[0.0015, 0.0025], [0, 0]], \
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
