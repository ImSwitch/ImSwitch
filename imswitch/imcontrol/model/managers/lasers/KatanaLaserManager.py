"""
Created on Wed Jan 13 09:40:00 2021

@author: jonatanalvelid
"""

import numpy as np
from .LaserManager import LaserManager


class KatanaLaserManager(LaserManager):
    def __init__(self, laserInfo, name, **kwargs):
        self._rs232manager = kwargs['rs232sManager'][laserInfo.managerProperties['rs232device']]

        self.__power_setting = 1  # To change power with python (1) or knob (0)
        self.__mode = 0  # Constant current (1) or constant power (0) mode
        self.__triggerMode = 0  # Trigger: internal (0)

        self.setPowerSetting(self.__power_setting)
        self.setTriggerSource(self.__triggerMode)
        self.setMode(self.__mode)        

        super().__init__(
            laserInfo, name, isBinary=False, isDigital=True, valueUnits='mW'
        )

    def setEnabled(self, enabled):
        """Turn on (1) or off (0) laser emission"""
        if enabled==True:
            value = 1
        else:
            value = 0
        cmd = "le=" + str(int(value))
        self._rs232manager.send(cmd)

    def setValue(self, power):
        """Handles output power.
        Sends a RS232 command to the laser specifying the new intensity.
        """        
        if(self.__power_setting != 1):
            print("Knob mode: impossible to change power.")
            return
        power = round(np.max([0,power])/1000, 3)  # Conversion from mW to W and round
        cmd = "lp=" + str(power)
        self._rs232manager.send(cmd)

    def setDigitalMod(self, digital, initialValue):
        pass

    def setPowerSetting(self, power_setting):
        """Power can be changed via this interface (1), or manual knob (0)"""
        cmd = "lps=" + str(power_setting)
        self._rs232manager.send(cmd)

    def setTriggerSource(self, source):
        """Internal frequency generator (0)
        External trigger source for adjustable trigger level (1), Tr-1 In
        External trigger source for TTL trigger (2), Tr-2 In
        """
        cmd = "lts=" + str(source)
        self._rs232manager.send(cmd)

    def setMode(self, mode):
        """Constant current mode (0) or constant power mode (1)"""
        cmd = "lip=" + str(mode)
        self._rs232manager.send(cmd)


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
