import numpy as np
from imswitch.imcommon.framework import Signal, Thread, Worker
from imswitch.imcommon.model import initLogger
from .DetectorManager import DetectorManager

class PMTanalogManager(DetectorManager):
    """ DetectorManager that deals with a photomultiplier tube connected to an
    analog input on a Nidaq card.

    Manager properties:

    - ``terminal`` -- the physical input terminal on the Nidaq to which the PMT
      is connected (e.g., AI0)
    """

    def __init__(self, detectorInfo, name, nidaqManager, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        model = name
        self._name = name
        self.setPixelSize([1, 1])
        fullShape = (100, 100)
        self._image = np.random.rand(fullShape[0], fullShape[1]) * 100
        self._ttlmultiplying = False

        # Here we specify the channel as AI0
        self._nidaq_clock_source = r'ctr2InternalOutput'  # Still needed for timing
        self._detection_samplerate = float(1e6)
        self.acquisition = True

        self._terminal = detectorInfo.managerProperties.get("terminal")
        
        self._scanWorker = None
        self._scanThread = None
        self._frameCount = 0
        self.__newFrameReady = False

        # Prepare parameters and signal connections
        parameters = {}
        self._nidaqManager = nidaqManager
        self._nidaqManager.sigScanBuilt.connect(
            lambda scanInfoDict, signalDict, _: self.initiateScan(scanInfoDict, signalDict)
        )
        self._nidaqManager.sigScanStarted.connect(self.startScan)
        self.__shape = fullShape
        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1],
                         model=model, parameters=parameters, croppable=False)

    def initiateScan(self, scanInfoDict, signalDict):
        if self.acquisition:
            self._scanWorker = ScanWorker(self, scanInfoDict, signalDict)
            self._scanThread = Thread()
            self._scanWorker.moveToThread(self._scanThread)
            self._scanThread.started.connect(self._scanWorker.run)
            self._scanWorker.scanning = True
            self._scanWorker.d2Step.connect(
                lambda pixels, pos: self.updateImage(pixels, pos)
            )
            self._scanWorker.acqDoneSignal.connect(self.stopAcquisitionLocal)
            self._scanWorker.newFrame.connect(lambda: self.sigNewFrame.emit())

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

    def stopAcquisitionLocal(self):
        try:
            self._scanWorker.scanning = False
            self._scanThread.quit()
            self._scanThread.wait()
            self._scanWorker.close()
            if self._ttlmultiplying:
                self._renewImage()
            self.__currSlice[-1] += 1
            self.__newFrameReady = True
        except Exception:
            pass

    def getLatestFrame(self, is_save=True):
        return self._image

    def _renewImage(self):
        im_squeezed, ax_rem = self.remove_nans(self._image)
        self.setShape(np.shape(im_squeezed))
        self._image = im_squeezed
        px_sizes = self.__pixel_sizes.copy()[::-1]
        for axis in ax_rem:
            px_sizes.pop(axis)
        self.setPixelSize(px_sizes[::-1])

    def updateImage(self, pixels, pos: tuple):
        pass
        # pos: tuple with current pos for new pixels to be entered, from high dim to low dim (ending at d2)
        (*pos_rest, pos_d2) = (0,) + pos
        img_slice = tuple(pos_rest)+tuple([pos_d2,])
        self._image[img_slice] = pixels
        self.__currSlice = pos_rest  # from high dim to low dim (ending at d3)
        if pos_d2 == 0:
            self.updateLatestFrame(True)
            self.__newFrameReady = True

    def initiateImage(self, img_dims):
        img_dims_extra = tuple(reversed((*img_dims,1)))
        if np.shape(self._image) != img_dims_extra:
            self._image = np.zeros(img_dims_extra)
            self.setShape(img_dims_extra)

    def setParameter(self, name, value):
        pass

    def getParameter(self, name):
        pass

    def setBinning(self, binning):
        super().setBinning(binning)

    def getChunk(self):
        if self.__newFrameReady and self.__currSlice[-1] > 0:
            self.__newFrameReady = False
            pos_d3_fin = self.__currSlice[-1] - 1
            pos_rest = self.__currSlice[:-1]
            data = self.getLatestFrame()
            data = data[tuple(pos_rest)+tuple([pos_d3_fin,])]
            return data[np.newaxis,:,:]
        else:
            return np.empty(shape=(0,0,0))
            
    def flushBuffers(self):
        pass

    @property
    def shape(self):
        return self.__shape

    def setShape(self, img_dims):
        self.__shape = tuple(img_dims)

    @property
    def scale(self):
        return self.__pixel_sizes[::-1]
        
    @property
    def pixelSizeUm(self):
        return [1, self.__pixel_sizes[-2], self.__pixel_sizes[-1]]

    def setPixelSize(self, pixel_sizes: list):
        self.__pixel_sizes = pixel_sizes

    def crop(self, hpos, vpos, hsize, vsize):
        pass

    def remove_nans(self, im):
        acc = np.maximum.accumulate
        m = ~np.isnan(im)
        dims = im.ndim

        if dims==1:
            return im[acc(m) & acc(m[::-1])[::-1]]    
        else:
            r = np.tile(np.arange(dims),dims)
            per_axis_combs = np.delete(r,range(0,len(r),dims+1)).reshape(-1,dims-1)
            per_axis_combs_tuple = map(tuple,per_axis_combs)

            mask = []
            for i in per_axis_combs_tuple:            
                m0 = m.any(i)            
                mask.append(acc(m0) & acc(m0[::-1])[::-1])
            im_new = im[np.ix_(*mask)]
            ax_rem = [i for i in range(dims) if im_new.shape[i]!=im.shape[i]]
            return im_new, ax_rem

