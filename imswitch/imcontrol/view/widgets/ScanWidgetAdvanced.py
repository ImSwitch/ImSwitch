# ScanWidgetAdvanced.py

import pyqtgraph as pg
import numpy as np

from qtpy.QtWidgets import QWidget, QCheckBox, QSpinBox, QGridLayout
from qtpy import QtCore, QtWidgets
from qtpy.QtCore import Signal
from imswitch.imcontrol.view import guitools as guitools
from .ScanWidgetBase import SuperScanWidget


class ScanWidgetAdvanced(SuperScanWidget):
    """
    PointScan-like widget with:
      - line-step checkbox matrix (per device, per linestep)
      - optional advanced intra-pixel pulses per (device, linestep)
      - TTL graph (line plot for now)
    """

    # SuperScanWidget typically provides these:
    # sigSeqTimeParChanged, sigStageParChanged, sigSignalParChanged
    # We'll emit sigSignalParChanged when TTL UI changes.

    # BeadRec-compatible signals (same contract as ScanWidgetMoNaLISA)
    sigUpdateBeadRecCenter = Signal(int, int)   # (y, x) in pixels
    sigShowBeadRecCenterCross = Signal(bool)    # show/hide crosshair on bead image
    sigAutoAxialToggled = Signal(bool)          # enable/disable axial scan sequence
    sigPlotScanClicked = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        # --- Scan timing params ---
        self.seqTimePar = QtWidgets.QLineEdit("0.02")  # ms
        self.phaseDelayPar = QtWidgets.QLineEdit("0")  # samples
        self.d3StepDelayPar = QtWidgets.QLineEdit("0")  # samples


        self.scanPar = {
            "seqTime": self.seqTimePar,
            "phaseDelay": self.phaseDelayPar,
            "frameDelay": self.d3StepDelayPar,
        }

        # --- TTL params containers ---
        self.ttl_line_steps = {}   # device -> ScanLineWidget (checkbox row)
        self.ttl_pulses = {}       # device -> list[PulseEditor] (len = n_linesteps)
        self._ttl_axis = {}        # optional: device -> axis combo, kept for future; not used now
        self.ttl_line_powers = {}
        self._ttl_device_names = []
        self._positioner_device_names = []
        self._line_step_device_widgets = {}  # device -> (label, ScanLineWidget)
        self._advanced_lock_master = {}       # device -> bool
        self._advanced_lock_target = {}       # follower device -> master device

        # --- Line-step count ---
        self.linestep_counter = QSpinBox()
        self.linestep_counter.setMinimum(1)
        self.linestep_counter.setMaximum(100)
        self.linestep_counter.setSingleStep(1)

        # --- Advanced mode ---
        self.advancedOptionsBox = QtWidgets.QCheckBox("Advanced Line Program")
        self.advancedOptionsBox.setChecked(False)
        self.intraPixelPositionersBox = QtWidgets.QCheckBox("Intra-pixel positioners movement")
        self.intraPixelPositionersBox.setChecked(False)
        self.intraPixelPositionersBox.setVisible(False)

        # --- Pulse editor selection controls (advanced mode UI) ---
        self._pulseSelectDevice = QtWidgets.QComboBox()
        self._pulseSelectStep = QtWidgets.QSpinBox()
        self._pulseSelectStep.setMinimum(1)
        self._pulseSelectStep.setMaximum(100)
        self._pulseSelectStep.setSingleStep(1)
        self._pulseMasterBox = QtWidgets.QCheckBox("Master")
        self._pulseLockBox = QtWidgets.QCheckBox("Lock-with:")
        self._pulseLockTarget = QtWidgets.QComboBox()

        self._pulseStartEdit = QtWidgets.QLineEdit("")  # ms list: "0.0, 0.2, ..."
        self._pulseEndEdit = QtWidgets.QLineEdit("")    # ms list
        self._positionerStepUmEdit = QtWidgets.QLineEdit("0.1")
        self._analogLevelEdit = QtWidgets.QSpinBox()
        self._analogLevelEdit.setMinimum(0)
        self._analogLevelEdit.setMaximum(100)
        self._analogLevelEdit.setSingleStep(1)
        self._analogLevelEdit.setValue(100)
        self.graph_steps = GraphFrame()  # always visible (scatter)
        self.graph_steps.setFixedHeight(140)

        self.graph_pixel = GraphFrame()  # only visible in advanced mode
        self.graph_pixel.setFixedHeight(140)

        self.plotScanButton = guitools.BetterPushButton("Plot")
        self.plotIncludeTTLBox = QtWidgets.QCheckBox("include TTL")

        # Connect scan timing signals
        self.seqTimePar.textChanged.connect(lambda: self.sigSeqTimeParChanged.emit())
        self.phaseDelayPar.textChanged.connect(lambda: self.sigStageParChanged.emit())
        self.d3StepDelayPar.textChanged.connect(lambda: self.sigStageParChanged.emit())

        # Connect TTL signals
        self.linestep_counter.valueChanged.connect(self._onLineStepsChanged)
        self.advancedOptionsBox.stateChanged.connect(self._onAdvancedModeChanged)
        self.intraPixelPositionersBox.stateChanged.connect(self._onIntraPixelPositionersChanged)
        self._pulseSelectDevice.currentIndexChanged.connect(self._syncPulseEditsFromModel)
        self._pulseSelectStep.valueChanged.connect(self._syncPulseEditsFromModel)
        self._pulseMasterBox.stateChanged.connect(lambda: self._onPulseMasterChanged())
        self._pulseLockBox.stateChanged.connect(lambda: self._onPulseLockChanged())
        self._pulseLockTarget.currentIndexChanged.connect(lambda: self._onPulseLockTargetChanged())
        self._pulseStartEdit.textChanged.connect(lambda: self._onPulseEditsChanged())
        self._pulseEndEdit.textChanged.connect(lambda: self._onPulseEditsChanged())
        self._positionerStepUmEdit.textChanged.connect(lambda: self._onPulseEditsChanged())
        self._analogLevelEdit.valueChanged.connect(lambda: self._onPulseEditsChanged())
        self.plotScanButton.clicked.connect(self.sigPlotScanClicked)


        # Internal: track when we are programmatically updating the pulse edits
        self._updatingPulseEdits = False
        self._updatingLockControls = False
        self._syncingLockedDevices = False
        # Devices (laser lines) that support per-linestep analog power programming
        self._linestep_power_capable_devices = set()

        # --- BeadRec controls ---
        self._showBeadCenterBox = QtWidgets.QCheckBox("Show bead center")
        self._beadCenterXEdit = QtWidgets.QLineEdit("0")
        self._beadCenterXEdit.setMaximumWidth(55)
        self._beadCenterYEdit = QtWidgets.QLineEdit("0")
        self._beadCenterYEdit.setMaximumWidth(55)

        # Connect BeadRec signals
        self._showBeadCenterBox.stateChanged.connect(
            lambda state: self.sigShowBeadRecCenterCross.emit(bool(state))
        )
        self._beadCenterXEdit.textChanged.connect(self._emitBeadRecCenter)
        self._beadCenterYEdit.textChanged.connect(self._emitBeadRecCenter)

    # -----------------------------
    # UI layout
    # -----------------------------

    def initControls(self, positionerNames, TTLDeviceNames,TTLTimeunit):
        currentRow = 0
        self._ttl_device_names = list(TTLDeviceNames)
        self._positioner_device_names = list(positionerNames)
        self.scanDims = list(positionerNames)
        self.scanDims.append("None")

        # --- Top row: buttons ---
        self.grid.addWidget(self.loadScanBtn, currentRow, 0)
        self.grid.addWidget(self.saveScanBtn, currentRow, 1)
        self.grid.addWidget(self.repeatBox, currentRow, 3)
        self.grid.addItem(
            QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum),
            currentRow, 4, 1, 1
        )
        self.grid.addWidget(self.plotScanButton, currentRow, 5)
        self.grid.addWidget(self.plotIncludeTTLBox, currentRow, 6)
        self.grid.addWidget(self.scanButton, currentRow, 7)
        currentRow += 1

        # spacer
        self.grid.addItem(
            QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding),
            currentRow, 0, 1, -1
        )

        currentRow += 1

        # --- Scan parameter labels ---
        sizeLabel = QtWidgets.QLabel("Size (µm)")
        stepLabel = QtWidgets.QLabel("Step size (µm)")
        pixelsLabel = QtWidgets.QLabel("Pixels (#)")
        centerLabel = QtWidgets.QLabel("Center (µm)")
        scandimLabel = QtWidgets.QLabel("Scan dim")
        for lab in (sizeLabel, stepLabel, pixelsLabel, centerLabel, scandimLabel):
            lab.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)

        self.grid.addWidget(sizeLabel, currentRow, 1)
        self.grid.addWidget(stepLabel, currentRow, 2)
        self.grid.addWidget(pixelsLabel, currentRow, 3)
        self.grid.addWidget(centerLabel, currentRow, 4)
        self.grid.addWidget(scandimLabel, currentRow, 7)
        currentRow += 1

        for index, positionerName in enumerate(positionerNames):
            sizePar = QtWidgets.QDoubleSpinBox()
            sizePar.setValue(5)
            sizePar.setDecimals(2)
            sizePar.setSingleStep(1)
            sizePar.setMinimum(0)
            self.scanPar["size" + positionerName] = sizePar

            stepSizePar = QtWidgets.QDoubleSpinBox()
            stepSizePar.setDecimals(3)
            stepSizePar.setValue(.1)
            stepSizePar.setSingleStep(.04)
            stepSizePar.setMinimum(0)
            if "mock" in positionerName.lower():
                stepSizePar.setValue(1)
                stepSizePar.setEnabled(False)
            self.scanPar["stepSize" + positionerName] = stepSizePar

            numPixelsPar = QtWidgets.QLineEdit("50")
            numPixelsPar.setEnabled(False)
            self.scanPar["pixels" + positionerName] = numPixelsPar

            centerPar = QtWidgets.QDoubleSpinBox()
            centerPar.setDecimals(2)
            centerPar.setValue(0)
            centerPar.setSingleStep(.1)
            self.scanPar["center" + positionerName] = centerPar
            if "mock" in positionerName.lower():
                centerPar.setEnabled(False)

            self.grid.addWidget(QtWidgets.QLabel(positionerName), currentRow, 0)
            self.grid.addWidget(sizePar, currentRow, 1)
            self.grid.addWidget(stepSizePar, currentRow, 2)
            self.grid.addWidget(numPixelsPar, currentRow, 3)
            self.grid.addWidget(centerPar, currentRow, 4)

            dimlabel = QtWidgets.QLabel(f"{index+1}{guitools.ordinalSuffix(index+1)} dimension:")
            dimlabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.grid.addWidget(dimlabel, currentRow, 6)
            scanDimPar = QtWidgets.QComboBox()
            scanDimPar.addItems(self.scanDims)
            scanDimPar.setCurrentIndex(index if index < 2 else self.scanDims.index("None"))
            self.scanPar["scanDim" + str(index)] = scanDimPar
            self.grid.addWidget(scanDimPar, currentRow, 7)

            # Connect
            sizePar.textChanged.connect(lambda: self.sigStageParChanged.emit())
            stepSizePar.textChanged.connect(lambda: self.sigStageParChanged.emit())
            centerPar.textChanged.connect(lambda: self.sigStageParChanged.emit())
            scanDimPar.currentIndexChanged.connect(lambda: self.sigStageParChanged.emit())

            currentRow += 1

        currentRow += 1

        # --- Timing params ---
        self.grid.addWidget(QtWidgets.QLabel("Dwell time (ms):"), currentRow, 0)
        self.grid.addWidget(self.seqTimePar, currentRow, 1)


        self.grid.addWidget(QtWidgets.QLabel("Phase delay (samples):"), currentRow, 2)
        self.grid.addWidget(self.phaseDelayPar, currentRow, 3)


        self.grid.addWidget(QtWidgets.QLabel("D3 step delay (samples):"), currentRow, 4)
        self.grid.addWidget(self.d3StepDelayPar, currentRow, 5)
        currentRow += 1

        # Spacer
        self.grid.addItem(
            QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding),
            currentRow, 0, 1, -1
        )
        currentRow += 1

        # ---------------------------
        # line steps
        # ---------------------------
        linestepsHeader = QtWidgets.QLabel("Line program devices")
        linestepsHeader.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.grid.addWidget(linestepsHeader, currentRow, 0, 1, 2)

        self.grid.addWidget(QtWidgets.QLabel("#Line repeats:"), currentRow, 2, 1, 1)
        self.grid.addWidget(self.linestep_counter, currentRow, 3, 1, 1)

        currentRow += 1

        allAdvancedDeviceNames = self._ttl_device_names + self._positioner_device_names

        self.grid.addWidget(self.graph_steps, currentRow, 4, max(1, len(allAdvancedDeviceNames)), 3)

        # Line-step matrix rows per device
        ttldevgroup = QtWidgets.QGroupBox()
        ttldevgrouplayout = QGridLayout()
        ttldevgroup.setLayout(ttldevgrouplayout)
        adv_row_counter = 0
        for deviceName in allAdvancedDeviceNames:
            deviceLabel = QtWidgets.QLabel(deviceName)
            ttldevgrouplayout.addWidget(deviceLabel, adv_row_counter, 0)
            row = ScanLineWidget(initial_count=self.linestep_counter.value())
            if deviceName in self._positioner_device_names:
                for cb in row.checkboxes:
                    cb.setChecked(False)
            row.line_steps_changed.connect(self.sigSignalParChanged)
            self.ttl_line_steps[deviceName] = row
            ttldevgrouplayout.addWidget(row, adv_row_counter, 1, 1, 3)
            self._line_step_device_widgets[deviceName] = (deviceLabel, row)

            # Build pulse editor model storage (one per step)
            self.ttl_pulses[deviceName] = [PulseEditor() for _ in range(self.linestep_counter.value())]
            self._advanced_lock_master.setdefault(deviceName, False)

            adv_row_counter += 1
            currentRow += 1

        self.grid.addWidget(ttldevgroup, currentRow-adv_row_counter, 0, max(1, adv_row_counter), 4)
        self._refreshAdvancedLineProgramDeviceVisibility()

        self.grid.addWidget(self.advancedOptionsBox, currentRow, 0, 1, 2)
        self.grid.addWidget(self.intraPixelPositionersBox, currentRow, 2, 1, 3)
        currentRow += 1

        # ---------------------------
        # Advanced pulse editor panel + graph
        # ---------------------------
        self._refreshPulseDeviceChoices()

        advGroup = QtWidgets.QGroupBox("Advanced intra-pixel pulses (per device, per line-step)")
        advLayout = QtWidgets.QGridLayout()
        advGroup.setLayout(advLayout)

        advLayout.addWidget(QtWidgets.QLabel("Device:"), 0, 0)
        advLayout.addWidget(self._pulseSelectDevice, 0, 1)

        advLayout.addWidget(QtWidgets.QLabel("Line step:"), 0, 2)
        advLayout.addWidget(self._pulseSelectStep, 0, 3)

        advLayout.addWidget(self._pulseMasterBox, 1, 0)
        advLayout.addWidget(self._pulseLockBox, 1, 1)
        advLayout.addWidget(self._pulseLockTarget, 1, 2, 1, 2)

        self._pulseStartLabel = QtWidgets.QLabel("Start(s) (ms, comma-separated):")
        advLayout.addWidget(self._pulseStartLabel, 2, 0, 1, 2)
        advLayout.addWidget(self._pulseStartEdit, 2, 2, 1, 2)

        self._pulseEndLabel = QtWidgets.QLabel("End(s) (ms, comma-separated):")
        advLayout.addWidget(self._pulseEndLabel, 3, 0, 1, 2)
        advLayout.addWidget(self._pulseEndEdit, 3, 2, 1, 2)

        self._positionerStepUmLabel = QtWidgets.QLabel("Step(s) (um, comma-separated):")
        advLayout.addWidget(self._positionerStepUmLabel, 4, 0, 1, 2)
        advLayout.addWidget(self._positionerStepUmEdit, 4, 2, 1, 2)

        self._analogLevelLabel = QtWidgets.QLabel("Power Level (%)")
        advLayout.addWidget(self._analogLevelLabel, 5, 0, 1, 2)
        advLayout.addWidget(self._analogLevelEdit, 5, 2, 1, 2)
        advanced_row_height = self._pulseStartEdit.sizeHint().height()
        for widget in (
            self._pulseEndEdit,
            self._positionerStepUmEdit,
            self._analogLevelEdit,
        ):
            widget.setMinimumHeight(advanced_row_height)
            widget.setMaximumHeight(advanced_row_height)
            widget.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)

        advLayout.addWidget(self.graph_pixel, 0, 4, 6, 4)

        self._advGroup = advGroup
        self._advGroup.setVisible(False)

        self.grid.addWidget(self._advGroup, currentRow, 0, 1, 8)

        currentRow += 1

        # Initial sync pulse edit panel
        self._syncPulseEditsFromModel()

        # --- BeadRec control row ---
        beadRecRow = QtWidgets.QHBoxLayout()
        beadRecRow.addWidget(self._showBeadCenterBox)
        beadRecRow.addWidget(QtWidgets.QLabel("X:"))
        beadRecRow.addWidget(self._beadCenterXEdit)
        beadRecRow.addWidget(QtWidgets.QLabel("Y:"))
        beadRecRow.addWidget(self._beadCenterYEdit)
        beadRecRow.addStretch()
        beadRecContainer = QtWidgets.QWidget()
        beadRecContainer.setLayout(beadRecRow)
        self.grid.addWidget(beadRecContainer, currentRow, 0, 1, 8)
        currentRow += 1

        # Column widths
        self.grid.setColumnMinimumWidth(7, 90)

    # -----------------------------
    # New controller-facing getters
    # -----------------------------

    def isadvancedOptionsMode(self) -> bool:
        return self.advancedOptionsBox.isChecked()

    def setadvancedOptionsMode(self, enabled: bool) -> None:
        self.advancedOptionsBox.setChecked(bool(enabled))

    def isIntraPixelPositionersMode(self) -> bool:
        return self.advancedOptionsBox.isChecked() and self.intraPixelPositionersBox.isChecked()

    def setIntraPixelPositionersMode(self, enabled: bool) -> None:
        self.intraPixelPositionersBox.setChecked(bool(enabled))

    def isPlotTTLIncluded(self) -> bool:
        return bool(self.plotIncludeTTLBox.isChecked())

    def getAdvancedDeviceLockMaster(self):
        return {
            dev: bool(self._advanced_lock_master.get(dev, False))
            for dev in self._visibleAdvancedProgramDevices()
        }

    def getAdvancedDeviceLockTarget(self):
        return dict(self._advanced_lock_target)

    def setAdvancedDeviceLockState(self, masters=None, targets=None):
        devices = set(self._visibleAdvancedProgramDevices())
        self._advanced_lock_master = {
            dev: bool((masters or {}).get(dev, False))
            for dev in devices
        }
        self._advanced_lock_target = {
            dev: target for dev, target in (targets or {}).items()
            if dev in devices and target in devices and target != dev
        }
        self._cleanupLockState()
        self._refreshLockControlsFromModel()

    def getNumLineSteps(self) -> int:
        return int(self.linestep_counter.value())

    def setNumLineSteps(self, n: int) -> None:
        n = int(n)
        self.linestep_counter.setValue(n)

    def getLineStepEnabled(self, deviceName: str, stepIdx: int) -> bool:
        # stepIdx is 0-based
        row = self.ttl_line_steps.get(deviceName)
        if row is None:
            return False
        if stepIdx < 0 or stepIdx >= len(row.checkboxes):
            return False
        return row.checkboxes[stepIdx].isChecked()

    def getPulseStarts(self, deviceName: str, stepIdx: int):
        # return seconds
        pe = self._getPulseEditor(deviceName, stepIdx)
        return pe.starts_s

    def getPulseEnds(self, deviceName: str, stepIdx: int):
        pe = self._getPulseEditor(deviceName, stepIdx)
        return pe.ends_s

    def getLineStepPowerPercent(self, deviceName: str, stepIdx: int) -> float:
        pe = self._getPulseEditor(deviceName, stepIdx)
        return float(getattr(pe, "power_percent", 100.0))

    def setLineStepPowerPercent(self, deviceName: str, stepIdx: int, value: float) -> None:
        pe = self._getPulseEditor(deviceName, stepIdx)
        pe.power_percent = float(value)

    def getLineStepPositionerStepUm(self, deviceName: str, stepIdx: int):
        pe = self._getPulseEditor(deviceName, stepIdx)
        return self._coerce_positioner_step_list(getattr(pe, "positioner_step_um", [0.1]))

    def setLineStepPositionerStepUm(self, deviceName: str, stepIdx: int, value) -> None:
        pe = self._getPulseEditor(deviceName, stepIdx)
        pe.positioner_step_um = self._coerce_positioner_step_list(value)

    def isAdvancedLineProgramPositioner(self, deviceName: str) -> bool:
        return deviceName in self._positioner_device_names

    def getAdvancedLineProgramDeviceNames(self):
        return self._visibleAdvancedProgramDevices()


    def getLineEnableVectorExpanded(self, deviceName: str, Ny: int, S: int):
        """
        Returns a boolean vector of length Ny*S telling whether the device should be enabled
        on each *expanded* Y line (line index = y*S + s).
        """
        Ny = int(Ny)
        S = int(S)
        S = max(S, 1)

        out = np.zeros(Ny * S, dtype=bool)
        row = self.ttl_line_steps.get(deviceName)
        if row is None:
            return out

        # If fewer checkboxes than S (shouldn't happen, but be defensive)
        enabled_steps = [False] * S
        for s in range(S):
            if s < len(row.checkboxes):
                enabled_steps[s] = row.checkboxes[s].isChecked()

        # Expand: for each physical y, apply per-step enable
        for y in range(Ny):
            base = y * S
            for s in range(S):
                out[base + s] = enabled_steps[s]

        return out

    def getPulseSegmentsOrFull(self, deviceName: str, stepIdx: int):
        """
        Returns list of (t0_s, t1_s) pulses. If none specified, returns [(0, dwell)] sentinel
        to indicate 'full on'.
        Note: the controller can clip to dwell time.
        """
        pe = self._getPulseEditor(deviceName, stepIdx)
        if pe.starts_s and pe.ends_s and len(pe.starts_s) == len(pe.ends_s):
            return list(zip(pe.starts_s, pe.ends_s))
        return None  # meaning "full on"

    def isAdvancedTTLMode(self) -> bool:
        # controller expects this name
        return self.isadvancedOptionsMode()

    def setAdvancedTTLMode(self, enabled: bool) -> None:
        return self.setadvancedOptionsMode(enabled)

    def setLinestepPowerCapableDevices(self, deviceNames):
        self._linestep_power_capable_devices = set(deviceNames or [])
        # refresh visibility + value when device changes
        self._syncPulseEditsFromModel()


    # -----------------------------
    # Existing scan param getters used by controller
    # -----------------------------

    def getScanStepSize(self, positionerName):
        if self.scanPar["stepSize" + positionerName].isEnabled():
            return float(self.scanPar["stepSize" + positionerName].value())
        return float(1)

    def getScanCenterPos(self, positionerName):
        if self.scanPar["center" + positionerName].isEnabled():
            return float(self.scanPar["center" + positionerName].value())
        return float(0)

    def getScanSize(self, positionerName):
        if self.scanPar["size" + positionerName].isEnabled():
            return float(self.scanPar["size" + positionerName].value())
        return float(0)

    def getScanDim(self, i: int) -> str:
        return self.scanPar["scanDim" + str(i)].currentText()

    def getSeqTimePar(self):
        # seconds
        return float(self.seqTimePar.text()) / 1000.0

    def getPhaseDelayPar(self):
        return float(self.phaseDelayPar.text())

    def getd3StepDelayPar(self):
        return float(self.d3StepDelayPar.text())

    # Setters used by controller
    def setScanPixels(self, positionerName, pixels):
        txt = str(pixels) if pixels > 1 else "-"
        self.scanPar["pixels" + positionerName].setText(txt)

    def setSeqTimePar(self, seqTimePar):
        self.seqTimePar.setText(str(round(float(1000 * seqTimePar), 3)))

    def setPhaseDelayPar(self, phaseDelayPar):
        self.phaseDelayPar.setText(str(round(int(phaseDelayPar))))

    def setd3StepDelayPar(self, d3StepDelayPar):
        self.d3StepDelayPar.setText(str(round(int(d3StepDelayPar))))

    def plotSignalGraph(self, signals, colors, sampleRate, labels=None):
        # labels are optional; if not provided, make something sane

        if labels is None:
            labels = [self._pulseSelectDevice.itemText(i) for i in range(self._pulseSelectDevice.count())]

        try:
            self._plotLineStepScatter(signals=signals, colors=colors, labels=labels)

            if self.isadvancedOptionsMode():
                self._plotPerPixelProgram(labels=labels, colors=colors, sampleRate=sampleRate)
        except Exception as e:
            print(e)


    def _plotPerPixelProgram(self, labels, colors, sampleRate):
        plot = self.graph_pixel.plot
        plot.clear()

        spp = int(round(self.getSeqTimePar() * float(sampleRate)))
        spp = max(spp, 1)
        S = self.getNumLineSteps()

        total = spp * S
        x = np.arange(total)

        vlines = [k * spp for k in range(1, S)]
        for xv in vlines:
            plot.addItem(pg.InfiniteLine(pos=xv, angle=90, movable=False))

        plot_labels = list(labels)
        plot_colors = list(colors)
        if self.isIntraPixelPositionersMode():
            for pos_idx, dev in enumerate(self._positioner_device_names):
                if dev not in plot_labels:
                    plot_labels.append(dev)
                    plot_colors.append(
                        pg.intColor(pos_idx, hues=max(1, len(self._positioner_device_names))).name()
                    )

        ymin = -0.15 * len(plot_labels) - 0.2
        ymax = 110.0

        for dev_idx, dev in enumerate(plot_labels):
            y = np.zeros(total, dtype=float)

            for step in range(S):
                start = step * spp
                end = start + spp

                if dev in self._positioner_device_names:
                    pe = self._getPulseEditor(dev, step)
                    starts = list(pe.starts_s or [])
                    ends = list(pe.ends_s or [])
                    steps_um = self._coerce_positioner_step_list(
                        getattr(pe, "positioner_step_um", [])
                    )

                    seg = np.zeros(spp, dtype=float)
                    for window_idx, t0 in enumerate(starts):
                        if window_idx >= len(ends):
                            continue

                        if window_idx < len(steps_um):
                            step_um = float(steps_um[window_idx])
                        elif steps_um:
                            step_um = float(steps_um[-1])
                        else:
                            step_um = 0.0

                        i0 = int(round(float(t0) * sampleRate))
                        i1 = int(round(float(ends[window_idx]) * sampleRate))
                        i0 = max(0, min(spp, i0))
                        i1 = max(0, min(spp, i1))
                        if i1 > i0:
                            seg[i0:i1] = 100.0 if step_um >= 0 else -100.0
                    y[start:end] = seg
                    continue

                if not self.getLineStepEnabled(dev, step):
                    continue

                pe = self._getPulseEditor(dev, step)
                if pe.starts_s and pe.ends_s and pe.power_percent:
                    seg = np.zeros(spp, dtype=float)
                    for t0, t1 in zip(pe.starts_s, pe.ends_s):
                        i0 = int(round(float(t0) * sampleRate))
                        i1 = int(round(float(t1) * sampleRate))
                        i0 = max(0, min(spp, i0))
                        i1 = max(0, min(spp, i1))
                        if i1 > i0:
                            seg[i0:i1] = pe.power_percent
                else:
                    seg = np.ones(spp, dtype=float)*100

                y[start:end] = seg

            # stack traces slightly
            yy = y.astype(float) - 0.15 * dev_idx
            ymin = min(ymin, float(np.min(yy)) - 5.0)
            ymax = max(ymax, float(np.max(yy)) + 5.0)
            plot.plot(x, yy, pen=pg.mkPen(plot_colors[dev_idx]), name=dev)

        plot.setYRange(ymin, ymax)
        plot.setLabel("bottom", "Samples within single dwell time")
        plot.setLabel("left", "Power [%]")

    @staticmethod
    def _lockPlotXRange(plot, n_samples):
        xmax = max(1, int(n_samples))
        plot.setXRange(0, xmax, padding=0)
        try:
            plot.getViewBox().setLimits(xMin=0, xMax=xmax, minXRange=1, maxXRange=xmax)
            plot.getViewBox().setRange(xRange=(0, xmax), padding=0)
        except Exception:
            pass
        try:
            plot.disableAutoRange()
        except Exception:
            pass


    def _plotLineStepScatter(self, signals, colors,  labels, vlines=None):

        plot = self.graph_steps.plot
        plot.clear()

        for dev_idx, sig in enumerate(signals):
            sig = np.asarray(sig).astype(bool)
            on_pixels = np.where(sig)[0]
            if on_pixels.size == 0:
                continue

            x = on_pixels
            y = np.full_like(on_pixels, dev_idx, dtype=float)

            plot.addItem(
                pg.ScatterPlotItem(
                    x=x+1,
                    y=y,
                    pen=None,
                    brush=pg.mkBrush(colors[dev_idx]),
                    size=8,
                    symbol="s",
                )
            )
        if vlines:
            for xv in vlines:
                inf = pg.InfiniteLine(pos=xv+1, angle=90, movable=False)
                plot.addItem(inf)

        plot.setLabel("bottom", "Line index")
        plot.setLabel("left", "Device")

        n_devices = len(signals)
        n_samples = max((len(s) for s in signals), default=0)
        plot.setYRange(-0.5, n_devices - 0.5)
        plot.setXRange(0.5, n_samples + 0.5)

        ticks = [(i, labels[i]) for i in range(n_devices)]
        plot.getAxis("left").setTicks([ticks])

        plot.showGrid(x=True, y=True, alpha=0.3)
        plot.disableAutoRange()


    def _onLineStepsChanged(self):
        n = int(self.linestep_counter.value())
        self._pulseSelectStep.setMaximum(max(1, n))

        # Resize checkbox rows
        for dev, row in self.ttl_line_steps.items():
            row.n_checkboxes_changed(n)

        # Resize pulse editor storage
        for dev in self.ttl_pulses.keys():
            cur = self.ttl_pulses[dev]
            if len(cur) < n:
                cur.extend([PulseEditor() for _ in range(n - len(cur))])
            elif len(cur) > n:
                self.ttl_pulses[dev] = cur[:n]

        self.sigSignalParChanged.emit()
        self._syncPulseEditsFromModel()

    def _onAdvancedModeChanged(self):
        enabled = self.advancedOptionsBox.isChecked()
        self._advGroup.setVisible(enabled)
        self.intraPixelPositionersBox.setVisible(enabled)
        self._refreshAdvancedLineProgramDeviceVisibility()
        self._refreshPulseDeviceChoices()

        # On toggle, refresh the pulse editor panel from stored model
        self._syncPulseEditsFromModel()
        self.sigSignalParChanged.emit()

    def _onIntraPixelPositionersChanged(self):
        self._refreshAdvancedLineProgramDeviceVisibility()
        self._refreshPulseDeviceChoices()
        self._syncPulseEditsFromModel()
        self.sigSignalParChanged.emit()

    def _visibleAdvancedProgramDevices(self):
        devices = list(self._ttl_device_names)
        if self.isIntraPixelPositionersMode():
            devices.extend(self._positioner_device_names)
        return devices

    def _refreshAdvancedLineProgramDeviceVisibility(self):
        for dev, widgets in self._line_step_device_widgets.items():
            visible = dev not in self._positioner_device_names
            for widget in widgets:
                widget.setVisible(visible)

    def _refreshPulseDeviceChoices(self):
        if not hasattr(self, "_pulseSelectDevice"):
            return

        current = self._pulseSelectDevice.currentText()
        devices = self._visibleAdvancedProgramDevices()
        for dev in devices:
            self._advanced_lock_master.setdefault(dev, False)
        self._cleanupLockState()

        self._pulseSelectDevice.blockSignals(True)
        try:
            self._pulseSelectDevice.clear()
            self._pulseSelectDevice.addItems(devices)
            if current in devices:
                self._pulseSelectDevice.setCurrentIndex(devices.index(current))
            elif devices:
                self._pulseSelectDevice.setCurrentIndex(0)
        finally:
            self._pulseSelectDevice.blockSignals(False)
        self._refreshLockControlsFromModel()

    def _cleanupLockState(self):
        devices = set(self._visibleAdvancedProgramDevices())
        self._advanced_lock_master = {
            dev: bool(self._advanced_lock_master.get(dev, False))
            for dev in devices
        }

        cleaned_targets = {}
        for dev, target in self._advanced_lock_target.items():
            if dev not in devices or target not in devices or dev == target:
                continue
            if self._advanced_lock_master.get(dev, False):
                continue
            if not self._advanced_lock_master.get(target, False):
                continue
            cleaned_targets[dev] = target
        self._advanced_lock_target = cleaned_targets

    def _refreshLockControlsFromModel(self):
        if not hasattr(self, "_pulseMasterBox"):
            return
        if self._pulseSelectDevice.count() == 0:
            return

        self._cleanupLockState()
        dev = self._pulseSelectDevice.currentText()
        is_master = bool(self._advanced_lock_master.get(dev, False))
        target = self._advanced_lock_target.get(dev, None)
        master_devices = [
            name for name, enabled in self._advanced_lock_master.items()
            if enabled and name != dev
        ]

        self._updatingLockControls = True
        try:
            self._pulseMasterBox.setChecked(is_master)
            self._pulseLockTarget.blockSignals(True)
            try:
                self._pulseLockTarget.clear()
                self._pulseLockTarget.addItems(master_devices)
                if target in master_devices:
                    self._pulseLockTarget.setCurrentIndex(master_devices.index(target))
                elif master_devices:
                    self._pulseLockTarget.setCurrentIndex(0)
            finally:
                self._pulseLockTarget.blockSignals(False)

            can_lock = (not is_master) and bool(master_devices)
            locked = (not is_master) and target in master_devices
            self._pulseLockBox.setChecked(locked)
            self._pulseLockBox.setEnabled(can_lock)
            self._pulseLockTarget.setEnabled(can_lock and locked)
        finally:
            self._updatingLockControls = False

    def _onPulseMasterChanged(self):
        if self._updatingLockControls:
            return
        dev = self._pulseSelectDevice.currentText()
        if not dev:
            return

        is_master = bool(self._pulseMasterBox.isChecked())
        self._advanced_lock_master[dev] = is_master
        if is_master:
            self._advanced_lock_target.pop(dev, None)
        else:
            self._advanced_lock_target = {
                follower: target
                for follower, target in self._advanced_lock_target.items()
                if target != dev
            }

        self._cleanupLockState()
        self._refreshLockControlsFromModel()
        self._syncPulseEditsFromModel()
        self.sigSignalParChanged.emit()

    def _onPulseLockChanged(self):
        if self._updatingLockControls:
            return
        dev = self._pulseSelectDevice.currentText()
        if not dev or self._advanced_lock_master.get(dev, False):
            return

        if self._pulseLockBox.isChecked() and self._pulseLockTarget.count() > 0:
            target = self._pulseLockTarget.currentText()
            if target and target != dev:
                self._advanced_lock_target[dev] = target
                self._copyTimingFromMasterToFollower(target, dev)
        else:
            self._advanced_lock_target.pop(dev, None)

        self._cleanupLockState()
        self._refreshLockControlsFromModel()
        self._syncPulseEditsFromModel()
        self.sigSignalParChanged.emit()

    def _onPulseLockTargetChanged(self):
        if self._updatingLockControls or not self._pulseLockBox.isChecked():
            return
        dev = self._pulseSelectDevice.currentText()
        target = self._pulseLockTarget.currentText()
        if not dev or not target or dev == target:
            return

        self._advanced_lock_target[dev] = target
        self._copyTimingFromMasterToFollower(target, dev)
        self._cleanupLockState()
        self._syncPulseEditsFromModel()
        self.sigSignalParChanged.emit()

    def _copyTimingFromMasterToFollower(self, master, follower, stepIdx=None):
        if not master or not follower or master == follower:
            return

        step_indices = [int(stepIdx)] if stepIdx is not None else range(self.getNumLineSteps())
        for s in step_indices:
            mpe = self._getPulseEditor(master, s)
            fpe = self._getPulseEditor(follower, s)
            fpe.starts_s = list(mpe.starts_s or [])
            fpe.ends_s = list(mpe.ends_s or [])
            if master in self._positioner_device_names and follower in self._positioner_device_names:
                fpe.positioner_step_um = self._coerce_positioner_step_list(
                    getattr(mpe, "positioner_step_um", [0.1])
                )

    def _propagateMasterTiming(self, master, stepIdx=None):
        if self._syncingLockedDevices:
            return
        if not self._advanced_lock_master.get(master, False):
            return

        self._syncingLockedDevices = True
        try:
            for follower, target in list(self._advanced_lock_target.items()):
                if target == master:
                    self._copyTimingFromMasterToFollower(master, follower, stepIdx=stepIdx)
        finally:
            self._syncingLockedDevices = False

    def _getPulseEditor(self, deviceName: str, stepIdx: int) -> "PulseEditor":
        stepIdx = int(stepIdx)
        if stepIdx < 0:
            stepIdx = 0
        if deviceName not in self.ttl_pulses:
            self.ttl_pulses[deviceName] = []
        if stepIdx >= len(self.ttl_pulses[deviceName]):
            # Extend if needed
            need = stepIdx + 1 - len(self.ttl_pulses[deviceName])
            self.ttl_pulses[deviceName].extend([PulseEditor() for _ in range(need)])
        return self.ttl_pulses[deviceName][stepIdx]

    def _syncPulseEditsFromModel(self):
        if not self.isadvancedOptionsMode():
            return
        if self._pulseSelectDevice.count() == 0:
            return

        dev = self._pulseSelectDevice.currentText()
        step0 = int(self._pulseSelectStep.value()) - 1  # UI is 1-based
        lock_target = self._advanced_lock_target.get(dev, None)
        if lock_target:
            self._copyTimingFromMasterToFollower(lock_target, dev, stepIdx=step0)
        pe = self._getPulseEditor(dev, step0)
        self._refreshLockControlsFromModel()

        # Show/hide power editor depending on capability of selected device
        is_positioner = dev in self._positioner_device_names
        is_locked_follower = lock_target is not None
        power_ok = not is_positioner and dev in self._linestep_power_capable_devices
        self._pulseEndLabel.setVisible(True)
        self._pulseEndEdit.setVisible(True)
        self._pulseEndLabel.setText("End(s) (ms, comma-separated):")
        self._positionerStepUmLabel.setVisible(is_positioner)
        self._positionerStepUmEdit.setVisible(is_positioner)
        self._analogLevelLabel.setVisible(power_ok)
        self._analogLevelEdit.setVisible(power_ok)
        self._pulseStartEdit.setEnabled(not is_locked_follower)
        self._pulseEndEdit.setEnabled(not is_locked_follower)
        self._positionerStepUmEdit.setEnabled(is_positioner and not is_locked_follower)
        self._analogLevelEdit.setEnabled(power_ok)

        self._updatingPulseEdits = True
        try:
            # show in ms
            self._pulseStartEdit.setText(", ".join([str(round(s * 1000.0, 4)) for s in pe.starts_s]))
            self._pulseEndEdit.setText(", ".join([str(round(s * 1000.0, 4)) for s in pe.ends_s]))
            if is_positioner:
                steps_um = self._coerce_positioner_step_list(getattr(pe, "positioner_step_um", [0.1]))
                self._positionerStepUmEdit.setText(", ".join([str(round(v, 3)) for v in steps_um]))

            # per-linestep power (percent)
            self._analogLevelEdit.setValue(int(round(float(getattr(pe, "power_percent", 100.0)))))
        finally:
            self._updatingPulseEdits = False

    def _onPulseEditsChanged(self):
        if self._updatingPulseEdits:
            return
        if not self.isadvancedOptionsMode():
            return

        dev = self._pulseSelectDevice.currentText()
        step0 = int(self._pulseSelectStep.value()) - 1
        pe = self._getPulseEditor(dev, step0)

        is_positioner = dev in self._positioner_device_names
        is_locked_follower = dev in self._advanced_lock_target
        try:
            starts_ms = self._parse_float_list_ms(self._pulseStartEdit.text())
            ends_ms = self._parse_float_list_ms(self._pulseEndEdit.text())
            if is_positioner:
                positioner_steps = self._parse_float_list(self._positionerStepUmEdit.text())
            else:
                positioner_steps = []
        except ValueError:
            return

        if not is_locked_follower:
            if is_positioner:
                pe.starts_s = [v / 1000.0 for v in starts_ms]
                pe.ends_s = [v / 1000.0 for v in ends_ms]
            elif not starts_ms and not ends_ms:
                pe.starts_s = []
                pe.ends_s = []
            else:
                pe.starts_s = [v / 1000.0 for v in starts_ms]
                pe.ends_s = [v / 1000.0 for v in ends_ms]

            if is_positioner:
                pe.positioner_step_um = positioner_steps

        if not is_positioner:
            pe.power_percent = float(self._analogLevelEdit.value())

        self._propagateMasterTiming(dev, stepIdx=step0)
        self.sigSignalParChanged.emit()

    def getTTLIncluded(self, deviceName):
        row = self.ttl_line_steps.get(deviceName, None)
        if row is None:
            return False
        return any(cb.isChecked() for cb in row.checkboxes)

    def unsetTTL(self, deviceName):
        row = self.ttl_line_steps.get(deviceName, None)
        if row is None:
            return
        for cb in row.checkboxes:
            cb.setChecked(False)

        # also clear stored pulses for that device (optional but sensible)
        if deviceName in self.ttl_pulses:
            for pe in self.ttl_pulses[deviceName]:
                pe.starts_s = []
                pe.ends_s = []

    def setScanMode(self):
        # If you have a scan/cont toggle, set it here.
        # Otherwise, keep as a no-op to satisfy abstract API.
        if hasattr(self, "scanRadio"):
            self.scanRadio.setChecked(True)

    # --- BeadRec helpers ---

    def _emitBeadRecCenter(self):
        """Emit sigUpdateBeadRecCenter when either coordinate field changes."""
        try:
            x = int(self._beadCenterXEdit.text())
            y = int(self._beadCenterYEdit.text())
            self.sigUpdateBeadRecCenter.emit(y, x)  # (y, x) matches MoNaLISA convention
        except ValueError:
            pass  # non-numeric input, ignore silently

    def setLineStepEnabled(self, deviceName: str, stepIdx: int, enabled: bool) -> None:
        row = self.ttl_line_steps.get(deviceName)
        if row is None:
            return
        if 0 <= stepIdx < len(row.checkboxes):
            row.checkboxes[stepIdx].setChecked(bool(enabled))

    def setPulseTimes(self, deviceName: str, stepIdx: int, starts_s, ends_s) -> None:
        pe = self._getPulseEditor(deviceName, stepIdx)
        pe.starts_s = list(starts_s or [])
        pe.ends_s = list(ends_s or [])

    @staticmethod
    def _parse_float_list_ms(txt: str):
        return ScanWidgetAdvanced._parse_float_list(txt)

    @staticmethod
    def _parse_float_list(txt: str):
        txt = (txt or "").strip()
        if not txt:
            return []
        parts = [p.strip() for p in txt.split(",")]
        out = []
        for p in parts:
            if not p:
                continue
            out.append(float(p))
        return out

    @staticmethod
    def _coerce_positioner_step_list(value):
        if value is None:
            return []
        if isinstance(value, (list, tuple)):
            return [float(v) for v in value]
        return [float(value)]


