from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget


class RotatorWidget(Widget):
    """ Widget in control of a rotation mount movement. """

    sigMoveForwRelClicked = QtCore.Signal()
    sigMoveBackRelClicked = QtCore.Signal()
    sigMoveAbsClicked = QtCore.Signal()
    sigSetZeroClicked = QtCore.Signal()
    sigSetSpeedClicked = QtCore.Signal()
    sigStartContMovClicked = QtCore.Signal()
    sigStopContMovClicked = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.numPositioners = 0
        self.pars = {}
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

    def addRotator(self):
        label = 'Standa mot. rot.'

        self.pars['Label'] = QtWidgets.QLabel(f'<strong>{label}</strong>')
        self.pars['Label'].setTextFormat(QtCore.Qt.RichText)
        self.pars['Position'] = QtWidgets.QLabel(f'<strong>{0:.2f} deg</strong>')
        self.pars['Position'].setTextFormat(QtCore.Qt.RichText)
        self.pars['ForwButton'] = guitools.BetterPushButton('+')
        self.pars['BackButton'] = guitools.BetterPushButton('-')
        self.pars['RelStepEdit'] = QtWidgets.QLineEdit('10')
        self.pars['RelStepUnit'] = QtWidgets.QLabel(' deg')
        self.pars['SpeedEdit'] = QtWidgets.QLineEdit('100')
        self.pars['SpeedUnit'] = QtWidgets.QLabel(' mrpm')
        self.pars['SetZeroButton'] = guitools.BetterPushButton('Set zero')
        self.pars['AbsButton'] = guitools.BetterPushButton('Abs')
        self.pars['SetSpeedButton'] = guitools.BetterPushButton('Set speed')
        self.pars['StartMoveButton'] = guitools.BetterPushButton('Start move')
        self.pars['StopMoveButton'] = guitools.BetterPushButton('Stop move')
        self.pars['AbsPosEdit'] = QtWidgets.QLineEdit('0')
        self.pars['AbsPosUnit'] = QtWidgets.QLabel(' deg')

        self.grid.addWidget(self.pars['Label'], 0, 0)
        self.grid.addWidget(self.pars['Position'], 0, 1)
        self.grid.addWidget(self.pars['ForwButton'], 0, 2)
        self.grid.addWidget(self.pars['BackButton'], 0, 3)
        self.grid.addWidget(QtWidgets.QLabel('Step'), 0, 4)
        self.grid.addWidget(self.pars['RelStepEdit'], 0, 5)
        self.grid.addWidget(self.pars['RelStepUnit'], 0, 6)
        self.grid.addWidget(self.pars['SetZeroButton'], 1, 2)
        self.grid.addWidget(self.pars['AbsButton'], 1, 3)
        self.grid.addWidget(QtWidgets.QLabel('Pos'), 1, 4)
        self.grid.addWidget(self.pars['AbsPosEdit'], 1, 5)
        self.grid.addWidget(self.pars['AbsPosUnit'], 1, 6)
        self.grid.addWidget(self.pars['SpeedEdit'], 2, 0)
        self.grid.addWidget(self.pars['SpeedUnit'], 2, 1)
        self.grid.addWidget(self.pars['SetSpeedButton'], 2, 2)
        self.grid.addWidget(self.pars['StartMoveButton'], 2, 3)
        self.grid.addWidget(self.pars['StopMoveButton'], 2, 4)

        # Connect signals
        self.pars['ForwButton'].clicked.connect(self.sigMoveForwRelClicked.emit)
        self.pars['BackButton'].clicked.connect(self.sigMoveBackRelClicked.emit)
        self.pars['AbsButton'].clicked.connect(self.sigMoveAbsClicked.emit)
        self.pars['SetZeroButton'].clicked.connect(self.sigSetZeroClicked.emit)
        self.pars['SetSpeedButton'].clicked.connect(self.sigSetSpeedClicked.emit)
        self.pars['StartMoveButton'].clicked.connect(self.sigStartContMovClicked.emit)
        self.pars['StopMoveButton'].clicked.connect(self.sigStopContMovClicked.emit)

    def getRelStepSize(self):
        """ Returns the step size of the rotation mount, in degrees. """
        return float(self.pars['RelStepEdit'].text())

    def setRelStepSize(self, stepSize):
        """ Sets the step size to the specified number of degrees. """
        self.pars['RelStepEdit'].setText(stepSize)

    def getAbsPos(self):
        """ Returns the absolute position of the rotation mount, in degrees. """
        return float(self.pars['AbsPosEdit'].text())
    
    def getSpeed(self):
        """ Returns the user-input speed, in mrpm. """
        return int(self.pars['SpeedEdit'].text())

    def setAbsPos(self, absPos):
        """ Sets the absolute position to the specified number of degrees. """
        self.pars['AbsPosEdit'].setText(absPos)

    def updatePosition(self, position):
        self.pars['Position'].setText(f'<strong>{position:.2f} deg</strong>')


# Copyright (C) 2020-2022 ImSwitch developers
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
