# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 16:46:33 2020

"""
import operator
import time
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
        self.outputTasks = {}
        self.busy = False

    def __makeSortedTargets(self, sortingKey):
        targetPairs = []
        for targetId, targetInfo in self.__setupInfo.getAllDevices().items():
            value = getattr(targetInfo, sortingKey)
            if value is not None:
                pair = [targetId, value]
                targetPairs.append(pair)
        targetPairs.sort(key=operator.itemgetter(1))
        return targetPairs

    def __createChanAOTask(self, name, channels, acquisitionType, source, rate, min_val=-1,
                           max_val=1, sampsInScan=1000, starttrig=False, reference_trigger='ai/StartTrigger'):
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
        if starttrig:
            aotask.triggers.start_trigger.cfg_dig_edge_start_trig(reference_trigger)
        return aotask

    def __createLineDOTask(self, name, lines, acquisitionType, source, rate, sampsInScan=1000,
                           starttrig=False, reference_trigger='ai/StartTrigger'):
        """ Simplified function to create a digital output task """
        dotask = nidaqmx.Task(name)

        lines = np.atleast_1d(lines)

        for line in lines:
            dotask.do_channels.add_do_chan('Dev1/port0/line%s' % line)
        dotask.timing.cfg_samp_clk_timing(source=source, rate=rate,
                                          sample_mode=acquisitionType,
                                          samps_per_chan=sampsInScan)
        if starttrig:                                          
            dotask.triggers.start_trigger.cfg_dig_edge_start_trig(reference_trigger)
        return dotask

    def __createChanCITask(self, name, channel, acquisitionType, source, rate, sampsInScan=1000,
                           starttrig=False, reference_trigger='ai/StartTrigger', terminal='PFI0'):
        """ Simplified function to create a counter input task """
        citask = nidaqmx.Task(name)
        print('Dev1/ctr%s' % channel)
        citaskchannel = citask.ci_channels.add_ci_count_edges_chan('Dev1/ctr%s' % channel,
                                                                   initial_count=0,
                                                                   edge=nidaqmx.constants.Edge.RISING,
                                                                   count_direction=nidaqmx.constants.CountDirection.COUNT_UP)
        citaskchannel.ci_count_edges_term = terminal
        if acquisitionType=='finite':
            acqType = nidaqmx.constants.AcquisitionType.FINITE
        citask.timing.cfg_samp_clk_timing(source=source,
                                          rate=rate,
                                          sample_mode=acqType, 
                                          samps_per_chan=sampsInScan)
        #ci_ctr_timebase_master_timebase_div
        #citask.channels.ci_ctr_timebase_master_timebase_div = 20
        if starttrig:
            citask.triggers.arm_start_trigger.dig_edge_src = reference_trigger
            citask.triggers.arm_start_trigger.trig_type = nidaqmx.constants.TriggerType.DIGITAL_EDGE

        return citask

    def __createChanAITask(self, name, channels, acquisitionType, source, rate, min_val=-0.5,
                           max_val=10.0, sampsInScan=1000, starttrig=False, reference_trigger='ai/StartTrigger'):
        """ Simplified function to create an analog input task """
        aitask = nidaqmx.Task(name)
        for channel in channels:
            aitask.ai_channels.add_ai_voltage_chan('Dev1/ai%s' % channel)
        aitask.timing.cfg_samp_clk_timing(source=source,
                                          rate=rate,
                                          sample_mode=acquisitionType,
                                          samps_per_chan=sampsInScan)
        if starttrig:
            aitask.triggers.start_trigger.cfg_dig_edge_start_trig(reference_trigger)
        return aitask

    def __createChanCITaskLegacy(self, name, channel, acquisitionType, source, sampsInScan=1000, reference_trigger='PFI12'):
        """ Simplified function to create a counter input task """
        #citask = nidaqmx.CounterInputTask(name)
        citask = nidaqmx.Task(name)
        #for channel in channels:
        citask.create_channel_count_edges('Dev1/ctr' % channel, init=0)
        citask.set_terminal_count_edges('Dev1/ctr' % channel, "PFI0")

        citask.configure_timing_sample_clock(source=source,
                                             sample_mode=acquisitionType, 
                                             samps_per_chan=sampsInScan)
        citask.set_arm_start_trigger_source(reference_trigger)
        citask.set_arm_start_trigger(trigger_type='digital_edge')
        return citask

    def __createChanAITaskLegacy(self, name, channels, acquisitionType, source, min_val=-0.5,
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

    def startInputTask(self, taskName, taskType, *args):
        if taskType=='ai':
            task = self.__createChanAITask(taskName, *args)
        elif taskType=='ci':
            #print(taskName)
            #print(*args)
            task = self.__createChanCITask(taskName, *args)
        task.start()
        print('start CI task')
        self.inputTasks[taskName] = task

    def stopInputTask(self, taskName):
        self.inputTasks[taskName].stop()
        self.inputTasks[taskName].close()
        del self.inputTasks[taskName]
        print(f'Input task deleted: {taskName}')
    
    def readInputTask(self, taskName, samples=0, timeout=0):
        #print(f'NM: readInputTask {taskName}, #samples: {samples}')
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
                tasklen = 100
                dotask = self.__createLineDOTask('setDigitalTask',
                                                 line,
                                                 acquisitionTypeFinite,
                                                 r'100kHzTimebase',
                                                 100000,
                                                 tasklen,
                                                 False)
                # signal = np.array([enable])
                signal = enable * np.ones(tasklen, dtype=bool)
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
                                                 100000, min_val, max_val, 2, False)

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
            self.aoTaskWaiter = WaitThread()
            self.doTaskWaiter = WaitThread()
            #self.startTaskWaiter = WaitThread()
            self.busy = True
            self.signalSent = False
            # TODO: fill this
            stageDic = signalDic['scanSignalsDict']
            ttlDic = signalDic['TTLCycleSignalsDict']
            AOTargetChanPairs = self.__makeSortedTargets('analogChannel')

            AOsignals = []
            AOchannels = []
            for pair in AOTargetChanPairs:
                try:
                    #print('runScan 3')
                    signal = stageDic[pair[0]]
                    channel = pair[1]
                    AOsignals.append(signal)
                    AOchannels.append(channel)
                except:
                    pass

            DOTargetChanPairs = self.__makeSortedTargets('digitalLine')
            #print(DOTargetChanPairs)

            DOsignals = []
            DOlines = []
            for pair in DOTargetChanPairs:
                try:
                    signal = ttlDic[pair[0]]
                    #print(np.shape(signal))
                    line = pair[1]
                    DOsignals.append(signal)
                    DOlines.append(line)
                    #print(np.shape(DOsignals))
                except:
                    pass

            if len(AOsignals) < 1 and len(DOsignals) < 1:
                self.busy = False
                return
            # create dummy ai task
            #self.start_task = self.__createChanAITask('StartTask', [1],
            #                                    nidaqmx.constants.AcquisitionType.FINITE,
            #                                    r'OnboardClock', 1000000, min_val=0.0,
            #                                    max_val=10.0, sampsInScan=len(AOsignals[0])*10)
            #self.startTaskWaiter.connect(self.start_task)
            #self.startTaskWaiter.waitdoneSignal.connect(self.taskDoneStart)
            acquisitionTypeFinite = nidaqmx.constants.AcquisitionType.FINITE
            scanclock = r'100kHzTimebase'
            clockDO = scanclock
            if len(AOsignals) > 0:
                sampsInScan = len(AOsignals[0])
                #print(sampsInScan)
                #print(AOchannels)
                print(np.shape(AOsignals))
                self.aoTask = self.__createChanAOTask('ScanAOTask', AOchannels,
                                                      acquisitionTypeFinite, scanclock,
                                                      100000, min_val=-10, max_val=10,
                                                      sampsInScan=sampsInScan,
                                                      starttrig=False)#,
                                                      #reference_trigger='ai/StartTrigger')
                self.aoTask.write(np.array(AOsignals), auto_start=False)

                self.aoTaskWaiter.connect(self.aoTask)
                self.aoTaskWaiter.waitdoneSignal.connect(self.taskDoneAO)
                self.outputTasks['ao'] = self.aoTask
                clockDO = r'ao/SampleClock'
            if len(DOsignals) > 0:
                sampsInScan = len(DOsignals[0])
                #print(sampsInScan)
                #print(DOlines)
                print(np.shape(DOsignals))
                self.doTask = self.__createLineDOTask('ScanDOTask', DOlines,
                                                      acquisitionTypeFinite, clockDO,
                                                      100000, sampsInScan=sampsInScan,
                                                      starttrig=True,
                                                      reference_trigger='ao/StartTrigger')
                self.doTask.write(np.array(DOsignals), auto_start=False)

                self.doTaskWaiter.connect(self.doTask)
                self.doTaskWaiter.waitdoneSignal.connect(self.taskDoneDO)
                self.outputTasks['do'] = self.doTask
            self.scanInitiateSignal.emit(scanInfoDict)
            if len(DOsignals) > 0:
                self.doTask.start()
                print('dotask started')
                self.doTaskWaiter.start()
            if len(AOsignals) > 0:
                self.aoTask.start()
                print('aotask started')
                self.aoTaskWaiter.start()
            #self.start_task.start()
            #self.startTaskWaiter.start()
            print('starttask started')
            self.scanStartSignal.emit()
            print('Nidaq scan started!')
    
    def stopOutputTask(self, taskName):
        self.outputTasks[taskName].stop()
        self.outputTasks[taskName].close()
        del self.outputTasks[taskName]
        print(f'Output task deleted: {taskName}')

    def stopStartTask(self):
        self.start_task.stop()
        self.start_task.close()
        del self.start_task
        print('Start task deleted')

    def taskDoneAO(self):
        if not self.aoTaskWaiter.running and not self.signalSent:
            self.busy = False
            self.signalSent = True
            self.scanDoneSignal.emit()
            self.stopOutputTask('ao')
            print('AO scan finished!')

    def taskDoneDO(self):
        if not self.doTaskWaiter.running:
            self.stopOutputTask('do')
            print('DO scan finished!')

    def taskDoneStart(self):
        if not self.startTaskWaiter.running:
            self.stopStartTask()
            print('Start task finished!')

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
            print('WT for scan task finished.')
            self.close()
        else:
            self.quit()

    def close(self):
        self.running = False
        #if self.task is not None:
        #    self.task.stop()
        #    self.task.close()
        self.waitdoneSignal.emit()
        self.quit()
