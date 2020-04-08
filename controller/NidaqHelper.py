# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 16:46:33 2020

@author: _Xavi
"""
#import nidaqmx
#
#class NidaqHelper():
#    
#    def __init__(self, ):
#        import nidaqmx
#        self.deviceInfo = [['488 Exc', 1, [0, 247, 255]],
#                           ['405', 2, [130, 0, 200]],
#                           ['488 OFF', 3, [0, 247, 255]],
#                           ['Camera', 4, [255, 255, 255]]]
#                           
#    def __createDOTask(self, name, lines, acquisition, clock, rate):
#        dotask = nidaqmx.Task(name)
#        dotask.do_channels.add_do_chan(lines='Dev1/port0/line%s', lines)
#        dotask.timing.cfg_samp_clk_timing(source=clock, rate=rate, sample_mode=acquisition)
#        return dotask
#
#    def __createAOTask(self, name, lines, acquisition, clock, rate):
#        aotask = nidaqmx.Task(name)
#        aotask.ao_channels.add_ao_voltage_chan('Dev1/ao%s',lines,  min_val = 0, max_val = 5)
#        aotask.timing.cfg_samp_clk_timing(source=clock, rate=rate, sample_mode=acquisition)
#        return aotask
#        
#    def setDigital(self, target, enable):
#    def setAnalog(self, target, voltage):
#
#    def runScan(self, analog_targets, digital_targets, analog_signals, digital_signals):
#        self.aotask.close()
#    def runContinuous(self, digital_targets, digital_signals):
#
#        