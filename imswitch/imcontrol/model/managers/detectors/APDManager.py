import numpy as np

from imswitch.imcommon.framework import Signal, Thread, Worker
from imswitch.imcommon.model import initLogger
from .DetectorManager import DetectorManager


class APDManager(DetectorManager):
    """ DetectorManager that deals with an avalanche photodiode connected to a
    counter input on a Nidaq card.

    Manager properties:

    - ``terminal`` -- the physical input terminal on the Nidaq to which the APD
      is connected
    - ``ctrInputLine`` -- the counter that the physical input terminal is
      connected to
    """

    def __init__(self, detectorInfo, name, nidaqManager, **_lowLevelManagers):
        # TODO: use the same manager for the PMT, with the type of detector as an argument.
        #       NidaqPointDetectorManager
        self.__logger = initLogger(self, instanceName=name)

        model = name
        self._name = name
        self.setPixelSize(1, 1)
        fullShape = (100, 100)
        self._image = np.random.rand(fullShape[0], fullShape[1]) * 100

        # counter output task generating a 1 MHz frequency digitial pulse train
        self._nidaq_clock_source = r'ctr2InternalOutput'

        self._detection_samplerate = float(1e6)
        self.acquisition = True

        self._channel = detectorInfo.managerProperties["ctrInputLine"]
        if isinstance(self._channel, int):
            self._channel = f'Dev1/ctr{self._channel}'  # for backwards compatibility

        self._terminal = detectorInfo.managerProperties["terminal"]

        self._scanWorker = None
        self._scanThread = None

        # Prepare parameters and signal connections
        parameters = {}
        self._nidaqManager = nidaqManager
        self._nidaqManager.sigScanBuilt.connect(
            lambda scanInfoDict: self.initiateScan(scanInfoDict)
        )
        self.__logger.debug('sigScanInitiate is connected')
        self._nidaqManager.sigScanStarted.connect(self.startScan)
        self.__shape = fullShape
        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1],
                         model=model, parameters=parameters, croppable=False)

    def __del__(self):
        if self._scanThread is not None:
            self._scanThread.quit()
            self._scanThread.wait()
        if hasattr(super(), '__del__'):
            super().__del__()

    def initiateScan(self, scanInfoDict):
        if self.acquisition:
            self._scanWorker = ScanWorker(self, scanInfoDict)
            self._scanThread = Thread()
            self._scanWorker.moveToThread(self._scanThread)
            self._scanThread.started.connect(self._scanWorker.run)
            self._scanWorker.scanning = True
            self._scanWorker.newLine.connect(
                lambda line_pixels, line_count, frame: self.updateImage(line_pixels, line_count, frame)
            )
            self._scanWorker.acqDoneSignal.connect(self.stopAcquisition)

    def startScan(self):
        if self.acquisition:
            self._scanThread.start()

    def startAcquisition(self):
        self.acquisition = True

    def stopAcquisition(self):
        try:
            self._scanWorker.scanning = False
            self._scanThread.quit()
            self._scanThread.wait()
            self._scanWorker.close()
        except Exception:
            pass

    def getLatestFrame(self):
        # image = self._image
        # image.reshape(image.shape[1], image.shape[0]).T
        # return image
        return self._image

    def updateImage(self, line_pixels, line_count, frame):
        self._image[frame, -(line_count + 1), :] = line_pixels[::-1]
        if line_count == 0:
            # adjust viewbox shape to new image shape at the start of the image
            self.updateLatestFrame(True)

    def initiateImage(self, lines, pixels_line, frames=1):
        if np.shape(self._image) != (frames, lines, pixels_line):
            self._image = np.zeros((frames, lines, pixels_line))
            self.setShape(lines, pixels_line, frames)

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

    def setShape(self, ysize, xsize, framesize=1):
        self.__shape = (framesize, xsize, ysize)

    @property
    def pixelSizeUm(self):
        return [1, self.__pixelsize_ax2, self.__pixelsize_ax1]

    def setPixelSize(self, pixelsize_ax1, pixelsize_ax2, pixelsize_ax3=1):
        self.__pixelsize_ax1 = pixelsize_ax1
        self.__pixelsize_ax2 = pixelsize_ax2
        self.__pixelsize_ax3 = pixelsize_ax3

    def crop(self, hpos, vpos, hsize, vsize):
        pass


