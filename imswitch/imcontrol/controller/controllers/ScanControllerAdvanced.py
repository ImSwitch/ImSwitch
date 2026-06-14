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

      Optional intra-pixel positioner movement fields:
      intra_pixel_positioner_movement: bool
      positioner_target_device: list[str]
      positioner_linestep_enable: dict[str, list[bool]]
      positioner_movement_starts_s: dict[str, list[list[float]]]
      positioner_movement_ends_s: dict[str, list[list[float]]]
      positioner_step_size_um: dict[str, list[list[float]]]
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
            self._logger.debug("Could not detect power-capable devices:\n%s", traceback.format_exc())

        # ---- initial state ----
        self.updatePixels()
        self.updateScanStageAttrs()
        self.updateScanTTLAttrs()

        # ---- plotting hooks (optional, depends on your widget) ----
        for sig_name in ("sigSeqTimeParChanged", "sigSignalParChanged"):
            sig = getattr(self._widget, sig_name, None)
            if sig is not None:
                sig.connect(self.plotSignalGraph)
        if hasattr(self._widget, 'sigStageParChanged'):
            self._widget.sigStageParChanged.connect(self.updatePixels)
        if hasattr(self._widget, "sigPlotScanClicked"):
            self._widget.sigPlotScanClicked.connect(self.plotScanCurves)

        # Try initial plot
        try:
            self.plotSignalGraph()
        except Exception:
            self._logger.debug("[ScanControllerAdvanced] initial plotSignalGraph failed:\n%s", traceback.format_exc())

        # ---- BeadRec signal bridge (widget → commChannel) ----
        for widget_sig, comm_sig in [
            ("sigUpdateBeadRecCenter", "sigUpdateBeadRecCenter"),
            ("sigShowBeadRecCenterCross", "sigShowBeadRecCenterCross"),
            ("sigAutoAxialToggled", "sigAutoAxialToggled"),
        ]:
            src = getattr(self._widget, widget_sig, None)
            dst = getattr(self._commChannel, comm_sig, None)
            if src is not None and dst is not None:
                src.connect(dst.emit)

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
        self._copy_positioner_line_program_to_stage_params(stage_param, TTLParameters)

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
        ttl_param.update(self._ttl_parameters_without_positioners(TTLParameters))

        TTLCycleSignalsDict, scanInfoDict = ttl_des.make_signal(ttl_param, self._setupInfo, scanInfoDict)

        # scanInfoDict is already a complete ScanInfoContract dict from the scan designer.
        # No normalization or finalization needed.

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

        self._lastScanInfoDict = scanInfoDict
        self._lastSignalDict = signalDict
        self._lastTTLCycleSignalsDict = signalDict.get("TTLCycleSignalsDict", None)
        self._lastTTLParameters = copy.deepcopy(TTLParameters)

        return signalDict, scanInfoDict

    def _copy_positioner_line_program_to_stage_params(self, stage_param, TTLParameters):
        """Forward intra-pixel positioner program metadata to the scan designer."""
        for key in (
            "intra_pixel_positioner_movement",
            "positioner_target_device",
            "positioner_linestep_enable",
            "positioner_movement_starts_s",
            "positioner_movement_ends_s",
            "positioner_step_size_um",
        ):
            if key in (TTLParameters or {}):
                stage_param[key] = copy.deepcopy(TTLParameters[key])

    def _ttl_parameters_without_positioners(self, TTLParameters):
        """Keep scanning positioners out of the TTL designer target list."""
        out = copy.deepcopy(TTLParameters or {})
        ttl_device_names = set(self.TTLDevices.keys())
        targets = list(out.get("target_device", []) or [])
        filtered_targets = [dev for dev in targets if dev in ttl_device_names]
        out["target_device"] = filtered_targets

        for dict_key in (
            "linestep_enable",
            "pulse_starts_s",
            "pulse_ends_s",
            "linestep_power_percent",
        ):
            values = out.get(dict_key, None)
            if isinstance(values, dict):
                out[dict_key] = {
                    dev: value for dev, value in values.items()
                    if dev in ttl_device_names
                }

        return out

    def _make_scan_only(self, scanParameters, TTLParameters):
        scan_des = self._get_scan_designer()
        stage_param = copy.deepcopy(getattr(self._setupInfo.scan, "scanDesignerParams", {}))
        stage_param.update(scanParameters)
        stage_param["n_linesteps"] = int((TTLParameters or {}).get("n_linesteps", 1))
        self._copy_positioner_line_program_to_stage_params(stage_param, TTLParameters)
        return scan_des.make_signal(stage_param, self._setupInfo)

    def plotScanCurves(self):
        """Build and plot only analog scan curves for debugging."""
        try:
            if getattr(self, "settingParameters", False):
                return

            self.getParameters()
            include_ttl = False
            try:
                include_ttl = bool(self._widget.isPlotTTLIncluded())
            except Exception:
                include_ttl = False

            ttlSignalsDict = None
            if include_ttl:
                signalDict, scanInfoDict = self._make_full_scan(
                    self._analogParameterDict, self._digitalParameterDict
                )
                if signalDict is None:
                    return
                scanSignalsDict = signalDict.get("scanSignalsDict", {})
                ttlSignalsDict = signalDict.get("TTLCycleSignalsDict", {})
            else:
                scanSignalsDict, _, scanInfoDict = self._make_scan_only(
                    self._analogParameterDict, self._digitalParameterDict
                )
            if not scanSignalsDict:
                self._logger.warning("No scan curves to plot")
                return

            ordered_devices = [
                dev for dev in self._analogParameterDict.get("scan_dim_target_device", [])
                if dev != "None" and dev in scanSignalsDict
            ]
            if not ordered_devices:
                ordered_devices = [
                    dev for dev in self._analogParameterDict.get("target_device", [])
                    if dev in scanSignalsDict
                ]
            if not ordered_devices:
                self._logger.warning("No active scan axes to plot")
                return

            import matplotlib.pyplot as plt

            n_axes = len(ordered_devices)
            fig, axes = plt.subplots(
                n_axes,
                1,
                sharex=True,
                squeeze=False,
                figsize=(12, max(3, 2.2 * n_axes)),
            )
            axes = axes[:, 0]

            sample_rate = float(getattr(self._setupInfo.scan, "sampleRate", 1.0))
            ttl_handles = []
            ttl_labels = []
            for ax, dev in zip(axes, ordered_devices):
                signal = np.asarray(scanSignalsDict[dev], dtype=float)
                t_s = np.arange(signal.size) / sample_rate
                ax.plot(t_s, signal, color="black", linewidth=0.8, label=dev)
                ax.set_ylabel(dev)
                ax.grid(True, alpha=0.25)

                if include_ttl and ttlSignalsDict:
                    handles, labels = self._plot_ttl_overlay_on_axis(
                        ax, ttlSignalsDict, sample_rate, signal.size, signal
                    )
                    if not ttl_handles:
                        ttl_handles = handles
                        ttl_labels = labels

            axes[-1].set_xlabel("Time (s)")
            if ttl_handles:
                fig.legend(
                    ttl_handles,
                    ttl_labels,
                    loc="upper right",
                    bbox_to_anchor=(0.99, 0.99),
                    fontsize="small",
                )
            fig.suptitle("Scan Curves" + (" + TTL" if include_ttl else ""))
            fig.tight_layout()
            try:
                fig.canvas.manager.set_window_title("ImSwitch Scan Curves")
            except Exception:
                pass
            plt.show(block=False)

            self._lastPlottedScanInfoDict = scanInfoDict
            self._lastPlottedScanSignalsDict = scanSignalsDict
            self._lastPlottedTTLCycleSignalsDict = ttlSignalsDict
        except Exception:
            self._logger.error("[ScanControllerAdvanced] plotScanCurves failed:\n%s", traceback.format_exc())

    def _plot_ttl_overlay_on_axis(self, ax, ttlSignalsDict, sample_rate, max_samples, scan_signal):
        """Overlay full-scan TTL traces from the scan curve start level."""
        ttl_devices = [
            dev for dev in self.TTLDevices.keys()
            if dev in (ttlSignalsDict or {})
        ]
        active_targets = set(self._digitalParameterDict.get("target_device", []) or [])
        if active_targets:
            ttl_devices = [dev for dev in ttl_devices if dev in active_targets]

        handles = []
        labels = []

        ymin, ymax = ax.get_ylim()
        if ymin == ymax:
            ymin -= 0.5
            ymax += 0.5
        yrange = ymax - ymin
        scan_signal = np.asarray(scan_signal, dtype=float)
        ttl_low = float(scan_signal[0]) if scan_signal.size else ymin
        ttl_high = ttl_low + (yrange / 3.0)

        for dev in ttl_devices:
            signal = np.asarray(ttlSignalsDict[dev], dtype=float)
            n = min(int(max_samples), signal.size)
            if n <= 0:
                continue

            t_s = np.arange(n) / sample_rate
            y = np.where(signal[:n] > 0, ttl_high, ttl_low)
            line, = ax.step(
                t_s,
                y,
                where="post",
                linewidth=0.9,
                alpha=0.85,
                color=self._ttl_plot_color(dev),
                label=dev,
            )
            handles.append(line)
            labels.append(dev)

        ax.set_ylim(min(ymin, ttl_low), max(ymax, ttl_high))

        return handles, labels

    def _ttl_plot_color(self, deviceName):
        try:
            if deviceName in getattr(self._setupInfo, "lasers", {}):
                return colorutils.wavelengthToHex(
                    self._setupInfo.lasers[deviceName].wavelength,
                    gamma=6.0,
                )
        except Exception:
            pass

        lowered = str(deviceName).lower()
        if "camera" in lowered or "cam" in lowered:
            return "#864f1c"
        return "#4dabf7"

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
            self._widget.commitAdvancedProgramEdits()
        except Exception:
            pass

        try:
            S = int(self._widget.getNumLineSteps())
        except Exception:
            S = 1

        try:
            advanced_mode = bool(self._widget.isAdvancedTTLMode())
        except Exception:
            advanced_mode = False
        try:
            advanced_program_mode = self._widget.getAdvancedProgramMode()
        except Exception:
            advanced_program_mode = "timing"
        sequence_mode = advanced_mode and advanced_program_mode == "sequence"

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

                    if sequence_mode and starts_steps[s] and ends_steps[s]:
                        enable_vec[s] = True

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

        # Intra-pixel positioner movement metadata. These fields travel with the
        # digital/advanced line program UI, but are consumed by the scan designer.
        try:
            intra_pixel_positioner_movement = bool(self._widget.isIntraPixelPositionersMode())
        except Exception:
            intra_pixel_positioner_movement = False

        positioner_target_device = []
        positioner_linestep_enable = {}
        positioner_movement_starts_s = {}
        positioner_movement_ends_s = {}
        positioner_step_size_um = {}

        if advanced_mode and intra_pixel_positioner_movement:
            for positionerName in self.positioners.keys():
                starts_steps = [[] for _ in range(S)]
                ends_steps = [[] for _ in range(S)]
                step_sizes = [[] for _ in range(S)]
                enable_vec = [False for _ in range(S)]

                for s in range(S):
                    try:
                        starts_steps[s] = list(self._widget.getPulseStarts(positionerName, s) or [])
                    except Exception:
                        starts_steps[s] = []

                    try:
                        ends_steps[s] = list(self._widget.getPulseEnds(positionerName, s) or [])
                    except Exception:
                        ends_steps[s] = []

                    try:
                        step_sizes[s] = list(self._widget.getLineStepPositionerStepUm(positionerName, s) or [])
                    except Exception:
                        step_sizes[s] = []

                    # The upper line-step matrix intentionally does not expose
                    # positioner rows; an explicit movement interval is the enable.
                    enable_vec[s] = bool(starts_steps[s] and ends_steps[s])

                if any(enable_vec):
                    positioner_target_device.append(positionerName)
                    positioner_linestep_enable[positionerName] = enable_vec
                    positioner_movement_starts_s[positionerName] = starts_steps
                    positioner_movement_ends_s[positionerName] = ends_steps
                    positioner_step_size_um[positionerName] = step_sizes

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
            "intra_pixel_positioner_movement": intra_pixel_positioner_movement,
            "positioner_target_device": positioner_target_device,
            "positioner_linestep_enable": positioner_linestep_enable,
            "positioner_movement_starts_s": positioner_movement_starts_s,
            "positioner_movement_ends_s": positioner_movement_ends_s,
            "positioner_step_size_um": positioner_step_size_um,
        }

        try:
            self._digitalParameterDict["advanced_program_mode"] = (
                self._widget.getAdvancedProgramMode()
            )
            self._digitalParameterDict["advanced_sequence_rows"] = (
                self._widget.getAdvancedSequenceRows()
            )
            self._digitalParameterDict["line_program_devices_enabled"] = (
                self._widget.isLineProgramDevicesMode()
            )
            self._digitalParameterDict["advanced_device_lock_master"] = (
                self._widget.getAdvancedDeviceLockMaster()
            )
            self._digitalParameterDict["advanced_device_lock_target"] = (
                self._widget.getAdvancedDeviceLockTarget()
            )
        except Exception:
            pass

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
                self._widget.setLineProgramDevicesMode(
                    bool(dig.get("line_program_devices_enabled", False))
                )
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

            try:
                self._widget.setIntraPixelPositionersMode(
                    bool(dig.get("intra_pixel_positioner_movement", False))
                )
            except Exception:
                pass

            try:
                self._widget.setAdvancedDeviceLockState(
                    dig.get("advanced_device_lock_master", {}) or {},
                    dig.get("advanced_device_lock_target", {}) or {},
                )
            except Exception:
                pass

            positioner_starts_s = dig.get("positioner_movement_starts_s", {}) or {}
            positioner_ends_s = dig.get("positioner_movement_ends_s", {}) or {}
            positioner_step_size_um = dig.get("positioner_step_size_um", {}) or {}
            for dev in self.positioners.keys():
                starts_steps = positioner_starts_s.get(dev, None)
                ends_steps = positioner_ends_s.get(dev, None)
                if starts_steps is not None:
                    for s in range(min(S, len(starts_steps))):
                        try:
                            ends = ends_steps[s] if ends_steps is not None and s < len(ends_steps) else []
                            self._widget.setPulseTimes(dev, s, starts_steps[s], ends)
                        except Exception:
                            pass

                steps = positioner_step_size_um.get(dev, None)
                if steps is not None:
                    for s in range(min(S, len(steps))):
                        try:
                            self._widget.setLineStepPositionerStepUm(dev, s, steps[s])
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

            try:
                self._widget.setAdvancedProgramMode(
                    dig.get("advanced_program_mode", "timing")
                )
                self._widget.setAdvancedSequenceRows(
                    dig.get("advanced_sequence_rows", []) or []
                )
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
                        self._logger.warning("Failed to set %s to center:\n%s",
                                             positionerName, traceback.format_exc())

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
                self._logger.warning("Failed to reset ND-PiezoZ after scan:\n%s", traceback.format_exc())
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
            self._logger.debug("updatePixels failed:\n%s", traceback.format_exc())

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
