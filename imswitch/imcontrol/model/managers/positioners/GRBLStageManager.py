import platform
import serial
import serial.tools.list_ports
import time
import numpy as np

from imswitch.imcommon.model import shortcut
from .PositionerManager import PositionerManager
import imswitch.imcontrol.model.interfaces.grbldriver as grbldriver

# constants depending on the configuration
PHYS_TO_GRBL_FAC = 5/48.5 # in ImSwtich 5µm equal 48.5mm in reality
PHYS_TO_GRBL_FAC_Z = .1 # 10

# reverse display vs. motion?
DIR_X = -1
DIR_Y = 1
DIR_Z = 1

class GRBLStageManager(PositionerManager):
    def __init__(self, positionerInfo, name, **lowLevelManagers):
        self._rs232manager = lowLevelManagers['rs232sManager'][
            positionerInfo.managerProperties['rs232device']
        ]
        try:
            PHYS_TO_GRBL_FAC=positionerInfo.managerProperties['PHYS_TO_GRBL_FAC']
            PHYS_TO_GRBL_FAC_Z=positionerInfo.managerProperties['PHYS_TO_GRBL_FAC_Z']
        except:
            pass
        
        # Initialise backlash storage, used by property setter/getter
        self._backlash = None
        self.settle_time = 0.5  # Default move settle time
        self._position_on_enter = None

        super().__init__(positionerInfo, name, initialPosition={
            axis: 0 for axis in positionerInfo.axes
        })
        self.board = self._rs232manager._board


    def move(self, value, axis):
        if axis == 'X':
            self.board.move_rel((value*PHYS_TO_GRBL_FAC*DIR_X,0,0), blocking=False)
        elif axis == 'Y':
            self.board.move_rel((0,value*PHYS_TO_GRBL_FAC*DIR_Y,0), blocking=False)
        elif axis == 'Z':
            self.board.move_rel((0,0,value*PHYS_TO_GRBL_FAC_Z*DIR_Z), blocking=False)
        else:
            print('Wrong axis, has to be "X" "Y" or "Z".')
            return
        self._position[axis] = self._position[axis] + value

    def setPosition(self, value, axis):
        self._position[axis] = value

    def closeEvent(self):
        self.board.close()
     
    # test arrow key input
    from PyQt5 import QtCore
    @shortcut(QtCore.Qt.Key_Up, "Move up")
    def key_moveXup(self):
        self.move(value=100, axis = "X")
    @shortcut(QtCore.Qt.Key_Down, "Move down")
    def key_moveXdown(self):
        self.move(value=-100, axis = "X")
    @shortcut(QtCore.Qt.Key_Left, "Move left")
    def key_moveYleft(self):
        self.move(value=-100, axis = "Y")
    @shortcut(QtCore.Qt.Key_Right, "Move right")
    def key_moveYright(self):
        self.move(value=100, axis = "Y")                        
    @shortcut("-", "Move Z up")
    def key_moveZup(self):
        self.move(value=100, axis = "Z")                        
    @shortcut("+", "Move Z down")
    def key_moveZdown(self):
        self.move(value=-100, axis = "Z")                        
            


# Copyright (C) 2020, 2021 TestaLab
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
