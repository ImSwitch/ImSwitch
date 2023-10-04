import pyqtgraph as pg
from qtpy import QtCore, QtWidgets

from imswitch.imcommon.view.guitools import pyqtgraphtools, joystick
from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget


class JoystickWidget(NapariHybridWidget):
    """ Displays the Joystick transform of the image. """

    sigJoystickXY = QtCore.Signal(float, float)
    sigJoystickZA = QtCore.Signal(float, float)

    def __post_init__(self):

        # Add elements to GridLayout
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        
        # initialize the joystick
        self.textEditJoystickZA = QtWidgets.QLabel("Joystick Z/A")
        self.joystickZA = joystick.Joystick(callbackFct=self.getValueJoyStickXY)
        
        self.textEditJoystickXY = QtWidgets.QLabel("Joystick X/Y")
        self.joystickXY = joystick.Joystick(callbackFct=self.getValueJoyStickAZ)        
        
        self.grid.addWidget(self.textEditJoystickZA, 0, 1)
        self.grid.addWidget(self.joystickZA, 1, 0)
        self.grid.addWidget(self.textEditJoystickXY, 0, 0)
        self.grid.addWidget(self.joystickXY, 1, 1)
        
    def getValueJoyStickXY(self, x, y):
        self.sigJoystickXY.emit(x, y)
        return x, y
    
    def getValueJoyStickAZ(self, a, z):
        self.sigJoystickZA.emit(a, z)
        return a, z
        
        
       

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
