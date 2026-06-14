import json
import os
import traceback

from qtpy import QtCore, QtGui, QtWidgets

from imswitch.imcommon.model import dirtools
from ..basecontrollers import ImConWidgetController


class SetupModesController(ImConWidgetController):
    """UI controller for the compact setup modes widget."""

    defaultSafetySettings = {
        "warnAboveLaserPowerThreshold": True,
        "laserPowerThresholdMw": 50.0,
        "confirmHighPowerShortcutApply": True,
        "suppressedWarnings": [],
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._setupModeController = None
        self._modeShortcuts = []
        self._activeModeName = None
        self._safetySettingsPath = os.path.join(
            dirtools.UserFileDirs.Root, "imcontrol_setup_mode_settings.json"
        )
        self._safetySettings = self._loadSafetySettings()

        self._widget.setBackendAvailable(False)
        self._widget.sigModeSelected.connect(self.modeSelected)
        self._widget.sigReloadMode.connect(self.reloadSelectedMode)
        self._widget.sigInspectModes.connect(self.inspectModes)
        self._widget.sigUpdateMode.connect(self.updateCurrentMode)
        self._widget.sigSaveAsMode.connect(self.saveModeAs)
        self._widget.sigRenameMode.connect(self.renameMode)
        self._widget.sigDuplicateMode.connect(self.duplicateMode)
        self._widget.sigSetShortcut.connect(self.setShortcut)
        self._widget.sigSafetySettings.connect(self.editSafetySettings)
        self._widget.sigDeleteMode.connect(self.deleteMode)
        self._widget.sigRevealFolder.connect(self.revealModesFolder)

    def setSetupModeController(self, setupModeController):
        self._setupModeController = setupModeController
        self._widget.setBackendAvailable(True)
        self.refreshModes()

    def closeEvent(self):
        self._clearShortcuts()

    def refreshModes(self, selectedName=None):
        if self._setupModeController is None:
            self._widget.setBackendAvailable(False)
            self._widget.setModes([])
            return

        try:
            modeNames = self._setupModeController.listSetupModes()
            summaries = []
            for modeName in modeNames:
                try:
                    summaries.append(self._makeModeSummary(
                        self._setupModeController.getSetupMode(modeName)
                    ))
                except Exception:
                    self._logger.error(f'Failed to read setup mode "{modeName}"')
                    self._logger.error(traceback.format_exc())

            self._widget.setBackendAvailable(True)
            self._widget.setModes(summaries, selectedName)
            self._rebuildShortcuts(summaries)
        except Exception as e:
            self._logger.error("Failed to refresh setup modes")
            self._logger.error(traceback.format_exc())
            self._widget.showError("Setup modes", f"Could not refresh setup modes: {e}")

    def modeSelected(self, modeName):
        if not modeName:
            return

        if not self._applyMode(modeName, source="selection"):
            self.refreshModes(self._activeModeName)

    def reloadSelectedMode(self):
        modeName = self._widget.getSelectedModeName()
        if not modeName:
            return

        if not self._applyMode(modeName, source="reload"):
            self.refreshModes(self._activeModeName)

    def inspectModes(self):
        if self._setupModeController is None:
            return

        try:
            modeDetails = []
            for modeName in self._setupModeController.listSetupModes():
                modeDetails.append(
                    self._makeInspectModeDetails(
                        self._setupModeController.getSetupMode(modeName)
                    )
                )
        except Exception as e:
            self._logger.error("Failed to inspect setup modes")
            self._logger.error(traceback.format_exc())
            self._widget.showError("Inspect setup modes", f"Could not inspect setup modes: {e}")
            return

        self._widget.showInspectModesDialog(modeDetails, self._widget.getSelectedModeName())

    def saveModeAs(self):
        if self._setupModeController is None:
            return

        try:
            components = self._setupModeController.getSetupModeComponents()
        except Exception as e:
            self._logger.error("Failed to list setup mode components")
            self._logger.error(traceback.format_exc())
            self._widget.showError("Setup modes", f"Could not list setup mode components: {e}")
            return

        if not components:
            self._widget.showWarnings(
                "Setup modes",
                ["No setup-mode aware widgets are available in this setup."]
            )
            return

        selectedName = self._widget.getSelectedModeName()
        selectedMode = self._getMode(selectedName) if selectedName else {}
        selectedComponents = selectedMode.get("includedComponents") or components

        result = self._widget.showSaveModeDialog(
            selectedName or "",
            selectedMode.get("description", ""),
            selectedMode.get("shortcut", ""),
            components,
            selectedComponents
        )
        if result is None:
            return

        modeName = result["name"]
        if self._modeExists(modeName) and not self._widget.askOverwriteMode(modeName):
            return

        shortcut = self._normalizeShortcut(result.get("shortcut"))
        if not self._ensureShortcutAvailable(shortcut, modeName):
            return

        try:
            saveResult = self._setupModeController.saveSetupMode(
                modeName,
                componentNames=result["components"],
                description=result.get("description", ""),
                shortcut=shortcut or ""
            )
        except Exception as e:
            self._logger.error(f'Failed to save setup mode "{modeName}"')
            self._logger.error(traceback.format_exc())
            self._widget.showError("Save setup mode", f"Could not save setup mode: {e}")
            return

        self._activeModeName = modeName
        self.refreshModes(modeName)
        warnings = saveResult.get("warnings") or []
        if warnings:
            self._showWarnings("Setup mode saved with warnings", warnings)

    def updateCurrentMode(self):
        modeName = self._widget.getSelectedModeName()
        if not modeName or self._setupModeController is None:
            return

        savedMode = self._getMode(modeName)
        if not savedMode:
            return

        componentNames = savedMode.get("includedComponents") or list(
            (savedMode.get("state") or {}).keys()
        )
        if not componentNames:
            self._widget.showWarnings(
                "Update setup mode",
                [f'Setup mode "{modeName}" has no included components.']
            )
            return

        try:
            snapshot = self._setupModeController.snapshotSetupModeState(componentNames)
        except Exception as e:
            self._logger.error(f'Failed to snapshot setup mode update "{modeName}"')
            self._logger.error(traceback.format_exc())
            self._widget.showError("Update setup mode", f"Could not snapshot current state: {e}")
            return

        summaries = self._buildUpdateSummaries(savedMode, snapshot)
        warnings = snapshot.get("warnings") or []
        if not self._widget.showUpdateModeDialog(modeName, summaries, warnings):
            return

        try:
            saveResult = self._setupModeController.saveSetupMode(
                modeName,
                componentNames=componentNames,
                description=None,
                shortcut=None,
            )
        except Exception as e:
            self._logger.error(f'Failed to update setup mode "{modeName}"')
            self._logger.error(traceback.format_exc())
            self._widget.showError("Update setup mode", f"Could not update setup mode: {e}")
            return

        self._activeModeName = modeName
        self.refreshModes(modeName)
        saveWarnings = saveResult.get("warnings") or []
        if saveWarnings:
            self._showWarnings("Setup mode updated with warnings", saveWarnings)

    def renameMode(self):
        modeName = self._widget.getSelectedModeName()
        if not modeName or self._setupModeController is None:
            return

        newName = self._widget.showNameDialog("Rename setup mode", "New name:", modeName)
        if not newName or newName == modeName:
            return

        if self._modeExists(newName):
            self._widget.showWarnings(
                "Rename setup mode",
                [f'Setup mode "{newName}" already exists.']
            )
            return

        try:
            self._setupModeController.renameSetupMode(modeName, newName)
        except Exception as e:
            self._logger.error(f'Failed to rename setup mode "{modeName}"')
            self._logger.error(traceback.format_exc())
            self._widget.showError("Rename setup mode", f"Could not rename setup mode: {e}")
            return

        if self._activeModeName == modeName:
            self._activeModeName = newName
        self.refreshModes(newName)

    def duplicateMode(self):
        modeName = self._widget.getSelectedModeName()
        if not modeName or self._setupModeController is None:
            return

        suggestedName = self._uniqueCopyName(modeName)
        newName = self._widget.showNameDialog(
            "Duplicate setup mode", "New mode name:", suggestedName
        )
        if not newName:
            return

        if self._modeExists(newName):
            self._widget.showWarnings(
                "Duplicate setup mode",
                [f'Setup mode "{newName}" already exists.']
            )
            return

        try:
            self._setupModeController.duplicateSetupMode(
                modeName, newName, shortcut=""
            )
        except Exception as e:
            self._logger.error(f'Failed to duplicate setup mode "{modeName}"')
            self._logger.error(traceback.format_exc())
            self._widget.showError("Duplicate setup mode", f"Could not duplicate setup mode: {e}")
            return

        self.refreshModes(self._activeModeName)

    def setShortcut(self):
        modeName = self._widget.getSelectedModeName()
        if not modeName or self._setupModeController is None:
            return

        mode = self._getMode(modeName)
        shortcut = self._widget.showShortcutDialog(modeName, mode.get("shortcut", ""))
        if shortcut is None:
            return

        shortcut = self._normalizeShortcut(shortcut)
        if not self._ensureShortcutAvailable(shortcut, modeName):
            return

        try:
            self._setupModeController.updateSetupModeMetadata(
                modeName, shortcut=shortcut or ""
            )
        except Exception as e:
            self._logger.error(f'Failed to update shortcut for setup mode "{modeName}"')
            self._logger.error(traceback.format_exc())
            self._widget.showError("Set shortcut", f"Could not update shortcut: {e}")
            return

        self.refreshModes(modeName)

    def editSafetySettings(self):
        result = self._widget.showSafetySettingsDialog(self._safetySettings)
        if result is None:
            return

        suppressedWarnings = list(self._safetySettings.get("suppressedWarnings", []) or [])
        self._safetySettings = dict(self.defaultSafetySettings)
        self._safetySettings.update(result)
        self._safetySettings["suppressedWarnings"] = suppressedWarnings
        if self._safetySettings.pop("clearSuppressedWarnings", False):
            self._safetySettings["suppressedWarnings"] = []
        self._saveSafetySettings()

    def deleteMode(self):
        modeName = self._widget.getSelectedModeName()
        if not modeName or self._setupModeController is None:
            return

        if not self._widget.askDeleteMode(modeName):
            return

        try:
            self._setupModeController.deleteSetupMode(modeName)
        except Exception as e:
            self._logger.error(f'Failed to delete setup mode "{modeName}"')
            self._logger.error(traceback.format_exc())
            self._widget.showError("Delete setup mode", f"Could not delete setup mode: {e}")
            return

        if self._activeModeName == modeName:
            self._activeModeName = None
        self.refreshModes(self._activeModeName)

    def revealModesFolder(self):
        if self._setupModeController is None:
            return

        try:
            folder = self._setupModeController.getSetupModeStorageDir()
            opened = QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(folder))
            if not opened:
                self._widget.showInformation("Setup modes folder", folder)
        except Exception as e:
            self._logger.error("Failed to open setup mode folder")
            self._logger.error(traceback.format_exc())
            self._widget.showError("Setup modes folder", f"Could not open folder: {e}")

    def _applyMode(self, modeName, source):
        if self._setupModeController is None:
            return False

        mode = self._getMode(modeName)
        if not mode:
            return False

        highPowerEntries = self._getHighPowerLaserEntries(mode)
        shouldWarnHighPower = (
            highPowerEntries
            and self._safetySettings.get("warnAboveLaserPowerThreshold", True)
            and (
                source != "shortcut"
                or self._safetySettings.get("confirmHighPowerShortcutApply", True)
            )
        )

        if shouldWarnHighPower:
            thresholdMw = self._laserPowerThresholdMw()
            if not self._widget.confirmHighPowerApply(modeName, highPowerEntries, thresholdMw):
                return False

        try:
            warnings = self._setupModeController.loadSetupMode(modeName)
        except Exception as e:
            self._logger.error(f'Failed to apply setup mode "{modeName}"')
            self._logger.error(traceback.format_exc())
            self._widget.showError("Apply setup mode", f"Could not apply setup mode: {e}")
            return False

        if warnings:
            self._showWarnings("Setup mode applied with warnings", warnings)

        self._activeModeName = modeName
        self.refreshModes(modeName)
        return True

    def _getMode(self, modeName):
        if not modeName or self._setupModeController is None:
            return {}

        try:
            return self._setupModeController.getSetupMode(modeName)
        except Exception as e:
            self._logger.error(f'Failed to read setup mode "{modeName}"')
            self._logger.error(traceback.format_exc())
            self._widget.showError("Setup modes", f"Could not read setup mode: {e}")
            return {}

    def _modeExists(self, modeName):
        try:
            return modeName in self._setupModeController.listSetupModes()
        except Exception:
            self._logger.error("Failed to list setup modes")
            self._logger.error(traceback.format_exc())
            return False

    def _makeModeSummary(self, mode):
        name = mode["name"]
        shortcut = self._normalizeShortcut(mode.get("shortcut"))
        displayName = f"{name} ({shortcut})" if shortcut else name
        includedComponents = (
            mode.get("includedComponents")
            or sorted((mode.get("state") or {}).keys())
        )

        return {
            "name": name,
            "displayName": displayName,
            "description": mode.get("description", ""),
            "shortcut": shortcut,
            "includedComponents": includedComponents,
        }

    def _makeInspectModeDetails(self, mode):
        details = self._makeModeSummary(mode)
        details.update({
            "createdAt": mode.get("createdAt"),
            "updatedAt": mode.get("updatedAt"),
            "stateSummary": self._summarizeSavedState(mode),
        })
        return details

    def _summarizeSavedState(self, mode):
        state = mode.get("state") or {}
        componentNames = mode.get("includedComponents") or sorted(state.keys())
        summaries = []

        for componentName in componentNames:
            componentState = state.get(componentName)
            label = self._componentLabel(componentName)
            summaries.append(f"{label}:")

            if componentName not in state:
                summaries.append("  not saved")
            elif componentName == "Settings":
                summaries.extend(self._summarizeSavedDetectorState(componentState))
            elif componentName == "Laser":
                summaries.extend(self._summarizeSavedLaserState(componentState))
            elif componentName == "Scan":
                summaries.extend(self._summarizeSavedScanState(componentState))
            elif componentName in ("SLMs", "SLM"):
                summaries.extend(self._summarizeSavedSLMState(componentState))
            else:
                count = self._countSavedLeaves(componentState)
                summaries.append(f"  {count} saved value(s)" if count else "  saved")

            summaries.append("")

        if summaries and summaries[-1] == "":
            summaries.pop()
        return summaries

    def _summarizeSavedDetectorState(self, state):
        detectors = (state or {}).get("detectors") or {}
        if not detectors:
            return ["  no detector state"]

        summaries = []
        for detectorName, detectorState in sorted(detectors.items(), key=lambda item: str(item[0])):
            roiMode = detectorState.get("roiMode", detectorState.get("frameMode"))
            summaries.append(f"  {detectorName}:")
            if roiMode is not None:
                summaries.append(f"    mode: {self._fmt(roiMode)}")
            if detectorState.get("roi") is not None:
                summaries.append(f"    ROI: {self._fmt(detectorState.get('roi'))}")
            if detectorState.get("binning") is not None:
                summaries.append(f"    binning: {self._fmt(detectorState.get('binning'))}")

            parameters = detectorState.get("parameters") or {}
            triggerText = self._findSavedTriggerText(parameters)
            if triggerText:
                summaries.append(f"    {triggerText}")

        return summaries

    def _summarizeSavedLaserState(self, state):
        state = state or {}
        summaries = []

        if state.get("currentPreset") is not None:
            summaries.append(f"  preset: {self._fmt(state.get('currentPreset'))}")
        if state.get("scanDefaultPreset") is not None:
            summaries.append(f"  scan preset: {self._fmt(state.get('scanDefaultPreset'))}")

        lasers = state.get("lasers") or {}
        if lasers:
            summaries.append("  states:")

        for laserName, laserState in self._savedLaserItemsInDisplayOrder(lasers, state):
            enabled = self._onOff(laserState.get("enabled"))
            if laserState.get("isBinary"):
                summaries.append(f"    {laserName}: {enabled}")
            else:
                units = laserState.get("valueUnits") or ""
                unitText = f" {units}" if units else ""
                summaries.append(
                    f"    {laserName}: {enabled}, {self._fmt(laserState.get('value'))}{unitText}"
                )

        return summaries or ["  no laser state"]

    def _savedLaserItemsInDisplayOrder(self, lasers, state):
        names = []
        savedOrder = state.get("laserOrder")
        if isinstance(savedOrder, list):
            names.extend(savedOrder)

        names.extend(self._currentLaserDisplayOrder())
        names.extend(lasers.keys())

        orderedItems = []
        seen = set()
        for name in names:
            if name in seen or name not in lasers:
                continue
            orderedItems.append((name, lasers[name]))
            seen.add(name)

        return orderedItems

    def _currentLaserDisplayOrder(self):
        setupModeController = getattr(self, "_setupModeController", None)
        controllers = getattr(setupModeController, "_controllers", {}) or {}
        laserController = controllers.get("Laser")
        if laserController is None:
            return []

        lasersManager = getattr(getattr(laserController, "_master", None), "lasersManager", None)
        if lasersManager is not None:
            try:
                return [laserName for laserName, _ in lasersManager]
            except Exception:
                pass

        widget = getattr(laserController, "_widget", None)
        laserModules = getattr(widget, "laserModules", None)
        if isinstance(laserModules, dict):
            return list(laserModules.keys())

        return []

    def _summarizeSavedSLMState(self, state):
        slms = (state or {}).get("slms") or {}
        if not slms:
            return ["  no SLM state"]

        summaries = []
        for slmKey, slmState in sorted(slms.items(), key=lambda item: str(item[0])):
            slmName = slmState.get("slmName") or slmKey
            config = slmState.get("configName") or slmState.get("configPath") or "None"
            summaries.append(f"  {slmName}: {self._fmt(config)}")

        return summaries

    def _summarizeSavedScanState(self, state):
        if not isinstance(state, dict) or not state:
            return ["  no scan state"]

        analog = state.get("analogParameterDict") or {}
        digital = state.get("digitalParameterDict") or {}
        mode = state.get("mode") or {}
        summaries = []

        if state.get("controller"):
            summaries.append(f"  controller: {self._fmt(state.get('controller'))}")
        if state.get("scanWidgetType"):
            summaries.append(f"  widget type: {self._fmt(state.get('scanWidgetType'))}")

        modeLines = self._summarizeSavedScanMode(mode)
        if modeLines:
            summaries.append("  mode:")
            summaries.extend(modeLines)

        sequenceTime = analog.get("sequence_time", digital.get("sequence_time"))
        if sequenceTime is not None:
            summaries.append(f"  sequence time: {self._fmt(sequenceTime)}")

        scanDimensions = state.get("positionersScan") or analog.get("scan_dim_target_device")
        if scanDimensions:
            summaries.append(f"  scan dimensions: {self._fmt(scanDimensions)}")

        axisLines = self._summarizeSavedScanAxes(analog)
        if axisLines:
            summaries.append("  axes:")
            summaries.extend(axisLines)

        digitalOverviewLines = self._summarizeSavedScanDigitalOverview(digital)
        if digitalOverviewLines:
            summaries.append("  digital:")
            summaries.extend(digitalOverviewLines)

        ttlLines = self._summarizeSavedScanTTL(digital)
        if ttlLines:
            summaries.append("  TTL:")
            summaries.extend(ttlLines)

        analogExtraLines = self._summarizeSavedScanExtras(
            analog,
            {
                "target_device", "axis_length", "axis_step_size",
                "axis_centerpos", "axis_startpos", "scan_dim_target_device",
                "sequence_time",
            }
        )
        if analogExtraLines:
            summaries.append("  analog extras:")
            summaries.extend(analogExtraLines)

        digitalExtraLines = self._summarizeSavedScanExtras(
            digital,
            {
                "target_device", "TTL_start", "TTL_end", "TTL_sequence",
                "TTL_sequence_axis", "sequence_time", "n_linesteps", "Nx", "Ny",
                "advanced_mode", "linestep_enable", "pulse_starts_s",
                "pulse_ends_s", "linestep_power_percent",
            }
        )
        if digitalExtraLines:
            summaries.append("  digital extras:")
            summaries.extend(digitalExtraLines)

        return summaries or ["  no scan state"]

    def _summarizeSavedScanMode(self, mode):
        if not isinstance(mode, dict):
            return []

        labels = {
            "repeatEnabled": "repeat",
            "scanMode": "scan mode",
            "contLaserMode": "continuous laser mode",
        }
        summaries = []
        for key in ("repeatEnabled", "scanMode", "contLaserMode"):
            value = mode.get(key)
            if value is not None:
                summaries.append(f"    {labels[key]}: {self._fmt(value)}")
        return summaries

    def _summarizeSavedScanAxes(self, analog):
        if not isinstance(analog, dict):
            return []

        devices = analog.get("target_device") or []
        if not isinstance(devices, list):
            devices = [devices]

        axisKeys = [
            ("length", "axis_length"),
            ("step", "axis_step_size"),
            ("center", "axis_centerpos"),
            ("start", "axis_startpos"),
        ]
        maxAxisCount = max(
            [len(devices)]
            + [
                len(analog.get(key) or [])
                for _, key in axisKeys
                if isinstance(analog.get(key), list)
            ]
        )

        summaries = []
        for index in range(maxAxisCount):
            device = self._scanListValue(devices, index, f"axis {index + 1}")
            parts = []
            for label, key in axisKeys:
                value = self._scanListValue(analog.get(key), index)
                if value is not None:
                    parts.append(f"{label} {self._fmt(value)}")

            if parts:
                summaries.append(f"    {device}: " + ", ".join(parts))

        return summaries

    def _summarizeSavedScanDigitalOverview(self, digital):
        if not isinstance(digital, dict):
            return []

        labels = {
            "Nx": "Nx",
            "Ny": "Ny",
            "n_linesteps": "line steps",
            "advanced_mode": "advanced mode",
        }
        summaries = []
        for key in ("Nx", "Ny", "n_linesteps", "advanced_mode"):
            if key in digital:
                summaries.append(f"    {labels[key]}: {self._fmt(digital.get(key))}")
        return summaries

    def _summarizeSavedScanTTL(self, digital):
        if not isinstance(digital, dict):
            return []

        deviceNames = self._scanTTLDeviceNames(digital)
        if not deviceNames:
            return []

        summaries = []
        for index, deviceName in enumerate(deviceNames):
            parts = []

            ttlStart = self._scanListValue(digital.get("TTL_start"), index)
            ttlEnd = self._scanListValue(digital.get("TTL_end"), index)
            if ttlStart is not None:
                parts.append(f"start {self._fmtMilliseconds(ttlStart)}")
            if ttlEnd is not None:
                parts.append(f"end {self._fmtMilliseconds(ttlEnd)}")

            ttlSequence = self._scanListValue(digital.get("TTL_sequence"), index)
            ttlAxis = self._scanListValue(digital.get("TTL_sequence_axis"), index)
            if ttlSequence is not None:
                parts.append(f"sequence {self._fmtShort(ttlSequence)}")
            if ttlAxis is not None:
                parts.append(f"axis {self._fmtShort(ttlAxis)}")

            self._appendDictTTLPart(parts, digital.get("linestep_enable"), deviceName, "enabled")
            self._appendDictTTLPart(
                parts, digital.get("pulse_starts_s"), deviceName, "starts",
                formatter=self._fmtMilliseconds
            )
            self._appendDictTTLPart(
                parts, digital.get("pulse_ends_s"), deviceName, "ends",
                formatter=self._fmtMilliseconds
            )
            self._appendDictTTLPart(
                parts, digital.get("linestep_power_percent"), deviceName, "power"
            )

            summaries.append(f"    {deviceName}: " + (", ".join(parts) if parts else "saved"))

        return summaries

    def _scanTTLDeviceNames(self, digital):
        names = []

        targetDevices = digital.get("target_device") or []
        if not isinstance(targetDevices, list):
            targetDevices = [targetDevices]
        names.extend([name for name in targetDevices if name is not None])

        for key in ("linestep_enable", "pulse_starts_s", "pulse_ends_s", "linestep_power_percent"):
            value = digital.get(key)
            if isinstance(value, dict):
                names.extend(value.keys())

        uniqueNames = []
        seen = set()
        for name in names:
            key = str(name)
            if key in seen:
                continue
            uniqueNames.append(name)
            seen.add(key)

        return uniqueNames

    def _appendDictTTLPart(self, parts, valuesByDevice, deviceName, label, formatter=None):
        if not isinstance(valuesByDevice, dict) or deviceName not in valuesByDevice:
            return
        formatter = formatter or self._fmtShort
        parts.append(f"{label} {formatter(valuesByDevice.get(deviceName))}")

    def _summarizeSavedScanExtras(self, values, excludedKeys):
        if not isinstance(values, dict):
            return []

        summaries = []
        for key in sorted(set(values.keys()) - set(excludedKeys), key=str):
            summaries.append(f"    {key}: {self._fmtShort(values.get(key))}")
        return summaries

    def _scanListValue(self, value, index, default=None):
        if isinstance(value, list):
            if 0 <= index < len(value):
                return value[index]
            return default
        return value if value is not None else default

    def _findSavedTriggerText(self, parameters):
        for parameterName, parameterState in parameters.items():
            if "trigger" not in parameterName.lower():
                continue
            value = parameterState.get("value") if isinstance(parameterState, dict) else parameterState
            return f"{parameterName}: {self._fmt(value)}"
        return None

    def _countSavedLeaves(self, value):
        if isinstance(value, dict):
            return sum(self._countSavedLeaves(child) for child in value.values())
        if isinstance(value, list):
            return 1
        return 1 if value is not None else 0

    def _buildUpdateSummaries(self, savedMode, snapshot):
        savedState = savedMode.get("state") or {}
        currentState = snapshot.get("state") or {}
        componentNames = (
            savedMode.get("includedComponents")
            or snapshot.get("includedComponents")
            or sorted(set(savedState.keys()) | set(currentState.keys()))
        )

        summaries = []
        for componentName in componentNames:
            oldState = savedState.get(componentName)
            newState = currentState.get(componentName)
            label = self._componentLabel(componentName)

            if componentName not in currentState:
                summaries.append(f"{label}: unavailable in current setup")
                continue
            if oldState == newState:
                summaries.append(f"{label}: no change")
                continue

            summaries.append(
                f"{label}: {self._summarizeComponentChange(componentName, oldState, newState)}"
            )

        return summaries

    def _componentLabel(self, componentName):
        labels = {
            "Settings": "Detector",
            "SLMs": "SLM",
            "SLM": "SLM",
            "LeicaStand": "Leica stand",
            "FlipMirror": "Flip mirror",
        }
        return labels.get(componentName, componentName)

    def _summarizeComponentChange(self, componentName, oldState, newState):
        if componentName == "Settings":
            return self._summarizeDetectorChange(oldState, newState)
        if componentName == "Laser":
            return self._summarizeLaserChange(oldState, newState)
        if componentName in ("SLMs", "SLM"):
            return self._summarizeSLMChange(oldState, newState)

        changes = self._collectScalarChanges(oldState, newState, maxChanges=3)
        if changes:
            return "; ".join(changes)

        count = self._countChangedLeaves(oldState, newState)
        return f"{count} value(s) changed" if count else "changed"

    def _summarizeDetectorChange(self, oldState, newState):
        oldDetectors = (oldState or {}).get("detectors") or {}
        newDetectors = (newState or {}).get("detectors") or {}
        changes = []

        for detectorName in sorted(set(oldDetectors.keys()) | set(newDetectors.keys())):
            oldDetector = oldDetectors.get(detectorName) or {}
            newDetector = newDetectors.get(detectorName) or {}

            oldMode = oldDetector.get("roiMode", oldDetector.get("frameMode"))
            newMode = newDetector.get("roiMode", newDetector.get("frameMode"))
            if oldMode != newMode:
                changes.append(f"{detectorName} mode {self._fmt(oldMode)} => {self._fmt(newMode)}")

            oldROI = oldDetector.get("roi")
            newROI = newDetector.get("roi")
            if oldROI != newROI and oldMode == newMode:
                changes.append(f"{detectorName} ROI {self._fmt(oldROI)} => {self._fmt(newROI)}")

            if oldDetector.get("binning") != newDetector.get("binning"):
                changes.append(
                    f"{detectorName} binning {self._fmt(oldDetector.get('binning'))} "
                    f"=> {self._fmt(newDetector.get('binning'))}"
                )

            changes.extend(
                self._summarizeParameterChanges(
                    detectorName,
                    oldDetector.get("parameters") or {},
                    newDetector.get("parameters") or {},
                    limit=max(0, 4 - len(changes)),
                )
            )
            if len(changes) >= 4:
                break

        return "; ".join(changes[:4]) if changes else "changed"

    def _summarizeLaserChange(self, oldState, newState):
        oldState = oldState or {}
        newState = newState or {}
        changes = []

        if oldState.get("currentPreset") != newState.get("currentPreset"):
            changes.append(
                f"preset {self._fmt(oldState.get('currentPreset'))} "
                f"=> {self._fmt(newState.get('currentPreset'))}"
            )
        if oldState.get("scanDefaultPreset") != newState.get("scanDefaultPreset"):
            changes.append(
                f"scan preset {self._fmt(oldState.get('scanDefaultPreset'))} "
                f"=> {self._fmt(newState.get('scanDefaultPreset'))}"
            )

        oldLasers = oldState.get("lasers") or {}
        newLasers = newState.get("lasers") or {}
        for laserName in sorted(set(oldLasers.keys()) | set(newLasers.keys())):
            oldLaser = oldLasers.get(laserName) or {}
            newLaser = newLasers.get(laserName) or {}
            if oldLaser.get("enabled") != newLaser.get("enabled"):
                changes.append(
                    f"{laserName} {self._onOff(oldLaser.get('enabled'))} "
                    f"=> {self._onOff(newLaser.get('enabled'))}"
                )
            elif oldLaser.get("value") != newLaser.get("value"):
                units = newLaser.get("valueUnits") or oldLaser.get("valueUnits") or ""
                changes.append(
                    f"{laserName} {self._fmt(oldLaser.get('value'))}{units} "
                    f"=> {self._fmt(newLaser.get('value'))}{units}"
                )
            if len(changes) >= 4:
                break

        return "; ".join(changes[:4]) if changes else "changed"

    def _summarizeSLMChange(self, oldState, newState):
        oldSlms = (oldState or {}).get("slms") or {}
        newSlms = (newState or {}).get("slms") or {}
        changes = []

        for slmKey in sorted(set(oldSlms.keys()) | set(newSlms.keys())):
            oldSlm = oldSlms.get(slmKey) or {}
            newSlm = newSlms.get(slmKey) or {}
            oldConfig = oldSlm.get("configName") or oldSlm.get("configPath")
            newConfig = newSlm.get("configName") or newSlm.get("configPath")
            if oldConfig != newConfig:
                slmName = newSlm.get("slmName") or oldSlm.get("slmName") or slmKey
                changes.append(f"{slmName} {self._fmt(oldConfig)} => {self._fmt(newConfig)}")
            if len(changes) >= 4:
                break

        return "; ".join(changes[:4]) if changes else "changed"

    def _summarizeParameterChanges(self, prefix, oldParameters, newParameters, limit):
        if limit <= 0:
            return []

        changes = []
        for parameterName in sorted(set(oldParameters.keys()) | set(newParameters.keys())):
            oldParameter = oldParameters.get(parameterName)
            newParameter = newParameters.get(parameterName)
            oldValue = oldParameter.get("value") if isinstance(oldParameter, dict) else oldParameter
            newValue = newParameter.get("value") if isinstance(newParameter, dict) else newParameter
            if oldValue != newValue:
                changes.append(
                    f"{prefix} {parameterName} {self._fmt(oldValue)} => {self._fmt(newValue)}"
                )
                if len(changes) >= limit:
                    break
        return changes

    def _collectScalarChanges(self, oldValue, newValue, prefix="", maxChanges=3):
        if maxChanges <= 0 or oldValue == newValue:
            return []

        if isinstance(oldValue, dict) and isinstance(newValue, dict):
            changes = []
            for key in sorted(set(oldValue.keys()) | set(newValue.keys()), key=str):
                childPrefix = f"{prefix}.{key}" if prefix else str(key)
                changes.extend(
                    self._collectScalarChanges(
                        oldValue.get(key),
                        newValue.get(key),
                        childPrefix,
                        maxChanges=maxChanges - len(changes),
                    )
                )
                if len(changes) >= maxChanges:
                    break
            return changes

        if isinstance(oldValue, list) and isinstance(newValue, list):
            if oldValue == newValue:
                return []
            return [f"{prefix or 'value'} {self._fmt(oldValue)} => {self._fmt(newValue)}"]

        return [f"{prefix or 'value'} {self._fmt(oldValue)} => {self._fmt(newValue)}"]

    def _countChangedLeaves(self, oldValue, newValue):
        if oldValue == newValue:
            return 0
        if isinstance(oldValue, dict) and isinstance(newValue, dict):
            return sum(
                self._countChangedLeaves(oldValue.get(key), newValue.get(key))
                for key in set(oldValue.keys()) | set(newValue.keys())
            )
        if isinstance(oldValue, list) and isinstance(newValue, list):
            return 0 if oldValue == newValue else 1
        return 1

    def _fmt(self, value):
        if value is None:
            return "None"
        if isinstance(value, bool):
            return self._onOff(value)
        if isinstance(value, float):
            return f"{value:.4g}"
        if isinstance(value, (list, tuple)):
            return "[" + ", ".join(self._fmt(item) for item in value) + "]"
        return str(value)

    def _fmtShort(self, value, maxLength=140):
        text = self._fmt(value)
        if len(text) <= maxLength:
            return text
        return text[:maxLength - 3] + "..."

    def _fmtMilliseconds(self, value):
        if isinstance(value, (list, tuple)):
            return "[" + ", ".join(self._fmtMilliseconds(item) for item in value) + "]"

        seconds = self._asFloat(value)
        if seconds is None:
            return self._fmtShort(value)

        return f"{self._fmtDecimal(seconds * 1000)} ms"

    def _fmtDecimal(self, value):
        text = f"{value:.6f}".rstrip("0").rstrip(".")
        return "0" if text in ("", "-0") else text

    def _onOff(self, value):
        return "ON" if bool(value) else "OFF"

    def _showWarnings(self, title, warnings):
        visibleWarnings = self._filterSuppressedWarnings(warnings)
        if not visibleWarnings:
            return

        shouldSuppress = self._widget.showWarnings(
            title, visibleWarnings, allowSuppress=True
        )
        if shouldSuppress:
            self._suppressWarnings(visibleWarnings)

    def _filterSuppressedWarnings(self, warnings):
        suppressed = set(self._safetySettings.get("suppressedWarnings", []) or [])
        visibleWarnings = []
        seen = set()

        for warning in warnings:
            warning = str(warning)
            if warning in suppressed or warning in seen:
                continue
            visibleWarnings.append(warning)
            seen.add(warning)

        return visibleWarnings

    def _suppressWarnings(self, warnings):
        suppressedWarnings = list(self._safetySettings.get("suppressedWarnings", []) or [])
        suppressedSet = set(suppressedWarnings)

        for warning in warnings:
            warning = str(warning)
            if warning not in suppressedSet:
                suppressedWarnings.append(warning)
                suppressedSet.add(warning)

        self._safetySettings["suppressedWarnings"] = suppressedWarnings

    def _rebuildShortcuts(self, modeSummaries):
        self._clearShortcuts()

        for summary in modeSummaries:
            shortcutText = self._normalizeShortcut(summary.get("shortcut"))
            if not shortcutText:
                continue

            shortcut = QtGui.QKeySequence(shortcutText)
            if self._isEmptyShortcut(shortcut):
                continue

            qshortcut = QtWidgets.QShortcut(shortcut, self._widget)
            qshortcut.setContext(QtCore.Qt.ApplicationShortcut)
            qshortcut.activated.connect(
                lambda modeName=summary["name"]: self._applyMode(modeName, source="shortcut")
            )
            self._modeShortcuts.append(qshortcut)

    def _clearShortcuts(self):
        for shortcut in self._modeShortcuts:
            shortcut.setParent(None)
        self._modeShortcuts = []

    def _ensureShortcutAvailable(self, shortcut, targetModeName):
        if not shortcut:
            return True

        conflictModeName = self._findShortcutConflict(shortcut, targetModeName)
        if conflictModeName is None:
            return True

        if not self._widget.askShortcutConflict(shortcut, conflictModeName):
            return False

        self._setupModeController.updateSetupModeMetadata(
            conflictModeName, shortcut=""
        )
        return True

    def _findShortcutConflict(self, shortcut, targetModeName):
        shortcutKey = self._shortcutCompareKey(shortcut)
        if shortcutKey is None:
            return None

        for modeName in self._setupModeController.listSetupModes():
            if modeName == targetModeName:
                continue

            try:
                modeShortcut = self._setupModeController.getSetupMode(modeName).get("shortcut")
            except Exception:
                continue

            if self._shortcutCompareKey(modeShortcut) == shortcutKey:
                return modeName

        return None

    def _normalizeShortcut(self, shortcut):
        if shortcut is None:
            return None

        shortcutText = str(shortcut).strip()
        if not shortcutText:
            return None

        sequence = QtGui.QKeySequence(shortcutText)
        if self._isEmptyShortcut(sequence):
            return None

        return self._shortcutToText(sequence) or shortcutText

    def _shortcutCompareKey(self, shortcut):
        shortcut = self._normalizeShortcut(shortcut)
        if not shortcut:
            return None

        sequence = QtGui.QKeySequence(shortcut)
        try:
            text = sequence.toString(QtGui.QKeySequence.PortableText)
        except TypeError:
            text = sequence.toString()

        return (text or shortcut).lower()

    def _shortcutToText(self, sequence):
        try:
            return sequence.toString(QtGui.QKeySequence.NativeText).strip()
        except TypeError:
            return sequence.toString().strip()

    def _isEmptyShortcut(self, sequence):
        try:
            return sequence.isEmpty()
        except AttributeError:
            try:
                return sequence.count() == 0
            except Exception:
                return not sequence.toString()

    def _uniqueCopyName(self, modeName):
        baseName = f"{modeName} copy"
        candidate = baseName
        index = 2

        while self._modeExists(candidate):
            candidate = f"{baseName} {index}"
            index += 1

        return candidate

    def _getHighPowerLaserEntries(self, mode):
        laserState = ((mode.get("state") or {}).get("Laser") or {})
        lasers = laserState.get("lasers") or {}
        if not isinstance(lasers, dict):
            return []

        thresholdMw = self._laserPowerThresholdMw()
        entries = []

        for laserName, savedState in lasers.items():
            if not isinstance(savedState, dict):
                continue
            if not savedState.get("enabled", False):
                continue
            if savedState.get("isBinary", False):
                continue

            value = self._asFloat(savedState.get("value"))
            if value is None or value <= thresholdMw:
                continue

            units = savedState.get("valueUnits")
            if not self._isMilliwattUnit(units):
                continue

            entries.append({
                "laserName": laserName,
                "value": value,
                "units": units or "mW",
            })

        return entries

    def _isMilliwattUnit(self, units):
        if units is None or str(units).strip() == "":
            return True

        normalized = str(units).strip().lower()
        return normalized in {"mw", "milliwatt", "milliwatts"}

    def _laserPowerThresholdMw(self):
        thresholdMw = self._asFloat(
            self._safetySettings.get(
                "laserPowerThresholdMw",
                self.defaultSafetySettings["laserPowerThresholdMw"]
            )
        )
        if thresholdMw is None:
            return self.defaultSafetySettings["laserPowerThresholdMw"]
        return thresholdMw

    def _asFloat(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _loadSafetySettings(self):
        settings = dict(self.defaultSafetySettings)

        try:
            with open(self._safetySettingsPath, "r", encoding="utf-8") as file:
                savedSettings = json.load(file)
            if isinstance(savedSettings, dict):
                savedSettings = dict(savedSettings)
                savedSettings.pop("suppressedWarnings", None)
                savedSettings.pop("clearSuppressedWarnings", None)
                settings.update(savedSettings)
        except FileNotFoundError:
            pass
        except Exception:
            self._logger.error("Failed to load setup mode safety settings")
            self._logger.error(traceback.format_exc())

        settings["suppressedWarnings"] = []
        return settings

    def _saveSafetySettings(self):
        try:
            persistentSettings = dict(self._safetySettings)
            persistentSettings.pop("suppressedWarnings", None)
            persistentSettings.pop("clearSuppressedWarnings", None)

            tmpPath = self._safetySettingsPath + ".tmp"
            with open(tmpPath, "w", encoding="utf-8") as file:
                json.dump(persistentSettings, file, indent=2, sort_keys=True)
                file.write("\n")
            os.replace(tmpPath, self._safetySettingsPath)
        except Exception:
            self._logger.error("Failed to save setup mode safety settings")
            self._logger.error(traceback.format_exc())
            self._widget.showError(
                "Setup mode safety",
                "Could not save setup mode safety settings."
            )


# Copyright (C) 2026 ImSwitch developers
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
