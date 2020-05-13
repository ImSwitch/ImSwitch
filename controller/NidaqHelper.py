# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 16:46:33 2020

"""
import nidaqmx
import numpy as np
from controller.TempestaErrors import NidaqHelperError
import operator
from pyqtgraph.Qt import QtCore

class NidaqHelper(QtCore.QObject):
    scanDoneSignal = QtCore.pyqtSignal()
    
    def __init__(self, deviceInfo = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.busy = False
        if deviceInfo is None:
            self.__deviceInfo = {'405': {'AOChan': None, 'DOLine': 0},
                               '488': {'AOChan': None, 'DOLine': 1},
                               '473': {'AOChan': 3, 'DOLine': 2},
                               'CAM': {'AOChan': None, 'DOLine': 3},
                               'Stage_X': {'AOChan': 0, 'DOLine': None},
                               'Stage_Y': {'AOChan': 1, 'DOLine': None},
                               'Stage_Z': {'AOChan': 2, 'DOLine': None}}
                    
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

            
    def __createLineDOTask(self, name, lines, acquisition, source, rate, sampsInScan = 1000):
        """ Simplified function to create a digital output task """
        dotask = nidaqmx.Task(name)
        
        lines = np.atleast_1d(lines)
        
        for line in lines:
            dotask.do_channels.add_do_chan('Dev1/port0/line%s' % line)
        dotask.timing.cfg_samp_clk_timing(source=source, rate=rate, \
                                          sample_mode=acquisition, samps_per_chan = sampsInScan)
        return dotask

    def __createChanAOTask(self, name, channels, acquisitionType, \
                                 source, rate, min_val=-1, max_val=1, sampsInScan = 1000):
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
            if not self.busy:
                self.busy = True
                line = self.__deviceInfo[target]['DOLine']
                acquisitionTypeFinite = nidaqmx.constants.AcquisitionType.FINITE
                
                dotask = self.__createLineDOTask('setDigitalTask', \
                                           line, \
                                               acquisitionTypeFinite, \
                                                   '100kHzTimebase', \
                                                       100000)
                #signal = np.array([enable])
                signal = enable*np.ones(100, dtype=bool)
                dotask.write(signal, auto_start=True)
                dotask.wait_until_done()
                dotask.stop()
                dotask.close()
                self.busy = False
            
    def setAnalog(self, target, voltage, min_val=-1, max_val=1):
        """ Function to set the analog channel to a specific target
        to a certain voltage """
        if self.__deviceInfo[target]['AOChan'] is None:
            raise NidaqHelperError('Target has no analog output assigned to it')        
        else:
            if not self.busy:
                self.busy = True
                channel = self.__deviceInfo[target]['AOChan']
                acquisitionTypeFinite = nidaqmx.constants.AcquisitionType.FINITE
                
                aotask = self.__createChanAOTask('setAnalogTask', \
                                           channel, \
                                               acquisitionTypeFinite, \
                                                   '100kHzTimebase', \
                                                       100000, min_val, max_val)
                    
                signal = np.array([voltage])
                aotask.write(signal, auto_start=True)
                aotask.wait_until_done()
                aotask.stop()
                aotask.close()
                self.busy = False
            
    def runScan(self, signalDic):
        """ Function assuming that the user wants to run a full scan with a stage 
        controlled by analog voltage outputs and a cycle of TTL pulses continuously
        running. """
        if not self.busy:
            self.busy = True
            stageDic = signalDic['stageScanSignalsDict']
            ttlDic = signalDic['TTLCycleSignalsDict']
            AOTargetChanPairs = self.__makeSortedTargets('AOChan')
            
            AOsignals = []
            AOchannels = []
    
            for pair in AOTargetChanPairs:
                try:
                    signal = stageDic[pair[0]]
                    channel = pair[1]
                    AOsignals.append(signal)
                    AOchannels.append(channel)
                except:
                    pass
        
            DOTargetChanPairs = self.__makeSortedTargets('DOLine')
            
            DOsignals = []
            DOlines = []
    
            for pair in DOTargetChanPairs:
                try:
                    signal = ttlDic[pair[0]]
                    line = pair[1]
                    DOsignals.append(signal)
                    DOlines.append(line)
                except:
                    pass
                
            
            sampsInScan = len(AOsignals[0])
            acquisitionTypeFinite = nidaqmx.constants.AcquisitionType.FINITE
            self.aoTask = self.__createChanAOTask('ScanAOTask', AOchannels, acquisitionTypeFinite, \
                                     r'100kHzTimebase', 100000, min_val=-10, max_val=10, sampsInScan = sampsInScan)
            
    
            self.doTask = self.__createLineDOTask('ScanDOTask', DOlines, acquisitionTypeFinite, r'ao/SampleClock', 100000, sampsInScan = sampsInScan)
    
            
            
    
            self.aoTask.write(np.array(AOsignals), auto_start=False)
            self.doTask.write(np.array(DOsignals), auto_start=False)
            
            self.aoTaskWaiter = WaitThread()
            self.aoTaskWaiter.connect(self.aoTask)
            self.aoTaskWaiter.waitdoneSignal.connect(self.taskDone)
            
            self.doTaskWaiter = WaitThread()
            self.doTaskWaiter.connect(self.doTask)
            self.doTaskWaiter.waitdoneSignal.connect(self.taskDone)
            self.signalSent = False
            
            self.doTask.start()
            self.aoTask.start()
            
            self.doTaskWaiter.start()
            self.aoTaskWaiter.start()
        
    def taskDone(self):
        if not self.doTaskWaiter.running and not self.aoTaskWaiter.running and not self.signalSent:
            self.busy = False
            self.scanDoneSignal.emit()
            self.signalSent = True
        
    def runContinuous(self, digital_targets, digital_signals):
        pass

class WaitThread(QtCore.QThread):
    waitdoneSignal = QtCore.pyqtSignal()

    def connect(self, task):
        self.task = task
        self.running = True
        
    def run(self):
        if self.running:
            self.task.wait_until_done(nidaqmx.constants.WAIT_INFINITELY)
            self.close()
            
    def close(self):
        self.running = False
        self.task.stop()
        self.task.close()
        self.waitdoneSignal.emit()
        self.quit()