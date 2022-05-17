from imswitch.imcommon.model import initLogger
from .LaserManager import LaserManager

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
        super().__init__(laserInfo, name, isBinary=False, valueUnits='mW', valueDecimals=0)
        self._rs232manager = lowLevelManagers['rs232sManager'][
            laserInfo.managerProperties['rs232device']
        ]
        self.__logger = initLogger(self, instanceName=name)
        self.power = 0
        self.__channel_index = laserInfo.managerProperties['channel_index']
        try:
            self.__filter_change = laserInfo.managerProperties['filter_change']
        except:
            self.__filter_change = False

        self.enabled = False
        

    def setEnabled(self, enabled):
        """Turn on (N) or off (F) laser emission"""
        self.enabled = enabled
        self._rs232manager._esp32.set_laser(self.__channel_index, self.power*self.enabled, self.__filter_change, is_blocking=True)
        

    def setValue(self, power):
        """Handles output power.
        Sends a RS232 command to the laser specifying the new intensity.
        """
        self.power = power
        if self.enabled:
            self._rs232manager._esp32.set_laser(self.__channel_index, self.power, False, is_blocking=True)

    def sendTrigger(self, triggerId):
        self._rs232manager._esp32.sendTrigger(triggerId)



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