class ScanWorker(Worker):
    d2Step = Signal(np.ndarray, tuple)
    newLine = Signal(np.ndarray, int, int)
    newFrame = Signal()
    acqDoneSignal = Signal()

    def __init__(self, manager, scanInfoDict, signalDict):
        super().__init__()  # Make sure the parent class is properly initialized
        self.__logger = initLogger(self, tryInheritParent=True)

        self._samples_read = 0
        self._last_value = 0
        self._manager = manager
        self._name = self._manager._name
        self._channel = self._manager._terminal

        # time step of scanning, in seconds
        self._scan_dwell_time = scanInfoDict['dwell_time']

        # Ratio between detection sampling time and pixel dwell time
        self._frac_det_dwell = round(self._scan_dwell_time * self._manager._detection_samplerate)

        # Ratio between detection sample rate and scanning sample rate
        self._frac_scan_det_rate = round(self._manager._detection_samplerate * scanInfoDict['scan_time_step'])

        # Number of steps on each axis in image
        self._img_dims = scanInfoDict['img_dims']

        # det samples per line:
        self._samples_line = round(scanInfoDict['scan_samples'][1] * self._frac_scan_det_rate)
        # det samples per fast axis period
        self._samples_d2_period = round(scanInfoDict['scan_samples_d2_period'] * self._frac_scan_det_rate)
        # det samples in total signal
        self._samples_total = round(scanInfoDict['scan_samples_total'] * self._frac_scan_det_rate)
        # Other parameters for throwaway samples (like initial positioning)
        self._throw_startzero = round(scanInfoDict['scan_throw_startzero'] * self._frac_scan_det_rate)
        self._throw_initpos = round(scanInfoDict['scan_throw_initpos'] * self._frac_scan_det_rate)
        self._throw_settling = round(scanInfoDict['scan_throw_settling'] * self._frac_scan_det_rate)
        self._throw_startacc = round(scanInfoDict['scan_throw_startacc'] * self._frac_scan_det_rate)
        self._throw_finalpos = round(scanInfoDict['scan_throw_finalpos'] * self._frac_scan_det_rate)
        # Scan samples in a d3 step (period)
        self._samples_d3_step = round(scanInfoDict['scan_samples'][2] * self._frac_scan_det_rate)
        # Scan samples for zero padding at end of scanning curve dimensions
        self._samples_padlens = [round(scanInfoDict['padlens'][i] * self._frac_scan_det_rate) for i in range(len(scanInfoDict['padlens']))]

        self._phase_delay = int(scanInfoDict['phase_delay'])
        self._samples_throw_init = self._throw_startzero

        # Additional setup for managing analog input instead of digital counts
        self._manager._nidaqManager.startInputTask(self._name, 'ai', "Dev1/ai0", 'finite',
                                                   self._manager._nidaq_clock_source,
                                                   self._manager._detection_samplerate,
                                                   self._samples_total, True, 'ao/StartTrigger',
                                                   self._manager._terminal)
        self._manager.initiateImage(self._img_dims)
        self._manager.setPixelSize(scanInfoDict['pixel_sizes'])  # 'pixel_sizes' order: low dim to high dim

    def throwdata(self, datalen):
        """ Throw away data with length datalen, save the last value, 
        and add length of data to total samples_read length.
        """
        if datalen > 0:
            throwdata = self._manager._nidaqManager.readInputTask(self._name, datalen)
            self.__plot_curves(plot=False, xvals=range(int((self._samples_read)/10), int((self._samples_read+datalen)/10)), signal=self._ploty*np.ones(int((datalen)/10)))
            self._last_value = throwdata[-1]
            self._samples_read += datalen

    def readdata(self, datalen):
        """ Read data with length datalen and add length of data to total samples_read length.
        """
        data = self._manager._nidaqManager.readInputTask(self._name, datalen)
        self.__plot_curves(plot=False, xvals=range(int((self._samples_read)/10), int((self._samples_read+datalen)/10)), signal=self._ploty*np.ones(int((datalen)/10)))
        self._samples_read += datalen
        return data

    def samples_to_pixels(self, line_samples):
        """ Reshape read datastream over the line to a line with pixel counts.
        """
        line_pixels = np.array(line_samples).reshape(-1, self._frac_det_dwell).mean(axis=1)
        return line_pixels

    def __plot_curves(self, plot, xvals, signal):
        """ Plot detection curves, for debugging. """
        if plot:
            import matplotlib.pyplot as plt
            plt.figure(1)
            plt.plot(xvals, signal)
            self._ploty += 0.01
            if self._ploty > 1.1:
                self._ploty = 1

    def run(self):
        """ Main run for acquisition.
        """
        self._ploty = 1
        # create empty current position counter
        self._pos = np.zeros(len(self._img_dims), dtype='uint16')
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
                    for n in range(len(self._img_dims), 3, -1):
                        for m in range(n-1, 2, -1):
                            throwdatalen_term1_terms[(n-2)-1] *= self._img_dims[m-1]
                    throwdatalen_term1_terms[0] += 1
                    throwdatalen_highdsteps = sum([self._samples_padlens[dim] * self._pos[dim] for dim in range(3, len(self._img_dims))])
                    throwdatalen = self._throw_startzero + self._samples_d3_step * np.sum(throwdatalen_term1_terms) + throwdatalen_highdsteps - self._samples_read
                    if throwdatalen > 0:
                        self.throwdata(throwdatalen)
                if dim > 3:
                    self.throwdata(self._samples_padlens[dim-1])                  
            else:
                self.run_loop_d2()
            self._pos[dim-1] += 1
        self._pos[dim-1] = 0

    def run_loop_d2(self):
        """ Reading data on dim = 2, converting data to pixels, and emitting the d2 step of pixels.
        """
        if self.scanning:
            if self._pos[1] == self._img_dims[1] - 1:
                # read a line
                data = self.readdata(self._samples_line)
            else:
                # read a whole period, starting with the line and then the data during the flyback
                data = self.readdata(self._samples_d2_period)
            # Process the data for photon counts (or analog signals in this case)
            line_samples = data[:self._samples_line]
            pixels = self.samples_to_pixels(line_samples)
            # Signal new line of pixels, and the insertion position in all dimensions
            self.d2Step.emit(pixels, tuple(np.flip(self._pos[1:])))
        else:
            self.__logger.debug('Close data reading: not scanning any longer')
            self.close()

    def close(self):
        self._manager._nidaqManager.inputTaskDone(self._name)
