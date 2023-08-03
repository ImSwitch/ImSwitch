
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex
from imswitch.imcontrol.view import guitools
from imswitch.imcommon.model import initLogger
from ..basecontrollers import LiveUpdatedController


class JoystickController(LiveUpdatedController):
    """ Linked to JoystickWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # scaler
        self.scaler = 1
        
        # initialize the positioner
        self.positioner_name = self._master.positionersManager.getAllDeviceNames()[0]
        self.positioner = self._master.positionersManager[self.positioner_name]
        
        self._widget.sigJoystickXY.connect(self.moveXY)
        self._widget.sigJoystickZA.connect(self.moveZA)
        
    def moveXY(self, x, y):
        print(x)
        if abs(x)>0 or abs(y) >0:
            self.positioner.moveForever(speed=(0, x, y, 0), is_stop=False)
        else:
            self.stop_x()
            self.stop_y()
        return x, y
    
    def moveZA(self, a, z):
        print(z)
        if abs(a)>0 or abs(z) >0:
            self.positioner.moveForever(speed=(a, 0, 0, z), is_stop=False)
        else:
            self.stop_a()
            self.stop_z()
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
