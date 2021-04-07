# -*- coding: utf-8 -*-
"""
Created on Fri Jan 08 14:00:00 2021

@author: jonatanalvelid
"""

import numpy as np

from .DetectorManager import (
    DetectorManager, DetectorNumberParameter, DetectorListParameter
)
from framework import Signal, SignalInterface, Thread, Worker

class APDManager(DetectorManager):

    # TODO: use the same manager for the PMT, with the type of detector as an argument. NidaqPointDetectorManager
    def __init__(self, APDInfo, name, nidaqManager, **_kwargs):
        model = name
        self._name = name
        self.__pixelsizex = 0
        self.__pixelsizey = 0
        fullShape = (1000,1000)
        self._image = np.random.rand(fullShape[0],fullShape[1])*100
        #self._nidaq_clock_source = r'20MHzTimebase'
        #self._detection_samplerate = float(20e6)  # detection sampling rate for the Nidaq, in Hz
        #self._nidaq_clock_source = r'100kHzTimebase'
        #self._detection_samplerate = float(100e3)  # detection sampling rate for the Nidaq, in Hz
        #self._nidaq_clock_source = r'20MHzTimebase'
        #self._detection_samplerate = float(1e6)  # detection sampling rate for the Nidaq, in Hz
        self._nidaq_clock_source = r'ctr2InternalOutput'  # counter output task generating a 1 MHz frequency digitial pulse train
        self._detection_samplerate = float(1e6)
        self.acquisition = True

        self._channel = APDInfo.managerProperties["ctrInputLine"]
        self._terminal = APDInfo.managerProperties["terminal"]

        # Prepare parameters
        parameters = {}
        self._nidaqManager = nidaqManager
        self._nidaqManager.scanInitiateSignal.connect(lambda scanInfoDict: self.initiateScan(scanInfoDict))
        print(f'{self._name}: scanInitiateSignal is connected')
        self._nidaqManager.scanStartSignal.connect(self.startScan)
        self.__shape = fullShape
        super().__init__(name, fullShape, [1], model, parameters)

    def initiateScan(self, scanInfoDict):
        #print('APD: initiatescan 1')
        if self.acquisition:
            #print('APD: initiatescan 2')
            self._scanWorker = ScanWorker(self, scanInfoDict)
            #print('APD: initiatescan 3')
            self._scanThread = Thread()
            #print('APD: initiatescan 4')
            self._scanWorker.moveToThread(self._scanThread)
            #print('APD: initiatescan 5')
            self._scanThread.started.connect(self._scanWorker.run)
            #print('APD: initiatescan 6')
            self._scanWorker.scanning = True
            #print('APD: initiatescan 7')
            self._scanWorker.newLine.connect(lambda line_pixels, line_count: self.updateImage(line_pixels, line_count))
            #print('APD: initiatescan 8')
            self._scanWorker.acqDoneSignal.connect(self.stopAcquisition)
            #print('APD: initiatescan 9')
    
    def startScan(self):
        if self.acquisition:
            self._scanThread.start()
    
    def startAcquisition(self):
        self.acquisition = True

    def stopAcquisition(self):
        self._scanWorker.scanning = False
        self._scanThread.quit()
        self._scanThread.wait()

    def getLatestFrame(self):
        return self._image

    def updateImage(self, line_pixels, line_count):
        #print('ui: update image')
        #print(f'ui: line pixel shape{np.shape(line_pixels)}')
        #print(f'ui: line count: {line_count}')

        self._image[-(line_count+1),:] = line_pixels
        if line_count == 0:
            # adjust viewbox shape to new image shape at the start of the image
            self.updateLatestFrame(False)


    def setParameter(self, name, value):
        pass

    def getParameter(self, name):
       pass

    def setBinning(self, binning):
        super().setBinning(binning)
    
    def getChunk(self):
        pass

    def flushBuffers(self):
        pass

    @property
    def shape(self):
        return self.__shape

    def setShape(self, ysize, xsize):
        self.__shape = (xsize, ysize)

    @property
    def pixelSize(self):
        return tuple([1, self.__pixelsize_ax2, self.__pixelsize_ax1])

    def setPixelSize(self, pixelsize_ax1, pixelsize_ax2):
        self.__pixelsize_ax1 = pixelsize_ax1
        self.__pixelsize_ax2 = pixelsize_ax2

    def crop(self, hpos, vpos, hsize, vsize):
        pass

    def show_dialog(self):
        "Manager: open camera settings dialog mock."
        pass

