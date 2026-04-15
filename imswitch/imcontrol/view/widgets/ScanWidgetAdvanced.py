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

        # --- Line-step count ---
        self.linestep_counter = QSpinBox()
        self.linestep_counter.setMinimum(1)
        self.linestep_counter.setMaximum(100)
        self.linestep_counter.setSingleStep(1)

        # --- Advanced mode ---
        self.advancedOptionsBox = QtWidgets.QCheckBox("Advanced Line Program")
        self.advancedOptionsBox.setChecked(False)

        # --- Pulse editor selection controls (advanced mode UI) ---
        self._pulseSelectDevice = QtWidgets.QComboBox()
        self._pulseSelectStep = QtWidgets.QSpinBox()
        self._pulseSelectStep.setMinimum(1)
        self._pulseSelectStep.setMaximum(100)
        self._pulseSelectStep.setSingleStep(1)

        self._pulseStartEdit = QtWidgets.QLineEdit("")  # ms list: "0.0, 0.2, ..."
        self._pulseEndEdit = QtWidgets.QLineEdit("")    # ms list
        self._analogLevelEdit = QtWidgets.QSpinBox()
        self._analogLevelEdit.setMinimum(0)
        self._analogLevelEdit.setMaximum(100)
        self._analogLevelEdit.setSingleStep(1)
        self._analogLevelEdit.setValue(100)
        self._applyAdvancedOptionsButton = QtWidgets.QPushButton("Apply Advanced Options")

        self.graph_steps = GraphFrame()  # always visible (scatter)
        self.graph_steps.setFixedHeight(140)

        self.graph_pixel = GraphFrame()  # only visible in advanced mode
        self.graph_pixel.setFixedHeight(140)


        # Connect scan timing signals
        self.seqTimePar.textChanged.connect(lambda: self.sigSeqTimeParChanged.emit())
        self.phaseDelayPar.textChanged.connect(lambda: self.sigStageParChanged.emit())
        self.d3StepDelayPar.textChanged.connect(lambda: self.sigStageParChanged.emit())

        # Connect TTL signals
        self.linestep_counter.valueChanged.connect(self._onLineStepsChanged)
        self.advancedOptionsBox.stateChanged.connect(self._onAdvancedModeChanged)
        self._pulseSelectDevice.currentIndexChanged.connect(self._syncPulseEditsFromModel)
        self._pulseSelectStep.valueChanged.connect(self._syncPulseEditsFromModel)
        self._applyAdvancedOptionsButton.clicked.connect(self._onPulseEditsChanged)


        # Internal: track when we are programmatically updating the pulse edits
        self._updatingPulseEdits = False
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
        self.scanDims = list(positionerNames)
        self.scanDims.append("None")

        # --- Top row: buttons ---
        self.grid.addWidget(self.loadScanBtn, currentRow, 0)
        self.grid.addWidget(self.saveScanBtn, currentRow, 1)
        self.grid.addItem(
            QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum),
            currentRow, 2, 1, 3
        )

        self.grid.addWidget(self.repeatBox, currentRow, 3)
        self.grid.addWidget(self.scanButton, currentRow, 6)
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
        self.grid.addWidget(scandimLabel, currentRow, 6)
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
            self.grid.addWidget(dimlabel, currentRow, 5)
            scanDimPar = QtWidgets.QComboBox()
            scanDimPar.addItems(self.scanDims)
            scanDimPar.setCurrentIndex(index if index < 2 else self.scanDims.index("None"))
            self.scanPar["scanDim" + str(index)] = scanDimPar
            self.grid.addWidget(scanDimPar, currentRow, 6)

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
        linestepsHeader = QtWidgets.QLabel("Lasers")
        linestepsHeader.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.grid.addWidget(linestepsHeader, currentRow, 0, 1, 2)

        self.grid.addWidget(QtWidgets.QLabel("#Line repeats:"), currentRow, 2, 1, 1)
        self.grid.addWidget(self.linestep_counter, currentRow, 3, 1, 1)

        currentRow += 1

        self.grid.addWidget(self.graph_steps, currentRow, 4, len(TTLDeviceNames), 3)

        # Line-step matrix rows per device
        ttldevgroup = QtWidgets.QGroupBox()
        ttldevgrouplayout = QGridLayout()
        ttldevgroup.setLayout(ttldevgrouplayout)
        adv_row_counter = 0
        for deviceName in TTLDeviceNames:
            ttldevgrouplayout.addWidget(QtWidgets.QLabel(deviceName), adv_row_counter, 0)
            row = ScanLineWidget(initial_count=self.linestep_counter.value())
            row.line_steps_changed.connect(self.sigSignalParChanged)
            self.ttl_line_steps[deviceName] = row
            ttldevgrouplayout.addWidget(row, adv_row_counter, 1, 1, 3)

            # Build pulse editor model storage (one per step)
            self.ttl_pulses[deviceName] = [PulseEditor() for _ in range(self.linestep_counter.value())]

            adv_row_counter += 1
            currentRow += 1

        self.grid.addWidget(ttldevgroup, currentRow-adv_row_counter, 0, len(TTLDeviceNames), 4)

        self.grid.addWidget(self.advancedOptionsBox, currentRow, 0, 1, 2)
        currentRow += 1

        # ---------------------------
        # Advanced pulse editor panel + graph
        # ---------------------------
        self._pulseSelectDevice.addItems(list(TTLDeviceNames))

        advGroup = QtWidgets.QGroupBox("Advanced intra-pixel pulses (per device, per line-step)")
        advLayout = QtWidgets.QGridLayout()
        advGroup.setLayout(advLayout)

        advLayout.addWidget(QtWidgets.QLabel("Device:"), 0, 0)
        advLayout.addWidget(self._pulseSelectDevice, 0, 1)

        advLayout.addWidget(QtWidgets.QLabel("Line step:"), 0, 2)
        advLayout.addWidget(self._pulseSelectStep, 0, 3)

        advLayout.addWidget(QtWidgets.QLabel("Start(s) (ms, comma-separated):"), 1, 0, 1, 2)
        advLayout.addWidget(self._pulseStartEdit, 1, 2, 1, 2)

        advLayout.addWidget(QtWidgets.QLabel("End(s) (ms, comma-separated):"), 2, 0, 1, 2)
        advLayout.addWidget(self._pulseEndEdit, 2, 2, 1, 2)

        self._analogLevelLabel = QtWidgets.QLabel("Power Level (%)")
        advLayout.addWidget(self._analogLevelLabel, 3, 0, 1, 2)
        advLayout.addWidget(self._analogLevelEdit, 3, 2, 1, 2)

        advLayout.addWidget(self._applyAdvancedOptionsButton, 4, 0, 1, 4)

        advLayout.addWidget(self.graph_pixel, 0, 4, 4, 4)

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
        self.grid.setColumnMinimumWidth(6, 90)

    # -----------------------------
    # New controller-facing getters
    # -----------------------------

    def isadvancedOptionsMode(self) -> bool:
        return self.advancedOptionsBox.isChecked()

    def setadvancedOptionsMode(self, enabled: bool) -> None:
        self.advancedOptionsBox.setChecked(bool(enabled))

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
        x = np.arange(total)  # or ms: np.arange(total)/sampleRate*1000

        vlines = [k * spp for k in range(1, S)]
        for xv in vlines:
            plot.addItem(pg.InfiniteLine(pos=xv, angle=90, movable=False))

        for dev_idx, dev in enumerate(labels):
            y = np.zeros(total, dtype=np.uint8)

            for step in range(S):
                start = step * spp
                end = start + spp

                if not self.getLineStepEnabled(dev, step):
                    continue

                pe = self._getPulseEditor(dev, step)
                if pe.starts_s and pe.ends_s and pe.power_percent:
                    seg = np.zeros(spp, dtype=np.uint8)
                    for t0, t1 in zip(pe.starts_s, pe.ends_s):
                        i0 = int(round(float(t0) * sampleRate))
                        i1 = int(round(float(t1) * sampleRate))
                        i0 = max(0, min(spp, i0))
                        i1 = max(0, min(spp, i1))
                        if i1 > i0:
                            seg[i0:i1] = pe.power_percent
                else:
                    seg = np.ones(spp, dtype=np.uint8)*100

                y[start:end] = seg

            # stack traces slightly
            yy = y.astype(float) - 0.15 * dev_idx
            plot.plot(x, yy, pen=pg.mkPen(colors[dev_idx]), name=dev)

        plot.setYRange(-0.15 * len(labels) - 0.2, 110)
        plot.setLabel("bottom", "Samples within single dwell time")
        plot.setLabel("left", "Power [%]")


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

        # On toggle, refresh the pulse editor panel from stored model
        self._syncPulseEditsFromModel()
        self.sigSignalParChanged.emit()

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
        pe = self._getPulseEditor(dev, step0)

        # Show/hide power editor depending on capability of selected device
        power_ok = dev in self._linestep_power_capable_devices
        self._analogLevelEdit.setVisible(power_ok)
        if hasattr(self, "_analogLevelLabel"):
            self._analogLevelLabel.setVisible(power_ok)

        self._updatingPulseEdits = True
        try:
            # show in ms
            self._pulseStartEdit.setText(", ".join([str(round(s * 1000.0, 4)) for s in pe.starts_s]))
            self._pulseEndEdit.setText(", ".join([str(round(s * 1000.0, 4)) for s in pe.ends_s]))

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

        starts_ms = self._parse_float_list_ms(self._pulseStartEdit.text())
        ends_ms = self._parse_float_list_ms(self._pulseEndEdit.text())

        if not starts_ms and not ends_ms:
            pe.starts_s = []
            pe.ends_s = []
        else:
            pe.starts_s = [v / 1000.0 for v in starts_ms]
            pe.ends_s = [v / 1000.0 for v in ends_ms]

        pe.power_percent = float(self._analogLevelEdit.value())
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


class PulseEditor:
    """Stores intra-pixel pulses for one (device, linestep). Times are seconds."""
    def __init__(self):
        self.starts_s = []
        self.ends_s = []
        self.power_percent = 100.0  # constant within line, used for AO-capable lasers


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
