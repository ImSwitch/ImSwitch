from qtpy import QtCore, QtGui, QtWidgets
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget


class PositionerWidget(Widget):
    """ Widget in control of the piezo movement. """

    sigJoystickToggled = QtCore.Signal(bool, str)
    sigStepUpClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigStepDownClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigsetSpeedClicked = QtCore.Signal()  # (speed)
    sigSettingsClicked = QtCore.Signal()
    sigSettingsChanged = QtCore.Signal(object)
    sigStepModeChanged = QtCore.Signal(bool)  # True when coarse mode is selected

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.numPositioners = 1
        self.pars = {}
        self._positionerAxes = {}
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        self._coarseMode = False
        self._coarseStepMultiplier = 5.0
        self.pars['StepModeContainer'] = QtWidgets.QWidget()
        stepModeContainerLayout = QtWidgets.QHBoxLayout(self.pars['StepModeContainer'])
        stepModeContainerLayout.setContentsMargins(0, 0, 0, 0)
        stepModeContainerLayout.setSpacing(6)
        self.pars['StepModeWidget'] = QtWidgets.QWidget()
        stepModeLayout = QtWidgets.QHBoxLayout(self.pars['StepModeWidget'])
        stepModeLayout.setContentsMargins(0, 0, 0, 0)
        stepModeLayout.setSpacing(0)
        self.pars['CoarseModeButton'] = guitools.BetterPushButton('Coarse')
        self.pars['FineModeButton'] = guitools.BetterPushButton('Fine')
        self.pars['CoarseModeButton'].setObjectName('coarseModeBtn')
        self.pars['FineModeButton'].setObjectName('fineModeBtn')
        self.pars['CoarseModeButton'].setCheckable(True)
        self.pars['FineModeButton'].setCheckable(True)
        self.pars['FineModeButton'].setChecked(True)
        self.pars['CoarseModeButton'].setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        )
        self.pars['FineModeButton'].setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        )
        stepModeStyle = """
        QPushButton {
            padding: 2px 10px;
            border: 1px solid rgba(255,255,255,60);
        }

        QPushButton#coarseModeBtn {
            border-top-left-radius: 6px;
            border-bottom-left-radius: 6px;
        }

        QPushButton#fineModeBtn {
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
        }

        QPushButton:hover {
            border: 1px solid rgba(255,255,255,120);
        }

        QPushButton:checked {
            background-color: rgba(120,180,255,120);
            border: 1px solid rgba(120,180,255,200);
        }
        """
        self.pars['CoarseModeButton'].setStyleSheet(stepModeStyle)
        self.pars['FineModeButton'].setStyleSheet(stepModeStyle)
        self._updateCoarseModeTooltip()
        self._stepModeButtonGroup = QtWidgets.QButtonGroup(self)
        self._stepModeButtonGroup.setExclusive(True)
        self._stepModeButtonGroup.addButton(self.pars['CoarseModeButton'])
        self._stepModeButtonGroup.addButton(self.pars['FineModeButton'])
        stepModeLayout.addWidget(self.pars['CoarseModeButton'], 1)
        stepModeLayout.addWidget(self.pars['FineModeButton'], 1)
        self.pars['CoarseModeButton'].clicked.connect(lambda: self.sigStepModeChanged.emit(True))
        self.pars['FineModeButton'].clicked.connect(lambda: self.sigStepModeChanged.emit(False))
        stepModeContainerLayout.addStretch(1)
        stepModeContainerLayout.addWidget(self.pars['StepModeWidget'], 1)
        self.grid.addWidget(
            self.pars['StepModeContainer'],
            0,
            5
        )

        self.pars['SettingsButton'] = guitools.BetterPushButton('Settings')
        self.grid.addWidget(
            self.pars['SettingsButton'],
            0,
            6,
            alignment=QtCore.Qt.AlignRight
        )
        self.pars['SettingsButton'].clicked.connect(self.sigSettingsClicked.emit)

        stepModeHeight = self.pars['SettingsButton'].sizeHint().height()
        self.pars['StepModeContainer'].setFixedHeight(stepModeHeight)
        self.pars['StepModeWidget'].setFixedHeight(stepModeHeight)
        self.pars['CoarseModeButton'].setFixedHeight(stepModeHeight)
        self.pars['FineModeButton'].setFixedHeight(stepModeHeight)

    def addJoystick(self, pName):
        # create and add check box
        self.joystickCheck = QtWidgets.QCheckBox('Enable Joystick')
        self.joystickCheck.setCheckable(True)
        self.grid.addWidget(self.joystickCheck, 0, 0)
        # connect checkbox signal
        self.joystickCheck.clicked.connect(
            lambda state: self.sigJoystickToggled.emit(state, pName)
        )

    def addPositioner(self, positionerName, axes, speed, joystick):
        self._positionerAxes[positionerName] = list(axes)
        for i in range(len(axes)):
            axis = axes[i]
            parNameSuffix = self._getParNameSuffix(positionerName, axis)
            label = f'{positionerName} -- {axis}' if positionerName != axis else positionerName

            self.pars['Label' + parNameSuffix] = QtWidgets.QLabel(f'<strong>{label}</strong>')
            self.pars['Label' + parNameSuffix].setTextFormat(QtCore.Qt.RichText)
            self.pars['Position' + parNameSuffix] = QtWidgets.QLabel(f'<strong>{0:.2f} µm</strong>')

            self.pars['Position' + parNameSuffix].setTextFormat(QtCore.Qt.RichText)
            self.pars['UpButton' + parNameSuffix] = guitools.BetterPushButton('+')
            self.pars['DownButton' + parNameSuffix] = guitools.BetterPushButton('-')
            self.pars['FineStepLabel' + parNameSuffix] = QtWidgets.QLabel('Fine Step')
            if positionerName == 'Stage':
                self.pars['StepEdit' + parNameSuffix] = QtWidgets.QLineEdit('25')
            else:
                self.pars['StepEdit' + parNameSuffix] = QtWidgets.QLineEdit('0.05')

            self.pars['StepValuesWidget' + parNameSuffix] = QtWidgets.QWidget()
            stepValuesLayout = QtWidgets.QHBoxLayout(self.pars['StepValuesWidget' + parNameSuffix])
            stepValuesLayout.setContentsMargins(0, 0, 0, 0)
            stepValuesLayout.setSpacing(6)
            self.pars['CoarseStepPreview' + parNameSuffix] = QtWidgets.QLabel()
            self.pars['StepUnit' + parNameSuffix] = QtWidgets.QLabel('µm')

            self.pars['StepEdit' + parNameSuffix].setSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Fixed
            )
            self.pars['CoarseStepPreview' + parNameSuffix].setSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Fixed
            )
            stepValuesLayout.addWidget(self.pars['StepEdit' + parNameSuffix], 1)
            stepValuesLayout.addWidget(self.pars['CoarseStepPreview' + parNameSuffix], 1)

            self.grid.addWidget(self.pars['Label' + parNameSuffix], self.numPositioners, 0)
            self.grid.addWidget(self.pars['Position' + parNameSuffix], self.numPositioners, 1)
            self.grid.addWidget(self.pars['UpButton' + parNameSuffix], self.numPositioners, 2)
            self.grid.addWidget(self.pars['DownButton' + parNameSuffix], self.numPositioners, 3)
            self.grid.addWidget(self.pars['FineStepLabel' + parNameSuffix], self.numPositioners, 4)
            self.grid.addWidget(self.pars['StepValuesWidget' + parNameSuffix], self.numPositioners, 5)
            self.grid.addWidget(self.pars['StepUnit' + parNameSuffix], self.numPositioners, 6)

            # Connect signals
            self.pars['UpButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepUpClicked.emit(positionerName, axis)
            )
            self.pars['DownButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepDownClicked.emit(positionerName, axis)
            )
            self.pars['StepEdit' + parNameSuffix].textChanged.connect(
                lambda *args, positionerName=positionerName, axis=axis:
                self._updateCoarseStepPreview(positionerName, axis)
            )
            self._updateCoarseStepPreview(positionerName, axis)
            self._refreshStepModeStyles()

            if speed:
                self.pars['Speed'] = QtWidgets.QLabel(f'<strong>{0:.2f} µm/s</strong>')
                self.pars['Speed'].setTextFormat(QtCore.Qt.RichText)
                self.pars['ButtonSpeedEnter'] = guitools.BetterPushButton('Enter')
                self.pars['SpeedEdit'] = QtWidgets.QLineEdit('1000')
                self.pars['SpeedUnit'] = QtWidgets.QLabel(' µm/s')
                self.grid.addWidget(self.pars['SpeedEdit'], self.numPositioners, 10)
                self.grid.addWidget(self.pars['SpeedUnit'], self.numPositioners, 11)
                self.grid.addWidget(self.pars['ButtonSpeedEnter'], self.numPositioners, 12)
                self.grid.addWidget(self.pars['Speed'], self.numPositioners, 7)


                self.pars['ButtonSpeedEnter'].clicked.connect(
                    lambda *args: self.sigsetSpeedClicked.emit()
                )
            self.numPositioners += 1

    def getStepSize(self, positionerName, axis):
        """ Returns the step size of the specified positioner axis in
        micrometers. """
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        return float(self.pars['StepEdit' + parNameSuffix].text())

    def setStepSize(self, positionerName, axis, stepSize):
        """ Sets the step size of the specified positioner axis to the
        specified number of micrometers. """
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        self.pars['StepEdit' + parNameSuffix].setText(stepSize)
        self._updateCoarseStepPreview(positionerName, axis)

    def getSpeed(self):
        """ Returns the step size of the specified positioner axis in
        micrometers. """
        return float(self.pars['SpeedEdit'].text())

    def setSpeedSize(self, positionerName, axis, speedSize):
        """ Sets the step size of the specified positioner axis to the
        specified number of micrometers. """
        self.pars['SpeedEdit'].setText(speedSize)

    def updatePosition(self, positionerName, axis, position):
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        self.pars['Position' + parNameSuffix].setText(f'<strong>{position:.2f} µm</strong>')

    def setStepMode(self, coarseMode):
        self._coarseMode = bool(coarseMode)
        self.pars['CoarseModeButton'].setChecked(self._coarseMode)
        self.pars['FineModeButton'].setChecked(not self._coarseMode)
        self._refreshStepModeStyles()

    def setCoarseStepMultiplier(self, multiplier):
        self._coarseStepMultiplier = float(multiplier)
        self._updateCoarseModeTooltip()
        for positionerName, axes in self._positionerAxes.items():
            for axis in axes:
                self._updateCoarseStepPreview(positionerName, axis)
        self._refreshStepModeStyles()

    def showSettingsDialog(self, liveUpdateIntervalMs, positionerSettings, shortcutSettings=None,
                           settingsValidator=None):
        shortcutSettings = shortcutSettings or {}
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('Settings')

        layout = QtWidgets.QVBoxLayout(dialog)

        generalGrid = QtWidgets.QGridLayout()

        intervalSpinBox = QtWidgets.QSpinBox()
        intervalSpinBox.setRange(100, 2000)
        intervalSpinBox.setSingleStep(50)
        intervalSpinBox.setSuffix(' ms')
        intervalSpinBox.setValue(int(liveUpdateIntervalMs))
        generalGrid.addWidget(QtWidgets.QLabel('Live update interval'), 0, 0)
        generalGrid.addWidget(intervalSpinBox, 0, 1)

        movementPrefixCombo = self._makePrefixCombo(shortcutSettings.get('movementPrefix', 'Shift'))
        coarseMultiplierSpinBox = QtWidgets.QDoubleSpinBox()
        coarseMultiplierSpinBox.setRange(1.0, 1000.0)
        coarseMultiplierSpinBox.setDecimals(2)
        coarseMultiplierSpinBox.setSingleStep(0.5)
        coarseMultiplierSpinBox.setValue(float(shortcutSettings.get('coarseStepMultiplier', 5.0)))

        generalGrid.addWidget(QtWidgets.QLabel('Movement prefix'), 1, 0)
        generalGrid.addWidget(movementPrefixCombo, 1, 1)
        generalGrid.addWidget(QtWidgets.QLabel('Coarse multiplier'), 1, 2)
        generalGrid.addWidget(coarseMultiplierSpinBox, 1, 3)

        modeToggleShortcut = self._makeShortcutEditor(shortcutSettings.get('modeToggle', ''))
        generalGrid.addWidget(QtWidgets.QLabel('Coarse/Fine shortcut'), 2, 0)
        generalGrid.addWidget(modeToggleShortcut, 2, 1)
        joystickShortcut = self._makeShortcutEditor(shortcutSettings.get('joystickToggle', ''))
        joystickShortcut.setEnabled(bool(shortcutSettings.get('joystickAvailable', False)))
        generalGrid.addWidget(QtWidgets.QLabel('Joystick shortcut'), 2, 2)
        generalGrid.addWidget(joystickShortcut, 2, 3)
        generalGrid.setColumnStretch(6, 1)
        layout.addLayout(generalGrid)

        settingsGrid = QtWidgets.QGridLayout()
        settingsGrid.addWidget(QtWidgets.QLabel('Positioner'), 0, 0)
        settingsGrid.addWidget(QtWidgets.QLabel('+ shortcut'), 0, 1)
        settingsGrid.addWidget(QtWidgets.QLabel('- shortcut'), 0, 2)
        settingsGrid.addWidget(QtWidgets.QLabel('Live update'), 0, 3)

        liveUpdateChecks = {}
        shortcutEditors = {}
        positionerShortcuts = shortcutSettings.get(
            'movement',
            shortcutSettings.get('positioners', {})
        )
        row = 1
        for positionerName, axes in self._positionerAxes.items():
            settings = positionerSettings.get(positionerName, {})
            liveUpdateAvailable = bool(settings.get('liveUpdateAvailable', False))
            liveUpdateEnabled = bool(settings.get('liveUpdateEnabled', False)) and liveUpdateAvailable
            shortcutEditors[positionerName] = {}

            liveUpdateCheck = QtWidgets.QCheckBox()
            liveUpdateCheck.setEnabled(liveUpdateAvailable)
            liveUpdateCheck.setChecked(liveUpdateEnabled)
            liveUpdateChecks[positionerName] = liveUpdateCheck

            for axisIndex, axis in enumerate(axes):
                label = f'{positionerName} -- {axis}' if positionerName != axis else positionerName
                settingsGrid.addWidget(QtWidgets.QLabel(label), row, 0)

                axisShortcuts = positionerShortcuts.get(positionerName, {}).get(axis, {})
                upShortcut = self._makeShortcutEditor(axisShortcuts.get('up', ''))
                settingsGrid.addWidget(upShortcut, row, 1)

                downShortcut = self._makeShortcutEditor(axisShortcuts.get('down', ''))
                settingsGrid.addWidget(downShortcut, row, 2)
                shortcutEditors[positionerName][axis] = {
                    'up': upShortcut,
                    'down': downShortcut
                }

                if axisIndex == 0:
                    settingsGrid.addWidget(liveUpdateCheck, row, 3)

                row += 1

        layout.addLayout(settingsGrid)

        def collectSettings():
            shortcuts = {}
            for positionerName, axisEditors in shortcutEditors.items():
                shortcuts[positionerName] = {}
                for axis, editors in axisEditors.items():
                    shortcuts[positionerName][axis] = {
                        'up': self._shortcutEditorText(editors['up']),
                        'down': self._shortcutEditorText(editors['down'])
                    }

            return {
                'liveUpdateIntervalMs': intervalSpinBox.value(),
                'liveUpdateEnabled': {
                    positionerName: liveUpdateCheck.isChecked()
                    for positionerName, liveUpdateCheck in liveUpdateChecks.items()
                },
                'movementPrefix': movementPrefixCombo.currentText(),
                'coarseStepMultiplier': coarseMultiplierSpinBox.value(),
                'modeToggle': self._shortcutEditorText(modeToggleShortcut),
                'joystickToggle': self._shortcutEditorText(joystickShortcut),
                'movement': shortcuts
            }

        acceptedSettings = {}

        def acceptSettings():
            settings = collectSettings()
            if settingsValidator is not None:
                warning = settingsValidator(settings)
                if warning:
                    QtWidgets.QMessageBox.warning(dialog, 'Settings', warning)
                    return

            acceptedSettings.update(settings)
            dialog.accept()

        validateButton = guitools.BetterPushButton('Validate')
        validateButton.clicked.connect(acceptSettings)
        layout.addWidget(validateButton, alignment=QtCore.Qt.AlignRight)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.sigSettingsChanged.emit(acceptedSettings)

    def _makePrefixCombo(self, currentPrefix):
        combo = QtWidgets.QComboBox()
        prefixes = ['Ctrl', 'Shift', 'Alt', 'Meta']
        combo.addItems(prefixes)
        if currentPrefix in prefixes:
            combo.setCurrentText(currentPrefix)
        return combo

    def _makeShortcutEditor(self, shortcut):
        if hasattr(QtWidgets, "QKeySequenceEdit"):
            editor = QtWidgets.QKeySequenceEdit()
            if hasattr(editor, "setMaximumSequenceLength"):
                editor.setMaximumSequenceLength(1)
            if shortcut:
                editor.setKeySequence(QtGui.QKeySequence(shortcut))
        else:
            editor = QtWidgets.QLineEdit(shortcut or "")
            editor.setPlaceholderText("Up")
        return editor

    def _shortcutEditorText(self, editor):
        if hasattr(QtWidgets, "QKeySequenceEdit") and isinstance(editor, QtWidgets.QKeySequenceEdit):
            sequence = editor.keySequence()
            try:
                return sequence.toString(QtGui.QKeySequence.NativeText).strip()
            except TypeError:
                return sequence.toString().strip()

        return editor.text().strip()

    def _updateCoarseStepPreview(self, positionerName, axis):
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        preview = self.pars.get('CoarseStepPreview' + parNameSuffix)
        if preview is None:
            return

        try:
            fineStep = float(self.pars['StepEdit' + parNameSuffix].text())
            coarseStep = fineStep * self._coarseStepMultiplier
            preview.setText(f'Coarse: {self._formatStepValue(coarseStep)}')
        except ValueError:
            preview.setText('Coarse: -')

    def _refreshStepModeStyles(self):
        fineLabelStyle = 'color: gray;' if self._coarseMode else ''
        fineEditStyle = 'color: gray;' if self._coarseMode else ''
        coarsePreviewStyle = (
            'font-weight: bold; color: rgb(80, 140, 220);'
            if self._coarseMode else
            'color: gray;'
        )

        for positionerName, axes in self._positionerAxes.items():
            for axis in axes:
                parNameSuffix = self._getParNameSuffix(positionerName, axis)
                fineLabel = self.pars.get('FineStepLabel' + parNameSuffix)
                fineEdit = self.pars.get('StepEdit' + parNameSuffix)
                coarsePreview = self.pars.get('CoarseStepPreview' + parNameSuffix)

                if fineLabel is not None:
                    fineLabel.setStyleSheet(fineLabelStyle)
                if fineEdit is not None:
                    fineEdit.setStyleSheet(fineEditStyle)
                if coarsePreview is not None:
                    coarsePreview.setStyleSheet(coarsePreviewStyle)

    def _formatStepValue(self, value):
        return f'{value:.6g}'

    def _updateCoarseModeTooltip(self):
        self.pars['CoarseModeButton'].setToolTip(
            f'{self._formatStepValue(self._coarseStepMultiplier)}x'
        )

    def _getParNameSuffix(self, positionerName, axis):
        return f'{positionerName}--{axis}'


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
