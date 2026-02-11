import numpy as np
import matplotlib.pyplot as plt

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

        self.__logger = initLogger(self, instanceName=name)

        model = name
        self._name = name
        self.setPixelSize([1, 1])
        fullShape = (100, 100)
        self._image = np.random.rand(fullShape[0], fullShape[1]) * 100
        self._detection_samplerate = float(1e6)
        self._nidaq_clock_source = r'ctr2InternalOutput'  # counter output task generating a 1 MHz frequency digitial pulse train
        self._channel = detectorInfo.managerProperties["ctrInputLine"]
        if isinstance(self._channel, int):
            self._channel = f'Dev1/ctr{self._channel}'  # for backwards compatibility
        self._terminal = detectorInfo.managerProperties["terminal"]

        self._frameCount = 0
        self._scanWorker = None
        self._scanThread = None
        self.__newFrameReady = False
        self._ttlmultiplying = False
        self.acquisition = True
        self._debug_mode = False  # run mode for plotting detected samples
        self._simulation_mode = False  # run mode for generating detected samples

        # Prepare detector manager parameters and signal connections
        parameters = {}
        self._nidaqManager = nidaqManager
        self._nidaqManager.sigScanBuilt.connect(
            lambda scanInfoDict, signalDict, _: self.initiateScan(scanInfoDict, signalDict)
        )
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
            self._scanWorker.d3Step.connect(self._onFrameBoundary)
            if self._debug_mode:
                plt.figure(1)
            self._linestep = getattr(self._scanWorker, "_linestep", 1)

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
        if self._debug_mode:
            plt.show()

    def getLatestFrame(self, is_save=True):
        S = int(getattr(self, "_linestep", 1))
        if is_save and S > 1:
            return self._image  # raw stack (1,S,Ny,Nx)
        return self._image_display  # always (1,Ny,Nx)

    def _renewImage(self):
        im_squeezed, ax_rem = self.remove_nans(self._image)
        self.setShape(np.shape(im_squeezed))
        self._image = im_squeezed
        px_sizes = self.__pixel_sizes.copy()[::-1]
        for axis in ax_rem:
            px_sizes.pop(axis)
        self.setPixelSize(px_sizes[::-1])

    def updateImage(self, pixels, pos: tuple):
        """
        pos is emitted as tuple(np.flip(self._pos[1:])) from ScanWorker.
        For XY:           pos == (y,)
        For Z stacks:     pos == (z, y)
        For higher dims:  pos == (..., z, y)  (last element is always y_expanded)
        """
        if not hasattr(self, "_linestep"):
            self._linestep = 1
        S = int(self._linestep)

        # last entry is the (expanded) line index along Y
        y_expanded = int(pos[-1])

        # clip pixel write length to Nx
        Nx = self._image.shape[-1] if self._image.size else len(pixels)
        n = min(len(pixels), Nx)

        if S > 1:
            # raw buffer for 2D+linestep is typically: (1, S, Ny, Nx)
            y = y_expanded // S
            s = y_expanded % S
            Ny = self._image[0].shape[-2]
            if y >= Ny:
                return
            self._image[0, s, y, :n] = pixels[:n]
            self.__currSlice = (s, y)
            return

        # ---- S == 1: could be 2D (1, Ny, Nx) OR 3D (1, Nz, Ny, Nx) (or higher) ----
        if self._image.ndim == 3:
            # (1, Ny, Nx)
            Ny = self._image.shape[-2]
            if y_expanded >= Ny:
                return
            self._image[0, y_expanded, :n] = pixels[:n]
            self.__currSlice = (y_expanded,)
            return

        if self._image.ndim >= 4:
            # (1, Nz, Ny, Nx) for Z stacks (and potentially more dims in front of Ny,Nx)
            # pos[:-1] contains all outer indices (e.g. z), last is y
            outer = tuple(int(v) for v in pos[:-1])  # e.g. (z,) or (t,z,...) depending on scan
            # Build index into raw buffer:
            # raw layout is (1, ...outer..., y, x)
            # where y is always the second-to-last axis
            y = y_expanded
            Ny = self._image.shape[-2]
            if y >= Ny:
                return

            idx = (0,) + outer + (y, slice(0, n))
            self._image[idx] = pixels[:n]
            self.__currSlice = outer + (y,)
            return

    def initiateImage(self, img_dims):
        """
        img_dims comes from ScanWorker._output_image_dims:
          - 2D, S==1: (Nx, Ny)
          - 2D, S>1 : (Nx, Ny, S)
          - 3D Z    : (Nx, Ny, Nz)   (S==1)
          - 3D Z + S: (Nx, Ny, Nz, S)
        Raw buffer is allocated as reversed + leading 1.
        Display buffer is always (1, Ny, Nx).
        """
        img_dims = tuple(int(x) for x in img_dims)

        # Use current linestep to interpret the last dimension
        S = int(getattr(self, "_linestep", 1))
        S = max(1, S)

        img_dims_extra = tuple(reversed((*img_dims, 1)))
        if np.shape(self._image) != img_dims_extra:
            self._image = np.zeros(img_dims_extra)
            self.setShape(img_dims_extra)

        # Always allocate display as 3D (1, Nz, Ny, Nx)
        Nx = int(img_dims[0]) if len(img_dims) >= 1 else 1
        Ny = int(img_dims[1]) if len(img_dims) >= 2 else 1
        Nz = int(img_dims[2]) if len(img_dims) >= 3 else 1
        self._image_display = np.zeros((1, Nz, Ny, Nx))

    def setParameter(self, name, value):
        pass

    def getParameter(self, name):
        pass

    def setBinning(self, binning):
        super().setBinning(binning)

    def getChunk(self):
        if not self.__newFrameReady:
            return np.empty((0, 0, 0))
        self.__newFrameReady = False
        return self._image_display.copy()  # already shape (1,Ny,Nx)

    def flushBuffers(self):
        pass

    def _onFrameBoundary(self):
        """
        Called by ScanWorker.d3Step at the end of a full frame.
        Updates display buffer and triggers GUI redraw once per frame.

        Works for:
          - 2D acquisition: _image is (1, Y, X) or (Y, X)
          - 3D acquisition: _image is (Z, Y, X) or (1, Z, Y, X) depending on your pipeline
        """
        if self._image_display.size == 0:
            return

        S = int(getattr(self, "_linestep", 1))

        if S > 1:
            # Your existing logic: compute the “combined” display frame across linesteps
            frame2d = self._compute_display_frame()
        else:
            im = np.asarray(self._image)

            # raw buffer layout from initiateImage is reversed + leading 1
            # Common cases:
            # 2D: (1, Ny, Nx)
            # 3D: (1, Nz, Ny, Nx)
            if im.ndim == 3:
                # (1, Ny, Nx)
                frame2d = im[0]
            elif im.ndim == 4:
                # (1, Nz, Ny, Nx) -> max project over Z
                frame2d = im[0]  # axis 0 is Z here
            else:
                # fallback: take last two dims
                frame2d = im.reshape((-1,) + im.shape[-2:])[-1]

        # Write into display buffer (expected shape: (1, Y, X))
        self._image_display[0] = frame2d

        self.updateLatestFrame(True)
        self.__newFrameReady = True
        self.sigNewFrame.emit()

    def _compute_display_frame(self):
        S = int(getattr(self, "_linestep", 1))
        if S <= 1:
            return self._image[0]
        raw = self._image[0]  # (S,Ny,Nx)
        mode = getattr(self, "_linestep_view_mode", "sum")
        if mode == "max":
            return np.nanmax(raw, axis=0)
        if mode == "slice":
            idx = int(getattr(self, "_linestep_view_index", 0)) % raw.shape[0]
            return raw[idx]
        return np.nansum(raw, axis=0)

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
        return [1, *self.__pixel_sizes]

    def setPixelSize(self, pixel_sizes: list):
        # pixel_sizes: list of low dim to high dim
        self.__pixel_sizes = pixel_sizes

    def crop(self, hpos, vpos, hsize, vsize):
        pass

    def remove_nans(self, im):
        """ Remove slices which only contain np.nan values, called at end of acquisition.
        Source: https://stackoverflow.com/a/43724800 """
        acc = np.maximum.accumulate
        m = ~np.isnan(im)
        dims = im.ndim

        if dims == 1:
            return im[acc(m) & acc(m[::-1])[::-1]]
        else:
            r = np.tile(np.arange(dims), dims)
            per_axis_combs = np.delete(r, range(0, len(r), dims + 1)).reshape(-1, dims - 1)
            per_axis_combs_tuple = map(tuple, per_axis_combs)

            mask = []
            for i in per_axis_combs_tuple:
                m0 = m.any(i)
                mask.append(acc(m0) & acc(m0[::-1])[::-1])
            im_ret = im[np.ix_(*mask)]
            ax_rem = [i for i, val in enumerate(np.shape(im_ret)[1:]) if val == 1]
            return np.expand_dims(np.squeeze(im_ret), axis=0).astype(int), ax_rem


