from imswitch.imcommon.model import initLogger
from .PositionerManager import PositionerManager
import time
import numpy as np
from imswitch.imcommon.model import APIExport, generateAPI, initLogger
import threading

class VirtualStageManager(PositionerManager):
    def __init__(self, positionerInfo, name, **lowLevelManagers):
        super().__init__(positionerInfo, name, initialPosition={axis: 0 for axis in positionerInfo.axes})
        self.__logger = initLogger(self, instanceName=name)
        try:
            self.VirtualMicroscope = lowLevelManagers["rs232sManager"]["VirtualMicroscope"]
        except:
            return
        # assign the camera from the Virtual Microscope
        self._positioner = self.VirtualMicroscope._positioner

        # get bootup position and write to GUI
        self._position = self.getPosition()

    def move(self, value=0, axis="X", is_absolute=False, is_blocking=True, acceleration=None, speed=None, isEnable=None, timeout=1):
        if axis == "X":
            self._positioner.move(x=value, is_absolute=is_absolute)
        if axis == "Y":
            self._positioner.move(y=value, is_absolute=is_absolute)
        if axis == "Z":
            self._positioner.move(z=value, is_absolute=is_absolute)
        if axis == "A":
            self._positioner.move(t=value, is_absolute=is_absolute)
        if axis == "XYZ":
            self._positioner.move(x=value[0], y=value[1], z=value[2], is_absolute=is_absolute)
        if axis == "XY":
            self._positioner.move(x=value[0], y=value[1], is_absolute=is_absolute)

        #FIXME: for i, iaxis in enumerate(("A","X","Y","Z")):
        #    self._position[iaxis] = self._motor._position[i]

    def moveForever(self, speed=(0, 0, 0, 0), is_stop=False):
        pass

    def setSpeed(self, speed, axis=None):
        pass
    
    def setPosition(self, value, axis):
        pass
    
    def getPosition(self):
        # load position from device
        # t,x,y,z
        allPositionsDict = self._positioner.get_position()
        return allPositionsDict

    def forceStop(self, axis):
        if axis=="X":
            self.stop_x()
        elif axis=="Y":
            self.stop_y()
        elif axis=="Z":
            self.stop_z()
        elif axis=="A":
            self.stop_a()
        else:
            self.stopAll()

    def get_abs(self, axis="X"):
        return self._position[axis]

    def stop_x(self):
        pass
        
    def stop_y(self):
        pass 

    def stop_z(self):
        pass

    def stop_a(self):
        pass

    def stopAll(self):
        pass

    def doHome(self, axis, isBlocking=False):
        if axis == "X": self.home_x(isBlocking)
        if axis == "Y": self.home_y(isBlocking)
        if axis == "Z": self.home_z(isBlocking)
        

    def home_x(self, isBlocking):
        self.move(value=0, axis="X", is_absolute=True)
        self.setPosition(axis="X", value=0)
        
    def home_y(self,isBlocking):
        self.move(value=0, axis="Y", is_absolute=True)
        self.setPosition(axis="Y", value=0)

    def home_z(self,isBlocking):
        self.move(value=0, axis="Z", is_absolute=True)
        self.setPosition(axis="Z", value=0)

    def home_xyz(self):
        if self.homeXenabled and self.homeYenabled and self.homeZenabled:
            [self.setPosition(axis=axis, value=0) for axis in ["X","Y","Z"]]


# Copyright (C) 2020, 2021 The imswitch developers
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
