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
        self._image = np.array([])

        self.__channel = APDInfo.managerProperties["ctrInputLine"]

        fullShape = (0, 0)

        # Prepare parameters
        parameters = {}
        self._nidaqManager = nidaqManager
        self._nidaqManager.scanStartSignal.connect(lambda n_lines, pixels_line, samples_line, samples_period, samples_total: self.startScan(n_lines, pixels_line, samples_line, samples_period, samples_total))
        super().__init__(name, fullShape, [1], model, parameters)

    def startScan(self, n_lines, pixels_line, samples_line, samples_period, samples_total):
        if self.acquisition:
            self._scanWorker = ScanWorker(self, n_lines, samples_line, samples_period, samples_total)
            self._scanThread = Thread()
            self._scanWorker.moveToThread(self._scanThread)
            self._scanThread.started.connect(self._scanWorker.run)
            self._scanWorker.scanning = True
            self._scanWorker.newLine.connect(lambda line: self.updateImage(line))
            self._scanThread.start()
    
    def startAcquisition(self):
        self.acquisition = True

    def stopAcquisition(self):
        self._scanWorker.scanning = False
        self._scanThread.quit()
        self._scanThread.wait()
    

    def getLatestFrame(self):
        return self._image

    def updateImage(self, line):
        print('update image')

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
    newLine = Signal(np.ndarray)
    def __init__(self, manager, n_lines, pixels_line, samples_line, samples_period, samples_total):
        super().__init__()
        self._name = manager.__name
        self._channel = manager.__channel
        self._manager = manager
        self._n_lines = n_lines  # number of lines in image
        self._pixels_line = pixels_line  # number of pixels per line
        self._samples_line = samples_line  # number of samples per line
        self._samples_period = samples_period  # number of samples per fast axis period
        self._samples_total = samples_total  # number of samples in total signal 
        # TODO: How to I get the following parameters into this function? Or read them from within _nidaqmanager? channels should definitely come from here I suppose...
        self._manager._nidaqManager.startInputTask(self._name, 'ci', channel=self._channel, acquisitionType='finite', source=r'ao/SampleClock', sampsInScan=self._samples_total, reference_trigger='PFI12')

    def run(self):
        lineCounter = 0
        lastValue = 0
        throw_startzero_length = 100  # TODO: return this value from the signaldesigner, or send with a signal here
        throw_settling_length = 100  # TODO: return this value from the signaldesigner, or send with a signal here
        throw_startacc_length = 100  # TODO: return this value from the signaldesigner, or send with a signal here
        throw_delay = 100  # TODO: calculate this value somehow, depending on the scanning parameters probably, which is the phase delay we will have from the scanning signal to when the scanner is actually in the correct place. How do we find this out? Depends on the response of the galvos, can we measure this somehow?
        throwdata = self._manager._nidaqManager.readInputTask(self._name, throw_startzero_length + throw_settling_length + throw_startacc_length + throw_delay)
        while lineCounter < self._n_lines:
            if self.scanning:
                data = self._manager._nidaqManager.readInputTask(self._name, self._samples_period)  # read a whole period, starting with the line and then the data during the flyback
                # galvo-sensor-data reading
                subtractionArray = np.concatenate(([lastValue],data[:-1]))
                lastValue = data[-1]
                data = data - subtractionArray  # Now apd_data is an array contains at each position the number of counts at this position
                line_samples = data[:self._samples_line]  # only take the first samples that corresponds to the samples during the line
                line_pixels = samples_to_pixels(line_samples)  # translate sample stream to an array where each value corresponds to a pixel count
                newLine.emit(line_pixels)
                lineCounter = lineCounter + 1
            else:
                self.close()

    # TODO: the following function to create a line of pixels with photon counts from the line datastream
    # Do it smarter than the previous way, instead downsample/resample/elementSummation somehow. If I read with a higher sample rate (20 MHz probably, 50 ns per sample should be fine)
    # I can just sum the same number of samples probably for each pixel, as the sample rate will be so much higher than the pixel dwell time (only allow dwell times as multiples of 0.05 us for example if the sampling rate is 20 MHz),
    # so any kind of discrepancy will not be necessary
    def samples_to_pixels(self, line_samples):
        ### FROM OLD
        #for index,value in enumerate(detector_signal):
        #    pixel_pos = np.trunc(stage_sensor_signal[index]/voltage_increment)
        #    if pixel_pos< number_of_pixels and pixel_pos>=0:
        #        image_line[pixel_pos]+=value
        #        number_of_samples_per_pixel[pixel_pos]+=1    
        #image_line/=number_of_samples_per_pixel  # here the total signal per pixel is divided by the number of samples for that pixel, as that can be uneven for the different pixels in the line. is this the correct way to go?
        ###
        line_pixels = np.zeros(self._pixels_line)
        samples_pixel = np.zeros(self._pixels_line)
        for idx, val in enumerate(line_samples):
            pixel = 0  #TODO
            if pixel < self._pixels_line and pixel >= 0
                line_pixels[pixel] += val
                samples_pixel += 1
            pass
        
        line_pixels = line_pixels / samples_pixel  # think about if this is really the way to go, maybe it is not needed... probably depends on the sampling rate
        return line_pixels

    def close(self):
        self.manager.nidaqManager.stopInputTask(self._name)