class ScanWorker(Worker):
    newLine = Signal(np.ndarray, int)
    acqDoneSignal = Signal()
    def __init__(self, manager, scanInfoDict):
        super().__init__()
        self._alldata = 0
        self._manager = manager
        self._name = self._manager._name
        self._channel = self._manager._channel

        #self._throw_delay = int(13*20e6/100e3)  # TODO: calculate somehow, the phase delay from scanning signal to when the scanner is actually in the correct place. How do we find this out? Depends on the response of the galvos, can we measure this somehow?
        #self._throw_delay = 15200
        self._throw_delay = 25

        self._scan_dwell_time = scanInfoDict['dwell_time']  # time step of scanning, in s
        self._frac_det_dwell = round(self._scan_dwell_time * self._manager._detection_samplerate)  # ratio between detection sampling time and pixel dwell time (has nothing to do with sampling of scanning line)
        self._n_lines = round(scanInfoDict['n_lines'])  # number of lines in image
        self._pixels_line = round(scanInfoDict['pixels_line'])  # number of pixels per line
        self._samples_line = round(scanInfoDict['scan_samples_line'] * scanInfoDict['scan_time_step'] * self._manager._detection_samplerate)  # # det samples per line: time per line * det sampling rate
        self._samples_period = round(scanInfoDict['scan_samples_period'] * scanInfoDict['scan_time_step'] * self._manager._detection_samplerate)  # # det samples per fast axis period: time per period * det sampling rate
        #samptot = scanInfoDict['scan_samples_total']
        #scantimest = scanInfoDict['scan_time_step']
        #detsamprate = self._manager._detection_samplerate
        #samptotdet = round(samptot * scantimest * detsamprate)
        #print(f'scansampltot: {samptot}, scantimestep: {scantimest}, detsamprate: {detsamprate}, totdetsamp: {samptotdet}')
        self._samples_total = round(scanInfoDict['scan_samples_total'] * scanInfoDict['scan_time_step'] * self._manager._detection_samplerate)  # # det samples in total signal: time for total scan * det sampling rate
        self._throw_startzero = round(scanInfoDict['scan_throw_startzero'] * scanInfoDict['scan_time_step'] * self._manager._detection_samplerate)  # # samples to throw due to the starting zero-padding: time for zero_padding * det sampling rate
        self._throw_initpos = round(scanInfoDict['scan_throw_initpos'] * scanInfoDict['scan_time_step'] * self._manager._detection_samplerate)  # # samples to throw due to smooth inital positioning time: time for initpos * det sampling rate
        self._throw_settling = round(scanInfoDict['scan_throw_settling'] * scanInfoDict['scan_time_step'] * self._manager._detection_samplerate)  # # samples to throw due to settling time: time for settling * det sampling rate
        self._throw_startacc = round(scanInfoDict['scan_throw_startacc'] * scanInfoDict['scan_time_step'] * self._manager._detection_samplerate)  # # samples to throw due to starting acceleration: time for acceleration * det sampling rate
        self._throw_finalpos = round(scanInfoDict['scan_throw_finalpos'] * scanInfoDict['scan_time_step'] * self._manager._detection_samplerate)  # # samples to throw due to smooth final positioning time: time for initpos * det sampling rate
        self._samples_throw = self._throw_startzero + self._throw_initpos + self._throw_settling + self._throw_startacc + self._throw_delay
        # TODO: How to I get the following parameters into this function? Or read them from within _nidaqmanager? channels should definitely come from here I suppose...
        self._manager._nidaqManager.startInputTask(self._name, 'ci', self._channel, 'finite', self._manager._nidaq_clock_source, self._manager._detection_samplerate, self._samples_total, True, 'ao/StartTrigger', self._manager._terminal)
        self._manager._image = np.zeros((self._n_lines, self._pixels_line))
        self._manager.setShape(self._n_lines, self._pixels_line)
        self._manager.setPixelSize(float(scanInfoDict['pixel_size_ax1']),float(scanInfoDict['pixel_size_ax2']))

        self._last_value = 0
        self._line_counter = 0

    def run(self):
        throwdata = self._manager._nidaqManager.readInputTask(self._name, self._samples_throw)
        self._last_value = throwdata[-1]
        #self._alldata += len(throwdata)
        #print(f'sw0: throw data shape: {np.shape(throwdata)}')
        while self._line_counter < self._n_lines:
            if self.scanning:
                #print(f'sw1: line {self._line_counter} started')
                if self._line_counter == self._n_lines - 1:
                    data = self._manager._nidaqManager.readInputTask(self._name, self._samples_line)  # read a line
                else:  
                    data = self._manager._nidaqManager.readInputTask(self._name, self._samples_period)  # read a whole period, starting with the line and then the data during the flyback
                #self._alldata += len(data)
                #print(f'sw1.5: length of all data so far: {self._alldata}')
                #print(f'sw2: line {self._line_counter}: read data shape: {np.shape(data)}')
                # galvo-sensor-data reading
                subtractionArray = np.concatenate(([self._last_value],data[:-1]))
                self._last_value = data[-1]
                data = data - subtractionArray  # Now apd_data is an array contains at each position the number of counts at this position
                line_samples = data[:self._samples_line]  # only take the first samples that corresponds to the samples during the line
                #print(f'sw3: line {self._line_counter}: samples per line: {self._samples_line}')
                #print(f'sw4: line {self._line_counter}: save data shape: {np.shape(line_samples)}')
                line_pixels = self.samples_to_pixels(line_samples)  # translate sample stream to an array where each value corresponds to a pixel count
                #print(f'sw5: line {self._line_counter}: line data shape: {np.shape(line_pixels)}')
                self.newLine.emit(line_pixels, self._line_counter)
                #print(f'sw6: line {self._line_counter} finished')
                self._line_counter += 1
            else:
                self.close()
        throwdata = self._manager._nidaqManager.readInputTask(self._name, self._throw_startzero+self._throw_finalpos)
        #self._alldata += len(throwdata)
        #print(f'sw fin: {self._name}: length of all data so far: {self._alldata}')
        self.acqDoneSignal.emit()
        #print(self._name)
        #print(np.mean(self._manager._image))
        self.close()

    def samples_to_pixels(self, line_samples):
        """ Reshape read datastream over the line to a line with pixel counts.
        Do this by summing elements, with the rate ratio calculated previously. """
        # If reading with higher sample rate (ex. 20 MHz, 50 ns per sample), sum N samples for each pixel, since scanning curve is linear
        # (ex. only allow dwell times as multiples of 0.05 us if sampling rate is 20 MHz)
        line_pixels = np.array(line_samples).reshape(-1, self._frac_det_dwell).sum(axis=1)
        return line_pixels

    def close(self):
        self._manager._nidaqManager.stopInputTask(self._name)
