from typing import Dict, List

from imswitch.imcommon.model import APIExport
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model import configfiletools
from qtpy import QtCore, QtGui, QtWidgets

class PositionerController(ImConWidgetController):
    """ Linked to PositionerWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._liveUpdateIntervalMs = 300
        self._liveUpdateTimer = QtCore.QTimer()
        self._liveUpdateTimer.setInterval(self._liveUpdateIntervalMs)
        self._liveUpdateTimer.timeout.connect(self._refreshLiveUpdatedPositioners)

        self.settingAttr = False
        self._previousJoystickState = None
        self._liveUpdateAvailable = {}
        self._liveUpdateEnabled = {}
        self._positionerShortcutSettings = {}
        self._positionerShortcuts = []
        self._shortcutsDirty = False

        savedShortcutSettings = self._loadPositionerShortcutSettingsFromSetup()
        savedMovementShortcuts = savedShortcutSettings.get(
            'movement',
            savedShortcutSettings.get('positioners', {})
        )
        self._movementPrefix = self._normalizeShortcutPrefix(
            savedShortcutSettings.get('movementPrefix'),
            'Shift'
        )
        self._coarseStepMultiplier = self._normalizeCoarseStepMultiplier(
            savedShortcutSettings.get('coarseStepMultiplier', 5.0)
        )
        self._isCoarseMode = False
        self._modeToggleShortcut = self._normalizeFullShortcut(
            savedShortcutSettings.get('modeToggle', '')
        )
        self._joystickShortcut = self._normalizeFullShortcut(
            savedShortcutSettings.get('joystickToggle', '')
        )

        self.__logger = initLogger(self, tryInheritParent=True)

        # Set up positioners
        for pName, pManager in self._master.positionersManager:
            if not pManager.forPositioning:
                continue

            if not pManager.isAvailable:
                continue

            self._liveUpdateAvailable[pName] = bool(getattr(pManager, 'liveUpdate', False))
            self._liveUpdateEnabled[pName] = self._liveUpdateAvailable[pName]
            self._positionerShortcutSettings[pName] = {
                axis: {
                    'up': self._normalizeShortcutKey(
                        savedMovementShortcuts.get(pName, {}).get(axis, {}).get('up', '')
                    ),
                    'down': self._normalizeShortcutKey(
                        savedMovementShortcuts.get(pName, {}).get(axis, {}).get('down', '')
                    )
                }
                for axis in pManager.axes
            }

            if pManager.joystick:
                self._widget.addJoystick(pName)

            speed = hasattr(pManager, 'speed')
            self._widget.addPositioner(pName, pManager.axes, speed, pManager.joystick)
            for axis in pManager.axes:
                position = pManager.position[axis]
                self.setSharedAttr(pName, axis, _positionAttr, position)
                self._widget.updatePosition(pName, axis, position)
                if speed:
                    self.setSharedAttr(pName, axis, _positionAttr, pManager.speed)

            if pManager.joystick:
                # Set joystick checkbox status for first start
                self.setJoystickCheckStatus(self._master.positionersManager[pName].joystickStatus)
                # Connect channels
                self._commChannel.sigRecordingStarted.connect(
                    lambda pName=pName: self.setJoystickStatusForRec(False, pName)
                )
                self._commChannel.sigRecordingEnded.connect(
                    lambda pName=pName: self.setJoystickStatusAfterRec(pName)
                )
                # self._commChannel.sigInitiateEtMonalisa.connect(lambda state, pName=pName: self.setJoystickStatus(not state, pName))

                if hasattr(pManager, "sigJoystickStatusChanged"):
                    pManager.sigJoystickStatusChanged.connect(
                        lambda enabled, pName=pName: self._onManagerJoystickStatusChanged(pName, enabled)
                    )
        
        self._widget.sigJoystickToggled.connect(self.requestJoystickStatus)
        self._widget.sigSettingsClicked.connect(self.openSettingsDialog)
        self._widget.sigSettingsChanged.connect(self.applySettings)
        self._widget.sigStepModeChanged.connect(self.setStepMode)
        self._widget.setCoarseStepMultiplier(self._coarseStepMultiplier)
        self._widget.setStepMode(self._isCoarseMode)
        self._updateLiveTimerState()
        self._refreshLiveUpdatedPositioners()
        self._rebuildPositionerShortcuts()

        # Connect CommunicationChannel signals
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged)
        self._commChannel.sigSetSpeed.connect(lambda speed: self.setSpeedGUI(speed))


        # Connect PositionerWidget signals
        self._widget.sigStepUpClicked.connect(self.stepUp)
        self._widget.sigStepDownClicked.connect(self.stepDown)
        self._widget.sigsetSpeedClicked.connect(self.setSpeedGUI)
    

    def _onManagerJoystickStatusChanged(self, pName, enabled):
        self.setJoystickCheckStatus(enabled)

    def _hasLiveUpdatePositioner(self):
        for pName, pManager in self._master.positionersManager:
            if not pManager.forPositioning:
                continue
            if not pManager.isAvailable:
                continue
            if self._isLiveUpdateEnabled(pName, pManager):
                return True
        return False


    def _updateLiveTimerState(self):
        if self._hasLiveUpdatePositioner():
            if not self._liveUpdateTimer.isActive():
                self._liveUpdateTimer.start()
        else:
            if self._liveUpdateTimer.isActive():
                self._liveUpdateTimer.stop()


    def _refreshLiveUpdatedPositioners(self):
        for pName, pManager in self._master.positionersManager:
            if not pManager.forPositioning:
                continue
            if not pManager.isAvailable:
                continue
            if not self._isLiveUpdateEnabled(pName, pManager):
                continue

            self.updatePosition(pName, 'all')

    def _isLiveUpdateEnabled(self, positionerName, pManager=None):
        if pManager is None:
            pManager = self._master.positionersManager[positionerName]

        return bool(
            getattr(pManager, 'liveUpdate', False)
            and self._liveUpdateAvailable.get(positionerName, False)
            and self._liveUpdateEnabled.get(positionerName, False)
        )

    def openSettingsDialog(self):
        positionerSettings = {}
        for pName, pManager in self._master.positionersManager:
            if not pManager.forPositioning:
                continue
            if not pManager.isAvailable:
                continue

            positionerSettings[pName] = {
                'liveUpdateAvailable': self._liveUpdateAvailable.get(pName, False),
                'liveUpdateEnabled': self._liveUpdateEnabled.get(pName, False),
            }

        self._setPositionerShortcutsEnabled(False)
        try:
            self._widget.showSettingsDialog(
                self._liveUpdateIntervalMs,
                positionerSettings,
                {
                    'movementPrefix': self._movementPrefix,
                    'coarseStepMultiplier': self._coarseStepMultiplier,
                    'modeToggle': self._modeToggleShortcut,
                    'joystickAvailable': self._getJoystickPositionerName() is not None,
                    'joystickToggle': self._joystickShortcut,
                    'movement': self._positionerShortcutSettings
                },
                settingsValidator=self._validatePositionerSettingsShortcuts
            )
        finally:
            self._setPositionerShortcutsEnabled(True)

    def applySettings(self, settings, liveUpdateEnabled=None):
        if isinstance(settings, dict):
            warning = self._validatePositionerSettingsShortcuts(settings)
            if warning:
                self.__logger.warning(warning)
                return

            liveUpdateIntervalMs = settings.get('liveUpdateIntervalMs', self._liveUpdateIntervalMs)
            liveUpdateEnabled = settings.get('liveUpdateEnabled', {})
            self._movementPrefix = self._normalizeShortcutPrefix(
                settings.get('movementPrefix'),
                self._movementPrefix
            )
            self._coarseStepMultiplier = self._normalizeCoarseStepMultiplier(
                settings.get('coarseStepMultiplier', self._coarseStepMultiplier)
            )
            self._widget.setCoarseStepMultiplier(self._coarseStepMultiplier)
            self._modeToggleShortcut = self._normalizeFullShortcut(
                settings.get('modeToggle', self._modeToggleShortcut)
            )
            self._joystickShortcut = self._normalizeFullShortcut(
                settings.get('joystickToggle', self._joystickShortcut)
            )
            self._updatePositionerShortcutSettings(
                settings.get('movement', settings.get('shortcuts', {}))
            )
            self._writePositionerShortcutSettingsToSetup()
            self._shortcutsDirty = True
        else:
            liveUpdateIntervalMs = settings
            liveUpdateEnabled = liveUpdateEnabled or {}

        self._liveUpdateIntervalMs = max(100, min(2000, int(liveUpdateIntervalMs)))
        self._liveUpdateTimer.setInterval(self._liveUpdateIntervalMs)

        for pName, enabled in liveUpdateEnabled.items():
            if not self._liveUpdateAvailable.get(pName, False):
                self._liveUpdateEnabled[pName] = False
                continue

            self._liveUpdateEnabled[pName] = bool(enabled)

        if self._hasLiveUpdatePositioner():
            self._liveUpdateTimer.start()
        else:
            self._liveUpdateTimer.stop()

        self._rebuildPositionerShortcuts()

    def _updatePositionerShortcutSettings(self, shortcutSettings):
        for pName, axisSettings in shortcutSettings.items():
            if pName not in self._positionerShortcutSettings:
                continue

            for axis, shortcuts in axisSettings.items():
                if axis not in self._positionerShortcutSettings[pName]:
                    continue

                self._positionerShortcutSettings[pName][axis] = {
                    'up': self._normalizeShortcutKey(shortcuts.get('up', '')),
                    'down': self._normalizeShortcutKey(shortcuts.get('down', ''))
                }

    def _loadPositionerShortcutSettingsFromSetup(self):
        shortcutsInfo = getattr(self._setupInfo, 'shortcuts', None)
        if shortcutsInfo is None:
            return {}

        if isinstance(shortcutsInfo, dict):
            positionerShortcuts = shortcutsInfo.get('positioners', {})
        else:
            positionerShortcuts = getattr(shortcutsInfo, 'positioners', {})

        return positionerShortcuts if isinstance(positionerShortcuts, dict) else {}

    def _writePositionerShortcutSettingsToSetup(self):
        shortcutsInfo = getattr(self._setupInfo, 'shortcuts', None)
        if shortcutsInfo is None:
            return

        shortcutSettings = {
            'movementPrefix': self._movementPrefix,
            'coarseStepMultiplier': self._coarseStepMultiplier,
            'modeToggle': self._modeToggleShortcut,
            'joystickToggle': self._joystickShortcut,
            'movement': self._positionerShortcutSettings
        }

        if isinstance(shortcutsInfo, dict):
            shortcutsInfo['positioners'] = shortcutSettings
        else:
            shortcutsInfo.positioners = shortcutSettings

    def _savePositionerShortcutSettingsToSetup(self):
        if not self._shortcutsDirty:
            return

        self._writePositionerShortcutSettingsToSetup()
        try:
            options, _ = configfiletools.loadOptions()
            configfiletools.saveSetupInfo(options, self._setupInfo)
            self._shortcutsDirty = False
        except Exception as e:
            self.__logger.error(f'Failed to save positioner shortcuts to setup file: {e}')

    def _validatePositionerSettingsShortcuts(self, settings):
        requestedShortcuts = self._collectRequestedPositionerShortcuts(settings)
        seenShortcuts = {}
        for sequenceText, actionName in requestedShortcuts:
            sequence = QtGui.QKeySequence(sequenceText)
            if self._isEmptyShortcut(sequence):
                continue

            compareKey = self._shortcutCompareKey(sequence)
            if compareKey in seenShortcuts:
                return (
                    f'Shortcut "{sequenceText}" is already assigned to '
                    f'{seenShortcuts[compareKey]}. Choose another shortcut.'
                )

            seenShortcuts[compareKey] = actionName

        existingShortcuts = self._collectExistingShortcutAssignments()
        for sequenceText, actionName in requestedShortcuts:
            sequence = QtGui.QKeySequence(sequenceText)
            if self._isEmptyShortcut(sequence):
                continue

            compareKey = self._shortcutCompareKey(sequence)
            existingActionName = existingShortcuts.get(compareKey)
            if existingActionName:
                return (
                    f'Shortcut "{sequenceText}" is already assigned to '
                    f'{existingActionName}. Choose another shortcut.'
                )

        return None

    def _collectRequestedPositionerShortcuts(self, settings):
        movementPrefix = self._normalizeShortcutPrefix(
            settings.get('movementPrefix'),
            self._movementPrefix
        )

        requestedShortcuts = []
        movementSettings = settings.get('movement', settings.get('shortcuts', {}))
        for pName, axisSettings in movementSettings.items():
            for axis, shortcuts in axisSettings.items():
                for directionName, directionLabel in (('up', '+'), ('down', '-')):
                    keyText = self._normalizeShortcutKey(shortcuts.get(directionName, ''))
                    if not keyText:
                        continue

                    movementSequence = self._buildPositionerShortcutSequence(movementPrefix, keyText)
                    if movementSequence:
                        requestedShortcuts.append(
                            (movementSequence, f'{pName} {axis} {directionLabel}')
                        )

        modeToggleShortcut = self._normalizeFullShortcut(settings.get('modeToggle', ''))
        if modeToggleShortcut:
            requestedShortcuts.append((modeToggleShortcut, 'coarse/fine toggle'))

        joystickShortcut = self._normalizeFullShortcut(settings.get('joystickToggle', ''))
        if joystickShortcut and self._getJoystickPositionerName() is not None:
            requestedShortcuts.append((joystickShortcut, 'joystick toggle'))

        return requestedShortcuts

    def _collectExistingShortcutAssignments(self):
        existingShortcuts = {}
        rootWidget = self._widget.window()
        ignoredShortcuts = set(getattr(self, '_positionerShortcuts', []))

        for action in rootWidget.findChildren(QtWidgets.QAction):
            sequence = action.shortcut()
            if self._isEmptyShortcut(sequence):
                continue

            compareKey = self._shortcutCompareKey(sequence)
            actionName = action.text().replace('&', '').strip() or 'another action'
            existingShortcuts.setdefault(compareKey, actionName)

        for shortcut in rootWidget.findChildren(QtWidgets.QShortcut):
            if shortcut in ignoredShortcuts:
                continue

            sequence = shortcut.key()
            if self._isEmptyShortcut(sequence):
                continue

            compareKey = self._shortcutCompareKey(sequence)
            existingShortcuts.setdefault(compareKey, self._shortcutOwnerName(shortcut))

        return existingShortcuts

    def _shortcutOwnerName(self, shortcut):
        parent = shortcut.parent()
        while parent is not None and parent is not self._widget.window():
            objectName = parent.objectName()
            if objectName:
                return objectName

            parent = parent.parent()

        return 'another application shortcut'

    def _rebuildPositionerShortcuts(self):
        self._clearPositionerShortcuts()

        usedSequences = set()
        for pName, axisSettings in self._positionerShortcutSettings.items():
            try:
                pManager = self._master.positionersManager[pName]
            except Exception:
                continue

            if not pManager.forPositioning or not pManager.isAvailable:
                continue

            for axis in pManager.axes:
                shortcuts = axisSettings.get(axis, {})
                for directionName, direction in (('up', 1), ('down', -1)):
                    keyText = self._normalizeShortcutKey(shortcuts.get(directionName, ''))
                    if not keyText:
                        continue

                    self._addPositionerShortcut(
                        usedSequences, self._movementPrefix, keyText,
                        pName, axis, direction
                    )

        self._addModeToggleShortcut(usedSequences)
        self._addJoystickShortcut(usedSequences)

    def _addPositionerShortcut(self, usedSequences, prefix, keyText, pName, axis, direction):
        sequenceText = self._buildPositionerShortcutSequence(prefix, keyText)
        if not sequenceText:
            return

        sequence = QtGui.QKeySequence(sequenceText)
        if self._isEmptyShortcut(sequence):
            return

        compareKey = self._shortcutCompareKey(sequence)
        if compareKey in usedSequences:
            self.__logger.warning(
                f'Positioner shortcut "{sequenceText}" is duplicated; '
                f'skipping shortcut for {pName} axis {axis}'
            )
            return

        usedSequences.add(compareKey)
        qshortcut = QtWidgets.QShortcut(sequence, self._widget)
        qshortcut.setContext(QtCore.Qt.ApplicationShortcut)
        qshortcut.activated.connect(
            lambda pName=pName, axis=axis, direction=direction:
            self._triggerPositionerShortcut(pName, axis, direction)
        )
        self._positionerShortcuts.append(qshortcut)

    def _addModeToggleShortcut(self, usedSequences):
        if not self._modeToggleShortcut:
            return

        sequence = QtGui.QKeySequence(self._modeToggleShortcut)
        if self._isEmptyShortcut(sequence):
            return

        compareKey = self._shortcutCompareKey(sequence)
        if compareKey in usedSequences:
            self.__logger.warning(
                f'Coarse/Fine shortcut "{self._modeToggleShortcut}" is duplicated; skipping mode shortcut'
            )
            return

        usedSequences.add(compareKey)
        qshortcut = QtWidgets.QShortcut(sequence, self._widget)
        qshortcut.setContext(QtCore.Qt.ApplicationShortcut)
        qshortcut.activated.connect(self.toggleStepMode)
        self._positionerShortcuts.append(qshortcut)

    def _addJoystickShortcut(self, usedSequences):
        if not self._joystickShortcut or self._getJoystickPositionerName() is None:
            return

        sequence = QtGui.QKeySequence(self._joystickShortcut)
        if self._isEmptyShortcut(sequence):
            return

        compareKey = self._shortcutCompareKey(sequence)
        if compareKey in usedSequences:
            self.__logger.warning(
                f'Joystick shortcut "{self._joystickShortcut}" is duplicated; skipping joystick shortcut'
            )
            return

        usedSequences.add(compareKey)
        qshortcut = QtWidgets.QShortcut(sequence, self._widget)
        qshortcut.setContext(QtCore.Qt.ApplicationShortcut)
        qshortcut.activated.connect(self.toggleJoystick)
        self._positionerShortcuts.append(qshortcut)

    def _triggerPositionerShortcut(self, positionerName, axis, direction):
        try:
            stepSize = self._widget.getStepSize(positionerName, axis)
        except Exception as e:
            self.__logger.error(
                f'Could not read step size for positioner shortcut '
                f'{positionerName} axis {axis}: {e}'
            )
            return

        multiplier = self._getStepModeMultiplier()
        self.move(positionerName, axis, direction * stepSize * multiplier)

    def setStepMode(self, coarseMode):
        self._isCoarseMode = bool(coarseMode)
        self._widget.setStepMode(self._isCoarseMode)

    def toggleStepMode(self):
        self.setStepMode(not self._isCoarseMode)

    def _getStepModeMultiplier(self):
        return self._coarseStepMultiplier if self._isCoarseMode else 1.0

    def toggleJoystick(self):
        pName = self._getJoystickPositionerName()
        if pName is None:
            return

        pManager = self._master.positionersManager[pName]
        currentState = getattr(pManager, 'joystickStatus', None)
        if currentState is None and hasattr(self._widget, 'joystickCheck'):
            currentState = self._widget.joystickCheck.isChecked()

        targetState = not bool(currentState)
        self.requestJoystickStatus(targetState, pName)
        self.setJoystickCheckStatus(getattr(pManager, 'joystickStatus', targetState))

    def _getJoystickPositionerName(self):
        for pName, pManager in self._master.positionersManager:
            if not pManager.forPositioning:
                continue
            if not pManager.isAvailable:
                continue
            if not getattr(pManager, 'joystick', False):
                continue
            if not hasattr(pManager, 'setJoystickEnabled'):
                continue

            return pName

        return None

    def _clearPositionerShortcuts(self):
        for shortcut in self._positionerShortcuts:
            shortcut.setParent(None)
        self._positionerShortcuts = []

    def _setPositionerShortcutsEnabled(self, enabled):
        for shortcut in self._positionerShortcuts:
            shortcut.setEnabled(enabled)

    def _buildPositionerShortcutSequence(self, prefix, keyText):
        prefix = self._normalizeShortcutPrefix(prefix, None)
        keyText = self._normalizeShortcutKey(keyText)
        if not prefix or not keyText:
            return None

        return f'{prefix}+{keyText}'

    def _normalizeShortcutPrefix(self, prefix, default):
        if prefix is None:
            return default

        prefix = str(prefix).strip()
        if not prefix:
            return default

        prefixAliases = {
            'control': 'Ctrl',
            'ctrl': 'Ctrl',
            'shift': 'Shift',
            'alt': 'Alt',
            'meta': 'Meta',
            'cmd': 'Meta',
            'command': 'Meta'
        }
        return prefixAliases.get(prefix.lower(), default)

    def _normalizeShortcutKey(self, keyText):
        keyText = str(keyText or '').strip()
        if not keyText:
            return ''

        try:
            sequence = QtGui.QKeySequence(keyText)
            keyText = self._shortcutToText(sequence) or keyText
        except Exception:
            pass

        modifiers = {'ctrl', 'control', 'shift', 'alt', 'meta', 'cmd', 'command'}
        parts = [part.strip() for part in keyText.split('+') if part.strip()]
        nonModifierParts = [
            part for part in parts
            if part.lower() not in modifiers
        ]

        if nonModifierParts:
            return '+'.join(nonModifierParts)

        return ''

    def _normalizeFullShortcut(self, shortcutText):
        shortcutText = str(shortcutText or '').strip()
        if not shortcutText:
            return ''

        sequence = QtGui.QKeySequence(shortcutText)
        if self._isEmptyShortcut(sequence):
            return ''

        return self._shortcutToText(sequence) or shortcutText

    def _normalizeCoarseStepMultiplier(self, multiplier):
        try:
            multiplier = float(multiplier)
        except (TypeError, ValueError):
            return 5.0

        return max(1.0, min(1000.0, multiplier))

    def _shortcutCompareKey(self, sequence):
        try:
            text = sequence.toString(QtGui.QKeySequence.PortableText)
        except TypeError:
            text = sequence.toString()

        return text.lower()

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
            except AttributeError:
                return not self._shortcutToText(sequence)

    def setJoystickStatusAfterRec(self, pName):
        if self._previousJoystickState:
            # if the joystick was enabled before the scan, enable it again after rec
            self.requestJoystickStatus(True, pName)
        self._previousJoystickState = None

    def setJoystickStatusForRec(self, enabled, pName):
        if not enabled and self._previousJoystickState is None:
            pManager = self._master.positionersManager[pName]
            self._previousJoystickState = getattr(pManager, "joystickStatus", False)
        self.requestJoystickStatus(enabled, pName)


    def requestJoystickStatus(self, enabled, pName):
        pManager = self._master.positionersManager[pName]

        if not hasattr(pManager, "setJoystickEnabled"):
            return

        pManager.setJoystickEnabled(enabled)

    def setJoystickCheckStatus(self, state:bool):
        if not hasattr(self._widget, 'joystickCheck'):
            return

        if not state and self._widget.joystickCheck.isChecked():
            self._widget.joystickCheck.setChecked(False)
        if state and not self._widget.joystickCheck.isChecked():
            self._widget.joystickCheck.setChecked(True)

    def closeEvent(self):
        if hasattr(self, '_liveUpdateTimer') and self._liveUpdateTimer.isActive():
            self._liveUpdateTimer.stop()
        if hasattr(self, '_shortcutsDirty'):
            self._savePositionerShortcutSettingsToSetup()
        if hasattr(self, '_positionerShortcuts'):
            self._clearPositionerShortcuts()
        self._master.positionersManager.execOnAll(
            lambda p: [p.setPosition(0, axis) for axis in p.axes],
            condition = lambda p: p.resetOnClose
        )

    def getPos(self):
        return self._master.positionersManager.execOnAll(lambda p: p.position)

    def getSpeed(self):
        return self._master.positionersManager.execOnAll(lambda p: p.speed)

    def move(self, positionerName, axis, dist):
        """ Moves positioner by dist micrometers in the specified axis. """
        pManager = self._master.positionersManager[positionerName]
        result = pManager.move(dist, axis)
        if not self._isLiveUpdateEnabled(positionerName, pManager):
            # if result is a valid position we apply it immediately
            success = self._applyPositionResult(positionerName, axis, result)
            # otherwise we go through manager's update position path
            if not success:
                self.updatePosition(positionerName, axis)

    def setPos(self, positionerName, axis, position):
        """ Moves the positioner to the specified position in the specified axis. """
        pManager = self._master.positionersManager[positionerName]
        result = pManager.setPosition(position, axis)
        if not self._isLiveUpdateEnabled(positionerName, pManager):
            # if result is a valid position we apply it immediately
            success = self._applyPositionResult(positionerName, axis, result)
            # otherwise we go through manager's update position path
            if not success:
                self.updatePosition(positionerName, axis)

    def stepUp(self, positionerName, axis):
        stepSize = self._widget.getStepSize(positionerName, axis) * self._getStepModeMultiplier()
        self.move(positionerName, axis, stepSize)

    def stepDown(self, positionerName, axis):
        stepSize = self._widget.getStepSize(positionerName, axis) * self._getStepModeMultiplier()
        self.move(positionerName, axis, -stepSize)

    def setSpeedGUI(self):
        positionerName = self.getPositionerNames()[0]
        speed = self._widget.getSpeed()
        self.setSpeed(positionerName=positionerName, speed=speed)

    def setSpeed(self, positionerName, speed=(1000,1000,1000)):
        self._master.positionersManager[positionerName].setSpeed(speed)
        
    def updatePosition(self, positionerName, axis):
        pManager = self._master.positionersManager[positionerName]

        if hasattr(pManager, 'updatePosition'):
            pManager.updatePosition()

        if axis == 'all':
            for axisName in self._master.positionersManager[positionerName].axes:
                newPos = self._master.positionersManager[positionerName].position[axisName]
                self._widget.updatePosition(positionerName, axisName, newPos)
                self.setSharedAttr(positionerName, axisName, _positionAttr, newPos)
        else:
            newPos = self._master.positionersManager[positionerName].position[axis]
            self._widget.updatePosition(positionerName, axis, newPos)
            self.setSharedAttr(positionerName, axis, _positionAttr, newPos)


    def _applyPositionResult(self, positionerName, axis, result):
        """ Apply directly the result if it is a valid position, without passing
        by manager's udpatePosition. """
        if not isinstance(result, dict) or axis not in result:
            return False

        newPos = result[axis]
        self._widget.updatePosition(positionerName, axis, newPos)
        self.setSharedAttr(positionerName, axis, _positionAttr, newPos)
        return True


    def attrChanged(self, key, value):
        if self.settingAttr or len(key) != 4 or key[0] != _attrCategory:
            return

        positionerName = key[1]
        axis = key[2]
        if key[3] == _positionAttr:
            self.setPositioner(positionerName, axis, value)

    def setSharedAttr(self, positionerName, axis, attr, value):
        self.settingAttr = True
        try:
            self._commChannel.sharedAttrs[(_attrCategory, positionerName, axis, attr)] = value
        finally:
            self.settingAttr = False

    def setXYPosition(self, x, y):
        positionerX = self.getPositionerNames()[0]
        positionerY = self.getPositionerNames()[1]
        self.__logger.debug(f"Move {positionerX}, axis X, dist {str(x)}")
        self.__logger.debug(f"Move {positionerY}, axis Y, dist {str(y)}")
        #self.move(positionerX, 'X', x)
        #self.move(positionerY, 'Y', y)

    def setZPosition(self, z):
        positionerZ = self.getPositionerNames()[2]
        self.__logger.debug(f"Move {positionerZ}, axis Z, dist {str(z)}")
        #self.move(self.getPositionerNames[2], 'Z', z)

    @APIExport()
    def getPositionerNames(self) -> List[str]:
        """ Returns the device names of all positioners. These device names can
        be passed to other positioner-related functions. """
        return self._master.positionersManager.getAllDeviceNames()

    @APIExport()
    def getPositionerPositions(self) -> Dict[str, Dict[str, float]]:
        """ Returns the positions of all positioners. """
        return self.getPos()

    @APIExport(runOnUIThread=True)
    def setPositionerStepSize(self, positionerName: str, stepSize: float) -> None:
        """ Sets the step size of the specified positioner to the specified
        number of micrometers. """
        self._widget.setStepSize(positionerName, stepSize)

    @APIExport(runOnUIThread=True)
    def movePositioner(self, positionerName: str, axis: str, dist: float) -> None:
        """ Moves the specified positioner axis by the specified number of
        micrometers. """
        self.move(positionerName, axis, dist)

    @APIExport(runOnUIThread=True)
    def setPositioner(self, positionerName: str, axis: str, position: float) -> None:
        """ Moves the specified positioner axis to the specified position. """
        self.setPos(positionerName, axis, position)

    @APIExport(runOnUIThread=True)
    def setPositionerSpeed(self, positionerName: str, speed: float) -> None:
        """ Moves the specified positioner axis to the specified position. """
        self.setSpeed(positionerName, speed)

    @APIExport(runOnUIThread=True)
    def setMotorsEnabled(self, positionerName: str, is_enabled: int) -> None:
        """ Moves the specified positioner axis to the specified position. """
        self._master.positionersManager[positionerName].setEnabled(is_enabled)

    @APIExport(runOnUIThread=True)
    def stepPositionerUp(self, positionerName: str, axis: str) -> None:
        """ Moves the specified positioner axis in positive direction by its
        set step size. """
        self.stepUp(positionerName, axis)

    @APIExport(runOnUIThread=True)
    def stepPositionerDown(self, positionerName: str, axis: str) -> None:
        """ Moves the specified positioner axis in negative direction by its
        set step size. """
        self.stepDown(positionerName, axis)




_attrCategory = 'Positioner'
_positionAttr = 'Position'


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
