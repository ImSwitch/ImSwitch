# ScanControllerLineStepPointScan.py
import copy
import traceback
import configparser
from ast import literal_eval

import numpy as np
from PyQt5.QtCore import QTimer
from imswitch.imcommon.model import APIExport
from ..basecontrollers import SuperScanController

# Optional: only if you want wavelength-based colors like MoNaLISA
from imswitch.imcommon.view.guitools import colorutils
from ...model import SignalDesignerFactory


class ScanControllerAdvanced(SuperScanController):
    """
    Controller for a PointScan-like scan widget with:
      - line-step laser combinations (repeat same line multiple times with different device enables)
      - optional advanced intra-pixel pulse timing per device per linestep
      - TTL preview graph (stationary TTL generation, no scanInfo required)

    Digital parameter dict format (new, no backwards compat):
      target_device: list[str]
      n_linesteps: int
      linestep_enable: dict[str, list[bool]]
      pulse_starts_s: dict[str, list[list[float]]]
      pulse_ends_s: dict[str, list[list[float]]]
      sequence_time: float   # dwell time per pixel (sec)
      advanced_mode: bool
    """


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ---- widget init ----
        # Keep PointScan signature (pos, TTL devices)
        self._widget.initControls(
            self.positioners.keys(),
            self.TTLDevices.keys(),
            "ms"
        )

        # Tell the widget which TTL devices support per-linestep analog power (AO channel present)
        try:
            power_capable = []
            for name, info in getattr(self._setupInfo, "lasers", {}).items():
                ao = getattr(info, "analogChannel", None)
                if ao not in (None, "None"):
                    power_capable.append(name)
            self._widget.setLinestepPowerCapableDevices(power_capable)
        except Exception:
            pass

        # ---- initial state ----
        self.updatePixels()
        self.updateScanStageAttrs()
        self.updateScanTTLAttrs()

        # ---- plotting hooks (optional, depends on your widget) ----
        # If your widget emits these, connect them. If not, ignore.
        for sig_name in ("sigSeqTimeParChanged", "sigSignalParChanged"):
            try:
                getattr(self._widget, sig_name).connect(self.plotSignalGraph)
            except Exception:
                pass
        try:
            self._widget.sigStageParChanged.connect(self.updatePixels)
        except Exception:
            pass

        # Try initial plot
        try:
            self.plotSignalGraph()
        except Exception:
            self._logger.debug("[ScanControllerAdvanced] initial plotSignalGraph failed:\n%s", traceback.format_exc())

        # ---- BeadRec signal bridge (widget → commChannel) ----
        # Mirror the pattern from ScanControllerMoNaLISA so BeadRecController works
        # with the Advanced scan widget without modification.
        try:
            self._widget.sigUpdateBeadRecCenter.connect(
                self._commChannel.sigUpdateBeadRecCenter.emit
            )
        except Exception:
            pass
        try:
            self._widget.sigShowBeadRecCenterCross.connect(
                self._commChannel.sigShowBeadRecCenterCross.emit
            )
        except Exception:
            pass
        try:
            self._widget.sigAutoAxialToggled.connect(
                self._commChannel.sigAutoAxialToggled.emit
            )
        except Exception:
            pass

        # Emit initial (0, 0) bead center so BeadRecController.yCenter/xCenter
        # are non-None from startup.  Without this the crosshair can never appear
        # because updateCenterCrossWidget() guards on `yCenter is not None`.
        # Use singleShot(0) so all other controllers (including BeadRecController)
        # have finished __init__ before we emit.
        QTimer.singleShot(0, lambda: self._commChannel.sigUpdateBeadRecCenter.emit(0, 0))

    # ---------------------------------------------------------------------
    # Internal helpers: designer instances (no ScanManager in this branch)
    # ---------------------------------------------------------------------

    def _get_scan_designer(self):
        if not getattr(self._setupInfo, "scan", None):
            raise RuntimeError("setupInfo.scan is not defined; cannot scan")
        return SignalDesignerFactory(self._setupInfo.scan.scanDesigner)

    def _get_ttl_designer(self):
        if not getattr(self._setupInfo, "scan", None):
            raise RuntimeError("setupInfo.scan is not defined; cannot scan")
        return SignalDesignerFactory(self._setupInfo.scan.TTLCycleDesigner)

    def _make_full_scan(self, scanParameters, TTLParameters):
        """
        Constructs the full scan from scan parameters using the set parameters in the ScanWidgetAdvanced
        Returns:
          signalDict = {'scanSignalsDict': ..., 'TTLCycleSignalsDict': ...}
          scanInfoDict
        """
        scan_des = self._get_scan_designer()
        ttl_des = self._get_ttl_designer()

        # --- stage / analog ---
        stage_param = copy.deepcopy(getattr(self._setupInfo.scan, "scanDesignerParams", {}))
        stage_param.update(scanParameters)
        stage_param["n_linesteps"] = int(TTLParameters.get("n_linesteps", 1))

        # optional guard (like PointScan)
        if hasattr(scan_des, "checkSignalLength"):
            if not scan_des.checkSignalLength(scanParameters, self._setupInfo):
                self._logger.error(
                    "Signal too long: try scanning a smaller ROI, faster, or with a larger pixel size."
                )
                return None, None

        scanSignalsDict, positions, scanInfoDict = scan_des.make_signal(stage_param, self._setupInfo)

        # --- TTL / digital ---
        ttl_param = copy.deepcopy(getattr(self._setupInfo.scan, "TTLCycleDesignerParams", {}))
        ttl_param.update(TTLParameters)

        TTLCycleSignalsDict, scanInfoDict = ttl_des.make_signal(ttl_param, self._setupInfo, scanInfoDict)

        # ----------------------------
        # Normalize scanInfo for Advanced TTL (axis roles + line period model)
        # ----------------------------

        try:
            S = int(stage_param.get("n_linesteps", TTLParameters.get("n_linesteps", 1)))
            S = max(1, S)

            img_dims = list(scanInfoDict.get("img_dims", []))              # physical dims from scan designer
            scan_samples = list(scanInfoDict.get("scan_samples", []))      # [samples_per_pixel, line_len, d3_len, ...]

            # Fast axis is always "axis 0" in the scan designer ordering (whatever the user picked)
            n_pixels_fast = int(img_dims[0]) if len(img_dims) > 0 else 1
            samples_per_pixel = int(scan_samples[0]) if len(scan_samples) > 0 else 0

            # The active acquisition part of one fast sweep ("line")
            line_active_len = int(scan_samples[1]) if len(scan_samples) > 1 else int(n_pixels_fast * max(1, samples_per_pixel))

            if samples_per_pixel <= 0 and n_pixels_fast > 0:
                if line_active_len % n_pixels_fast == 0:
                    samples_per_pixel = line_active_len // n_pixels_fast

            # How many physical "lines" exist? (if only 1D, it's 1)
            n_lines_phys = int(img_dims[1]) if len(img_dims) > 1 else 1

            # Effective number of repeated line periods when linesteps are enabled
            n_line_periods_total = n_lines_phys * S

            # Period length (active + flyback). For 1D scans GalvoScanDesigner still provides scan_samples_d2_period.
            line_period_len = int(scanInfoDict.get("scan_samples_d2_period", 0)) or line_active_len
            flyback_len = max(0, line_period_len - line_active_len)

            # d3 length may not exist for 1D scans -> compute expected core length
            expected_d3_core = (n_line_periods_total - 1) * line_period_len + line_active_len

            scanInfoDict["advanced_scan"] = {
                "n_linesteps": S,
                "fast_axis_idx": 0,
                "line_axis_phys_idx": 1 if len(img_dims) > 1 else None,   # None means "virtual line axis = linesteps only"
                "n_pixels_fast": n_pixels_fast,
                "samples_per_pixel": samples_per_pixel,
                "line_active_len": line_active_len,
                "line_period_len": line_period_len,
                "flyback_len": flyback_len,
                "n_lines_phys": n_lines_phys,
                "n_line_periods_total": n_line_periods_total,
                "expected_d3_core_len": expected_d3_core,
            }

            # keep the keys your TTL designer already looks for (backwards compatibility)
            scanInfoDict["n_pixels_fast"] = n_pixels_fast
            scanInfoDict["samples_per_pixel"] = samples_per_pixel

        except Exception:
            self._logger.debug("[ScanControllerAdvanced] scanInfo normalization failed:\n%s", traceback.format_exc())



        # Inject per-linestep analog power waveforms for AO-capable lasers (constant within each line)
        if TTLParameters.get("advanced_mode", False):
            try:
                self._inject_linestep_power_ao(
                    scanSignalsDict, TTLCycleSignalsDict, scanInfoDict, TTLParameters
                )
            except Exception:
                self._logger.debug(
                    "[ScanControllerAdvanced] inject linestep power failed:\n%s",
                    traceback.format_exc()
                )


        signalDict = {
            "scanSignalsDict": scanSignalsDict,
            "TTLCycleSignalsDict": TTLCycleSignalsDict,
        }

        # Guarantee a complete standard contract for downstream consumers (e.g. APDManager),
        # regardless of which scan designer was used.
        self._finalize_scanInfoDict(scanInfoDict)

        self._lastScanInfoDict = scanInfoDict
        self._lastSignalDict = signalDict
        self._lastTTLCycleSignalsDict = signalDict.get("TTLCycleSignalsDict", None)
        self._lastTTLParameters = copy.deepcopy(TTLParameters)

        return signalDict, scanInfoDict

    def _finalize_scanInfoDict(self, scanInfoDict: dict) -> None:
        """
        Fill any missing standard scanInfoDict keys with safe defaults.

        Ensures APDManager.ScanWorker (and other consumers) work correctly
        regardless of which scan designer produced the dict. GalvoScanDesigner
        already provides all keys; BetaScanDesigner and future designers may not.
        """
        defaults = {
            'phase_delay': 0,
            'smooth_axes': [False, False, False],
            'scan_throw_startzero': 0,
            'scan_throw_settling': 0,
            'scan_throw_startacc': 0,
            'scan_pads_initpos': [],
        }
        for key, val in defaults.items():
            scanInfoDict.setdefault(key, val)

    # ---------------------------------------------------------------------
    # BeadRec interface (mirrors ScanControllerMoNaLISA)
    # ---------------------------------------------------------------------

    def getDimsScan(self):
        """Return (x, y, z) pixel counts for each scan axis (0 if axis not active)."""
        self.getParameters()
        lengths = self._analogParameterDict.get('axis_length', [])
        stepSizes = self._analogParameterDict.get('axis_step_size', [])
        dims = []
        for i in range(min(3, len(lengths))):
            step = stepSizes[i] if i < len(stepSizes) else 0
            dims.append(int(lengths[i] / step) if step != 0 else 0)
        # pad to 3 elements
        while len(dims) < 3:
            dims.append(0)
        return tuple(dims[:3])

    def getScanStepSizes(self):
        """Return step sizes for the first 3 scan axes (matching getDimsScan() length).

        BeadRecController indexes into this list with a boolean mask derived from
        getDimsScan(), so both methods must return the same number of elements (3).
        Virtual axes beyond index 2 (e.g. timelapse, repeat) are excluded.
        """
        stepSizes = self._analogParameterDict.get('axis_step_size', [])
        result = list(stepSizes[:3])
        while len(result) < 3:
            result.append(0.0)
        return result

    # ---------------------------------------------------------------------
    # Parameters: UI -> dicts
    # ---------------------------------------------------------------------

    def getParameters(self):
        """
        Populates:
          self._analogParameterDict
          self._digitalParameterDict
        from widget state.

        Analog format kept compatible with GalvoScanDesigner expectedParameters.
        Digital format expected by AdvancedScanTTLCycleDesigner.
        """
        if getattr(self, "settingParameters", False):
            return

        # -------------------------
        # Analog (PointScan-style)
        # -------------------------
        self._analogParameterDict["target_device"] = []
        self._analogParameterDict["axis_length"] = []
        self._analogParameterDict["axis_step_size"] = []
        self._analogParameterDict["axis_centerpos"] = []
        self._analogParameterDict["axis_startpos"] = []

        # Keep scan dim selection like PointScan
        self._positionersScan = []
        for i in range(len(self.positioners)):
            self._positionersScan.append(self._widget.getScanDim(i))
        self._analogParameterDict["scan_dim_target_device"] = list(self._positionersScan)

        for positionerName in self._positionersScan:
            if positionerName == "None":
                continue

            size = self._widget.getScanSize(positionerName)
            stepSize = self._widget.getScanStepSize(positionerName)
            center = self._widget.getScanCenterPos(positionerName)

            # startpos from current hardware
            start = [center]

            self._analogParameterDict["target_device"].append(positionerName)
            self._analogParameterDict["axis_length"].append(size)
            self._analogParameterDict["axis_step_size"].append(stepSize)
            self._analogParameterDict["axis_centerpos"].append(center)
            self._analogParameterDict["axis_startpos"].append(start)

        # Add non-scan axes as dummy (keeps older scan designers happy)
        for positionerName in self.positioners:
            if positionerName not in self._positionersScan:
                center = self._widget.getScanCenterPos(positionerName)
                self._analogParameterDict["target_device"].append(positionerName)
                self._analogParameterDict["axis_length"].append(1.0)
                self._analogParameterDict["axis_step_size"].append(1.0)
                self._analogParameterDict["axis_centerpos"].append(center)
                self._analogParameterDict["axis_startpos"].append([center])

        # timing
        seq_time = self._widget.getSeqTimePar()
        self._analogParameterDict["sequence_time"] = seq_time
        try:
            self._analogParameterDict["phase_delay"] = self._widget.getPhaseDelayPar()
        except Exception:
            self._analogParameterDict["phase_delay"] = 0
        try:
            self._analogParameterDict["d3step_delay"] = self._widget.getd3StepDelayPar()
        except Exception:
            self._analogParameterDict["d3step_delay"] = 0

        def _pixels_for(dev_name: str) -> int:
            if dev_name is None or dev_name == "None":
                return 1
            try:
                idx = self._analogParameterDict["target_device"].index(dev_name)
            except ValueError:
                return 1
            step = float(self._analogParameterDict["axis_step_size"][idx])
            if step == 0:
                return 1
            length = float(self._analogParameterDict["axis_length"][idx])
            return max(1, int(round(length / step)))

        x_dev = self._widget.getScanDim(0)
        y_dev = self._widget.getScanDim(1)

        Nx = _pixels_for(x_dev)
        Ny = _pixels_for(y_dev)

        # -------------------------
        # Digital (advanced schema)
        # -------------------------
        try:
            S = int(self._widget.getNumLineSteps())
        except Exception:
            S = 1

        try:
            advanced_mode = bool(self._widget.isAdvancedTTLMode())
        except Exception:
            advanced_mode = False

        included_devices = []
        linestep_enable = {}
        pulse_starts_s = {}
        pulse_ends_s = {}

        for deviceName in self.TTLDevices.keys():
            # IMPORTANT:
            # linestep_enable must be length S (per linestep), NOT Ny*S.
            # The TTL designer (and scanInfoDict) currently operate with img_dims[1] = Ny (not expanded),
            # and the designer maps expanded_line_idx -> s via (idx % S).
            try:
                enable_vec = [bool(self._widget.getLineStepEnabled(deviceName, s)) for s in range(S)]
            except Exception:
                enable_vec = [bool(self._widget.getTTLIncluded(deviceName))] + [False] * (S - 1)

            starts_steps = [[] for _ in range(S)]
            ends_steps = [[] for _ in range(S)]

            if advanced_mode:
                for s in range(S):
                    try:
                        segments = self._widget.getPulseSegmentsOrFull(deviceName, s)
                        if segments is None:
                            starts_steps[s] = []
                            ends_steps[s] = []
                        else:
                            starts_steps[s] = [t0 for t0, _ in segments]
                            ends_steps[s] = [t1 for _, t1 in segments]
                    except Exception:
                        starts_steps[s] = []
                        ends_steps[s] = []

            # Include device if any step enabled OR any pulses specified
            any_pulses = any(len(starts_steps[s]) or len(ends_steps[s]) for s in range(S))
            if any(enable_vec) or any_pulses:
                included_devices.append(deviceName)
                linestep_enable[deviceName] = enable_vec
                pulse_starts_s[deviceName] = starts_steps
                pulse_ends_s[deviceName] = ends_steps

        # Per-device per-linestep power (%) for AO-capable lasers
        linestep_power_percent = {}
        for deviceName in self.TTLDevices.keys():
            try:
                vec = [float(self._widget.getLineStepPowerPercent(deviceName, s)) for s in range(S)]
                vec = [max(0.0, min(100.0, v)) for v in vec]
                linestep_power_percent[deviceName] = vec
            except Exception:
                pass

        self._digitalParameterDict = {
            "target_device": included_devices,
            "n_linesteps": S,
            "Nx": Nx,
            "Ny": Ny,
            "linestep_enable": linestep_enable,
            "pulse_starts_s": pulse_starts_s,
            "pulse_ends_s": pulse_ends_s,
            "sequence_time": seq_time,
            "advanced_mode": advanced_mode,
            "linestep_power_percent": linestep_power_percent,
        }

    # ---------------------------------------------------------------------
    # Parameters: dicts -> UI (used by loadScan)
    # ---------------------------------------------------------------------

    def setParameters(self):
        self.settingParameters = True
        try:
            # --- analog back into widget (like PointScan) ---
            for i in range(len(self._analogParameterDict.get("target_device", []))):
                positionerName = self._analogParameterDict["target_device"][i]
                if positionerName == "None":
                    continue
                try:
                    self._widget.setScanSize(positionerName, self._analogParameterDict["axis_length"][i])
                    self._widget.setScanStepSize(positionerName, self._analogParameterDict["axis_step_size"][i])
                    self._widget.setScanCenterPos(positionerName, self._analogParameterDict["axis_centerpos"][i])
                except Exception:
                    pass

            for i, scanDimName in enumerate(self._analogParameterDict.get("scan_dim_target_device", [])):
                try:
                    self._widget.setScanDim(i, scanDimName)
                except Exception:
                    pass

            # timing
            if "sequence_time" in self._digitalParameterDict:
                try:
                    self._widget.setSeqTimePar(self._digitalParameterDict["sequence_time"])
                except Exception:
                    pass
            dig = self._digitalParameterDict or {}

            try:
                self._widget.setAdvancedTTLMode(bool(dig.get("advanced_mode", False)))
            except Exception:
                pass

            try:
                self._widget.setNumLineSteps(int(dig.get("n_linesteps", 1)))
            except Exception:
                pass

            S = int(dig.get("n_linesteps", 1))
            linestep_enable = dig.get("linestep_enable", {}) or {}
            pulse_starts_s = dig.get("pulse_starts_s", {}) or {}
            pulse_ends_s = dig.get("pulse_ends_s", {}) or {}

            linestep_power_percent = dig.get("linestep_power_percent", {}) or {}
            for dev, vec in linestep_power_percent.items():
                try:
                    for s in range(min(S, len(vec))):
                        self._widget.setLineStepPowerPercent(dev, s, float(vec[s]))
                except Exception:
                    pass

            for dev in self.TTLDevices.keys():
                enable_vec = linestep_enable.get(dev, None)
                if enable_vec is not None:
                    for s in range(min(S, len(enable_vec))):
                        try:
                            self._widget.setLineStepEnabled(dev, s, bool(enable_vec[s]))
                        except Exception:
                            pass

                # pulses only matter if advanced_mode, but restoring them always is fine
                starts_steps = pulse_starts_s.get(dev, None)
                ends_steps = pulse_ends_s.get(dev, None)
                if starts_steps is not None and ends_steps is not None:
                    for s in range(min(S, len(starts_steps), len(ends_steps))):
                        try:
                            self._widget.setPulseTimes(dev, s, starts_steps[s], ends_steps[s])
                        except Exception:
                            pass

            # ensure the advanced panel reflects the stored model
            try:
                self._widget._syncPulseEditsFromModel()
            except Exception:
                pass
        finally:
            self.settingParameters = False
            try:
                self.updatePixels()
                self.plotSignalGraph()
            except Exception:
                self._logger.debug("[ScanControllerAdvanced] setParameters follow-up failed:\n%s", traceback.format_exc())

    # ---------------------------------------------------------------------
    # Scan run
    # ---------------------------------------------------------------------

    def runScanAdvanced(
        self,
        *,
        recalculateSignals=True,
        isNonFinalPartOfSequence=False,
        sigScanStartingEmitted=False,
    ):
        """Runs a scan with current parameters."""
        try:
            self._widget.setScanButtonChecked(True)
            self.isRunning = True

            if recalculateSignals or self.signalDict is None or self.scanInfoDict is None:
                self.getParameters()
                sm = getattr(self._master, "scanManager", None)
                if False:#sm is not None:
                    out = sm.makeFullScan(self._analogParameterDict, self._digitalParameterDict, staticPositioner=False)
                    if out is None:
                        self.isRunning = False
                        self.abortScan()
                        return
                    self.signalDict, self.scanInfoDict = out
                else:
                    self.signalDict, self.scanInfoDict = self._make_full_scan(
                        self._analogParameterDict, self._digitalParameterDict
                    )

                if self.signalDict is None:
                    self.isRunning = False
                    self.abortScan()
                    return

            self.doingNonFinalPartOfSequence = isNonFinalPartOfSequence

            if not sigScanStartingEmitted:
                self.emitScanSignal(self._commChannel.sigScanStarting)

            # Set non-scanned positioners to center (same behavior as your PointScan controller)
            for index, positionerName in enumerate(self._analogParameterDict["target_device"]):
                if positionerName not in self._positionersScan:
                    try:
                        position = self._analogParameterDict["axis_centerpos"][index]
                        self._master.positionersManager[positionerName].setPosition(position, 0)
                    except Exception:
                        pass

            self._master.nidaqManager.runScan(self.signalDict, self.scanInfoDict)

        except Exception:
            self._logger.error(traceback.format_exc())
            self.isRunning = False
            self.abortScan()

    def scanDone(self):
        """Called by the system when nidaq finishes."""
        self.isRunning = False

        if not self._widget.repeatEnabled():
            self.emitScanSignal(self._commChannel.sigScanDone)
            if not getattr(self, "doingNonFinalPartOfSequence", False):
                self._widget.setScanButtonChecked(False)
                self.emitScanSignal(self._commChannel.sigScanEnded)

            # Optional special-case reset like your PointScan example
            try:
                for index, positionerName in enumerate(self._analogParameterDict["target_device"]):
                    if positionerName == "ND-PiezoZ":
                        position = self._analogParameterDict["axis_centerpos"][index]
                        self._master.positionersManager[positionerName].setPosition(position, 0)
            except Exception:
                pass
        else:
            self.runScanAdvanced(sigScanStartingEmitted=True)

    def emitScanSignal(self, signal, *args):
        signal.emit(*args)

    # ---------------------------------------------------------------------
    # Pixel counting
    # ---------------------------------------------------------------------

    def updatePixels(self):
        self.getParameters()
        try:
            for index, positionerName in enumerate(self._analogParameterDict["target_device"]):
                step = float(self._analogParameterDict["axis_step_size"][index])
                if step != 0:
                    length = float(self._analogParameterDict["axis_length"][index])
                    pixels = round(length / step)
                    self._widget.setScanPixels(positionerName, pixels)
        except Exception:
            pass

    # ---------------------------------------------------------------------
    # TTL preview plotting
    # ---------------------------------------------------------------------

    def plotSignalGraph(self):
        """
        Preview plots for Advanced widget:
          - graph_steps: scatter of enabled linesteps per device (length S)
          - graph_pixel: per-pixel TTL program constructed inside widget from pulse model
        """
        if getattr(self, "settingParameters", False):
            return

        try:
            self.getParameters()

            if not getattr(self._setupInfo, "scan", None):
                return

            sampleRate = self._setupInfo.scan.sampleRate

            # device order = stable order of TTLDevices
            labels = list(self.TTLDevices.keys())

            # number of linesteps (S)
            try:
                S = int(self._widget.getNumLineSteps())
            except Exception:
                S = int(self._digitalParameterDict.get("n_linesteps", 1))

            # build per-device enable vectors (length S)
            signals = []
            for dev in labels:
                try:
                    enable_vec = [bool(self._widget.getLineStepEnabled(dev, s)) for s in range(S)]
                except Exception:
                    enable_vec = [bool(self._widget.getTTLIncluded(dev))] + [False] * (S - 1)
                signals.append(np.asarray(enable_vec, dtype=bool))

            # colors (lasers get wavelength color, others white)
            colors = []
            for dev in labels:
                isLaser = dev in getattr(self._setupInfo, "lasers", {})
                colors.append(
                    colorutils.wavelengthToHex(self._setupInfo.lasers[dev].wavelength, gamma=6.0)
                    if isLaser else "#ffffff"
                )

            # Let the widget render BOTH plots:
            #  - graph_steps uses "signals" (length S)
            #  - graph_pixel uses the pulse editor / UI state internally
            self._widget.plotSignalGraph(signals, colors, sampleRate, labels=labels)

        except Exception:
            self._logger.debug(
                "[ScanControllerAdvanced] plotSignalGraph failed:\n%s",
                traceback.format_exc(),
            )

    def _inject_linestep_power_ao(self, scanSignalsDict, TTLCycleSignalsDict, scanInfoDict, TTLParameters):
        """
        Create AO waveforms for AO-capable lasers:
        - constant voltage during each line's active part
        - line index -> linestep index via (line_idx % S)
        - aligned using the generated line_clock (most robust across axis configs)
        """
        powers = (TTLParameters or {}).get("linestep_power_percent", {}) or {}
        if not powers:
            return

        S = int((TTLParameters or {}).get("n_linesteps", 1))
        S = max(1, S)

        total = int(scanInfoDict.get("scan_samples_total", 0))
        if total <= 0:
            return

        # line geometry from scanInfo
        scan_samples = scanInfoDict.get("scan_samples", None)
        if not isinstance(scan_samples, (list, tuple)) or len(scan_samples) < 2:
            return

        line_len = int(scan_samples[1])
        period_len = int(scanInfoDict.get("scan_samples_d2_period", 0)) or line_len
        flyback = max(0, period_len - line_len)

        # Use line_clock to find line starts (best alignment)
        line_clock = TTLCycleSignalsDict.get("line_clock", None)
        if line_clock is None:
            # fallback: assume starts every period_len from 0
            line_starts = np.arange(0, total, period_len, dtype=int)
        else:
            lc = np.asarray(line_clock, dtype=bool)
            # rising edges mark new line
            rises = np.flatnonzero(np.logical_and(lc[1:], ~lc[:-1])) + 1
            # if clock starts high at index 0
            if lc.size and lc[0]:
                rises = np.concatenate(([0], rises))
            line_starts = rises.astype(int)

        for laserName, vec in powers.items():
            laserInfo = getattr(self._setupInfo, "lasers", {}).get(laserName, None)
            if laserInfo is None:
                continue

            ao_chan = getattr(laserInfo, "analogChannel", None)
            if ao_chan in (None, "None"):
                continue

            vec = list(vec) if vec is not None else [100.0] * S
            if len(vec) < S:
                vec = vec + [vec[-1] if vec else 100.0] * (S - len(vec))
            vec = [max(0.0, min(100.0, float(v))) for v in vec[:S]]

            vmin = float(getattr(laserInfo, "valueRangeMin", 0.0))
            vmax = float(getattr(laserInfo, "valueRangeMax", 10.0))

            ao = np.zeros(total, dtype=np.float64)

            for line_idx, i0 in enumerate(line_starts):
                s = line_idx % S
                pct = vec[s]
                volts = vmin + (pct / 100.0) * (vmax - vmin)

                j0 = int(i0)
                j1 = min(total, j0 + line_len)
                if j1 > j0:
                    ao[j0:j1] = volts
                # flyback remains 0 by default

            # Mask by TTL if present (keeps AO at 0 when laser is off)
            mask = TTLCycleSignalsDict.get(laserName, None)
            if mask is not None:
                ao *= np.asarray(mask, dtype=np.float64)

            scanSignalsDict[laserName] = ao

    # ---------------------------------------------------------------------
    # Save / Load
    # ---------------------------------------------------------------------

    def saveScanParamsToFile(self, filePath: str) -> None:
        self.getParameters()
        config = configparser.ConfigParser()
        config.optionxform = str

        config["analogParameterDict"] = self._analogParameterDict
        config["digitalParameterDict"] = self._digitalParameterDict

        with open(filePath, "w") as f:
            config.write(f)

    @APIExport(runOnUIThread=True)
    def loadScanParamsFromFile(self, filePath: str) -> None:
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(filePath)

        for key in self._analogParameterDict:
            if key in config._sections.get("analogParameterDict", {}):
                self._analogParameterDict[key] = literal_eval(config._sections["analogParameterDict"][key])

        # digital dict might not have all keys pre-defined
        self._digitalParameterDict = {}
        for key, val in config._sections.get("digitalParameterDict", {}).items():
            self._digitalParameterDict[key] = literal_eval(val)

        self.setParameters()


    @APIExport(runOnUIThread=True)
    def changeScanCenterPos(self, positionerName, positionerScanCenterPos):
        self._widget.setScanCenterPos(positionerName, positionerScanCenterPos)

    @APIExport(runOnUIThread=True)
    def changeScanSize(self, positioner: str, size: float):
        self._widget.setScanSize(positioner, size)
