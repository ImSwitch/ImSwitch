import numpy as np
import matplotlib.pyplot as plt

from imswitch.imcommon.framework import Signal, Thread, Worker
from imswitch.imcommon.model import initLogger
from .DetectorManager import DetectorManager


class PMTManager(DetectorManager):
    """PMT analog-input manager with linestep-aware buffering + frame-boundary UI updates."""

    def __init__(self, detectorInfo, name, nidaqManager, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        model = name
        self._name = name

        self._image = np.array([])          # raw buffer (stack if linesteps > 1)
        self._image_display = np.array([])  # always (1, Ny, Nx)
        self.__newFrameReady = False

        # Pixel sizes stored low-dim to high-dim (ImSwitch convention used elsewhere)
        self.__pixel_sizes = [1, 1]

        self._detection_samplerate = float(1e6)
        self._nidaq_clock_source = r"ctr2InternalOutput"

        self._channel = detectorInfo.managerProperties.get("analogInputLine", None)
        if isinstance(self._channel, int):
            self._channel = f"Dev1/ai{self._channel}"

        self._offset_v = float(detectorInfo.managerProperties.get("offset_v", 0.0))

        self._scanWorker = None
        self._scanThread = None

        self._ttlmultiplying = False
        self._simulation_mode = False
        self._debug_mode = False

        # linestep settings (kept for manager-side display logic)
        self._linestep = 1
        self._linestep_view_mode = "sum"   # "sum" | "max" | "slice"
        self._linestep_view_index = 0      # used if mode == "slice"

        self.acquisition = True

        parameters = {}
        self._nidaqManager = nidaqManager
        self._nidaqManager.sigScanBuilt.connect(
            lambda scanInfoDict, signalDict, _: self.initiateScan(scanInfoDict, signalDict)
        )
        self._nidaqManager.sigScanStarted.connect(self.startScan)

        self.__shape = (100, 100)  # or self.fullShape if you prefer

        super().__init__(
            detectorInfo, name,
            fullShape=(100, 100),
            supportedBinnings=[1],
            model=model,
            parameters=parameters,
            croppable=False
        )

    def crop(self, hpos, vpos, hsize, vsize):
        pass

    def __del__(self):
        try:
            if self._scanThread is not None:
                self._scanThread.quit()
                self._scanThread.wait()
        except Exception:
            pass
        if hasattr(super(), "__del__"):
            super().__del__()

    @property
    def pixelSizeUm(self):
        # return [t, y, x] scale style
        return [1, self.__pixel_sizes[1], self.__pixel_sizes[0]]

    @property
    def scale(self):
        return self.__pixel_sizes[::-1]

    def setPixelSize(self, pixel_sizes: list):
        self.__pixel_sizes = list(pixel_sizes)

    def initiateScan(self, scanInfoDict, signalDict):
        if not self.acquisition:
            return

        self._scanWorker = ScanWorker(self, scanInfoDict, signalDict)

        self._scanThread = Thread()
        self._scanWorker.moveToThread(self._scanThread)
        self._scanThread.started.connect(self._scanWorker.run)

        self._scanWorker.scanning = True
        self._scanWorker.d2Step.connect(lambda pixels, pos: self.updateImage(pixels, pos))
        self._scanWorker.d3Step.connect(self._onFrameBoundary)
        self._scanWorker.acqDoneSignal.connect(self.stopAcquisitionLocal)

        # store linestep on manager for display logic
        self._linestep = int(getattr(self._scanWorker, "_linestep", 1))

        if self._debug_mode:
            plt.figure(1)

    def startScan(self):
        if self.acquisition and self._scanThread is not None:
            self._scanThread.start()

    def startAcquisition(self):
        self.acquisition = True
        self.__newFrameReady = False

    def stopAcquisition(self):
        self.stopAcquisitionLocal()

    def stopAcquisitionLocal(self):
        try:
            if self._scanWorker is not None:
                self._scanWorker.scanning = False

            if self._scanThread is not None:
                self._scanThread.quit()
                self._scanThread.wait()

            if self._scanWorker is not None:
                self._scanWorker.close()

            if self._ttlmultiplying:
                self._renewImage()

            # final refresh
            self._onFrameBoundary()

        except Exception:
            self.__logger.exception("Error stopping PMT acquisition")
        finally:
            if self._debug_mode:
                try:
                    plt.show()
                except Exception:
                    pass

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

        img_dims_extra = tuple(reversed((*img_dims, 1)))
        if np.shape(self._image) != img_dims_extra:
            self._image = np.zeros(img_dims_extra, dtype=float)
            self.setShape(img_dims_extra)

        # Always allocate display as 2D (1, Ny, Nx)
        Nx = int(img_dims[0]) if len(img_dims) >= 1 else 1
        Ny = int(img_dims[1]) if len(img_dims) >= 2 else 1
        Nz = int(img_dims[2]) if len(img_dims) >= 3 else 1
        self._image_display = np.zeros((1, Nz, Ny, Nx), dtype=float)

    def updateImage(self, pixels, pos: tuple):
        """
        pos is emitted as tuple(np.flip(self._pos[1:])) from ScanWorker.
        For XY:           pos == (y_expanded,)
        For Z stacks:     pos == (z, y_expanded)
        For higher dims:  pos == (..., z, y_expanded)  (last element is always y_expanded)
        """
        S = int(getattr(self, "_linestep", 1))
        y_expanded = int(pos[-1])

        # clip pixel write length to Nx
        Nx = self._image.shape[-1] if self._image.size else len(pixels)
        n = min(len(pixels), Nx)
        if n <= 0:
            return

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

    def _compute_display_frame(self):
        """
        Build a 2D plane (Ny, Nx) from the raw buffer.
        Keeps future flexibility: sum/max/slice over linestep.
        """
        S = int(getattr(self, "_linestep", 1))
        if S <= 1:
            return self._image[0]

        raw = self._image[0]  # (S, Ny, Nx) for 2D scans
        mode = getattr(self, "_linestep_view_mode", "sum")

        if mode == "max":
            return np.nanmax(raw, axis=0)
        if mode == "slice":
            idx = int(getattr(self, "_linestep_view_index", 0)) % raw.shape[0]
            return raw[idx]
        return np.nansum(raw, axis=0)

    def _onFrameBoundary(self):
        """
        Called at the end of a full frame (one complete XY image) for each higher-d step (e.g. each Z).
        Updates display buffer and triggers GUI redraw once per frame.
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

    def getLatestFrame(self, is_save=True):
        """
        - when saving and linesteps>1, return raw stack
        - otherwise return display plane
        """
        S = int(getattr(self, "_linestep", 1))
        if is_save and S > 1:
            return self._image
        return self._image_display

    def getChunk(self):
        if not self.__newFrameReady:
            return np.empty((0, 0, 0))
        self.__newFrameReady = False
        return self._image_display.copy()  # always (1, Ny, Nx)

    def flushBuffers(self):
        self.__newFrameReady = False

    def _renewImage(self):
        self._image = np.nan_to_num(self._image, nan=0.0)

    @property
    def shape(self):
        return self.__shape

    def setShape(self, img_dims):
        self.__shape = tuple(img_dims)


class ScanWorker(Worker):
    d2Step = Signal(np.ndarray, tuple)
    d3Step = Signal()
    acqDoneSignal = Signal()

    def __init__(self, manager, scanInfoDict, signalDict):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

        self._samples_read = 0
        self._manager = manager
        self._name = self._manager._name
        self._channel = self._manager._channel

        self._scan_dwell_time = scanInfoDict["dwell_time"]
        self._frac_det_dwell = round(self._scan_dwell_time * self._manager._detection_samplerate)
        self._frac_scan_det_rate = round(self._manager._detection_samplerate * scanInfoDict["scan_time_step"])

        # ----------------------------
        # Axis-aware linestep parsing
        # ----------------------------
        img_dims_in = list(scanInfoDict["img_dims"])
        axes = list(scanInfoDict.get("img_axes_with_linesteps", []))  # preferred

        if not axes:
            axes = list(scanInfoDict.get("img_axes_phys", []))
            n_ls = int(scanInfoDict.get("n_linesteps", 1))
            if n_ls > 1:
                axes = axes + ["linestep"]

        linestep_idx = axes.index("linestep") if "linestep" in axes else None
        if linestep_idx is not None:
            self._linestep = int(img_dims_in[linestep_idx])
        else:
            self._linestep = int(scanInfoDict.get("n_linesteps", 1))
        self._linestep = max(1, self._linestep)

        # remove linestep from recursion dims
        if linestep_idx is not None:
            scan_dims = [d for i, d in enumerate(img_dims_in) if i != linestep_idx]
            scan_axes = [a for i, a in enumerate(axes) if i != linestep_idx]
        else:
            scan_dims = img_dims_in
            scan_axes = axes

        # identify Y axis (default to 1)
        y_idx = scan_axes.index("y") if "y" in scan_axes else 1

        # recursion dims (no linestep axis)
        self._img_dims = scan_dims
        self._loop_dims = scan_dims.copy()

        # expand Y by linestep (Ny -> Ny*S)
        if len(self._loop_dims) > y_idx:
            self._loop_dims[y_idx] = int(self._loop_dims[y_idx] * self._linestep)

        # output dims for manager allocation: append linestep at end if >1 (keeps stack possible)
        self._output_image_dims = tuple(scan_dims + ([self._linestep] if self._linestep > 1 else []))

        # Nx for pixel binning (by convention img_dims starts with Nx,Ny,...)
        self._Nx = int(scan_dims[0]) if len(scan_dims) >= 1 else 1

        # ----------------------------
        # TTL sequence expansion
        # ----------------------------
        self._manager._ttlmultiplying = scanInfoDict.get("ttlmultiplying", self._manager._ttlmultiplying)
        if self._manager._ttlmultiplying:
            for target in signalDict["TTLCycleSignalsDict"].keys():
                if self._name == target:
                    self._seq_signal = signalDict["TTLCycleSignalsDict"][target].copy()
                    self._seq_signal = np.repeat(self._seq_signal, self._frac_scan_det_rate).astype(float)
                    self._seq_signal[self._seq_signal == 0] = np.nan
                    break

        # det samples per scan steps in different dims
        self._samples_d_scanstep = [round(samples) * self._frac_scan_det_rate for samples in scanInfoDict["scan_samples"]]
        self._samples_d2_period = round(scanInfoDict["scan_samples_d2_period"] * self._frac_scan_det_rate)
        self._samples_total = round(scanInfoDict["scan_samples_total"] * self._frac_scan_det_rate)

        self._throw_startzero = round(scanInfoDict["scan_throw_startzero"] * self._frac_scan_det_rate)
        self._scan_pads_initpos = [round(initpos) * self._frac_scan_det_rate for initpos in scanInfoDict["scan_pads_initpos"]]
        self._throw_settling = round(scanInfoDict["scan_throw_settling"] * self._frac_scan_det_rate)
        self._throw_startacc = round(scanInfoDict["scan_throw_startacc"] * self._frac_scan_det_rate)

        self._phase_delay = int(scanInfoDict["phase_delay"])
        self._smooth_axes = scanInfoDict["smooth_axes"]

        pad_initpos = self._scan_pads_initpos[0] if len(self._scan_pads_initpos) > 0 else 0
        self._throw_init_smooth = (pad_initpos + self._throw_settling + self._throw_startacc)
        self._throw_init_higher_d = False

        # start input task
        if not self._manager._simulation_mode:
            self._manager._nidaqManager.startInputTask(
                self._name, "ai", self._channel, "finite",
                self._manager._nidaq_clock_source,
                self._manager._detection_samplerate,
                None, None,
                self._samples_total, True, "ao/StartTrigger"
            )

        # allocate buffers
        self._manager.initiateImage(self._output_image_dims)
        self._manager.setPixelSize(scanInfoDict["pixel_sizes"])

    def throwdata(self, datalen):
        if datalen > 0:
            if self._manager._simulation_mode:
                _ = self.randomInput(datalen)
            else:
                _ = self._manager._nidaqManager.readInputTask(self._name, datalen)
            self._samples_read += datalen

    def readdata(self, datalen):
        if self._manager._simulation_mode:
            data = self.randomInput(datalen)
        else:
            data = self._manager._nidaqManager.readInputTask(self._name, datalen)
        self._samples_read += datalen
        return data

    def samples_to_pixels(self, line_samples):
        arr = np.asarray(line_samples, dtype=float)
        expected = int(self._Nx) * int(self._frac_det_dwell)
        if arr.size < expected:
            arr = np.pad(arr, (0, expected - arr.size), mode="constant", constant_values=0)
        elif arr.size > expected:
            arr = arr[:expected]
        return arr.reshape(int(self._Nx), int(self._frac_det_dwell)).sum(axis=1)

    def run(self):
        self._pos = np.zeros(len(self._loop_dims), dtype="uint16")

        self.throwdata(self._phase_delay)
        self.throwdata(self._throw_startzero)

        if len(self._scan_pads_initpos) > 1:
            if any(np.greater(self._scan_pads_initpos[1:], self._scan_pads_initpos[0])):
                self._throw_init_higher_d = np.max(self._scan_pads_initpos[1:]) - self._scan_pads_initpos[0]
                self.throwdata(self._throw_init_higher_d)

        if len(self._loop_dims) == 2:
            self.throwdata(self._throw_init_smooth)

        self.run_loop_dx(dim=len(self._loop_dims))

        if self._manager._simulation_mode:
            self._manager._nidaqManager.finishExternalMock()

        self.acqDoneSignal.emit()

    def run_loop_dx(self, dim):
        while self._pos[dim - 1] < self._loop_dims[dim - 1]:
            if dim > 2:
                if dim == 3:
                    if any(self._smooth_axes[:dim - 1]) or self._pos[dim - 1] == 0:
                        self.throwdata(self._throw_init_smooth)

                self.run_loop_dx(dim - 1)

                if dim >= 3:
                    # realign read samples
                    pos = np.copy(self._pos)
                    pos[dim - 1] += 1
                    supposed_samples_read = self._throw_startzero + np.sum(
                        np.multiply(pos, self._samples_d_scanstep[:-1])
                    )

                    if self._throw_init_higher_d:
                        supposed_samples_read += self._throw_init_higher_d

                    throwdatalen = supposed_samples_read - (self._samples_read - self._phase_delay)
                    if throwdatalen > 0:
                        self.throwdata(throwdatalen)

                    # full "frame" completed for this higher-d step
                    self.d3Step.emit()
            else:
                self.run_loop_d2()

            self._pos[dim - 1] += 1

        self._pos[dim - 1] = 0

    def run_loop_d2(self):
        if not self.scanning:
            self.close()
            return

        # line index along expanded-Y (Ny*S)
        line_idx = int(self._pos[1])

        if self._pos[1] == self._loop_dims[1] - 1:
            if self._manager._ttlmultiplying:
                seq_start = self._samples_read - self._phase_delay
            data = self.readdata(self._samples_d_scanstep[1])
            if self._manager._ttlmultiplying:
                seq_end = self._samples_read - self._phase_delay
                ttl_seq = self._seq_signal[seq_start:seq_end]
        else:
            if self._manager._ttlmultiplying:
                seq_start = self._samples_read - self._phase_delay
            data = self.readdata(self._samples_d2_period)
            if self._manager._ttlmultiplying:
                seq_end = self._samples_read - self._phase_delay
                ttl_seq = self._seq_signal[seq_start:seq_end]

        # analog samples + offset
        data_arr = np.asarray(data, dtype=float) - float(self._manager._offset_v)
        line_samples = data_arr[:self._samples_d_scanstep[1]]

        if self._manager._ttlmultiplying:
            ttl_seq = ttl_seq[:self._samples_d_scanstep[1]]
            line_samples = np.multiply(line_samples, 1 * ttl_seq)

        pixels = self.samples_to_pixels(line_samples)

        # emit line and its insertion pos
        # IMPORTANT: keep same convention as APD: emit flipped pos[1:] (for XY, this is (line_idx,))
        self.d2Step.emit(pixels, tuple(np.flip(self._pos[1:])))


        # frame boundary for plain XY scan: only once after ALL expanded-Y lines
        if len(self._loop_dims) == 2 and (line_idx == self._loop_dims[1] - 1):
            self.d3Step.emit()

    def close(self):
        try:
            self._manager._nidaqManager.inputTaskDone(self._name)
        except Exception:
            pass

    def randomInput(self, datalen):
        return np.random.randint(100, size=datalen)
