import numpy as np
import time

from imswitch.imcommon.framework import Signal, Thread, Worker
from imswitch.imcommon.model import initLogger
from .DetectorManager import DetectorManager

# TimeTagger is optional hardware-specific library — guard against missing installs
# so that loading the module never crashes unrelated setups.
try:
    import TimeTagger
    from TimeTagger import Flim, createTimeTagger
    _TIMETAGGER_AVAILABLE = True
except ImportError:
    TimeTagger = None
    Flim = None
    createTimeTagger = None
    _TIMETAGGER_AVAILABLE = False


class SwabianTimeTaggerManager(DetectorManager):
    """
    TimeTagger FLIM detector without physical pixel pulses.

    We generate virtual pixel begin/end pulses from the line clock using scan timing:
      - pixel_period_ps = samples_per_pixel / sampleRate
      - per line: generate Nx pixel-begin events spaced by pixel_period_ps
      - pixel-end is delayed by pixel_width_ps (default = pixel_period_ps)

    Then we use Flim(...) to get (n_pixels, n_bins) histograms and compute lifetime per pixel.
    """

    def __init__(self, detectorInfo, name, nidaqManager, **_lowLevelManagers):
        self._logger = initLogger(self, instanceName=name)

        if not _TIMETAGGER_AVAILABLE:
            self._logger.error(
                "TimeTagger Python library not found. Install it from the Swabian Instruments "
                "software package. SwabianTimeTaggerManager will not function."
            )

        self._detectorInfo = detectorInfo
        self._nidaqManager = nidaqManager
        props = getattr(detectorInfo, "managerProperties", {}) or {}

        self._enabled = bool(props.get("enabled", True))
        self._click_ch = int(props["click_channel"])
        self._line_ch = int(props["line_channel"])
        self._start_ch = int(props["start_channel"])

        self._trigger_levels = props.get("trigger_levels", {}) or {}

        self._min_counts_per_pixel = int(props.get("min_counts_per_pixel", 20))
        self._n_bins = int(props.get("n_bins", 64))
        self._binwidth_ps = int(props.get("binwidth_ps", 32))

        # Hardcode virtual output channels (keeps config small)
        self._pix_begin_ch = int(props.get("virtual_pixel_begin_channel", 5))
        self._pix_end_ch = int(props.get("virtual_pixel_end_channel", 5))

        self._tt = None
        self._flim = None
        self._ev_pix = None


        self._scan = {}
        fullShape = (64, 64)
        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1], model=name)

        self._nidaqManager.sigScanBuilt.connect(
            lambda scanInfoDict, signalDict, _: self.initiateScan(scanInfoDict, signalDict)
        )
        self._nidaqManager.sigScanStarted.connect(self.startScan)

        self._scanThread = None
        self._scanWorker = None


    def __del__(self):
        """Release TimeTagger hardware and stop worker thread on destruction."""
        try:
            self.stopAcquisition()
        except Exception:
            pass
        try:
            # Free measurement objects before releasing the tagger
            self._ev_pix = None
            self._flim = None
            self._tt = None
        except Exception:
            pass
        if hasattr(super(), '__del__'):
            super().__del__()

    def initiateScan(self, scanInfoDict, signalDict):
        if not self._enabled:
            return
        if not _TIMETAGGER_AVAILABLE:
            self._logger.warning("TimeTagger not available — initiateScan skipped.")
            return

        Nx, Ny, S, outer_axes, outer_dims = self._infer_dims_from_scanInfo(scanInfoDict)

        self._newFrameReady = False

        # Always keep display as (1,Ny,Nx)
        self._image_display = (np.random.rand(1, Ny, Nx).astype(np.float32) * 100.0)  # or *100 if you want visible noise
        self._image_intensity = np.zeros((1, Ny, Nx), dtype=np.float32)

        # Raw: only if S>1 (APD returns raw stack on save when S>1) :contentReference[oaicite:3]{index=3}
        if S > 1:
            self._image_raw = np.zeros((1, S, Ny, Nx), dtype=np.float32)  # e.g. lifetime raw
            self._intensity_raw = np.zeros((1, S, Ny, Nx), dtype=np.float32)
        else:
            self._image_raw = None
            self._intensity_raw = None

        self._pixel_size_um = [1, 1]

        pixel_period_s = float(scanInfoDict.get("dwell_time", 0.0))
        if pixel_period_s <= 0:
            raise RuntimeError(f"Missing/invalid dwell_time in scanInfoDict: {scanInfoDict.get('dwell_time')}")

        pixel_period_ps = int(round(pixel_period_s * 1e12))

        # Optional: define pixel width = dwell (can later subtract blanking if you want)
        pixel_width_ps = pixel_period_ps

        # Optional sanity: scan_time_step is the NI sampling period (seconds) :contentReference[oaicite:2]{index=2}
        scan_time_step = float(scanInfoDict.get("scan_time_step", 0.0))
        if scan_time_step > 0:
            # how many NI samples per pixel, purely informational
            spp_est = pixel_period_s / scan_time_step
            # only log; don't enforce
            self._logger.debug(f"Estimated samples_per_pixel ~= {spp_est:.3f} from dwell_time/scan_time_step")

        self._scan = dict(
            Nx=Nx, Ny=Ny,
            n_pixels_total=Nx * Ny,
            pixel_period_ps=pixel_period_ps,
            pixel_width_ps=pixel_width_ps
        )

        self._fullShape = (Ny, Nx)  # NOTE: image arrays are (Y, X)
        self._shape = self._fullShape  # some managers use _shape; harmless if unused

        # --- Connect and configure TimeTagger ---
        if self._tt is None:
            self._tt = createTimeTagger()

        for ch_str, lvl in self._trigger_levels.items():
            ch = int(ch_str)
            self._tt.setTriggerLevel(ch, float(lvl))

        # --- Create virtual pixel markers from line clock ---
        self._create_virtual_pixel_pulses()

        # --- Create FLIM measurement ---
        # IMPORTANT: Flim expects pixel begin/end channels for segmentation.
        # We provide our virtual channels.
        self._flim = Flim(
            self._tt,
            start_channel=self._start_ch,
            click_channel=self._click_ch,
            pixel_begin_channel=self._pix_begin_ch,
            pixel_end_channel=self._pix_end_ch,  # <-- no minus here
            n_pixels=int(self._scan["n_pixels_total"]),
            n_bins=self._n_bins,
            binwidth=self._binwidth_ps,
        )


        self._logger.info(
            f"TimeTagger prepared: click={self._click_ch}, start={self._start_ch}, line={self._line_ch}, "
            f"pix_begin={self._pix_begin_ch}, pix_end={self._pix_end_ch}, "
            f"Nx={Nx}, Ny={Ny}, pixel_period_ps={pixel_period_ps}"
        )

    def _create_virtual_pixel_pulses(self):
        Nx = int(self._scan["Nx"])
        period_ps = int(self._scan["pixel_period_ps"])
        width_ps = int(self._scan["pixel_width_ps"])

        # vector<long long> required -> numpy int64
        begin_pattern = (np.arange(Nx, dtype=np.int64) * np.int64(period_ps))
        end_pattern = begin_pattern + np.int64(width_ps)

        self._ev_pix_begin = None
        self._ev_pix_end = None

        # EventGenerator(tagger, trigger_channel, pattern, output_channel)
        self._ev_pix_begin = TimeTagger.EventGenerator(
            self._tt,
            int(self._line_ch),
            begin_pattern,
            int(self._pix_begin_ch),
        )

        self._ev_pix_end = TimeTagger.EventGenerator(
            self._tt,
            int(self._line_ch),
            end_pattern,
            int(self._pix_end_ch),
        )

    def startScan(self):
        if not self._enabled or self._flim is None:
            return

        self.acquisition = True

        self._scanWorker = _TTFlimWorker(self)
        self._scanThread = Thread()
        self._scanWorker.moveToThread(self._scanThread)

        self._scanThread.started.connect(self._scanWorker.run)
        self._scanWorker.sigFrameReady.connect(self._on_frame_ready)
        self._scanWorker.sigFinished.connect(self._scanThread.quit)
        self._scanWorker.sigFinished.connect(self._scanWorker.deleteLater)
        self._scanThread.finished.connect(self._scanThread.deleteLater)

        self._scanThread.start()

    def stopScan(self):
        if self._scanWorker is not None:
            self._scanWorker.stop()

    def _on_frame_ready(self, intensity_img, lifetime_img):
        """
        intensity_img and lifetime_img are expected to be 2D arrays (Ny, Nx)
        """
        # store
        self._image_intensity[0] = intensity_img
        self._image_display[0] = lifetime_img

        self._newFrameReady = True

        # publish to GUI: lifetime as primary, intensity as extra
        self.sigImageUpdated.emit(self._image_display, False, [self._image_intensity])

        # if DetectorManager provides updateLatestFrame, keep it, otherwise skip safely
        if hasattr(self, "updateLatestFrame"):
            self.updateLatestFrame(True)

        self.sigNewFrame.emit()

    # --- Required abstract-method implementations (DetectorManager) ---

    def pixelSizeUm(self):
        """
        Match APDManager/DetectorManager.scale convention: [Z_or_leading, Y, X].
        DetectorManager.scale slices [1:] so we need at least 3 elements.
        """
        stored = getattr(self, "_pixel_size_um", [1, 1])
        # Ensure 3-element [Z, Y, X] format (Z defaults to 1 for 2-D FLIM)
        if len(stored) < 3:
            return [1] + list(stored)
        return list(stored)

    def crop(self, hpos, vpos, hsize, vsize):
        """
        Placeholder like APDManager. For now do nothing (no ROI cropping).
        You can later implement by cropping _image_display and updating shape.
        """
        pass

    def getLatestFrame(self, is_save=True):
        if is_save and self._image_raw is not None:
            return self._image_raw
        return self._image_display

    def getChunk(self):
        if not getattr(self, "_newFrameReady", False):
            return self._image_display
        self._newFrameReady = False
        return self._image_display.copy()

    def flushBuffers(self):
        """
        Placeholder like APDManager.
        If later you buffer TT data / histograms, clear them here.
        """
        pass

    def startAcquisition(self):
        """
        Called by the framework when acquisition starts.
        Keep same semantics as APDManager.
        """
        self.acquisition = True
        self._newFrameReady = False

    def stopAcquisition(self):
        """
        Called by framework when acquisition stops.
        Stop worker/thread safely and set _newFrameReady so the last frame can be fetched.
        """
        self.acquisition = False
        try:
            if getattr(self, "_scanWorker", None) is not None:
                self._scanWorker.stop()
            if getattr(self, "_scanThread", None) is not None:
                self._scanThread.quit()
                self._scanThread.wait()
        except Exception:
            pass
        self._newFrameReady = True

    def _infer_dims_from_scanInfo(self, scanInfoDict):
        img_dims_in = list(scanInfoDict["img_dims"])
        axes = list(scanInfoDict.get("img_axes_with_linesteps", []))  # preferred (APD does this)
        if not axes:
            axes = list(scanInfoDict.get("img_axes_phys", []))
            n_ls = int(scanInfoDict.get("n_linesteps", 1))
            if n_ls > 1:
                axes = axes + ["linestep"]

        # linestep index + size (APD logic)
        linestep_idx = axes.index("linestep") if "linestep" in axes else None
        if linestep_idx is not None:
            S = int(img_dims_in[linestep_idx])
        else:
            S = int(scanInfoDict.get("n_linesteps", 1))
        S = max(1, S)

        # “scan dims” excluding linestep (APD logic)
        if linestep_idx is not None:
            scan_dims = [d for i, d in enumerate(img_dims_in) if i != linestep_idx]
            scan_axes = [a for i, a in enumerate(axes) if i != linestep_idx]
        else:
            scan_dims = img_dims_in
            scan_axes = axes

        # Choose Nx, Ny from axes if possible, else fall back to last two dims
        if "x" in scan_axes and "y" in scan_axes:
            Nx = int(scan_dims[scan_axes.index("x")])
            Ny = int(scan_dims[scan_axes.index("y")])
        else:
            Nx = int(scan_dims[-1])
            Ny = int(scan_dims[-2])

        # Any remaining scan dims are “outer” dims (e.g. z, t, etc.)
        outer_axes = [a for a in scan_axes if a not in ("y", "x")]
        outer_dims = [int(scan_dims[scan_axes.index(a)]) for a in outer_axes]

        return Nx, Ny, S, outer_axes, outer_dims


