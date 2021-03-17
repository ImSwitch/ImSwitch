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
        model = 0
        self.__name = name
        fullShape = (1000, 1000)
        self._image = np.random.rand(fullShape[0],fullShape[1])*100
        self._detection_samplerate = 100e6  # detection sampling rate for the Nidaq, in Hz
        self._nidaq_clock_source = r'20MHzTimebase'

        self.__channel = APDInfo.managerProperties["ctrInputLine"]

        # Prepare parameters
        parameters = {}
        self._nidaqManager = nidaqManager
        self._nidaqManager.scanInitiateSignal.connect(lambda scanInfoDict: self.initiateScan(scanInfoDict))
        self._nidaqManager.scanStartSignal.connect(self.startScan)
        super().__init__(name, fullShape, [1], model, parameters)

    def initiateScan(self, scanInfoDict):
        if self.acquisition:
            self._scanWorker = ScanWorker(self, scanInfoDict)
            self._scanThread = Thread()
            self._scanWorker.moveToThread(self._scanThread)
            self._scanThread.started.connect(self._scanWorker.run)
            self._scanWorker.scanning = True
            self._scanWorker.newLine.connect(lambda line_pixels, line_count: self.updateImage(line_pixels, line_count))
    
    def startScan(self):
        if self.acquistion:
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
        print('update image')
        print(np.shape(line), self.__shape)

        self._image[line_count,:] = line_pixels
        # not sure, maybe enough with every 100ms updated image as without below call?
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

    def pixelSize(self):
        pass

    def crop(self, hpos, vpos, hsize, vsize):
        pass

    def show_dialog(self):
        "Manager: open camera settings dialog mock."
        pass

class ScanWorker(Worker):
    newLine = Signal(np.ndarray, int)
    def __init__(self, manager, scanInfoDict):
        super().__init__()
        self._name = manager.__name
        self._channel = manager.__channel
        self._manager = manager
        self._scantimestep = scanInfoDict['time_step'] * 1e-6  # time step of scanning, in s
        self._ratefrac_det_scan = self._scantimestep * self._manager._detection_samplerate  # sampling rate ratio between detection and scanning (=200 if scanning at 100 kHz and det at 20 MHz)
        self._n_lines = scanInfoDict['n_lines']  # number of lines in image
        self._pixels_line = scanInfoDict['pixels_line']  # number of pixels per line
        self._samples_line = scanInfoDict['samples_line'] * self._ratefrac_det_scan  # number of samples per line
        self._samples_period = scanInfoDict['samples_period'] * self._ratefrac_det_scan  # number of samples per fast axis period
        self._samples_total = scanInfoDict['samples_total'] * self._ratefrac_det_scan  # number of samples in total signal
        self._throw_startzero = scanInfoDict['throw_startzero'] * self._ratefrac_det_scan  # number of samples to throw due to the starting zero-padding
        self._throw_settling = scanInfoDict['throw_settling'] * self._ratefrac_det_scan  # number of samples to throw due to settling time
        self._throw_startacc = scanInfoDict['throw_startacc'] * self._ratefrac_det_scan  # number of samples to throw due to starting acceleration
        self._samples_throw = self._throw_startzero + self._throw_settling + self._throw_startacc + self._throw_delay
        detectionsamples_total = self._samples_total * self._ratefrac_det_scan  # total number of detection samples, unit: 1 * s * 1/s = 1
        self._throw_delay = 100  # TODO: calculate somehow, the phase delay from scanning signal to when the scanner is actually in the correct place. How do we find this out? Depends on the response of the galvos, can we measure this somehow?
        # TODO: How to I get the following parameters into this function? Or read them from within _nidaqmanager? channels should definitely come from here I suppose...
        self._manager._nidaqManager.startInputTask(self._name, 'ci', channel=self._channel, acquisitionType='finite', source=self._manager._nidaq_clock_source, sampsInScan=detectionsamples_total, reference_trigger='PFI12')
        self._manager._image = np.zeros((self._n_lines, self._pixels_line))
        self._manager.__fullShape = (self._n_lines, self._pixels_line)

        self._last_value = 0
        self._line_counter = 0

    def run(self):
        throwdata = self._manager._nidaqManager.readInputTask(self._name, self._samples_throw)
        while self._line_counter < self._n_lines:
            if self.scanning:
                data = self._manager._nidaqManager.readInputTask(self._name, self._samples_period)  # read a whole period, starting with the line and then the data during the flyback
                # galvo-sensor-data reading
                subtractionArray = np.concatenate(([self._last_value],data[:-1]))
                self._last_value = data[-1]
                data = data - subtractionArray  # Now apd_data is an array contains at each position the number of counts at this position
                line_samples = data[:self._samples_line]  # only take the first samples that corresponds to the samples during the line
                line_pixels = samples_to_pixels(line_samples)  # translate sample stream to an array where each value corresponds to a pixel count
                newLine.emit(line_pixels, self._line_counter)
                self._line_counter += 1
            else:
                self.close()

    def samples_to_pixels(self, line_samples):
        """ Reshape read datastream over the line to a line with pixel counts.
        Do this by summing elements, with the rate ratio calculated previously. """
        # If reading with higher sample rate (ex. 20 MHz, 50 ns per sample), sum N samples for each pixel, since scanning curve is linear
        # (ex. only allow dwell times as multiples of 0.05 us if sampling rate is 20 MHz)
        line_pixels = np.array(line_samples).reshape(-1, self._ratefrac_det_scan).sum(axis=1)
        return line_pixels

    def close(self):
        self.manager.nidaqManager.stopInputTask(self._name)
