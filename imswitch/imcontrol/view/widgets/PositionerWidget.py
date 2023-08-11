from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget


class PositionerWidget(Widget):
    """ Widget in control of the piezo movement. """

    sigStepUpClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigStepDownClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigStepAbsoluteClicked = QtCore.Signal(str, str)
    sigHomeAxisClicked = QtCore.Signal(str, str)
    sigStopAxisClicked = QtCore.Signal(str, str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.numPositioners = 0
        self.pars = {}
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

    def addPositioner(self, positionerName, axes, hasSpeed, hasHome=True, hasStop=True):
        for i in range(len(axes)):
            axis = axes[i]
            parNameSuffix = self._getParNameSuffix(positionerName, axis)
            label = f'{axis}' if positionerName != axis else positionerName #f'{positionerName} -- {axis}' if positionerName != axis else positionerName

            self.pars['Label' + parNameSuffix] = QtWidgets.QLabel(f'<strong>{label}</strong>')
            self.pars['Label' + parNameSuffix].setTextFormat(QtCore.Qt.RichText)
            self.pars['Position' + parNameSuffix] = QtWidgets.QLabel(f'<strong>{0:.2f} µm</strong>')
            self.pars['Position' + parNameSuffix].setTextFormat(QtCore.Qt.RichText)
            self.pars['UpButton' + parNameSuffix] = guitools.BetterPushButton('+') #self.pars['UpButton' + parNameSuffix].setStyleSheet(f'max-width: {30}px')
            self.pars['DownButton' + parNameSuffix] = guitools.BetterPushButton('-')
            self.pars['StepEdit' + parNameSuffix] = QtWidgets.QLineEdit('1000')

            self.pars['AbsolutePosEdit' + parNameSuffix] = QtWidgets.QLineEdit('0')
            self.pars['AbsolutePosButton' + parNameSuffix] = guitools.BetterPushButton('Go!')

            self.grid.addWidget(self.pars['Label' + parNameSuffix], 2*self.numPositioners, 0)
            self.grid.addWidget(self.pars['Position' + parNameSuffix], 2*self.numPositioners, 1)
            self.grid.addWidget(self.pars['UpButton' + parNameSuffix], 2*self.numPositioners, 2)
            self.grid.addWidget(self.pars['DownButton' + parNameSuffix], 2*self.numPositioners, 3)
            self.grid.addWidget(QtWidgets.QLabel('Rel: '), 2*self.numPositioners, 4)
            self.grid.addWidget(self.pars['StepEdit' + parNameSuffix], 2*self.numPositioners, 5)
            self.grid.addWidget(QtWidgets.QLabel('Abs: '), 2*self.numPositioners+1, 0)

            # Create a new row
            self.grid.addWidget(self.pars['AbsolutePosEdit' + parNameSuffix], 2*self.numPositioners+1, 1)
            self.grid.addWidget(self.pars['AbsolutePosButton' + parNameSuffix], 2*self.numPositioners+1, 2)

            if hasSpeed:
                self.pars['Speed' + parNameSuffix] = QtWidgets.QLabel('Speed:')
                self.pars['Speed' + parNameSuffix].setTextFormat(QtCore.Qt.RichText)
                self.pars['SpeedEdit' + parNameSuffix] = QtWidgets.QLineEdit('1000')

                self.grid.addWidget(self.pars['Speed' + parNameSuffix], 2*self.numPositioners+1, 3)
                self.grid.addWidget(self.pars['SpeedEdit' + parNameSuffix], 2*self.numPositioners+1, 4)

            if hasHome:
                self.pars['Home' + parNameSuffix] = guitools.BetterPushButton('Home ' + parNameSuffix)
                self.grid.addWidget(self.pars['Home' + parNameSuffix], 2*self.numPositioners+1, 5)

                self.pars['Home' + parNameSuffix].clicked.connect(
                    lambda *args, axis=axis: self.sigHomeAxisClicked.emit(positionerName, axis)
                )

            if hasStop:
                self.pars['Stop' + parNameSuffix] = guitools.BetterPushButton('Stop ' + parNameSuffix)
                self.grid.addWidget(self.pars['Stop' + parNameSuffix], self.numPositioners+1, 6)

                self.pars['Stop' + parNameSuffix].clicked.connect(
                    lambda *args, axis=axis: self.sigStopAxisClicked.emit(positionerName, axis)
                )

            # Connect signals
            self.pars['UpButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepUpClicked.emit(positionerName, axis)
            )
            self.pars['DownButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepDownClicked.emit(positionerName, axis)
            )
            self.pars['AbsolutePosButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepAbsoluteClicked.emit(positionerName, axis)
            )

            self.numPositioners += 1
            
    

    def getAbsPosition(self, positionerName, axis):
        """ Returns the absolute position of the  specified positioner axis in
        micrometers. """
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        return float(self.pars['AbsolutePosEdit' + parNameSuffix].text())

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

    def getSpeed(self, positionerName, axis):
        """ Returns the step size of the specified positioner axis in
        micrometers. """
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        return float(self.pars['SpeedEdit' + parNameSuffix].text())

    def setSpeedSize(self, positionerName, axis, speedSize):
        """ Sets the step size of the specified positioner axis to the
        specified number of micrometers. """
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        try:
            self.pars['SpeedEdit' + parNameSuffix].setText(str(speedSize))
        except:
            pass

    def updatePosition(self, positionerName, axis, position):
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        self.pars['Position' + parNameSuffix].setText(f'<strong>{position:.2f} µm</strong>')

    def updateSpeed(self, positionerName, axis, speed):
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        self.pars['SpeedEdit' + parNameSuffix].setText(f'<strong>{speed:.2f}</strong>')

    def _getParNameSuffix(self, positionerName, axis):
        return f'{positionerName[0]}--{axis}'

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
