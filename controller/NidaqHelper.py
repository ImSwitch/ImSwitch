# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 16:46:33 2020

"""
import nidaqmx
import numpy as np
from controller.TempestaErrors import NidaqHelperError
import operator

class NidaqHelper():
    
    def __init__(self, deviceInfo = None):
        if deviceInfo is None:
            self.__deviceInfo = {'488': {'AOChan': None, 'DOLine': 0},
                               '405': {'AOChan': None, 'DOLine': 1},
                               '473': {'AOChan': None, 'DOLine': 2},
                               'StageX': {'AOChan': 0, 'DOLine': None},
                               'StageY': {'AOChan': 1, 'DOLine': None},
                               'StageZ': {'AOChan': 2, 'DOLine': None}}
        else:
            self.__deviceInfo = deviceInfo
                

        
    def __makeSortedTargets(self, sortingKey):
        targetPairs = []
        for target in [*self.__deviceInfo]:
            value = self.__deviceInfo[target][sortingKey]
            if value is not None:
                pair = [target, value]
                targetPairs.append(pair)
        targetPairs.sort(key = operator.itemgetter(1))
        return targetPairs

            
    def __createLineDOTask(self, name, lines, acquisition, source, rate, sampsInScan = None):
        """ Simplified function to create a digital output task """
        dotask = nidaqmx.Task(name)
        
        lines = np.atleast_1d(lines)
        
        for line in lines:
            dotask.do_channels.add_do_chan('Dev1/port0/line%s' % line)
        dotask.timing.cfg_samp_clk_timing(source=source, rate=rate, \
                                          sample_mode=acquisition, samps_per_chan = sampsInScan)
        return dotask

    def __createChanAOTask(self, name, channels, acquisitionType, \
                                 source, rate, min_val=-1, max_val=1, sampsInScan = None):
        """ Simplified function to create an analog output task """
        aotask = nidaqmx.Task(name)
        
        channels = np.atleast_1d(channels)
        
        for channel in channels:
            aotask.ao_channels.add_ao_voltage_chan('Dev1/ao%s' % channel,  \
                                               min_val = min_val, \
                                                   max_val = max_val)
        aotask.timing.cfg_samp_clk_timing(source=source, rate=rate, \
                                          sample_mode=acquisitionType, samps_per_chan = sampsInScan)
        return aotask
        
    def setDigital(self, target, enable):
        """ Function to set the digital line to a specific target
        to either "high" or "low" voltage """
        if self.__deviceInfo[target]['DOLine'] is None:
            raise NidaqHelperError('Target has no digital output assigned to it')        
        else:
            line = self.__deviceInfo[target]['DOLine']
            acquisitionTypeFinite = nidaqmx.constants.AcquisitionType.FINITE
            
            dotask = self.__createLineDOTask('setDigitalTask', \
                                       line, \
                                           acquisitionTypeFinite, \
                                               '100kHzTimebase', \
                                                   100000)
            signal = np.array([enable])
            print(dotask.write(signal, auto_start=True))
            dotask.wait_until_done()
            dotask.stop()
            dotask.close()
            
    def setAnalog(self, target, voltage):
        """ Function to set the analog channel to a specific target
        to a certain voltage """
        if self.__deviceInfo[target]['AOChan'] is None:
            raise NidaqHelperError('Target has no analog output assigned to it')        
        else:
            channel = self.__deviceInfo[target]['AOChan']
            acquisitionTypeFinite = nidaqmx.constants.AcquisitionType.FINITE
            
            aotask = self.__createChanAOTask('setAnalogTask', \
                                       channel, \
                                           acquisitionTypeFinite, \
                                               '100kHzTimebase', \
                                                   100000)
                
            signal = np.array([voltage])
            aotask.write(signal, auto_start=True)
            aotask.wait_until_done()
            aotask.stop()
            aotask.close()
            
    def runScan(self, signalDic):
        """ Function assuming that the user wants to run a full scan with a stage 
        controlled by analog voltage outputs and a cycle of TTL pulses continuously
        running. """
        stageDic = signalDic['stageScanSignalsDict']
        ttlDic = signalDic['TTLCycleSignalsDict']
        
        AOTargetChanPairs = self.__makeSortedTargets('AOChan')
        
        AOsignals = []
        
        for pair in AOTargetChanPairs:
            signal = stageDic[pair[0]]
            AOsignals.append(signal)
    
        DOTargetChanPairs = self.__makeSortedTargets('DOLine')
        
        DOsignals = []
        
        for pair in DOTargetChanPairs:
            signal = ttlDic[pair[0]]
            DOsignals.append(signal)
            
        AOchannels = []
        for device in [*stageDic]:
            channel = self.__deviceInfo[device]['AOChan']
            if channel is not None:
                AOchannels.append(channel)
        
        sampsInScan = len(AOsignals[0])
        acquisitionTypeFinite = nidaqmx.constants.AcquisitionType.FINITE
        AOtask = self.__createChanAOTask('ScanAOTask', AOchannels, acquisitionTypeFinite, \
                                 r'100kHzTimebase', 100000, min_val=-10, max_val=10, sampsInScan = sampsInScan)
        
        DOlines = []
        for device in [*ttlDic]:
            line = self.__deviceInfo[device]['DOLine']
            if line is not None: 
                DOlines.append(line)
        
        acquisitionTypeContinuous = nidaqmx.constants.AcquisitionType.CONTINUOUS
        DOtask = self.__createLineDOTask('ScanDOTask', DOlines, acquisitionTypeContinuous, r'ao/SampleClock', 100000, sampsInScan = sampsInScan)
        
        
        print(np.shape(np.array(AOsignals)))
        print(np.shape(np.array(DOsignals)))
        AOtask.write(np.array(AOsignals), auto_start=False)
        DOtask.write(np.array(DOsignals), auto_start=False)
        
        DOtask.start()
        AOtask.start()
        
        
    def runContinuous(self, digital_targets, digital_signals):
        pass
        