class _TTFlimWorker(Worker):
    sigFrameReady = Signal(object, object)
    sigFinished = Signal()

    def __init__(self, m: SwabianTimeTaggerManager):
        super().__init__()
        self._logger = initLogger(self, tryInheritParent=True)
        self._m = m
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        try:
            Nx = int(self._m._scan["Nx"])
            Ny = int(self._m._scan["Ny"])
            n_bins = int(self._m._n_bins)
            poll_s = 0.02

            while self._running and getattr(self._m, "acquisition", True):
                # Get current histograms
                # Many versions expose getData() for Flim (n_pixels, n_bins).
                h = self._m._flim.getCurrentFrame()
                arr = np.asarray(h, dtype=np.float32)

                if arr.ndim != 2 or arr.shape != (Nx * Ny, n_bins):
                    time.sleep(poll_s)
                    continue

                cube = arr.reshape(Ny, Nx, n_bins)

                intensity = cube.sum(axis=2)

                # Fast "fit": mean microtime (moment). Cheap and stable.
                # Time axis (seconds)
                t = (np.arange(n_bins, dtype=np.float32) + 0.5) * float(self._m._binwidth_ps) * 1e-12
                numer = (cube * t[None, None, :]).sum(axis=2)
                denom = intensity
                lifetime = np.zeros_like(intensity, dtype=np.float32)
                good = denom > 0
                lifetime[good] = numer[good] / denom[good]

                # Fail rule: low counts -> 0
                lifetime[intensity < self._m._min_counts_per_pixel] = 0.0
                lifetime[~np.isfinite(lifetime)] = 0.0
                lifetime[lifetime < 0] = 0.0

                self.sigFrameReady.emit(intensity.astype(np.float32), lifetime.astype(np.float32))
                time.sleep(poll_s)

        except Exception:
            self._logger.exception("TimeTagger FLIM worker crashed.")
        finally:
            self.sigFinished.emit()
