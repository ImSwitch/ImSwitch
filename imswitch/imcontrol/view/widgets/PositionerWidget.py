from qtpy import QtCore, QtWidgets
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
    sigSettingsChanged = QtCore.Signal(int, object)  # (liveUpdateIntervalMs, liveUpdateEnabled)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.numPositioners = 1
        self.pars = {}
        self._positionerAxes = {}
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        self.pars['SettingsButton'] = guitools.BetterPushButton('Settings')
        self.grid.addWidget(
            self.pars['SettingsButton'],
            0,
            6,
            alignment=QtCore.Qt.AlignRight
        )
        self.pars['SettingsButton'].clicked.connect(self.sigSettingsClicked.emit)

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
            if positionerName == 'Stage':
                self.pars['StepEdit' + parNameSuffix] = QtWidgets.QLineEdit('25')
            else:
                self.pars['StepEdit' + parNameSuffix] = QtWidgets.QLineEdit('0.05')

            self.pars['StepUnit' + parNameSuffix] = QtWidgets.QLabel(' µm')

            self.grid.addWidget(self.pars['Label' + parNameSuffix], self.numPositioners, 0)
            self.grid.addWidget(self.pars['Position' + parNameSuffix], self.numPositioners, 1)
            self.grid.addWidget(self.pars['UpButton' + parNameSuffix], self.numPositioners, 2)
            self.grid.addWidget(self.pars['DownButton' + parNameSuffix], self.numPositioners, 3)
            self.grid.addWidget(QtWidgets.QLabel('Step'), self.numPositioners, 4)
            self.grid.addWidget(self.pars['StepEdit' + parNameSuffix], self.numPositioners, 5)
            self.grid.addWidget(self.pars['StepUnit' + parNameSuffix], self.numPositioners, 6)

            # Connect signals
            self.pars['UpButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepUpClicked.emit(positionerName, axis)
            )
            self.pars['DownButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepDownClicked.emit(positionerName, axis)
            )

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

    def showSettingsDialog(self, liveUpdateIntervalMs, positionerSettings):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('Settings')

        layout = QtWidgets.QVBoxLayout(dialog)

        intervalLayout = QtWidgets.QHBoxLayout()
        intervalLayout.addWidget(QtWidgets.QLabel('Live update interval'))
        intervalSpinBox = QtWidgets.QSpinBox()
        intervalSpinBox.setRange(100, 2000)
        intervalSpinBox.setSingleStep(50)
        intervalSpinBox.setSuffix(' ms')
        intervalSpinBox.setValue(int(liveUpdateIntervalMs))
        intervalLayout.addWidget(intervalSpinBox)
        intervalLayout.addStretch()
        layout.addLayout(intervalLayout)

        settingsGrid = QtWidgets.QGridLayout()
        settingsGrid.addWidget(QtWidgets.QLabel('Positioner'), 0, 0)
        settingsGrid.addWidget(QtWidgets.QLabel('+ shortcut'), 0, 1)
        settingsGrid.addWidget(QtWidgets.QLabel('- shortcut'), 0, 2)
        settingsGrid.addWidget(QtWidgets.QLabel('Live update'), 0, 3)

        liveUpdateChecks = {}
        row = 1
        for positionerName, axes in self._positionerAxes.items():
            settings = positionerSettings.get(positionerName, {})
            liveUpdateAvailable = bool(settings.get('liveUpdateAvailable', False))
            liveUpdateEnabled = bool(settings.get('liveUpdateEnabled', False)) and liveUpdateAvailable

            liveUpdateCheck = QtWidgets.QCheckBox()
            liveUpdateCheck.setEnabled(liveUpdateAvailable)
            liveUpdateCheck.setChecked(liveUpdateEnabled)
            liveUpdateChecks[positionerName] = liveUpdateCheck

            for axisIndex, axis in enumerate(axes):
                label = f'{positionerName} -- {axis}' if positionerName != axis else positionerName
                settingsGrid.addWidget(QtWidgets.QLabel(label), row, 0)

                upShortcut = QtWidgets.QLineEdit()
                upShortcut.setEnabled(False)
                settingsGrid.addWidget(upShortcut, row, 1)

                downShortcut = QtWidgets.QLineEdit()
                downShortcut.setEnabled(False)
                settingsGrid.addWidget(downShortcut, row, 2)

                if axisIndex == 0:
                    settingsGrid.addWidget(liveUpdateCheck, row, 3)

                row += 1

        layout.addLayout(settingsGrid)

        validateButton = guitools.BetterPushButton('Validate')
        validateButton.clicked.connect(dialog.accept)
        layout.addWidget(validateButton, alignment=QtCore.Qt.AlignRight)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.sigSettingsChanged.emit(
                intervalSpinBox.value(),
                {
                    positionerName: liveUpdateCheck.isChecked()
                    for positionerName, liveUpdateCheck in liveUpdateChecks.items()
                }
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