class ScanWorker(Worker):
    d2Step = Signal(np.ndarray, tuple)
    d3Step = Signal()
    acqDoneSignal = Signal()

    def __init__(self, manager, scanInfoDict, signalDict):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

        self._samples_read = 0
        self._last_value = 0
        self._manager = manager
        self._name = self._manager._name
        self._channel = self._manager._channel

        # time step of scanning, in s
        self._scan_dwell_time = scanInfoDict['dwell_time']

        # ratio between detection sampling time and pixel dwell time (has nothing to do with
        # sampling of scanning line)
        self._frac_det_dwell = round(self._scan_dwell_time * self._manager._detection_samplerate)

        # ratio between detection sample rate and scanning sample rate
        self._frac_scan_det_rate = round(self._manager._detection_samplerate * scanInfoDict['scan_time_step'])

        # extract APD signals from signalDict
        if self._manager._ttlmultiplying:
            for target in signalDict['TTLCycleSignalsDict'].keys():
                if self._name == target:
                    self._seq_signal = np.repeat(signalDict['TTLCycleSignalsDict'][target].copy(),
                                                 self._frac_scan_det_rate)
                    self._seq_signal = self._seq_signal.astype('float')
                    self._seq_signal[self._seq_signal == 0] = np.nan
                    break

        # number of steps on each axis in image
        img_dims_in = list(scanInfoDict["img_dims"])
        axes = list(scanInfoDict.get("img_axes_with_linesteps", []))  # preferred

        # Fallback if axes not provided (older designers): assume linestep is last dim iff n_linesteps>1 and len matches
        if not axes:
            axes = list(scanInfoDict.get("img_axes_phys", []))
            n_ls = int(scanInfoDict.get("n_linesteps", 1))
            if n_ls > 1:
                axes = axes + ["linestep"]

        # Determine linestep size + index
        linestep_idx = axes.index("linestep") if "linestep" in axes else None
        if linestep_idx is not None:
            self._linestep = int(img_dims_in[linestep_idx])
        else:
            self._linestep = int(scanInfoDict.get("n_linesteps", 1))
        self._linestep = max(1, self._linestep)

        # Build "scan recursion dims" (NO linestep axis here!)
        if linestep_idx is not None:
            scan_dims = [d for i, d in enumerate(img_dims_in) if i != linestep_idx]
            scan_axes = [a for i, a in enumerate(axes) if i != linestep_idx]
        else:
            scan_dims = img_dims_in
            scan_axes = axes

        # We assume X/Y are present and Y is the slow scan axis
        # (This matches your designer contract: img_axes_phys starts as ["x","y","z"...])
        y_idx = scan_axes.index("y") if "y" in scan_axes else 1

        # Loop dims: expand Y by linestep (Ny -> Ny*S), keep other dims unchanged
        self._img_dims = scan_dims  # recursion uses physical scan axes only (x,y,z,...)
        self._loop_dims = scan_dims.copy()
        self._loop_dims[y_idx] = int(self._loop_dims[y_idx] * self._linestep)

        # Output dims for manager allocation: keep linestep as its own axis (for later stack/sum/max)
        # We append linestep as the LAST axis in output_image_dims (manager can reorder if desired)
        self._output_image_dims = tuple(scan_dims + ([self._linestep] if self._linestep > 1 else []))

        # det samples per scan steps in different dims
        self._samples_d_scanstep = [round(samples) * self._frac_scan_det_rate for samples in
                                    scanInfoDict['scan_samples']]
        # det samples per fast axis period
        self._samples_d2_period = round(scanInfoDict['scan_samples_d2_period'] * self._frac_scan_det_rate)
        # det samples in total signal
        self._samples_total = round(scanInfoDict['scan_samples_total'] * self._frac_scan_det_rate)
        # samples to throw due to:
        self._throw_startzero = round(
            scanInfoDict['scan_throw_startzero'] * self._frac_scan_det_rate)  # starting zero-padding
        self._scan_pads_initpos = [round(initpos) * self._frac_scan_det_rate for initpos in
                                   scanInfoDict['scan_pads_initpos']]  # smooth inital positioning times
        self._throw_settling = round(scanInfoDict['scan_throw_settling'] * self._frac_scan_det_rate)  # settling time
        self._throw_startacc = round(
            scanInfoDict['scan_throw_startacc'] * self._frac_scan_det_rate)  # starting acceleration

        self._phase_delay = int(scanInfoDict['phase_delay'])  # phase delay samples - galvo response time
        self._smooth_axes = scanInfoDict['smooth_axes']

        # samples to throw due to smooth between d>2 step transitioning
        pad_initpos = self._scan_pads_initpos[0] if len(self._scan_pads_initpos) > 0 else 0
        self._throw_init_smooth = (pad_initpos + self._throw_settling + self._throw_startacc)
        # initiate parameter for thrown samples for smooth higher dimensions step init
        self._throw_init_higher_d = False

        if not self._manager._simulation_mode:
            self._manager._nidaqManager.startInputTask(self._name, 'ci', self._channel, 'finite',
                                                       self._manager._nidaq_clock_source,
                                                       self._manager._detection_samplerate,
                                                       self._samples_total, True, 'ao/StartTrigger',
                                                       self._manager._terminal)
        self._manager.initiateImage(self._output_image_dims)
        self._manager.setPixelSize(scanInfoDict['pixel_sizes'])  # 'pixel_sizes' order: low dim to high dim

    def throwdata(self, datalen):
        """ Throw away data with length datalen, save the last value,
        and add length of data to total samples_read length.
        """
        if datalen > 0:
            if self._manager._simulation_mode:
                throwdata = self.randomInput(datalen)
            else:
                throwdata = self._manager._nidaqManager.readInputTask(self._name, datalen)
            if self._manager._debug_mode:
                self.__plot_curves(plot=True, xvals=range(int((self._samples_read) / 10),
                                                          int((self._samples_read + datalen) / 10)),
                                   signal=self._ploty * np.ones(int((datalen) / 10)),
                                   style='r-')
            self._last_value = throwdata[-1]
            self._samples_read += datalen

    def readdata(self, datalen):
        """ Read data with length datalen and add length of data to total samples_read length.
        """
        if self._manager._simulation_mode:
            data = self.randomInput(datalen)
        else:
            data = self._manager._nidaqManager.readInputTask(self._name, datalen)
        if self._manager._debug_mode:
            self.__plot_curves(plot=True, xvals=range(int((self._samples_read) / 10),
                                                      int((self._samples_read + datalen) / 10)),
                               signal=self._ploty * np.ones(int((datalen) / 10)),
                               style='k-')
        self._samples_read += datalen
        return data

    def samples_to_pixels(self, line_samples):
        """ Reshape read datastream over the line to a line with pixel counts.
        Do this by summing elements, with the rate ratio calculated previously.
        """
        frac = int(self._frac_det_dwell)
        n = (len(line_samples) // frac) * frac
        if n == 0:
            return np.zeros((0,), dtype=float)
        if n != len(line_samples):
            # optional: logger warning
            line_samples = line_samples[:n]
        return np.asarray(line_samples).reshape(-1, frac).sum(axis=1)

    def __plot_curves(self, plot, xvals, signal, style='k-'):
        """ Plot read and thrown samples, for debugging. """
        if plot:
            plt.figure(1)
            plt.plot(xvals, signal, style)
            self._ploty += 0.01
            if self._ploty > 1.1:
                self._ploty = 1

    def run(self):
        """ Main run for acquisition.
        """
        if self._manager._debug_mode:
            self._ploty = 1
        # create empty current position counter
        self._pos = np.zeros(len(self._loop_dims), dtype='uint16')
        # throw away phase delay samples and start zero samples
        self.throwdata(self._phase_delay)
        self.throwdata(self._throw_startzero)
        # throw away higher dim initpos, if any
        if len(self._scan_pads_initpos) > 1:
            if any(np.greater(self._scan_pads_initpos[1:], self._scan_pads_initpos[0])):
                self._throw_init_higher_d = np.max(self._scan_pads_initpos[1:]) - self._scan_pads_initpos[0]
                self.throwdata(self._throw_init_higher_d)
        if len(self._loop_dims) == 2:
            # begin d3 step: throw data from initial d3 step positioning
            self.throwdata(self._throw_init_smooth)
        # loop through all dimensions to record data, starting with the outermost dimension
        self.run_loop_dx(dim=len(self._loop_dims))
        if self._manager._simulation_mode:
            # call mock acquisition done in nidaqmanager
            self._manager._nidaqManager.finishExternalMock()
        # emit acquisition done signal
        self.acqDoneSignal.emit()

    def run_loop_dx(self, dim):
        """ Recursive looping through all scanning dimensions, actually read samples at dim = 2,
        and step through all steps in each dimension.
        Works for arbitrary amount of dimensions, tested for <=5.
        """
        while self._pos[dim - 1] < self._loop_dims[dim - 1]:
            if dim > 2:
                if dim == 3:
                    if any(self._smooth_axes[:dim - 1]) or self._pos[dim - 1] == 0:
                        # begin d step: throw data from initial smooth step positioning,
                        # if this is the first smooth axis, or if it is the first step on the axis
                        self.throwdata(self._throw_init_smooth)
                self.run_loop_dx(dim - 1)
                if dim >= 3:
                    # end higher dim step: realign actual N read samples with supposed N read samples,
                    # compensating for all axis initpos and finalpos
                    pos = np.copy(self._pos)
                    pos[dim - 1] += 1
                    # supposed samples = start_zero_samples + d_steps * d samples_per_step
                    supposed_samples_read = self._throw_startzero + np.sum(
                        np.multiply(pos, self._samples_d_scanstep[:-1]))
                    if self._throw_init_higher_d:
                        # if some smooth higher dim init, add those samples to the supposedly read samples
                        supposed_samples_read += self._throw_init_higher_d
                    throwdatalen = supposed_samples_read - (self._samples_read - self._phase_delay)
                    if throwdatalen > 0:
                        self.throwdata(throwdatalen)
                    if dim == 3:
                        self.d3Step.emit()
            else:
                self.run_loop_d2()
            self._pos[dim - 1] += 1
        self._pos[dim - 1] = 0

    def run_loop_d2(self):
        """ Reading data on dim = 2, changing data to pixels, and emitting the d2 step of pixels.
        """
        if self.scanning:
            if self._pos[1] == self._loop_dims[1] - 1:
                # read a line
                if self._manager._ttlmultiplying:
                    seq_signal_xstart = self._samples_read - self._phase_delay
                data = self.readdata(self._samples_d_scanstep[1])
                if self._manager._ttlmultiplying:
                    seq_signal_xend = self._samples_read - self._phase_delay
                    ttl_seq = self._seq_signal[seq_signal_xstart:seq_signal_xend]
            else:
                # read a whole period, starting with the line and then the data during the flyback
                if self._manager._ttlmultiplying:
                    seq_signal_xstart = self._samples_read - self._phase_delay
                data = self.readdata(self._samples_d2_period)
                if self._manager._ttlmultiplying:
                    seq_signal_xend = self._samples_read - self._phase_delay
                    ttl_seq = self._seq_signal[seq_signal_xstart:seq_signal_xend]
            # get photon counts from data array (which is cumsummed)
            data_cnts = np.concatenate(([data[0] - self._last_value], np.diff(data)))
            self._last_value = data[-1]
            # only take the first samples that corresponds to the samples during the line
            line_samples = data_cnts[:self._samples_d_scanstep[1]]
            if self._manager._ttlmultiplying:
                ttl_seq = ttl_seq[:self._samples_d_scanstep[1]]
                # mask with TTL sequence from ScanWidget, to say if detector should be on or not
                line_samples = np.multiply(line_samples, 1 * ttl_seq)
            # resample sample array to pixel counts array
            pixels = self.samples_to_pixels(line_samples)
            # signal new line of pixels, and the insertion position in all dimensions
            self.d2Step.emit(pixels, tuple(np.flip(self._pos[1:])))
            if len(self._loop_dims) == 2 and self._pos[1] == self._loop_dims[1] - 1:
                self.d3Step.emit()
        else:
            self.__logger.debug('Close data reading: not scanning any longer')
            self.close()

    def close(self):
        pass
        self._manager._nidaqManager.inputTaskDone(self._name)

    def randomInput(self, datalen):
        return np.random.randint(100, size=datalen)

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
