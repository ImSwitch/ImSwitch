# ScanControllerLineStepPointScan.py
import copy
import traceback
import configparser
from ast import literal_eval

import numpy as np
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
        )

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
        Replacement for ScanManager.makeFullScan() in branches where master.scanManager is absent.

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

        if hasattr(scan_des, "checkSignalComp"):
            if not scan_des.checkSignalComp(scanParameters, self._setupInfo, scanInfoDict):
                self._logger.error(
                    "Signal voltages outside scanner ranges: try scanning a smaller ROI or a slower scan."
                )
                return None, None

        # --- TTL / digital ---
        ttl_param = copy.deepcopy(getattr(self._setupInfo.scan, "TTLCycleDesignerParams", {}))
        ttl_param.update(TTLParameters)

        TTLCycleSignalsDict = ttl_des.make_signal(ttl_param, self._setupInfo, scanInfoDict)

        signalDict = {
            "scanSignalsDict": scanSignalsDict,
            "TTLCycleSignalsDict": TTLCycleSignalsDict,
        }
        return signalDict, scanInfoDict

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
        Digital format expected by AdvancedScanTTLCycleDesigner (your new TTL designer).
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

            # call the widget with its NEW signature
            self._widget.plotSignalGraph(signals, colors, sampleRate, labels=labels)

        except Exception:
            self._logger.debug(
                "[ScanControllerAdvanced] plotSignalGraph failed:\n%s",
                traceback.format_exc(),
            )

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
