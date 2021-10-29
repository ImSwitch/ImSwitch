"""
Created on Wed Jan 13 09:40:00 2021

@author: jonatanalvelid
"""
from imswitch.imcommon.model import initLogger
from .LaserManager import LaserManager
from imswitch.imcontrol.model.interfaces.ESP32RestAPI import ESP32Client

class ESP32LEDLaserManager(LaserManager):
    """ LaserManager for controlling LEDs and LAsers connected to an 
    ESP32 exposing a REST API
    Each LaserManager instance controls one LED.

    Manager properties:

    - ``rs232device`` -- name of the defined rs232 communication channel
      through which the communication should take place
    - ``channel_index`` -- laser channel (A to H)
    """

    def __init__(self, laserInfo, name, **lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)
        self.power = 0

        self.esp32 = ESP32Client(laserInfo.managerProperties['host'], port=80)

        self.__channel_index = laserInfo.managerProperties['channel_index']

        super().__init__(laserInfo, name, isBinary=False, valueUnits='mW', valueDecimals=0)

    def setEnabled(self, enabled):
        """Turn on (N) or off (F) laser emission"""
        self.esp32.set_laser(self.__channel_index, self.power*enabled)

    def setValue(self, power):
        """Handles output power.
        Sends a RS232 command to the laser specifying the new intensity.
        """
        self.power = power
        self.esp32.set_laser(self.__channel_index, self.power)



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
