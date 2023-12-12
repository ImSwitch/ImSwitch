from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget


class RotatorWidget(Widget):
    """ Widget in control of a rotation mount movement. """

    sigMoveRelClicked = QtCore.Signal(str, int)
    sigMoveAbsClicked = QtCore.Signal(str)
    sigSetZeroClicked = QtCore.Signal(str)
    sigSetSpeedClicked = QtCore.Signal(str)
    sigStartContMovClicked = QtCore.Signal(str)
    sigStopContMovClicked = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.numPositioners = 0
        self.pars = {}
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

    def addRotator(self, name):
        self.pars['Label'+name] = QtWidgets.QLabel(f'<strong>{name}</strong>')
        self.pars['Label'+name].setTextFormat(QtCore.Qt.RichText)
        self.pars['Position'+name] = QtWidgets.QLabel(f'<strong>{0:.2f} deg</strong>')
        self.pars['Position'+name].setTextFormat(QtCore.Qt.RichText)
        self.pars['ForwButton'+name] = guitools.BetterPushButton('+')
        self.pars['BackButton'+name] = guitools.BetterPushButton('-')
        self.pars['RelStepEdit'+name] = QtWidgets.QLineEdit('0')
        self.pars['RelStepUnit'+name] = QtWidgets.QLabel(' deg')
        self.pars['SpeedEdit'+name] = QtWidgets.QLineEdit('100')
        self.pars['SpeedUnit'+name] = QtWidgets.QLabel(' mrpm')
        self.pars['SetZeroButton'+name] = guitools.BetterPushButton('Set zero')
        self.pars['AbsButton'+name] = guitools.BetterPushButton('Abs')
        self.pars['SetSpeedButton'+name] = guitools.BetterPushButton('Set speed')
        self.pars['StartMoveButton'+name] = guitools.BetterPushButton('Start move')
        self.pars['StopMoveButton'+name] = guitools.BetterPushButton('Stop move')
        self.pars['AbsPosEdit'+name] = QtWidgets.QLineEdit('0')
        self.pars['AbsPosUnit'+name] = QtWidgets.QLabel(' deg')

        self.grid.addWidget(self.pars['Label'+name], self.numPositioners*4, 0)
        self.grid.addWidget(self.pars['Position'+name], self.numPositioners*4+1, 0)
        self.grid.addWidget(self.pars['ForwButton'+name], self.numPositioners*4+1, 1)
        self.grid.addWidget(self.pars['BackButton'+name], self.numPositioners*4+1, 2)
        self.grid.addWidget(QtWidgets.QLabel('Step'), self.numPositioners*4+1, 3)
        self.grid.addWidget(self.pars['RelStepEdit'+name], self.numPositioners*4+1, 4)
        self.grid.addWidget(self.pars['RelStepUnit'+name], self.numPositioners*4+1, 5)

        self.grid.addWidget(self.pars['SetZeroButton'+name], self.numPositioners*4+2, 1)
        self.grid.addWidget(self.pars['AbsButton'+name], self.numPositioners*4+2, 2)
        self.grid.addWidget(QtWidgets.QLabel('Position'), self.numPositioners*4+2, 3)
        self.grid.addWidget(self.pars['AbsPosEdit'+name], self.numPositioners*4+2, 4)
        self.grid.addWidget(self.pars['AbsPosUnit'+name], self.numPositioners*4+2, 5)
        self.grid.addWidget(self.pars['SpeedEdit'+name], self.numPositioners*4+3, 0)
        self.grid.addWidget(self.pars['SpeedUnit'+name], self.numPositioners*4+3, 1)
        self.grid.addWidget(self.pars['SetSpeedButton'+name], self.numPositioners*4+3, 2)
        self.grid.addWidget(self.pars['StartMoveButton'+name], self.numPositioners*4+3, 3)
        self.grid.addWidget(self.pars['StopMoveButton'+name], self.numPositioners*4+3, 4)

        # Connect signals
        self.pars['ForwButton'+name].clicked.connect(lambda: self.sigMoveRelClicked.emit(name, 1))
        self.pars['BackButton'+name].clicked.connect(lambda: self.sigMoveRelClicked.emit(name, -1))
        self.pars['AbsButton'+name].clicked.connect(lambda: self.sigMoveAbsClicked.emit(name))
        self.pars['SetZeroButton'+name].clicked.connect(lambda: self.sigSetZeroClicked.emit(name))
        self.pars['SetSpeedButton'+name].clicked.connect(lambda: self.sigSetSpeedClicked.emit(name))
        self.pars['StartMoveButton'+name].clicked.connect(lambda: self.sigStartContMovClicked.emit(name))
        self.pars['StopMoveButton'+name].clicked.connect(lambda: self.sigStopContMovClicked.emit(name))
        
        if self.numPositioners == 0:
            # Add space item to make the grid look nicer
            self.grid.addItem(
                QtWidgets.QSpacerItem(10, 10,
                                    QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding),
                self.numPositioners*4+3, 0, 1, -1
            )

        self.numPositioners += 1

    def getRelStepSize(self, name):
        """ Returns the step size of the rotation mount, in degrees. """
        return float(self.pars['RelStepEdit'+name].text())

    def setRelStepSize(self, name, stepSize):
        """ Sets the step size to the specified number of degrees. """
        self.pars['RelStepEdit'+name].setText(stepSize)

    def getAbsPos(self, name):
        """ Returns the absolute position of the rotation mount, in degrees. """
        return float(self.pars['AbsPosEdit'+name].text())
    
    def getSpeed(self, name):
        """ Returns the user-input speed, in mrpm. """
        return int(self.pars['SpeedEdit'+name].text())

    def setAbsPos(self, name, absPos):
        """ Sets the absolute position to the specified number of degrees. """
        self.pars['AbsPosEdit'+name].setText(absPos)

    def updatePosition(self, name, position):
        self.pars['Position'+name].setText(f'<strong>{position:.2f} deg</strong>')


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
