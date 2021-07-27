"""
Created on Tue Apr  7 16:46:33 2020

"""
import operator
import traceback
import warnings

import nidaqmx
import nidaqmx.constants
import nidaqmx._lib
import numpy as np

from imswitch.imcommon.framework import Signal, SignalInterface, Thread


class NidaqManager(SignalInterface):
    """ For interaction with NI-DAQ hardware interfaces. """

    sigScanBuilt = Signal(object, object)  # (scanInfoDict, deviceList)
    sigScanStarted = Signal()
    sigScanDone = Signal()

    sigScanBuildFailed = Signal()

    def __init__(self, setupInfo):
        super().__init__()
        self.__setupInfo = setupInfo
        self.tasks = {}
        self.busy = False
        self.__timerCounterChannel = setupInfo.nidaq.timerCounterChannel
        self.__startTrigger = setupInfo.nidaq.startTrigger

    def __makeSortedTargets(self, sortingKey):
        targetPairs = []
        for targetId, targetInfo in self.__setupInfo.getAllDevices().items():
            value = getattr(targetInfo, sortingKey)
            if value is not None:
                pair = [targetId, value]
                targetPairs.append(pair)
        targetPairs.sort(key=operator.itemgetter(1))
        return targetPairs

    def __createChanAOTask(self, name, channels, acquisitionType, source, rate,
                           min_val=-1, max_val=1, sampsInScan=1000, starttrig=False,
                           reference_trigger='ai/StartTrigger'):
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
        citaskchannel = citask.ci_channels.add_ci_count_edges_chan(
            'Dev1/ctr%s' % channel,
            initial_count=0,
            edge=nidaqmx.constants.Edge.RISING,
            count_direction=nidaqmx.constants.CountDirection.COUNT_UP
        )
        citaskchannel.ci_count_edges_term = terminal
        # not sure if below is needed/what is standard/if I should use DMA (seems to be preferred) or INTERRUPT (as in Imspector, more load on CPU)
        citaskchannel.ci_data_xfer_mech = nidaqmx.constants.DataTransferActiveTransferMode.DMA

        if acquisitionType == 'finite':
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

    def __createChanCOTask(self, name, channel, rate, sampsInScan=1000, starttrig=False,
                           reference_trigger='ai/StartTrigger'):
        cotask = nidaqmx.Task(name)
        cotaskchannel = cotask.co_channels.add_co_pulse_chan_freq(
            'Dev1/ctr%s' % channel, freq=rate, units=nidaqmx.constants.FrequencyUnits.HZ
        )
        #cotask.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)
        cotask.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                                          samps_per_chan=sampsInScan)

        if starttrig:
            cotask.triggers.arm_start_trigger.dig_edge_src = reference_trigger
            cotask.triggers.arm_start_trigger.trig_type = nidaqmx.constants.TriggerType.DIGITAL_EDGE

        return cotask

    def __createChanAITask(self, name, channels, acquisitionType, source, rate,
                           min_val=-0.5, max_val=10.0, sampsInScan=1000, starttrig=False,
                           reference_trigger='ai/StartTrigger'):
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

    def __createChanCITaskLegacy(self, name, channel, acquisitionType, source, sampsInScan=1000,
                                 reference_trigger='PFI12'):
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
            task = self.__createChanCITask(taskName, *args)
        task.start()
        self.tasks[taskName] = task

    def readInputTask(self, taskName, samples=0, timeout=False):
        if not timeout:
            return self.tasks[taskName].read(samples)
        else:
            return self.tasks[taskName].read(samples, timeout)

    def setDigital(self, target, enable):
        """ Function to set the digital line to a specific target
        to either "high" or "low" voltage """
        line = self.__setupInfo.getDevice(target).digitalLine
        if line is None:
            raise NidaqManagerError('Target has no digital output assigned to it')
        else:
            if not self.busy:
                self.busy = True
                try:
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
                except (nidaqmx._lib.DaqNotFoundError, nidaqmx._lib.DaqFunctionNotSupportedError,
                        nidaqmx.DaqError) as e:
                    warnings.warn(str(e), RuntimeWarning)
                finally:
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
                try:
                    acquisitionTypeFinite = nidaqmx.constants.AcquisitionType.FINITE
                    tasklen = 10
                    aotask = self.__createChanAOTask('setAnalogTask',
                                                     channel,
                                                     acquisitionTypeFinite,
                                                     r'100kHzTimebase',
                                                     100000, min_val, max_val, tasklen, False)

                    signal = voltage*np.ones(tasklen, dtype=np.float)
                    try:
                        aotask.write(signal, auto_start=True)
                    except:
                        print('Attempted writing analog data that is too large or too small, or other error when writing the task.')
                    aotask.wait_until_done()
                    aotask.stop()
                    aotask.close()
                except (nidaqmx._lib.DaqNotFoundError, nidaqmx._lib.DaqFunctionNotSupportedError,
                        nidaqmx.DaqError) as e:
                    warnings.warn(str(e), RuntimeWarning)
                finally:
                    self.busy = False

    def runScan(self, signalDic, scanInfoDict):
        """ Function assuming that the user wants to run a full scan with a stage
        controlled by analog voltage outputs and a cycle of TTL pulses continuously
        running. """
        if not self.busy:
            self.busy = True
            self.signalSent = False
            print('Create nidaq scan...')

            try:
                # TODO: fill this
                stageDic = signalDic['scanSignalsDict']
                ttlDic = signalDic['TTLCycleSignalsDict']

                AOTargetChanPairs = self.__makeSortedTargets('analogChannel')
                AOdevices = []
                AOsignals = []
                AOchannels = []

                for device, channel in AOTargetChanPairs:
                    if device not in stageDic:
                        continue
                    AOdevices.append(device)
                    AOsignals.append(stageDic[device])
                    AOchannels.append(channel)

                DOTargetChanPairs = self.__makeSortedTargets('digitalLine')
                DOdevices = []
                DOsignals = []
                DOlines = []

                for device, line in DOTargetChanPairs:
                    if device not in ttlDic:
                        continue
                    DOdevices.append(device)
                    DOsignals.append(ttlDic[device])
                    DOlines.append(line)

                if len(AOsignals) < 1 and len(DOsignals) < 1:
                    raise NidaqManagerError('No signals to send')

                # create task waiters and change constants for beginning scan
                self.aoTaskWaiter = WaitThread()
                self.doTaskWaiter = WaitThread()
                if self.__timerCounterChannel is not None:
                    self.timerTaskWaiter = WaitThread()
                    # create timer counter output task, to control the acquisition timing (1 MHz)
                    sampsInScan = np.int(len(AOsignals[0] if len(AOsignals) > 0 else DOsignals[0]) * 10)
                    self.timerTask = self.__createChanCOTask(
                        'TimerTask', channel=self.__timerCounterChannel, rate=1e6, sampsInScan=sampsInScan,
                        starttrig=self.__startTrigger, reference_trigger='ao/StartTrigger'
                    )
                    self.timerTaskWaiter.connect(self.timerTask)
                    self.timerTaskWaiter.sigWaitDone.connect(
                        lambda: self.taskDone('timer', self.timerTaskWaiter)
                    )
                    self.tasks['timer'] = self.timerTask
                acquisitionTypeFinite = nidaqmx.constants.AcquisitionType.FINITE
                scanclock = r'100kHzTimebase'
                ref_trigger = 'ao/StartTrigger'
                clockDO = scanclock
                if len(AOsignals) > 0:
                    sampsInScan = len(AOsignals[0])
                    self.aoTask = self.__createChanAOTask('ScanAOTask', AOchannels,
                                                          acquisitionTypeFinite, scanclock,
                                                          100000, min_val=-10, max_val=10,
                                                          sampsInScan=sampsInScan,
                                                          starttrig=False)
                    self.tasks['ao'] = self.aoTask
                    self.aoTask.write(np.array(AOsignals), auto_start=False)

                    self.aoTaskWaiter.connect(self.aoTask)
                    self.aoTaskWaiter.sigWaitDone.connect(
                        lambda: self.taskDone('ao', self.aoTaskWaiter)
                    )
                    clockDO = r'ao/SampleClock'
                if len(DOsignals) > 0:
                    sampsInScan = len(DOsignals[0])
                    self.doTask = self.__createLineDOTask('ScanDOTask', DOlines,
                                                          acquisitionTypeFinite, clockDO,
                                                          100000, sampsInScan=sampsInScan,
                                                          starttrig=self.__startTrigger,
                                                          reference_trigger='ao/StartTrigger')
                    self.tasks['do'] = self.doTask
                    self.doTask.write(np.array(DOsignals), auto_start=False)

                    self.doTaskWaiter.connect(self.doTask)
                    self.doTaskWaiter.sigWaitDone.connect(
                        lambda: self.taskDone('do', self.doTaskWaiter)
                    )
            except Exception:
                print(traceback.format_exc())
                for task in self.tasks.values():
                    task.close()
                self.tasks = {}
                self.busy = False
                self.sigScanBuildFailed.emit()
            else:
                self.sigScanBuilt.emit(scanInfoDict, AOdevices + DOdevices)

                if self.__timerCounterChannel is not None:
                    self.tasks['timer'].start()
                    self.timerTaskWaiter.start()
                if len(DOsignals) > 0:
                    self.tasks['do'].start()
                    #print('DO task started')
                    self.doTaskWaiter.start()

                if len(AOsignals) > 0:
                    self.tasks['ao'].start()
                    #print('AO task started')
                    self.aoTaskWaiter.start()
                self.sigScanStarted.emit()
                print('Nidaq scan started!')

    def stopTask(self, taskName):
        self.tasks[taskName].stop()
        self.tasks[taskName].close()
        del self.tasks[taskName]
        #print(f'Task {taskName} deleted')

    def inputTaskDone(self, taskName):
        if not self.signalSent:
            self.stopTask(taskName)
            if not self.tasks:
                self.scanDone()

    def taskDone(self, taskName, taskWaiter):
        if not taskWaiter.running and not self.signalSent:
            self.stopTask(taskName)
            if not self.tasks:
                self.scanDone()

    def scanDone(self):
        self.signalSent = True
        self.busy = False
        print('Nidaq scan finished!')
        self.sigScanDone.emit()

    def runContinuous(self, digital_targets, digital_signals):
        pass


class WaitThread(Thread):
    sigWaitDone = Signal()

    def __init__(self, *args, **lowLevelManagers):
        super().__init__(*args, **lowLevelManagers)
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
        self.sigWaitDone.emit()
        self.quit()


class NidaqManagerError(Exception):
    """ Exception raised when error occurs in NidaqManager """
    def __init__(self, message):
        self.message = message


# Copyright (C) 2020, 2021 TestaLab
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