class ScanWorker(Worker):
    newLine = Signal(np.ndarray, int, int)
    acqDoneSignal = Signal()

    def __init__(self, manager, scanInfoDict):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

        self._alldata = 0
        self._manager = manager
        self._name = self._manager._name
        self._channel = self._manager._channel

        # TODO: calculate somehow, the phase delay from scanning signal to when the scanner is
        #       actually in the correct place. How do we find this out? Depends on the response of
        #       the galvos, can we measure this somehow?
        # self._throw_delay = int(13*20e6/100e3)
        # self._throw_delay = 15200
        self._throw_delay = 50  # should be larger the smaller the faster the scanning/smaller the FOV?

        self._scan_dwell_time = scanInfoDict['dwell_time']  # time step of scanning, in s

        # ratio between detection sampling time and pixel dwell time (has nothing to do with
        # sampling of scanning line)
        self._frac_det_dwell = round(self._scan_dwell_time * self._manager._detection_samplerate)

        self._n_lines = round(scanInfoDict['n_lines'])  # number of lines in image
        self._pixels_line = round(scanInfoDict['pixels_line'])  # number of pixels per line
        if len(scanInfoDict['img_dims']) == 3:
            self._n_frames = round(scanInfoDict['img_dims'][2])  # number of pixels per line
        else:
            self._n_frames = 1

        # # det samples per line:
        # time per line * det sampling rate
        self._samples_line = round(
            scanInfoDict['scan_samples_line'] * scanInfoDict['scan_time_step'] *
            self._manager._detection_samplerate
        )

        # det samples per fast axis period
        self._samples_period = round(
            scanInfoDict['scan_samples_period'] * scanInfoDict['scan_time_step'] *
            self._manager._detection_samplerate
        )

        # det samples in total signal
        self._samples_total = round(
            scanInfoDict['scan_samples_total'] * scanInfoDict['scan_time_step'] *
            self._manager._detection_samplerate
        )

        # samples to throw due to the starting zero-padding
        self._throw_startzero = round(
            scanInfoDict['scan_throw_startzero'] * scanInfoDict['scan_time_step'] *
            self._manager._detection_samplerate
        )

        # samples to throw due to smooth inital positioning time
        self._throw_initpos = round(
            scanInfoDict['scan_throw_initpos'] * scanInfoDict['scan_time_step'] *
            self._manager._detection_samplerate
        )

        # samples to throw due to settling time
        self._throw_settling = round(
            scanInfoDict['scan_throw_settling'] * scanInfoDict['scan_time_step'] *
            self._manager._detection_samplerate
        )

        # samples to throw due to starting acceleration
        self._throw_startacc = round(
            scanInfoDict['scan_throw_startacc'] * scanInfoDict['scan_time_step'] *
            self._manager._detection_samplerate
        )

        # samples to throw due to smooth final positioning time
        self._throw_finalpos = round(
            scanInfoDict['scan_throw_finalpos'] * scanInfoDict['scan_time_step'] *
            self._manager._detection_samplerate
        )

        # scan samples in a frame (period)
        self._samples_frame = round(
            scanInfoDict['scan_samples_frame'] * scanInfoDict['scan_time_step'] *
            self._manager._detection_samplerate
        )

        self._samples_throw_init = self._throw_startzero
        
        # samples to throw due to smooth between frames transitioning
        self._throw_init_frame = (self._throw_initpos + self._throw_settling + self._throw_startacc + self._throw_delay)

        #self.__logger.debug(f'samples line: {self._samples_line}')
        #self.__logger.debug(f'samples period: {self._samples_period}')
        #self.__logger.debug(f'samples frame: {self._samples_frame}')
        #self.__logger.debug(f'init throw: {self._samples_throw_init}')
        #self.__logger.debug(f'init frame throw: {self._throw_init_frame}')

        self._manager._nidaqManager.startInputTask(self._name, 'ci', self._channel, 'finite',
                                                   self._manager._nidaq_clock_source,
                                                   self._manager._detection_samplerate,
                                                   self._samples_total, True, 'ao/StartTrigger',
                                                   self._manager._terminal)
        self._manager.initiateImage(self._n_lines, self._pixels_line, self._n_frames)
        
        if len(scanInfoDict['img_dims']) == 3:
            self._manager.setPixelSize(float(scanInfoDict['pixel_size_ax1']),
                                       float(scanInfoDict['pixel_size_ax2']),
                                       float(scanInfoDict['pixel_size_ax3']))
        else:
            self._manager.setPixelSize(float(scanInfoDict['pixel_size_ax1']),
                                       float(scanInfoDict['pixel_size_ax2']))

        self._last_value = 0
        self._line_counter = 0

    def run(self):
        #self.__logger.debug('scanWorker.run initiated')
        #self.__logger.debug(f'Samples to throw init: {self._samples_throw_init}')
        throwdata = self._manager._nidaqManager.readInputTask(self._name, self._samples_throw_init)
        #self.__logger.debug(f'sw0: throw data shape: {np.shape(throwdata)}')
        self._last_value = throwdata[-1]
        self._alldata += len(throwdata)
        for i in range(self._n_frames):
            #self.__logger.debug(f'Currently data for frame {i+1} out of {self._n_frames}')
            throwdata = self._manager._nidaqManager.readInputTask(self._name, self._throw_init_frame)
            self._last_value = throwdata[-1]
            self._alldata += len(throwdata)
            while self._line_counter < self._n_lines:
                if self.scanning:
                    #self.__logger.debug(f'sw1: line {self._line_counter} started')
                    if self._line_counter == self._n_lines - 1:
                        # read a line
                        data = self._manager._nidaqManager.readInputTask(self._name,
                                                                        self._samples_line)
                    else:
                        # read a whole period, starting with the line and then the data during the
                        # flyback
                        data = self._manager._nidaqManager.readInputTask(self._name,
                                                                        self._samples_period)
                    self._alldata += len(data)
                    # galvo-sensor-data reading
                    subtractionArray = np.concatenate(([self._last_value], data[:-1]))
                    self._last_value = data[-1]

                    # Now data is an array containing at each position the number of counts
                    # at this position
                    data = data - subtractionArray

                    # only take the first samples that corresponds to the samples during the line
                    line_samples = data[:self._samples_line]

                    # translate sample stream to an array where each value corresponds to a pixel count
                    line_pixels = self.samples_to_pixels(line_samples)

                    self.newLine.emit(line_pixels, self._line_counter, i)
                    self._line_counter += 1
                else:
                    self.__logger.debug('Close data reading: not scanning any longer')
                    self.close()
            #throwdata = self._manager._nidaqManager.readInputTask(
            #    self._name, self._throw_between_frames
            #)
            throwdatalen = self._throw_startzero + self._samples_frame * (i+1) - self._alldata
            throwdata = self._manager._nidaqManager.readInputTask(
                self._name, throwdatalen
            )
            self._alldata += len(throwdata)
            self._line_counter = 0
            #self.__logger.debug(f'length of all data after frame {i+1}: {self._alldata}')

        throwdata = self._manager._nidaqManager.readInputTask(
            self._name, self._throw_startzero + self._throw_finalpos
        )
        self._alldata += len(throwdata)
        #self.__logger.debug(f'length of all data, end: {self._alldata}')
        self.acqDoneSignal.emit()
        # self.__logger.debug(self._name)
        # self.close()

    def samples_to_pixels(self, line_samples):
        """ Reshape read datastream over the line to a line with pixel counts.
        Do this by summing elements, with the rate ratio calculated previously. """
        # If reading with higher sample rate (ex. 1 MHz, 1 us per sample) than scanning, sum N
        # samples for each pixel, since scanning curve is linear (ex. only allow dwell times as
        # multiples of 1 us if sampling rate is 1 MHz)
        line_pixels = np.array(line_samples).reshape(-1, self._frac_det_dwell).sum(axis=1)
        return line_pixels

    def close(self):
        self._manager._nidaqManager.inputTaskDone(self._name)


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
