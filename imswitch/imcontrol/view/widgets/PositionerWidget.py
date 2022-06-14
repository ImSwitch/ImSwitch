from turtle import position
from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget


class PositionerWidget(Widget):
    """ Widget in control of the piezo movement. """

    sigStepUpClicked = QtCore.Signal(str, str)    # (positionerName, axis)
    sigStepDownClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigsetSpeedClicked = QtCore.Signal()  # (speed)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.numPositioners = 0
        self.pars = {}
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

    def addPositioner(self, positionerName, axes):
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
            self.pars['StepEdit' + parNameSuffix] = QtWidgets.QLineEdit('1000')
            self.pars['StepUnit' + parNameSuffix] = QtWidgets.QLabel(' µm')

            self.grid.addWidget(self.pars['Label' + parNameSuffix], self.numPositioners, 0)
            self.grid.addWidget(self.pars['Position' + parNameSuffix], self.numPositioners, 1)
            self.grid.addWidget(self.pars['UpButton' + parNameSuffix], self.numPositioners, 2)
            self.grid.addWidget(self.pars['DownButton' + parNameSuffix], self.numPositioners, 3)
            self.grid.addWidget(QtWidgets.QLabel('Step'), self.numPositioners, 4)
            self.grid.addWidget(self.pars['StepEdit' + parNameSuffix], self.numPositioners, 5)
            self.grid.addWidget(self.pars['StepUnit' + parNameSuffix], self.numPositioners, 6)
            
            self.numPositioners += 1

            # Connect signals
            self.pars['UpButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepUpClicked.emit(positionerName, axis)
            )
            self.pars['DownButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepDownClicked.emit(positionerName, axis)
            )
            
        self.pars['Speed'] = QtWidgets.QLabel(f'<strong>{0:.2f} µm</strong>')
        self.pars['Speed'].setTextFormat(QtCore.Qt.RichText)
        self.pars['ButtonSpeedEnter'] = guitools.BetterPushButton('Enter')
        self.pars['SpeedEdit'] = QtWidgets.QLineEdit('1000')
        self.pars['SpeedUnit'] = QtWidgets.QLabel(' µm/s')

        self.grid.addWidget(QtWidgets.QLabel('Speed'), 0, 9)
        self.grid.addWidget(self.pars['SpeedEdit'], 0, 10)
        self.grid.addWidget(self.pars['SpeedUnit'], 0, 11)
        self.grid.addWidget(self.pars['ButtonSpeedEnter'], 0, 12)
        self.pars['ButtonSpeedEnter'].clicked.connect(
            lambda *args: self.sigsetSpeedClicked.emit()
        )

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
