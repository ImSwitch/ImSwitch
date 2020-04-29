# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 16:46:33 2020

@author: _Xavi
"""
import nidaqmx
import numpy as np
from controller.TempestaErrors import NidaqHelperError

class NidaqHelper():
    
    def __init__(self, deviceInfo = None):
        if deviceInfo is None:
            self.deviceInfo = {'OFF_Laser': {'AOChan': None, 'DOLine': 0},
                               'ON_Laser': {'AOChan': None, 'DOLine': 1},
                               'RO_Laser': {'AOChan': None, 'DOLine': 2},
                               'X_Stage': {'AOChan': 0, 'DOLine': None},
                               'Y_Stage': {'AOChan': 1, 'DOLine': None},
                               'Z_Stage': {'AOChan': 2, 'DOLine': None}}
        else:
            self.deviceInfo = deviceInfo
                

        
    def __createSingleLineDOTask(self, name, lines, acquisition, source, rate):
        """ Simplified function to create a digital output task """
        dotask = nidaqmx.Task(name)
        
        lines = np.atleast_1d(lines)
        
        for line in lines:
            dotask.do_channels.add_do_chan('Dev1/port0/line%s' % line)
        dotask.timing.cfg_samp_clk_timing(source=source, rate=rate, \
                                          sample_mode=acquisition)
        return dotask

    def __createSingleChanAOTask(self, name, channels, acquisitionType, \
                                 source, rate, min_val=-1, max_val=1):
        """ Simplified function to create an analog output task """
        aotask = nidaqmx.Task(name)
        
        channels = np.atleast_1d(channels)
        
        for channel in channels:
            aotask.ao_channels.add_ao_voltage_chan('Dev1/ao%s' % channel,  \
                                               min_val = min_val, \
                                                   max_val = max_val)
        aotask.timing.cfg_samp_clk_timing(source=source, rate=rate, \
                                          sample_mode=acquisitionType)
        return aotask
        
    def setDigital(self, target, enable):
        """ Function to set the digital line to a specific target
        to either "high" or "low" voltage """
        if self.deviceInfo[target]['DOLine'] is None:
            raise NidaqHelperError('Target has no digital output assigned to it')        
        else:
            line = self.deviceInfo[target]['DOLine']
            acquisittionTypeFinite = nidaqmx.constants.AcquisitionType.FINITE
            
            dotask = self.__createSingleLineDOTask('setDigitalTask', \
                                       line, \
                                           acquisittionTypeFinite, \
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
        if self.deviceInfo[target]['AOChan'] is None:
            raise NidaqHelperError('Target has no analog output assigned to it')        
        else:
            channel = self.deviceInfo[target]['AOChan']
            acquisittionTypeFinite = nidaqmx.constants.AcquisitionType.FINITE
            
            aotask = self.__createSingleChanAOTask('setAnalogTask', \
                                       channel, \
                                           acquisittionTypeFinite, \
                                               '100kHzTimebase', \
                                                   100000)
                
            signal = np.array([voltage])
            aotask.write(signal, auto_start=True)
            aotask.wait_until_done()
            aotask.stop()
            aotask.close()
            
    def runScan(self, signalDic):
        stageDic = signalDic['stageScanSignalsDict']
        ttlDic = signalDic['TTLCycleSignalsDict']
         
        
    
    def runContinuous(self, digital_targets, digital_signals):
        pass
        