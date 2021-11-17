"""
Created on Wed Jan 13 09:40:00 2021

@author: jonatanalvelid
"""
from imswitch.imcommon.model import initLogger
from .LaserManager import LaserManager
from imswitch.imcontrol.model.interfaces.ESP32RestAPI import ESP32Client

class ESP32LightSheetManager(LaserManager):

    def __init__(self, laserInfo, name, **lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)
        self.power = 0

        self.esp32 = ESP32Client(laserInfo.managerProperties['host'], port=80)
        super().__init__(laserInfo, name, isBinary=False, valueUnits='AU', valueDecimals=0)

    def setEnabled(self, enabled):
        """Turn on (N) or off (F) laser emission"""

    def setValue(self, amplitude_x):
        """Handles output power.
        Sends a RS232 command to the laser specifying the new intensity.
        """
        self.esp32.galvo_x(amplitude_x)



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
