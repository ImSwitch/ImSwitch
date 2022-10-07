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
        self.setPixelSize([1, 1])
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
        self._frameCount = 0
        self.__newFrameReady = False

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
            self._scanWorker.d2Step.connect(
                lambda pixels, pos: self.updateImage(pixels, pos)
            )
            self._scanWorker.acqDoneSignal.connect(self.stopAcquisition)

    def startScan(self):
        if self.acquisition:
            self._scanThread.start()

    def startAcquisition(self):
        self.acquisition = True
        self.__newFrameReady = False

    def stopAcquisition(self):
        try:
            self._scanWorker.scanning = False
            self._scanThread.quit()
            self._scanThread.wait()
            self._scanWorker.close()
            self.__currSlice[-1] += 1
            self.__newFrameReady = True
        except Exception:
            pass

    def getLatestFrame(self):
        return self._image

    def updateImage(self, pixels, pos: tuple):
        pass
        # pos: tuple with current pos for new pixels to be entered, from high dim to low dim (ending at d2)
        (*pos_rest, pos_d2) = (0,) + pos
        img_slice = tuple(pos_rest)+tuple([pos_d2,])
        #self.__logger.debug([pixels, pos, img_slice])
        self._image[img_slice] = pixels
        self.__currSlice = pos_rest  # from high dim to low dim (ending at d3)
        if pos_d2 == 0:
            # adjust viewbox shape to new image shape at the start of a d3 step
            self.updateLatestFrame(True)
            self.__newFrameReady = True

    def initiateImage(self, img_dims):
        img_dims_extra = (*img_dims,1)
        if np.shape(self._image) != tuple(reversed(img_dims_extra)):
            self._image = np.zeros(tuple(reversed(img_dims_extra)))
            self.setShape(img_dims_extra)  # not sure it will work. Previous order: [1],[0],[2], even if self._image was [2],[1],[0]

    def setParameter(self, name, value):
        pass

    def getParameter(self, name):
        pass

    def setBinning(self, binning):
        super().setBinning(binning)

    # TODO: potentially fix for d>3, currently returns last finished frame
    def getChunk(self):
        if self.__newFrameReady and self.__currSlice[-1] > 0:
            self.__newFrameReady = False
            pos_d3_fin = self.__currSlice[-1] - 1
            pos_rest = self.__currSlice[:-1]
            data = self.getLatestFrame()
            data = data[tuple(pos_rest)+tuple([pos_d3_fin,])]  # get the last finished d3 position from image ([...,:,:] ending in the indexing is not written, but all x,y taken)
            return data[np.newaxis,:,:]
        else:
            return np.empty(shape=(0,0,0))
            
    def flushBuffers(self):
        pass

    @property
    def shape(self):
        return self.__shape

    def setShape(self, img_dims):
        self.__shape = tuple(reversed(img_dims))  # previous order: [2],[0],[1] for d=3

    @property
    def scale(self):
        return list(reversed(self.__pixel_sizes))
        
    @property
    def pixelSizeUm(self):
        return [1, self.__pixel_sizes[-2], self.__pixel_sizes[-1]]  # TODO: is this not in the wrong order, considering setPixelSize below?

    def setPixelSize(self, pixel_sizes: list):
        # pixel_sizes: list of low dim to high dim
        #pixel_sizes.append(1)
        self.__pixel_sizes = pixel_sizes

    def crop(self, hpos, vpos, hsize, vsize):
        pass


