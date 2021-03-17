# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 16:46:33 2020

"""
import operator

import nidaqmx
import numpy as np

from framework import Signal, SignalInterface, Thread


class NidaqManager(SignalInterface):
    scanDoneSignal = Signal()
    scanInitiateSignal = Signal(dict)
    scanStartSignal = Signal()

    def __init__(self, setupInfo):
        super().__init__()
        self.__setupInfo = setupInfo
        self.inputTasks = {}
        self.busy = False
        self.aoTaskWaiter = WaitThread()
        self.doTaskWaiter = WaitThread()

    def __makeSortedTargets(self, sortingKey):
        targetPairs = []
        for targetId, targetInfo in self.__setupInfo.getAllDevices().items():
            value = getattr(targetInfo, sortingKey)
            if value is not None:
                pair = [targetId, value]
                targetPairs.append(pair)
        targetPairs.sort(key=operator.itemgetter(1))
        return targetPairs

    def __createChanAOTask(self, name, channels, acquisitionType,
                           source, rate, min_val=-1, max_val=1, sampsInScan=1000):
        """ Simplified function to create an analog output task """
        aotask = nidaqmx.Task(name)

        channels = np.atleast_1d(channels)

        for channel in channels:
            aotask.ao_channels.add_ao_voltage_chan('Dev1/ao%s' % channel,
                                                   min_val=min_val,
                                                   max_val=max_val)

        aotask.timing.cfg_samp_clk_timing(source=source,
                                          rate=rate,
                                          sample_mode=acquisitionType,
                                          samps_per_chan=sampsInScan)
        return aotask

    def __createLineDOTask(self, name, lines, acquisitionType, source, rate, sampsInScan=1000):
        """ Simplified function to create a digital output task """
        dotask = nidaqmx.Task(name)

        lines = np.atleast_1d(lines)

        for line in lines:
            dotask.do_channels.add_do_chan('Dev1/port0/line%s' % line)
        dotask.timing.cfg_samp_clk_timing(source=source, rate=rate,
                                          sample_mode=acquisitionType,
                                          samps_per_chan=sampsInScan)
        return dotask

    def __createChanAITask(self, name, channels, acquisitionType, source, min_val=-0.5,
                           max_val=10.0, sampsInScan=1000, reference_trigger='PFI12'):
        """ Simplified function to create an analog input task """
        aitask = nidaqmx.AnalogInputTask(name)
        for channel in channels:
            aitask.create_voltage_channel(channel, min_val, max_val)        
        aitask.configure_timing_sample_clock(source=source,
                                             sample_mode=acquisitionType,
                                             samps_per_chan=sampsInScan)
        aitask.configure_trigger_digital_edge_start(reference_trigger) 
        return aitask

    def __createChanCITask(self, name, channel, acquisitionType, source, sampsInScan=1000, reference_trigger='PFI12'):
        """ Simplified function to create a counter input task """
        citask = nidaqmx.CounterInputTask(name)
        #for channel in channels:
        citask.create_channel_count_edges('Dev1/ctr' % channel, init=0)
        citask.set_terminal_count_edges('Dev1/ctr' % channel, "PFI0")

        citask.configure_timing_sample_clock(source=source,
                                             sample_mode=acquisitionType, 
                                             samples_per_channel=sampsInScan)
        citask.set_arm_start_trigger_source(reference_trigger)
        citask.set_arm_start_trigger(trigger_type='digital_edge')
        return citask

    def startInputTask(self, taskName, taskType, *args):
        if taskType=='ai':
            task = self.__createChanAITask(self, taskName, *args)
        elif taskType=='ci':
            task = self.__createChanCITask(self, taskName, *args)
        task.start()
        #TODO: do something here to read and throw out the first read signal data? Or do somewhere else...
        self.inputTasks[taskName] = task

    def stopInputTask(self, taskName):
        self.inputTasks[taskName].stop()
        del self.inputTasks[taskName]
    
    def readInputTask(self, taskName, samples=0, timeout=0):
        if timeout==0:
            return self.inputTasks[taskName].read(samples)
        else:
            return self.inputTasks[taskName].read(samples, timeout)

    def setDigital(self, target, enable):
        """ Function to set the digital line to a specific target
        to either "high" or "low" voltage """
        line = self.__setupInfo.getDevice(target).digitalLine
        if line is None:
            raise NidaqManagerError('Target has no digital output assigned to it')
        else:
            if not self.busy:
                self.busy = True
                acquisitionTypeFinite = nidaqmx.constants.AcquisitionType.FINITE

                dotask = self.__createLineDOTask('setDigitalTask',
                                                 line,
                                                 acquisitionTypeFinite,
                                                 '100kHzTimebase',
                                                 100000)
                # signal = np.array([enable])
                signal = enable * np.ones(100, dtype=bool)
                try:
                    dotask.write(signal, auto_start=True)
                except:
                    print(' Attempted writing analog data that is too large or too small.')
                dotask.wait_until_done()
                dotask.stop()
                dotask.close()
                self.busy = False

    def setAnalog(self, target, voltage, min_val=-1, max_val=1):
        """ Function to set the analog channel to a specific target
        to a certain voltage """
        channel = self.__setupInfo.getDevice(target).analogChannel
        if channel is None:
            raise NidaqManagerError('Target has no analog output assigned to it')
        else:
            if not self.busy:
                self.busy = True
                acquisitionTypeFinite = nidaqmx.constants.AcquisitionType.FINITE

                aotask = self.__createChanAOTask('setAnalogTask',
                                                 channel,
                                                 acquisitionTypeFinite,
                                                 '100kHzTimebase',
                                                 100000, min_val, max_val, 2)

                signal = voltage*np.ones(2, dtype=np.float)
                try:
                    aotask.write(signal, auto_start=True)
                except:
                    print(' Attempted writing analog data that is too large or too small.')
                aotask.wait_until_done()
                aotask.stop()
                aotask.close()
                self.busy = False

    def runScan(self, signalDic, scanInfoDict):
        """ Function assuming that the user wants to run a full scan with a stage 
        controlled by analog voltage outputs and a cycle of TTL pulses continuously
        running. """
        print('Create nidaq scan...')
        if not self.busy:
            print('runScan 1')
            self.busy = True
            self.signalSent = False
            # TODO: fill this
            stageDic = signalDic['scanSignalsDict']
            ttlDic = signalDic['TTLCycleSignalsDict']
            AOTargetChanPairs = self.__makeSortedTargets('analogChannel')

            AOsignals = []
            AOchannels = []
            print('runScan 2')
            for pair in AOTargetChanPairs:
                try:
                    print('runScan 3')
                    signal = stageDic[pair[0]]
                    channel = pair[1]
                    AOsignals.append(signal)
                    AOchannels.append(channel)
                    print('runScan 4')
                except:
                    pass

            DOTargetChanPairs = self.__makeSortedTargets('digitalLine')

            DOsignals = []
            DOlines = []
            print('runScan 5')
            for pair in DOTargetChanPairs:
                try:
                    print('runScan 6')
                    signal = ttlDic[pair[0]]
                    line = pair[1]
                    DOsignals.append(signal)
                    DOlines.append(line)
                    print('runScan 7')
                except:
                    pass

            if len(AOsignals) < 1 and len(DOsignals) < 1:
                self.busy = False
                return
            print('runScan 8')
            acquisitionTypeFinite = nidaqmx.constants.AcquisitionType.FINITE
            clockDO = r'100kHzTimebase'
            print('runScan 9')
            if len(AOsignals) > 0:
                sampsInScan = len(AOsignals[0])
                self.aoTask = self.__createChanAOTask('ScanAOTask', AOchannels,
                                                      acquisitionTypeFinite, r'100kHzTimebase',
                                                      100000, min_val=-10, max_val=10,
                                                      sampsInScan=sampsInScan)
                self.aoTask.write(np.array(AOsignals), auto_start=False)

                self.aoTaskWaiter.connect(self.aoTask)
                self.aoTaskWaiter.waitdoneSignal.connect(self.taskDone)
                clockDO = r'ao/SampleClock'
            print('runScan 10')
            if len(DOsignals) > 0:
                sampsInScan = len(DOsignals[0])
                self.doTask = self.__createLineDOTask('ScanDOTask', DOlines,
                                                      acquisitionTypeFinite, clockDO,
                                                      100000, sampsInScan=sampsInScan)
                self.doTask.write(np.array(DOsignals), auto_start=False)

                self.doTaskWaiter.connect(self.doTask)
                self.doTaskWaiter.waitdoneSignal.connect(self.taskDone)
            print('runScan 11')
            scanInitiateSignal.emit(scanInfoDict)
            print('runScan 12')
            if len(DOsignals) > 0:
                self.doTask.start()
                self.doTaskWaiter.start()
            print('runScan 13')
            if len(AOsignals) > 0:
                self.aoTask.start()
                self.aoTaskWaiter.start()
            scanStartSignal.emit()
            print('runScan 14')
            print('Nidaq scan started!')
  
    def taskDone(self):
        if not self.doTaskWaiter.running and not self.aoTaskWaiter.running and not self.signalSent:
            self.busy = False
            self.signalSent = True
            self.scanDoneSignal.emit()

    def runContinuous(self, digital_targets, digital_signals):
        pass


class WaitThread(Thread):
    waitdoneSignal = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task = None
        self.running = False

    def connect(self, task):
        self.task = task
        self.running = True

    def run(self):
        if self.running:
            self.task.wait_until_done(nidaqmx.constants.WAIT_INFINITELY)
            self.close()
        else:
            self.quit()

    def close(self):
        self.running = False
        if self.task is not None:
            self.task.stop()
            self.task.close()
        self.waitdoneSignal.emit()
        self.quit()