class PulseEditor:
    """Stores intra-pixel pulses for one (device, linestep). Times are seconds."""
    def __init__(self):
        self.starts_s = []
        self.ends_s = []
        self.power_percent = 100.0  # constant within line, used for AO-capable lasers
        self.positioner_step_um = [0.1]


class ScanLineWidget(QWidget):
    """
    N checkboxes representing if a device is on during which of the N line steps.
    """
    line_steps_changed = Signal()

    def __init__(self, parent=None, initial_count=1):
        super().__init__(parent)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)
        self.checkboxes = []
        for _ in range(initial_count):
            self._add_checkbox()

    def _add_checkbox(self, checked=True):
        cb = QCheckBox()
        cb.setChecked(bool(checked))
        cb.toggled.connect(self.line_steps_changed)
        self.checkboxes.append(cb)
        self.layout.addWidget(cb)

    def n_checkboxes_changed(self, n_total: int):
        n_total = int(n_total)
        # grow
        while len(self.checkboxes) < n_total:
            # copy last state as convenience
            cb = QCheckBox()
            if len(self.checkboxes) > 0 and self.checkboxes[-1].isChecked():
                cb.setChecked(True)
            cb.toggled.connect(self.line_steps_changed)
            self.checkboxes.append(cb)
            self.layout.addWidget(cb)
        # shrink
        while len(self.checkboxes) > n_total:
            cb = self.checkboxes.pop()
            self.layout.removeWidget(cb)
            cb.setParent(None)
            cb.deleteLater()


class GraphFrame(pg.GraphicsLayoutWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plot = self.addPlot(row=1, col=0)