class ScanWorker(Worker):
    d2Step = Signal(np.ndarray, tuple)
    acqDoneSignal = Signal()

    def __init__(self, manager, scanInfoDict):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

        self._alldata = 0
        self._last_value = 0
        self._manager = manager
        self._name = self._manager._name
        self._channel = self._manager._channel

        # TODO: calculate somehow, the phase delay from scanning signal to when the scanner is
        #       actually in the correct place. How do we find this out? Depends on the response of
        #       the galvos, can we measure this somehow?

        # time step of scanning, in s
        self._scan_dwell_time = scanInfoDict['dwell_time']

        # ratio between detection sampling time and pixel dwell time (has nothing to do with
        # sampling of scanning line)
        self._frac_det_dwell = round(self._scan_dwell_time * self._manager._detection_samplerate)

        # number of steps on each axis in image
        self._img_dims = scanInfoDict['img_dims']

        # # det samples per line:
        # time per line * det sampling rate
        self._samples_line = round(
            scanInfoDict['scan_samples'][1] * scanInfoDict['scan_time_step'] *
            self._manager._detection_samplerate
        )

        # det samples per fast axis period
        self._samples_d2_period = round(
            scanInfoDict['scan_samples_d2_period'] * scanInfoDict['scan_time_step'] *
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

        # scan samples in a d3 step (period)
        self._samples_d3_step = round(
            scanInfoDict['scan_samples'][2] * scanInfoDict['scan_time_step'] *
            self._manager._detection_samplerate
        )

        self._phase_delay = int(scanInfoDict['phase_delay'])

        self._samples_throw_init = self._throw_startzero
        
        # samples to throw due to smooth between d>2 step transitioning
        self._throw_init_d2_step = (self._throw_initpos + self._throw_settling + self._throw_startacc + self._phase_delay)

        #self.__logger.debug(f'samples line: {self._samples_line}')
        #self.__logger.debug(f'samples period: {self._samples_d2_step}')
        #self.__logger.debug(f'samples d3 step: {self._samples_d3_step}')
        #self.__logger.debug(f'init throw: {self._samples_throw_init}')
        #self.__logger.debug(f'init d>2 step throw: {self._throw_init_d2_step}')

        self._manager._nidaqManager.startInputTask(self._name, 'ci', self._channel, 'finite',
                                                   self._manager._nidaq_clock_source,
                                                   self._manager._detection_samplerate,
                                                   self._samples_total, True, 'ao/StartTrigger',
                                                   self._manager._terminal)
        self._manager.initiateImage(self._img_dims)
        self._manager.setPixelSize(scanInfoDict['pixel_sizes'])  # 'pixel_sizes' order: low dim to high dim

    def throwdata(self, datalen):
        """ Throw away data with length datalen, save the last value, 
        and add length of data to total alldata length.
        """
        if datalen > 0:
            throwdata = self._manager._nidaqManager.readInputTask(self._name, datalen)
            self._last_value = throwdata[-1]
            self._alldata += len(throwdata)

    def readdata(self, datalen):
        """ Read data with length datalen and add length of data to total alldata length.
        """
        data = self._manager._nidaqManager.readInputTask(self._name, datalen)
        self._alldata += len(data)
        return data

    def samples_to_pixels(self, line_samples):
        """ Reshape read datastream over the line to a line with pixel counts.
        Do this by summing elements, with the rate ratio calculated previously.
        """
        # If reading with higher sample rate (ex. 1 MHz, 1 us per sample) than scanning, sum N
        # samples for each pixel, since scanning curve is linear (ex. only allow dwell times as
        # multiples of 1 us if sampling rate is 1 MHz)
        line_pixels = np.array(line_samples).reshape(-1, self._frac_det_dwell).sum(axis=1)
        return line_pixels

    def run(self):
        """ Main run for acquisition.
        """
        # create empty current position counter
        self._pos = np.zeros(len(self._img_dims), dtype='uint8')
        # throw away initial recording samples
        self.throwdata(self._samples_throw_init)
        if len(self._img_dims) == 2:
            # begin d3 step: throw data from initial d3 step positioning
            self.throwdata(self._throw_init_d2_step)
        # start looping through all dimensions to record data, starting with the outermost dimension
        self.run_loop_dx(dim=len(self._img_dims))

        # throw acquisition-final positioning data
        self.throwdata(self._throw_startzero + self._throw_finalpos)
        self.acqDoneSignal.emit()

    def run_loop_dx(self, dim):
        """ Recursive looping through all scanning dimensions, actually read samples at dim = 2,
        and step through all steps in each dimension.
        """
        while self._pos[dim-1] < self._img_dims[dim-1]:
            if dim > 2:
                if dim == 3:
                    # begin d3 step: throw data from initial d3 step positioning
                    self.throwdata(self._throw_init_d2_step)
                self.run_loop_dx(dim-1)
                if dim == 3:
                    # end d3 step: realign actual N read samples with supposed N read samples, in case of discrepancy
                    throwdatalen_term1_terms = np.copy(self._pos[2:])
                    for n in range(len(self._img_dims),3,-1):
                        for m in range(n-1,2,-1):
                            throwdatalen_term1_terms[(n-2)-1] *= self._img_dims[m-1]
                    throwdatalen_term1_terms[0] += 1
                    throwdatalen = self._throw_startzero + self._samples_d3_step * np.sum(throwdatalen_term1_terms) - self._alldata
                    if throwdatalen > 0:
                        self.throwdata(throwdatalen)
            else:
                self.run_loop_d2()
            self._pos[dim-1] += 1
        self._pos[dim-1] = 0

    def run_loop_d2(self):
        """ Reading data on dim = 2, changing data to pixels, and emitting the d2 step of pixels.
        """
        if self.scanning:
            if self._pos[1] == self._img_dims[1] - 1:
                # read a line
                data = self.readdata(self._samples_line)
            else:
                # read a whole period, starting with the line and then the data during the flyback
                data = self.readdata(self._samples_d2_period)
            # get photon counts from data array (which is cumsummed)
            data_cnts = np.concatenate(([data[0]-self._last_value], np.diff(data)))
            self._last_value = data[-1]
            # only take the first samples that corresponds to the samples during the line
            line_samples = data_cnts[:self._samples_line]
            # resample sample array to pixel counts array
            pixels = self.samples_to_pixels(line_samples)
            # signal new line of pixels, and the insertion position in all dimensions
            self.d2Step.emit(pixels, tuple(np.flip(self._pos[1:])))
        else:
            self.__logger.debug('Close data reading: not scanning any longer')
            self.close()

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
