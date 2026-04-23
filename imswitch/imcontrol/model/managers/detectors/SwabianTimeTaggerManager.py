import numpy as np
import time

from imswitch.imcommon.framework import Signal, Thread, Worker
from imswitch.imcommon.model import initLogger
from .DetectorManager import (
    DetectorManager, DetectorNumberParameter, DetectorListParameter)

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
    TimeTagger FLIM detector. Returns fitted fluorescence lifetime per pixel.

    Channel and TCSPC settings are exposed as detector parameters and can be
    changed between scans via the GUI or setParameter(). Changes take effect
    on the next initiateScan() call.

    Required config properties:
      click_channel, start_channel, line_channel

    Optional config properties:
      n_bins (default 64), binwidth_ps (default 32),
      min_counts_per_pixel (default 20), fit_method (default 'moment'),
      trigger_levels (dict {channel_str: volts}, used only to seed
        click_trigger / start_trigger / line_trigger defaults),
      enabled (default True)

    Pixel markers are generated internally via EventGenerator using
    auto-assigned virtual channel IDs — no physical channels are consumed.
    """

    def __init__(self, detectorInfo, name, nidaqManager, **_lowLevelManagers):
        self._logger = initLogger(self, instanceName=name)

        if not _TIMETAGGER_AVAILABLE:
            self._logger.error(
                'TimeTagger Python library not found. Install it from the Swabian Instruments '
                'software package. SwabianTimeTaggerManager will not function.'
            )


        self._detectorInfo = detectorInfo
        self._nidaqManager = nidaqManager
        props = getattr(detectorInfo, 'managerProperties', {}) or {}

        self._enabled = bool(props.get('enabled', True))
        tl = props.get('trigger_levels', {}) or {}

        # Internal state — always kept in sync with parameters via setParameter()
        self._click_ch = int(props['click_channel'])
        self._start_ch = int(props['start_channel'])
        self._line_ch = int(props['line_channel'])
        # Trigger levels keyed by role — defaults pulled from the trigger_levels
        # dict (keyed by channel number string) for backward compatibility.
        self._click_trigger = float(tl.get(str(self._click_ch), 0.5))
        self._start_trigger = float(tl.get(str(self._start_ch), 0.5))
        self._line_trigger = float(tl.get(str(self._line_ch), 0.5))
        self._n_bins = int(props.get('n_bins', 64))
        self._binwidth_ps = int(props.get('binwidth_ps', 32))
        self._min_counts_per_pixel = int(props.get('min_counts_per_pixel', 20))
        self._fit_method = str(props.get('fit_method', 'moment'))

        parameters = {
            # --- Channel routing ---
            'click_channel': DetectorNumberParameter(
                group='Channels', value=self._click_ch,
                valueUnits='ch', editable=True),
            'start_channel': DetectorNumberParameter(
                group='Channels', value=self._start_ch,
                valueUnits='ch', editable=True),
            'line_channel': DetectorNumberParameter(
                group='Channels', value=self._line_ch,
                valueUnits='ch', editable=True),
            # --- Trigger levels (one per named channel role) ---
            'click_trigger': DetectorNumberParameter(
                group='Trigger Levels', value=self._click_trigger,
                valueUnits='V', editable=True),
            'start_trigger': DetectorNumberParameter(
                group='Trigger Levels', value=self._start_trigger,
                valueUnits='V', editable=True),
            'line_trigger': DetectorNumberParameter(
                group='Trigger Levels', value=self._line_trigger,
                valueUnits='V', editable=True),
            # --- TCSPC settings ---
            'n_bins': DetectorNumberParameter(
                group='TCSPC', value=self._n_bins,
                valueUnits='bins', editable=True),
            'binwidth_ps': DetectorNumberParameter(
                group='TCSPC', value=self._binwidth_ps,
                valueUnits='ps', editable=True),
            'min_counts_per_pixel': DetectorNumberParameter(
                group='TCSPC', value=self._min_counts_per_pixel,
                valueUnits='counts', editable=True),
            # --- Lifetime fitting ---
            'fit_method': DetectorListParameter(
                group='Fitting', value=self._fit_method,
                options=['moment', 'phasor', 'exp1'],
                editable=True),
        }

        self._tt = None
        self._flim = None
        self._ev_pix_begin = None
        self._ev_pix_end = None
        self._scan = {}
        self._isMock = False  # True when hardware connection failed

        self._image_display = np.zeros((1, 64, 64), dtype=np.float32)
        self._image_intensity = np.zeros((1, 64, 64), dtype=np.float32)
        self._image_raw = None
        self._newFrameReady = False
        self.__pixel_sizes = [1, 1]

        super().__init__(detectorInfo, name, fullShape=(64, 64),
                         supportedBinnings=[1], model=name,
                         parameters=parameters, croppable=False)

        self._nidaqManager.sigScanBuilt.connect(
            lambda scanInfoDict, signalDict, _: self.initiateScan(scanInfoDict, signalDict)
        )
        self._nidaqManager.sigScanStarted.connect(self.startScan)
        self._nidaqManager.sigScanDone.connect(self._onScanDone)

        self._scanThread = None
        self._scanWorker = None

    def __del__(self):
        try:
            self.stopAcquisition()
        except Exception:
            pass
        try:
            self._ev_pix_begin = None
            self._ev_pix_end = None
            self._flim = None
            self._tt = None
        except Exception:
            pass
        if hasattr(super(), '__del__'):
            super().__del__()

    # ------------------------------------------------------------------ #
    # Parameter handling                                                   #
    # ------------------------------------------------------------------ #

    def setParameter(self, name, value):
        """Update a parameter and mirror it into the corresponding internal attr."""
        super().setParameter(name, value)
        if name == 'click_channel':
            self._click_ch = int(value)
        elif name == 'start_channel':
            self._start_ch = int(value)
        elif name == 'line_channel':
            self._line_ch = int(value)
        elif name == 'click_trigger':
            self._click_trigger = float(value)
        elif name == 'start_trigger':
            self._start_trigger = float(value)
        elif name == 'line_trigger':
            self._line_trigger = float(value)
        elif name == 'n_bins':
            self._n_bins = int(value)
        elif name == 'binwidth_ps':
            self._binwidth_ps = int(value)
        elif name == 'min_counts_per_pixel':
            self._min_counts_per_pixel = int(value)
        elif name == 'fit_method':
            self._fit_method = str(value)
        return self.parameters

    # ------------------------------------------------------------------ #
    # Scan lifecycle                                                        #
    # ------------------------------------------------------------------ #

    def initiateScan(self, scanInfoDict, signalDict):
        if not self._enabled:
            return
        if not _TIMETAGGER_AVAILABLE:
            self._logger.warning('TimeTagger not available — initiateScan skipped.')
            return

        Nx, Ny, S, _outer_axes, _outer_dims = self._infer_dims_from_scanInfo(scanInfoDict)

        self._newFrameReady = False
        self._image_display = np.zeros((1, Ny, Nx), dtype=np.float32)
        self._image_intensity = np.zeros((1, Ny, Nx), dtype=np.float32)
        self._image_raw = None

        # pixel_sizes: list from low to high dim (matches APDManager convention)
        self.setPixelSize(list(scanInfoDict.get('pixel_sizes', [1, 1])) or [1, 1])

        pixel_period_s = float(scanInfoDict.get('dwell_time', 0.0))
        if pixel_period_s <= 0:
            raise RuntimeError(
                f"Missing/invalid dwell_time in scanInfoDict: {scanInfoDict.get('dwell_time')}"
            )
        pixel_period_ps = int(round(pixel_period_s * 1e12))

        scan_time_step = float(scanInfoDict.get('scan_time_step', 0.0))
        if scan_time_step > 0:
            self._logger.debug(
                f'Estimated samples_per_pixel ~= {pixel_period_s / scan_time_step:.3f}'
            )

        self._scan = dict(
            Nx=Nx, Ny=Ny,
            n_pixels_total=Nx * Ny,
            pixel_period_ps=pixel_period_ps,
            # end[i] = begin[i] + pixel_period - 1 ps. If end and next begin
            # share a timestamp, TimeTagger's edge ordering can drop or
            # reorder the end edge — Flim's pixel index then stalls mid-line.
            pixel_width_ps=pixel_period_ps - 1,
        )
        self._fullShape = (Ny, Nx)
        self._shape = self._fullShape

        try:
            if self._tt is None:
                self._tt = createTimeTagger()
                self._isMock = False
        except Exception:
            self._logger.exception(
                'createTimeTagger() failed — running in mock mode (no FLIM data).'
            )
            self._isMock = True
            self._flim = None
            return

        try:
            self._tt.setTriggerLevel(self._click_ch, self._click_trigger)
            self._tt.setTriggerLevel(self._start_ch, self._start_trigger)
            self._tt.setTriggerLevel(self._line_ch, self._line_trigger)

            self._create_virtual_pixel_pulses()

            # Recreate Flim every scan so channel/bin changes always take effect
            self._flim = Flim(
                self._tt,
                start_channel=self._start_ch,
                click_channel=self._click_ch,
                pixel_begin_channel=self._ev_pix_begin.getChannel(),
                pixel_end_channel=self._ev_pix_end.getChannel(),
                n_pixels=int(self._scan['n_pixels_total']),
                n_bins=self._n_bins,
                binwidth=self._binwidth_ps,
            )
        except Exception:
            self._logger.exception(
                'TimeTagger FLIM setup failed — no data this scan.'
            )
            self._flim = None
            return

        tot_scan_time_s = float(scanInfoDict.get('tot_scan_time_s', 0.0))
        ideal_scan_time_s = Nx * Ny * pixel_period_s
        overhead_pct = (
            (tot_scan_time_s - ideal_scan_time_s) / ideal_scan_time_s * 100
            if ideal_scan_time_s > 0 and tot_scan_time_s > 0 else 0.0
        )

        self._logger.info(
            f'TimeTagger prepared: click={self._click_ch}@{self._click_trigger}V, '
            f'start={self._start_ch}@{self._start_trigger}V, '
            f'line={self._line_ch}@{self._line_trigger}V, n_bins={self._n_bins}, '
            f'binwidth={self._binwidth_ps}ps, fit={self._fit_method}, '
            f'Nx={Nx}, Ny={Ny}, pixel_period={pixel_period_ps}ps, '
            f'scan_time={tot_scan_time_s:.3f}s '
            f'(ideal={ideal_scan_time_s:.3f}s, +{overhead_pct:.1f}% settling/flyback)'
        )

    def _create_virtual_pixel_pulses(self):
        Nx = int(self._scan['Nx'])
        period_ps = int(self._scan['pixel_period_ps'])
        width_ps = int(self._scan['pixel_width_ps'])

        begin_pattern = np.arange(Nx, dtype=np.int64) * np.int64(period_ps)
        end_pattern = begin_pattern + np.int64(width_ps)

        # Release previous generators before creating new ones
        self._ev_pix_begin = None
        self._ev_pix_end = None

        # No output_channel argument — the API auto-assigns virtual channel IDs
        # that are guaranteed not to collide with any physical channel.
        self._ev_pix_begin = TimeTagger.EventGenerator(
            self._tt, int(self._line_ch), begin_pattern
        )
        self._ev_pix_end = TimeTagger.EventGenerator(
            self._tt, int(self._line_ch), end_pattern
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

    def _onScanDone(self):
        """Triggered by NidaqManager.sigScanDone — mirrors APD's acqDoneSignal
        path. Flips acquisition off so the worker's polling loop exits and
        captures one final completed frame before terminating.
        """
        self.acquisition = False

    def _on_frame_ready(self, intensity_img, lifetime_img):
        self._image_intensity[0] = intensity_img
        self._image_display[0] = lifetime_img
        self._newFrameReady = True
        self.sigImageUpdated.emit(self._image_display, False, self.scale)
        if hasattr(self, 'updateLatestFrame'):
            self.updateLatestFrame(True)
        self.sigNewFrame.emit()

    # ------------------------------------------------------------------ #
    # DetectorManager abstract method implementations                      #
    # ------------------------------------------------------------------ #

    @property
    def pixelSizeUm(self):
        return [1, *self.__pixel_sizes]

    @property
    def scale(self):
        return list(self.__pixel_sizes[::-1])

    def setPixelSize(self, pixel_sizes: list):
        """pixel_sizes: list from low dim to high dim (matches APDManager)."""
        self.__pixel_sizes = list(pixel_sizes)

    def crop(self, hpos, vpos, hsize, vsize):
        pass

    def getLatestFrame(self, is_save=True):
        if is_save and self._image_raw is not None:
            return self._image_raw
        return self._image_display

    def getChunk(self):
        if not getattr(self, '_newFrameReady', False):
            return np.empty((0, 0))
        self._newFrameReady = False
        return self._image_display.copy()

    def flushBuffers(self):
        pass

    def startAcquisition(self):
        self.acquisition = True
        self._newFrameReady = False

    def stopAcquisition(self):
        self.acquisition = False
        try:
            if getattr(self, '_scanWorker', None) is not None:
                self._scanWorker.stop()
            if getattr(self, '_scanThread', None) is not None:
                self._scanThread.quit()
                self._scanThread.wait()
        except Exception:
            pass
        self._newFrameReady = True

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _infer_dims_from_scanInfo(self, scanInfoDict):
        scan_dims = list(scanInfoDict['img_dims'])
        scan_axes = list(scanInfoDict.get('img_axes_phys', ['x', 'y', 'z'][:len(scan_dims)]))
        S = max(1, int(scanInfoDict.get('n_linesteps', 1)))
        if 'x' in scan_axes and 'y' in scan_axes:
            Nx = int(scan_dims[scan_axes.index('x')])
            Ny = int(scan_dims[scan_axes.index('y')])
        else:
            Nx = int(scan_dims[-1])
            Ny = int(scan_dims[-2])
        outer_axes = [a for a in scan_axes if a not in ('y', 'x')]
        outer_dims = [int(scan_dims[scan_axes.index(a)]) for a in outer_axes]
        return Nx, Ny, S, outer_axes, outer_dims


# --------------------------------------------------------------------------- #
# Lifetime fit helpers — pure numpy, no Qt                                     #
# --------------------------------------------------------------------------- #

def _fit_moment(cube, t_axis):
    """
    Mean photon arrival time (1st moment of the histogram).
    Fastest method. Biased by background and IRF width, but requires no model.
    Returns (intensity, lifetime) both shape (Ny, Nx).
    """
    intensity = cube.sum(axis=2)
    numer = (cube * t_axis[None, None, :]).sum(axis=2)
    lifetime = np.zeros_like(intensity, dtype=np.float32)
    good = intensity > 0
    lifetime[good] = numer[good] / intensity[good]
    return intensity.astype(np.float32), lifetime


def _fit_phasor(cube, binwidth_ps, n_bins):
    """
    Phasor / Fourier method for single-exponential lifetime.
    Estimates the laser repetition period as the full histogram window
    (T_rep = n_bins * binwidth_ps). Returns tau = s / (omega * g) where
    g and s are the cosine and sine projections of the normalised histogram
    onto the first harmonic.

    Same speed as moment. Assumes single-exponential decay; gives the
    phase lifetime which is a useful proxy even for multi-exponential samples.
    Returns (intensity, lifetime) both shape (Ny, Nx).
    """
    intensity = cube.sum(axis=2).astype(np.float32)

    T_rep_s = n_bins * binwidth_ps * 1e-12
    omega = 2.0 * np.pi / T_rep_s
    t_s = (np.arange(n_bins, dtype=np.float64) + 0.5) * binwidth_ps * 1e-12

    h = cube.astype(np.float64) / intensity.clip(1).astype(np.float64)[:, :, None]

    g = (h * np.cos(omega * t_s)[None, None, :]).sum(axis=2)
    s = (h * np.sin(omega * t_s)[None, None, :]).sum(axis=2)

    denom = omega * g
    lifetime = np.where(np.abs(denom) > 1e-30, s / denom, 0.0).astype(np.float32)
    return intensity, lifetime


def _fit_exp1(cube, t_axis):
    """
    Vectorised weighted log-linear single-exponential fit.
    Minimises sum_k w_k * (log h_k - a - b*t_k)^2 with w_k = sqrt(h_k)
    (Poisson weighting). Returns tau = -1/slope from the fitted slope b.

    Slower than moment/phasor but correct for clean mono-exponential decays.
    Returns (intensity, lifetime) both shape (Ny, Nx).
    """
    intensity = cube.sum(axis=2).astype(np.float32)
    h = cube.astype(np.float64)
    t = t_axis.astype(np.float64)[None, None, :]   # (1, 1, n_bins)

    # Weights: sqrt(h), zero where h == 0
    w = np.sqrt(np.where(h > 0, h, 0.0))
    log_h = np.where(h > 0, np.log(h), 0.0)       # log(0) replaced with 0, masked by w

    # Weighted normal equations for [intercept, slope]
    sw   = w.sum(axis=2)
    swt  = (w * t).sum(axis=2)
    swt2 = (w * t ** 2).sum(axis=2)
    swlh  = (w * log_h).sum(axis=2)
    swtlh = (w * t * log_h).sum(axis=2)

    det = sw * swt2 - swt ** 2
    with np.errstate(invalid='ignore', divide='ignore'):
        slope = np.where(np.abs(det) > 1e-30,
                         (sw * swtlh - swt * swlh) / det,
                         0.0)

    lifetime = np.where(slope < 0, (-1.0 / slope).astype(np.float32), 0.0)
    return intensity, lifetime.astype(np.float32)


# --------------------------------------------------------------------------- #
# Background worker                                                            #
# --------------------------------------------------------------------------- #

class _TTFlimWorker(Worker):
    sigFrameReady = Signal(object, object)
    sigFinished = Signal()

    def __init__(self, m: SwabianTimeTaggerManager):
        super().__init__()
        self._logger = initLogger(self, tryInheritParent=True)
        self._m = m
        self._running = True
        self._last_total_counts = 0.0

    def stop(self):
        self._running = False

    def run(self):
        try:
            Nx = int(self._m._scan['Nx'])
            Ny = int(self._m._scan['Ny'])
            n_bins = int(self._m._n_bins)
            binwidth_ps = int(self._m._binwidth_ps)
            # Snapshot fit settings at scan start so mid-scan parameter changes
            # don't corrupt a frame in progress.
            fit_method = str(self._m._fit_method)
            min_counts = int(self._m._min_counts_per_pixel)
            poll_s = 0.05           # live-preview poll interval
            expected_shape = (Nx * Ny, n_bins)
            STALL_MAX = int(10.0 / poll_s)  # 10 s of consecutive bad frames

            t_axis = (np.arange(n_bins, dtype=np.float32) + 0.5) * binwidth_ps * 1e-12
            stall_count = 0
            got_valid_frame = False

            # --- Live polling loop — emits progressive frames for preview.
            # Exits when acquisition flips False (sigScanDone → _onScanDone) or
            # the worker is stopped externally.
            while self._running and getattr(self._m, 'acquisition', True):
                cube = self._poll_frame(expected_shape, Nx, Ny, n_bins)
                if cube is None:
                    stall_count += 1
                    if stall_count >= STALL_MAX:
                        self._logger.error(
                            'TimeTagger: no valid frame for 10 s. '
                            'Check line trigger signal. Stopping worker.'
                        )
                        break
                    time.sleep(poll_s)
                    continue

                stall_count = 0
                got_valid_frame = True
                #self._emit_frame(cube, t_axis, fit_method, binwidth_ps, n_bins, min_counts)
                time.sleep(poll_s)

            # --- Final read after scan completes: captures the completed
            # histogram in full (mirrors APD's d3Step behaviour at scan end).
            if got_valid_frame and self._m._flim is not None:
                final_cube = self._poll_frame(expected_shape, Nx, Ny, n_bins)
                if final_cube is not None:
                    self._emit_frame(final_cube, t_axis, fit_method,
                                     binwidth_ps, n_bins, min_counts)

            if self._last_total_counts == 0.0:
                self._logger.warning(
                    'FLIM scan finished with zero photons in all pixels. '
                    'Flim.getCurrentFrame() returned a shape-correct but empty '
                    'buffer on every poll. Likely causes: '
                    '(1) click_channel does not actually carry photon pulses '
                    '(check trigger_level sign and amplitude), '
                    '(2) line_channel does not fire — EventGenerator only '
                    'emits pixel_begin/pixel_end when its trigger channel '
                    'sees edges, '
                    '(3) wrong channel assignment in config '
                    '(your minimal example has LINECLOCK on ch2, LASERSYNC on ch3 — '
                    'verify click/start/line match your actual wiring).'
                )

        except Exception:
            self._logger.exception('TimeTagger FLIM worker crashed.')
        finally:
            self.sigFinished.emit()

    def _poll_frame(self, expected_shape, Nx, Ny, n_bins):
        """Single non-throwing poll. Returns a (Ny, Nx, n_bins) cube or None."""
        if self._m._flim is None:
            return None
        try:
            h = self._m._flim.getCurrentFrame()
        except Exception:
            self._logger.exception('getCurrentFrame() raised.')
            return None
        if h is None:
            return None
        arr = np.asarray(h, dtype=np.float32)
        if arr.ndim != 2 or arr.shape != expected_shape:
            return None
        return arr.reshape(Ny, Nx, n_bins)

    def _emit_frame(self, cube, t_axis, fit_method, binwidth_ps, n_bins, min_counts):
        if fit_method == 'phasor':
            intensity, lifetime = _fit_phasor(cube, binwidth_ps, n_bins)
        elif fit_method == 'exp1':
            intensity, lifetime = _fit_exp1(cube, t_axis)
        else:
            intensity, lifetime = _fit_moment(cube, t_axis)

        lifetime[intensity < min_counts] = 0.0
        lifetime[~np.isfinite(lifetime)] = 0.0
        lifetime[lifetime < 0] = 0.0

        total = float(intensity.sum())
        self._last_total_counts = total
        self._logger.debug(
            f'FLIM emit: total={int(total)} '
            f'max_pix={int(intensity.max())} '
            f'nonzero_px={int((intensity > 0).sum())}'
        )

        self.sigFrameReady.emit(
            intensity.astype(np.float32),
            lifetime.astype(np.float32),
        )
