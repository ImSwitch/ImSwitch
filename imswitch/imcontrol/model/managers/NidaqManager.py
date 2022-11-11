import operator
import traceback
import warnings

import nidaqmx
import nidaqmx._lib
import nidaqmx.constants
import numpy as np

from imswitch.imcommon.framework import Signal, SignalInterface, Thread
from imswitch.imcommon.model import initLogger


class NidaqManager(SignalInterface):
    """ For interaction with NI-DAQ hardware interfaces. """

    sigScanBuilt = Signal(object, object, object)  # (scanInfoDict, signalDict, deviceList)
    sigScanStarted = Signal()
    sigScanDone = Signal()

    sigScanBuildFailed = Signal()

    def __init__(self, setupInfo):
        super().__init__()
        self.__logger = initLogger(self)

        self.__setupInfo = setupInfo
        self.tasks = {}
        self.doTaskWaiter = None
        self.aoTaskWaiter = None
        self.timerTaskWaiter = None
        self.busy = False
        self.busy_scan = False
        self.__timerCounterChannel = setupInfo.nidaq.getTimerCounterChannel()
        self.__startTrigger = setupInfo.nidaq.startTrigger

    def __del__(self):
        for taskWaiter in [self.doTaskWaiter, self.aoTaskWaiter, self.timerTaskWaiter]:
            if taskWaiter is not None:
                taskWaiter.quit()
                taskWaiter.wait()
        if hasattr(super(), '__del__'):
            super().__del__()

    def __makeSortedTargets(self, sortingKey):
        targetPairs = []
        for targetId, targetInfo in self.__setupInfo.getAllDevices().items():
            value = getattr(targetInfo, sortingKey)
            if callable(value):
                value = value()
            if value is not None:
                pair = [targetId, value]
                targetPairs.append(pair)
        targetPairs.sort(key=operator.itemgetter(1))
        return targetPairs

    def __createChanAOTask(self, name, channels, acquisitionType, source, rate,
                           min_val=-1, max_val=1, sampsInScan=1000, starttrig=False,
                           reference_trigger='ai/StartTrigger'):
        """ Simplified function to create an analog output task """
        #self.__logger.debug(f'Create AO task: {name}')
        aotask = nidaqmx.Task(name)
        channels = np.atleast_1d(channels)

        for channel in channels:
            aotask.ao_channels.add_ao_voltage_chan(channel,
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
        self.__logger.debug(f'Create DO task: {name}')
        #self.__logger.debug(lines)
        dotask = nidaqmx.Task(name)

        lines = np.atleast_1d(lines)

        for line in lines:
            dotask.do_channels.add_do_chan(line)
        if source:
            dotask.timing.cfg_samp_clk_timing(source=source, rate=rate,
                                            sample_mode=acquisitionType,
                                            samps_per_chan=sampsInScan)
        else:
            dotask.timing.cfg_samp_clk_timing(rate=rate,
                                            sample_mode=acquisitionType,
                                            samps_per_chan=sampsInScan)
        if starttrig:
            dotask.triggers.start_trigger.cfg_dig_edge_start_trig(reference_trigger)
        self.__logger.debug(f'Created DO task: {name}')
        return dotask

    def __createChanCITask(self, name, channel, acquisitionType, source, rate, sampsInScan=1000,
                           starttrig=False, reference_trigger='ai/StartTrigger', terminal='PFI0'):
        """ Simplified function to create a counter input task """
        #self.__logger.debug(f'Create CI task: {name}')
        citask = nidaqmx.Task(name)
        citaskchannel = citask.ci_channels.add_ci_count_edges_chan(
            channel,
            initial_count=0,
            edge=nidaqmx.constants.Edge.RISING,
            count_direction=nidaqmx.constants.CountDirection.COUNT_UP
        )
        citaskchannel.ci_count_edges_term = terminal
        # not sure if below is needed/what is standard/if I should use DMA (seems to be preferred)
        # or INTERRUPT (as in Imspector, more load on CPU)
        citaskchannel.ci_data_xfer_mech = nidaqmx.constants.DataTransferActiveTransferMode.DMA

        if acquisitionType == 'finite':
            acqType = nidaqmx.constants.AcquisitionType.FINITE
        citask.timing.cfg_samp_clk_timing(source=source,
                                          rate=rate,
                                          sample_mode=acqType,
                                          samps_per_chan=sampsInScan)
        # ci_ctr_timebase_master_timebase_div
        # citask.channels.ci_ctr_timebase_master_timebase_div = 20
        if starttrig:
            citask.triggers.arm_start_trigger.dig_edge_src = reference_trigger
            citask.triggers.arm_start_trigger.trig_type = nidaqmx.constants.TriggerType.DIGITAL_EDGE

        return citask

    def __createChanCOTask(self, name, channel, rate, sampsInScan=1000, starttrig=False,
                           reference_trigger='ai/StartTrigger'):
        #self.__logger.debug(f'Create CO task: {name}')
        cotask = nidaqmx.Task(name)
        self.cotaskchannel = cotask.co_channels.add_co_pulse_chan_freq(
            channel, freq=rate, units=nidaqmx.constants.FrequencyUnits.HZ
        )
        # cotask.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)
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
        #self.__logger.debug(f'Create AI task: {name}')
        aitask = nidaqmx.Task(name)
        for channel in channels:
            aitask.ai_channels.add_ai_voltage_chan(channel)
        aitask.timing.cfg_samp_clk_timing(source=source,
                                          rate=rate,
                                          sample_mode=acquisitionType,
                                          samps_per_chan=sampsInScan)
        if starttrig:
            aitask.triggers.start_trigger.cfg_dig_edge_start_trig(reference_trigger)
        return aitask

    def startInputTask(self, taskName, taskType, *args):
        if taskType == 'ai':
            task = self.__createChanAITask(taskName, *args)
        elif taskType == 'ci':
            task = self.__createChanCITask(taskName, *args)
        task.start()
        self.tasks[taskName] = task

    def readInputTask(self, taskName, samples=0, timeout=False):
        if not timeout:
            #self.__logger.debug(f'Read {samples} samples from {taskName}')
            return self.tasks[taskName].read(samples)
        else:
            return self.tasks[taskName].read(samples, timeout)

    def setDigital(self, target, enable):
        """ Function to set the digital line to a specific target
        to either "high" or "low" voltage """
        line = self.__setupInfo.getDevice(target).getDigitalLine()
        if line is None:
            raise NidaqManagerError('Target has no digital output assigned to it')
        else:
            self.__logger.debug(f'{target} setDigital start: {enable}')
            #if not self.busy:
            self.__logger.debug(f'{target} setDigital st1')
            #self.busy = True
            try:
                self.__logger.debug(f'{target} setDigital st2')
                acquisitionTypeFinite = nidaqmx.constants.AcquisitionType.FINITE
                tasklen = 100
                if not self.busy_scan:
                    start_condition = True
                    self.__logger.debug("Do with 100kHz")
                    self.setDigitalTask = self.__createLineDOTask('setDigitalTask',
                                                        line,
                                                        acquisitionTypeFinite,
                                                        None,
                                                        100000,
                                                        tasklen,
                                                        False)
                else:
                    # TODO: works one time now, but the task is probably not stopped, closed, and deleted properly, so the second time it's called during a scan it doesn't work
                    self.setDigitalTaskWaiter = WaitThread()
                    start_condition = False
                    self.setDigitalTask = self.__createLineDOTask('setDigitalTask', line,
                                                          acquisitionTypeFinite, r'ao/SampleClock',
                                                          100000, tasklen,
                                                          starttrig=self.__startTrigger,
                                                          reference_trigger='ao/StartTrigger')
                self.__logger.debug(f'{target} setDigital st3')
                # signal = np.array([enable])
                signal = enable * np.ones(tasklen, dtype=bool)
                try:
                    self.setDigitalTask.write(signal, auto_start=start_condition)
                    if self.busy_scan:
                        self.setDigitalTaskWaiter.sigWaitDone.connect(lambda: self.stopTaskSingle(self.setDigitalTask))
                except Exception:
                    self.__logger.exception(Exception)
                    self.__logger.warning(
                        'Attempted writing digital data that is too large or too small, or other'
                        ' error when writing the task.'
                    )
                if self.busy_scan:
                    self.setDigitalTask.start()
                else:
                    self.setDigitalTask.wait_until_done()
                    self.setDigitalTask.stop()
                    self.setDigitalTask.close()
            except (nidaqmx._lib.DaqNotFoundError, nidaqmx._lib.DaqFunctionNotSupportedError,
                    nidaqmx.DaqError) as e:
                warnings.warn(str(e), RuntimeWarning)
            finally:
                #self.busy = False
                self.__logger.debug(f'{target} setDigital finished: {enable}')

    def setAnalog(self, target, voltage, min_val=-1, max_val=1):
        """ Function to set the analog channel to a specific target
        to a certain voltage """
        channel = self.__setupInfo.getDevice(target).getAnalogChannel()
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

                    signal = voltage * np.ones(tasklen, dtype=float)
                    try:
                        aotask.write(signal, auto_start=True)
                    except Exception:
                        self.__logger.error(
                            'Attempted writing analog data that is too large or too small, or other'
                            ' error when writing the task.'
                        )
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
            self.busy_scan = True
            self.signalSent = False
            self.__logger.debug('Create nidaq scan...')

            try:
                # TODO: fill this
                stageDic = signalDic['scanSignalsDict']
                ttlDic = signalDic['TTLCycleSignalsDict']

                AOTargetChanPairs = self.__makeSortedTargets('getAnalogChannel')
                AOdevices = []
                AOsignals = []
                AOchannels = []

                for device, channel in AOTargetChanPairs:
                    #self.__logger.debug(f'Device {device}, channel {channel} is part of scan')
                    if device not in stageDic:
                        continue
                    AOdevices.append(device)
                    AOsignals.append(stageDic[device])
                    AOchannels.append(channel)

                DOTargetChanPairs = self.__makeSortedTargets('getDigitalLine')
                DOdevices = []
                DOsignals = []
                DOlines = []

                for device, line in DOTargetChanPairs:
                    if device not in ttlDic or 'Dev' not in line:
                        continue
                    DOdevices.append(device)
                    DOsignals.append(ttlDic[device])
                    DOlines.append(line)
                
                # check if line and frame clock should be outputted, if so add to DO lists
                if self.__setupInfo.scan.lineClockLine:
                    DOdevices.append('LineClock')
                    DOsignals.append(ttlDic['line_clock'])
                    DOlines.append(self.__setupInfo.scan.lineClockLine)
                if self.__setupInfo.scan.frameClockLine:
                    DOdevices.append('FrameClock')
                    DOsignals.append(ttlDic['frame_clock'])
                    DOlines.append(self.__setupInfo.scan.frameClockLine)

                if len(AOsignals) < 1 and len(DOsignals) < 1:
                    raise NidaqManagerError('No signals to send')

                # create task waiters and change constants for beginning scan
                self.aoTaskWaiter = WaitThread()
                self.doTaskWaiter = WaitThread()
                if self.__timerCounterChannel is not None:
                    self.timerTaskWaiter = WaitThread()
                    # create timer counter output task, to control the acquisition timing (1 MHz)
                    detSampsInScan = int(
                        len(AOsignals[0] if len(AOsignals) > 0 else DOsignals[0]) * (1e6/100e3)
                    )
                    #self.__logger.debug(f'Total detection samples in scan: {detSampsInScan}')
                    self.timerTask = self.__createChanCOTask(
                        'TimerTask', channel=self.__timerCounterChannel, rate=1e6,
                        sampsInScan=detSampsInScan, starttrig=self.__startTrigger,
                        reference_trigger='ao/StartTrigger'
                    )
                    self.timerTaskWaiter.connect(self.timerTask)
                    self.timerTaskWaiter.sigWaitDone.connect(
                        lambda: self.taskDone('timer', self.timerTaskWaiter)
                    )
                    self.tasks['timer'] = self.timerTask
                acquisitionTypeFinite = nidaqmx.constants.AcquisitionType.FINITE
                scanclock = r'100kHzTimebase'
                clockDO = scanclock
                if len(AOsignals) > 0:
                    scanSampsInScan = len(AOsignals[0])
                    self.__logger.debug(f'Total scan samples in scan: {scanSampsInScan}')
                    self.aoTask = self.__createChanAOTask('ScanAOTask', AOchannels,
                                                          acquisitionTypeFinite, scanclock,
                                                          100000, min_val=-10, max_val=10,
                                                          sampsInScan=scanSampsInScan,
                                                          starttrig=False)
                    self.tasks['ao'] = self.aoTask

                    # Important to squeeze the array, otherwise we might get an "invalid number of
                    # channels" error
                    self.aoTask.write(np.array(AOsignals).squeeze(), auto_start=False)

                    self.aoTaskWaiter.connect(self.aoTask)
                    self.aoTaskWaiter.sigWaitDone.connect(
                        lambda: self.taskDone('ao', self.aoTaskWaiter)
                    )
                    clockDO = r'ao/SampleClock'
                if len(DOsignals) > 0:
                    scanSampsInScan = len(DOsignals[0])
                    self.doTask = self.__createLineDOTask('ScanDOTask', DOlines,
                                                          acquisitionTypeFinite, clockDO,
                                                          100000, sampsInScan=scanSampsInScan,
                                                          starttrig=self.__startTrigger,
                                                          reference_trigger='ao/StartTrigger')
                    self.tasks['do'] = self.doTask

                    # Important to squeeze the array, otherwise we might get an "invalid number of
                    # channels" error
                    self.doTask.write(np.array(DOsignals).squeeze(), auto_start=False)

                    self.doTaskWaiter.connect(self.doTask)
                    self.doTaskWaiter.sigWaitDone.connect(
                        lambda: self.taskDone('do', self.doTaskWaiter)
                    )
            except Exception:
                self.__logger.error(traceback.format_exc())
                for task in self.tasks.values():
                    task.close()
                self.tasks = {}
                self.busy = False
                self.busy_scan = False
                self.sigScanBuildFailed.emit()
            else:
                self.sigScanBuilt.emit(scanInfoDict, signalDic, AOdevices + DOdevices)

                if self.__timerCounterChannel is not None:
                    self.tasks['timer'].start()
                    self.timerTaskWaiter.start()
                if len(DOsignals) > 0:
                    self.tasks['do'].start()
                    # self.__logger.debug('DO task started')
                    self.doTaskWaiter.start()

                if len(AOsignals) > 0:
                    self.tasks['ao'].start()
                    # self.__logger.debug('AO task started')
                    self.aoTaskWaiter.start()
                self.sigScanStarted.emit()
                self.__logger.info('Nidaq scan started!')

    def stopTask(self, taskName):
        self.tasks[taskName].stop()
        self.tasks[taskName].close()
        del self.tasks[taskName]
        # self.__logger.debug(f'Task {taskName} deleted')

    def stopTaskSingle(self, taskName):
        taskName.stop()
        taskName.close()
        del taskName

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
        self.busy_scan = False
        self.__logger.info('Nidaq scan finished!')
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


# Copyright (C) 2020-2021 ImSwitch developers
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
