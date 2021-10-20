import platform
import serial
import serial.tools.list_ports
import time
import numpy as np

from .PositionerManager import PositionerManager
import imswitch.imcontrol.model.interfaces.grbldriver as grbldriver

# constants depending on the configuration
PHYS_TO_GRBL_FAC = 1000 #74820/1000 # 1000 steps are 74.2 mm
PHYS_TO_GRBL_FAC_Z = 1000 # 10

# reverse display vs. motion?
DIR_X = 1
DIR_Y = 1
DIR_Z = 1

class GRBLStageManager(PositionerManager):
    def __init__(self, positionerInfo, name, *args, **kwargs):
        self.port = positionerInfo.managerProperties['rs232device']
        self.board = grbldriver.GrblDriver(self.port)


        # Initialise backlash storage, used by property setter/getter
        self._backlash = None
        self.settle_time = 0.5  # Default move settle time
        self._position_on_enter = None

        # init the stage
        self.board.write_global_config()
        self.board.write_all_settings()
        self.board.verify_settings()

        #self.board.home()
        self.board.reset_stage()

        super().__init__(positionerInfo, name, initialPosition={
            axis: 0 for axis in positionerInfo.axes
        })


    def move(self, value, axis):
        if axis == 'X':
            self.board.move_rel((value*PHYS_TO_GRBL_FAC,0,0), blocking=False)
        elif axis == 'Y':
            self.board.move_rel((0,value*PHYS_TO_GRBL_FAC,0), blocking=False)
        elif axis == 'Z':
            self.board.move_rel((0,0,value*PHYS_TO_GRBL_FAC_Z), blocking=False)
        else:
            print('Wrong axis, has to be "X" "Y" or "Z".')
            return
        self._position[axis] = self._position[axis] + value

    def setPosition(self, value, axis):
        self._position[axis] = value


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
