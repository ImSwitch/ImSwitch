
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex
from imswitch.imcontrol.view import guitools
from imswitch.imcommon.model import initLogger
from ..basecontrollers import LiveUpdatedController


class JoystickController(LiveUpdatedController):
    """ Linked to JoystickWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # scaler
        self.scaler = 100
        
        # initialize the positioner
        self.positioner_name = self._master.positionersManager.getAllDeviceNames()[0]
        self.positioner = self._master.positionersManager[self.positioner_name]
        
        self._widget.sigJoystickXY.connect(self.moveXY)
        self._widget.sigJoystickZA.connect(self.moveZA)
        
    def moveXY(self, x, y):
        if abs(x)>0 or abs(y) >0:
            self.positioner.moveForever(speed=(0, x*self.scaler, y*self.scaler, 0), is_stop=False)
        else:
            for i in range(3):
                self.stop("X")
                self.stop("Y")
        return x, y
    
    def moveZA(self, a, z):
        if abs(a)>0 or abs(z) >0:
            self.positioner.moveForever(speed=(a*self.scaler, 0, 0, z*self.scaler), is_stop=False)
        else:
            for i in range(3):
                # currently it takes a few trials to stop the stage
                self.stop("A")
                self.stop("Z")
        return a, z
    
    def stop(self, axis="X"):
        self.positioner.forceStop(axis)

        
        
        
        



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
