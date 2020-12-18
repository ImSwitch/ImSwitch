# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 16:46:33 2020

"""
import operator

import nidaqmx
import numpy as np
from pyqtgraph.Qt import QtCore

from controller.errors import NidaqHelperError


class NidaqHelper(QtCore.QObject):
    scanDoneSignal = QtCore.pyqtSignal()

    def __init__(self, setupInfo, *args, **kwargs):  #detectorHelper, 
        super().__init__(*args, **kwargs)
        self.__setupInfo = setupInfo

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

    def __createLineDOTask(self, name, lines, acquisition, source, rate, sampsInScan=1000):
        """ Simplified function to create a digital output task """
        dotask = nidaqmx.Task(name)

        lines = np.atleast_1d(lines)

        for line in lines:
            dotask.do_channels.add_do_chan('Dev1/port0/line%s' % line)
        dotask.timing.cfg_samp_clk_timing(source=source, rate=rate,
                                          sample_mode=acquisition, samps_per_chan=sampsInScan)
        return dotask

    def __createChanAITask(self, name, channels, acquisitionType, source, rate, min_val=-0.5,
                           max_val=10.0, sampsInScan=1000, reference_trigger='PFI12'):
        """ Simplified function to create an analog input task """
        aitask = nidaqmx.AnalogInputTask(name)
        for channel in channels:
            aitask.create_voltage_channel(channel, min_val, max_val)        
        aitask.configure_timing_sample_clock(source, sample_mode=acquisitionType, samps_per_chan=sampsInScan)
        aitask.configure_trigger_digital_edge_start(reference_trigger) 
        return aitask

    def __createChanCITask(self, name, channels, acquisitionType, source, rate, sampsInScan=1000, reference_trigger='PFI12'):
        """ Simplified function to create a counter input task """
        citask = nidaqmx.CounterInputTask()
        for channel in channels:
            citask.create_channel_count_edges(channel, init=0)
            citask.set_terminal_count_edges(channel, "PFI0")
        citask.configure_timing_sample_clock(source=source,
                                             sample_mode=acquisitionType, 
                                             samples_per_channel=sampsInScan)
        citask.set_arm_start_trigger_source(reference_trigger)
        citask.set_arm_start_trigger(trigger_type='digital_edge')
        return citask

    def __createChanAOTask(self, name, channels, acquisitionType,
                           source, rate, min_val=-1, max_val=1, sampsInScan=1000):
        """ Simplified function to create an analog output task """
        aotask = nidaqmx.Task(name)

        channels = np.atleast_1d(channels)

        for channel in channels:
            aotask.ao_channels.add_ao_voltage_chan('Dev1/ao%s' % channel,
                                                   min_val=min_val,
                                                   max_val=max_val)

        aotask.timing.cfg_samp_clk_timing(source=source, rate=rate,
                                          sample_mode=acquisitionType, samps_per_chan=sampsInScan)
        return aotask
    
    def setDigital(self, target, enable):
        """ Function to set the digital line to a specific target
        to either "high" or "low" voltage """
        line = self.__setupInfo.getDevice(target).digitalLine
        if line is None:
            raise NidaqHelperError('Target has no digital output assigned to it')
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
            raise NidaqHelperError('Target has no analog output assigned to it')
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
   
    def runScan(self, signalDic, detectors):
        """ Function assuming that the user wants to run a full scan with a stage 
        controlled by analog voltage outputs and a cycle of TTL pulses continuously
        running. """
        if not self.busy:
            self.busy = True
            self.signalSent = False
            stageDic = signalDic['stageScanSignalsDict']
            ttlDic = signalDic['TTLCycleSignalsDict']
            AOTargetChanPairs = self.__makeSortedTargets('analogChannel')

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

            DOTargetChanPairs = self.__makeSortedTargets('digitalLine')

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

            if len(AOsignals) < 1 and len(DOsignals) < 1:
                self.busy = False
                return

            acquisitionTypeFinite = nidaqmx.constants.AcquisitionType.FINITE

            if len(AOsignals) > 0:
                sampsInScan = len(AOsignals[0])
                self.aoTask = self.__createChanAOTask('ScanAOTask', AOchannels,
                                                      acquisitionTypeFinite, r'100kHzTimebase',
                                                      100000, min_val=-10, max_val=10,
                                                      sampsInScan=sampsInScan)
                self.aoTask.write(np.array(AOsignals), auto_start=False)

                self.aoTaskWaiter.connect(self.aoTask)
                self.aoTaskWaiter.waitdoneSignal.connect(self.taskDone)

            if len(DOsignals) > 0:
                sampsInScan = len(DOsignals[0])
                self.doTask = self.__createLineDOTask('ScanDOTask', DOlines,
                                                      acquisitionTypeFinite, r'ao/SampleClock',
                                                      100000, sampsInScan=sampsInScan)
                self.doTask.write(np.array(DOsignals), auto_start=False)

                self.doTaskWaiter.connect(self.doTask)
                self.doTaskWaiter.waitdoneSignal.connect(self.taskDone)

            if len(AOsignals) > 0:
                self.aoTask.start()

            if len(DOsignals) > 0:
                self.doTask.start()

            self.aoTaskWaiter.start()
            self.doTaskWaiter.start()

            self.record_thread = []

            if detectors is not None:
                for i in range(0, length(detectors)):
                    d = detectors[i]
                    if d.type == "PMT":
                        self.aitask = __createChanAITask(d.name, d.channels, d.acquisitionType, source, rate, min_val=-0.5,
                           max_val=10.0, sampsInScan=1000, reference_trigger='PFI12')
                        self.aitask.start()
                        self.record_thread[i] = RecordingThreadPMT()
                        self.record_thread[i].lineSignal.connect(lambda: self._detectorHelper.newLine(i))
                        self.record_thread[i].start()
                    elif d.type == "APD":
                        self.citask = __createChanCITask(d.name, d.channels, d.acquisitionType, source, rate, sampsInScan=1000, reference_trigger='PFI12')
                        self.citask.start()
                        self.record_thread[i] = RecordingThreadAPD()
                        self.record_thread[i].lineSignal.connect(lambda: self._detectorHelper.newLine(i))
                        self.record_thread[i].start()

    def taskDone(self):
        if not self.doTaskWaiter.running and not self.aoTaskWaiter.running and not self.signalSent:
            self.busy = False
            self.signalSent = True
            self.scanDoneSignal.emit()

    def runContinuous(self, digital_targets, digital_signals):
        pass


class WaitThread(QtCore.QThread):
    waitdoneSignal = QtCore.pyqtSignal()

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


class RecordingThreadAPD(QtCore.QThread):
    """Thread recording an image with an APD (Counter input) while the stage is scanning
    
    :param ImageDisplay display: ImageDisplay in scanwidget"""
    lineSignal = QtCore.pyqtSignal()

    def __init__(self,tasks):
        super().__init__()
        self.imageDisplay=main
        self.exiting = True
        self.delay=0
        
        #Initiation of the analog and counter input tasks necessary to avoid crashing the program in certain cases (see stop) 
        self.aitask=0
        self.citask=0
        
    def setParameters(self,sequence_samples,samples_per_channel,sample_rate,samples_per_line,main_axis):
        """prepares the thread for data acquisition with the different parameters values
        
        :param int sequence_samples: number of samples for acquisition of 1 point
        :param int samples_per_channel: Total number of samples generated per channel in the scan
        :param int sample_rate: sample rate in number of samples per second
        :param int samples_per_line: Total number of samples acquired or generate per line, to go back and forth.
        :param string main_axis: The axis driven with a sine
        """
        self.samples_per_line = samples_per_line
        self.sequence_samples = sequence_samples
        self.rate = sample_rate 
        self.main_axis=main_axis #Usually it is x
        self.frequency= self.rate / self.samples_per_line
        print("frequency in apd thread",self.frequency)
        self.steps_per_line = self.imageDisplay.shape[1]
 
        self.n_frames=self.imageDisplay.shape[0]
        
        self.samples_in_scan = samples_per_channel
            
        try:
            #disables the oscilloscope if it is running
            if self.imageDisplay.scanWidget.main.oscilloscope.isRunning:
                self.imageDisplay.scanWidget.main.oscilloscope.start()
        except:
            print("error oscilloscope")


        #To record the sensor output
        record_channel='Dev1/ai5'
        if self.main_axis=="y":
            record_channel='Dev1/ai6'
            
        self.delay = self.rate/self.frequency/4     #elimination of 1/4 period at the beginning
        self.delay+= phase_correction(self.frequency)/self.frequency * self.rate/2/np.pi
        self.delay = int(self.delay)
        
        self.aitask = nidaqmx.AnalogInputTask()
        self.aitask.create_voltage_channel(record_channel,  min_val=-0.5, max_val=10.0)        
        self.aitask.configure_timing_sample_clock(source = r'ao/SampleClock',
                                             sample_mode = 'finite', 
                                             samples_per_channel = self.samples_in_scan+self.delay)
        self.aitask.configure_trigger_digital_edge_start(reference_trigger) 
        print("init citask")
        self.citask = nidaqmx.CounterInputTask()
        self.citask.create_channel_count_edges("Dev1/ctr0", init=0 )
        self.citask.set_terminal_count_edges("Dev1/ctr0","PFI0")
        self.citask.configure_timing_sample_clock(source = r'ao/SampleClock',
                                             sample_mode = 'finite', 
                                            samples_per_channel = self.samples_in_scan+self.delay)
        self.citask.set_arm_start_trigger_source(reference_trigger)
        self.citask.set_arm_start_trigger(trigger_type='digital_edge')
    def run(self):
        """runs this thread to acquire the data in task"""
        self.exiting=False
        self.aitask.start()
        self.citask.start()
#        while not self.imageDisplay.scanWidget.scanner.waiter.isRunning:
#            print("we wait for beginning of aotask")   
#        while self.citask.get_samples_per_channel_acquired()<2:
#            print("waiting for 1st samples to be acquired")
        print("samples apd acquired beofre:",self.citask.get_samples_per_channel_acquired())
        throw_apd_data = self.citask.read(self.delay)
        print("samples apd acquired after:",self.citask.get_samples_per_channel_acquired())
        throw_sensor_data=self.aitask.read(self.delay,timeout=10)  #To synchronize analog input and output

        print("self.delay",self.delay)
        counter = self.n_frames
        print("samples per line",self.samples_per_line)
        last_value = throw_apd_data[-1]        
        
        amplitude=float(self.imageDisplay.scanWidget.widthPar.text())/correction_factors[self.main_axis]
        initial_position = getattr(self.imageDisplay.scanWidget.positionner,self.main_axis)
        
        while(counter>0 and not self.exiting):
            apd_data=self.citask.read(self.samples_per_line)
            sensor_data = self.aitask.read(self.samples_per_line,timeout=10)
            sensor_data=sensor_data[:,0]
            if counter==self.n_frames:
                np.save(r"C:\Users\aurelien.barbotin\Documents\Data\signal5.npy",sensor_data)
            substraction_array = np.concatenate(([last_value],apd_data[:-1]))
            last_value = apd_data[-1]
            apd_data = apd_data-substraction_array #Now apd_data is an array contains at each position the number of counts at this position
            
            length_signal=len(sensor_data)//2
            apd_data=np.absolute(apd_data[0:length_signal])        
            sensor_data=sensor_data[0:length_signal]
            
            line = line_from_sine(apd_data,sensor_data,self.steps_per_line,amplitude,initial_position)
            self.lineSignal.emit(line)
            if counter<6:
                print("counter",counter)
            counter-=1
        self.exiting=True
        self.aitask.stop()
        self.citask.stop()
        
    def stop(self):
        self.exiting=True
        if self.aitask !=0:
            self.aitask.stop()
            del self.aitask
        if self.citask!=0:
            self.citask.stop()
            del self.citask
        
    
class RecordingThreadPMT(QtCore.QThread):
    """Thread to record an image with the PMT while the stage is scanning
    
    :param ImageDisplay main: ImageDisplay in scanwidget"""
    lineSignal = QtCore.pyqtSignal()

    def __init__(self,main):
        super().__init__()
        self.imageDisplay=main
        self.exiting = True
        self.delay=0
        
    def setParameters(self,sequence_samples,samples_per_channel,sample_rate,samples_per_line,main_axis):
        """prepares the thread for data acquisition with the different parameters values
        
        :param int sequence_samples: number of samples for acquisition of 1 point
        :param int samples_per_channel: Total number of samples generated per channel in the scan
        :param int sample_rate: sample rate in number of samples per second
        :param int samples_per_line: Total number of samples acquired or generate per line, to go back and forth.
        :param string main_axis: The axis driven with a sine
        """
        self.samples_per_line = samples_per_line
        self.sequence_samples = sequence_samples
        self.rate = sample_rate 
        self.main_axis=main_axis #Usually it is x
        self.frequency= self.rate / self.samples_per_line/2
        
        self.steps_per_line = self.imageDisplay.shape[1]
 
        self.n_frames=self.imageDisplay.shape[0]
        
        self.samples_in_scan = samples_per_channel   
        if(self.rate != sample_rate * self.samples_in_scan / samples_per_channel):
            print("error arrondi")
            
        print("parameters for acquisition of data : sample rate",self.rate,"samples_per_channel:",self.samples_in_scan)
        self.aitask = nidaqmx.AnalogInputTask()
        self.aitask.create_voltage_channel('Dev1/ai0', terminal = 'rse', min_val=-1, max_val=10.0)

    #To record the sensor output
        record_channel='Dev1/ai5'
        if self.main_axis=="y":
            record_channel='Dev1/ai6'
            
        self.aitask.create_voltage_channel(record_channel, terminal = 'rse', min_val=-0.5, max_val=10.0)
        self.delay = self.rate/self.frequency/4     #elimination of 1/4 period at the beginning
        self.delay+= phase_correction(self.frequency)/self.frequency * self.rate/2/np.pi
        print("delay",self.delay,"value 1",phase_correction(self.frequency)/self.frequency * self.rate/2/np.pi,"value 2",self.rate/self.frequency/4)
        self.delay = int(self.delay)
        
        self.aitask.configure_timing_sample_clock(source = r'ao/SampleClock',
                                             sample_mode = 'finite', 
                                             samples_per_channel = self.samples_in_scan+self.delay)

    def run(self):
        """runs this thread to acquire the data in task"""
        self.exiting=False
        self.aitask.start()
        dat=self.aitask.read(self.delay,timeout=30)  #To synchronize analog input and output
        #To change!!
        counter = self.n_frames
        if record_sensor_output:
            sensor_vals = np.zeros(self.samples_in_scan+self.delay)
            sensor_vals[0:self.delay]=dat[:,1]
            
        amplitude=float(self.imageDisplay.scanWidget.widthPar.text())/correction_factors[self.main_axis]
        initial_position = getattr(self.imageDisplay.scanWidget.positionner,self.main_axis)

        
        while(counter>0 and not self.exiting):
            data=self.aitask.read(self.samples_per_line,timeout=10)
            if record_sensor_output:
                sensor_vals[self.delay+(self.n_frames-counter)*self.samples_per_line:self.delay+(self.n_frames-counter+1)*self.samples_per_line] = data[:,1]

            line = line_from_sine(data[:,0],data[:,1],self.steps_per_line,amplitude,initial_position)
            self.lineSignal.emit(line)
            if counter<6:
                print("counter:",counter)
            counter-=1  #Why are you subtracting?
            
        if record_sensor_output:
            name=str(round(self.rate /self.samples_per_line))+"Hz"
            np.save(save_folder+"\\" +"sensor_output_x"+name,sensor_vals)
        self.aitask.stop()
        self.exiting=True
    def stop(self):
        """Stops the worker"""
        try:
            self.aitask.stop()
            self.aitask.clear()
            del self.aitask
        except:
            pass
