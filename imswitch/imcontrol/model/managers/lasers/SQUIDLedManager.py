from imswitch.imcommon.model import initLogger
from .LaserManager import LaserManager

class SQUIDLedManager(LaserManager):
    """ LaserManager for controlling LEDs and LAsers connected to an 
    ESP32 exposing a REST API
    Each LaserManager instance controls one LED.

    Manager properties:

    - ``rs232device`` -- name of the defined rs232 communication channel
      through which the communication should take place
    - ``channel_index`` -- laser channel (A to H)
    """
    
    ILLUMINATION_SOURCE_LED_ARRAY_FULL = 0;
    ILLUMINATION_SOURCE_LED_ARRAY_LEFT_HALF = 1
    ILLUMINATION_SOURCE_LED_ARRAY_RIGHT_HALF = 2
    ILLUMINATION_SOURCE_LED_ARRAY_LEFTB_RIGHTR = 3
    ILLUMINATION_SOURCE_LED_ARRAY_LOW_NA = 4;
    ILLUMINATION_SOURCE_LED_ARRAY_LEFT_DOT = 5;
    ILLUMINATION_SOURCE_LED_ARRAY_RIGHT_DOT = 6;
    ILLUMINATION_SOURCE_LED_EXTERNAL_FET = 20


    def __init__(self, laserInfo, name, **lowLevelManagers):
        self._rs232manager = lowLevelManagers['rs232sManager'][
            laserInfo.managerProperties['rs232device']
        ]
        self.__logger = initLogger(self, instanceName=name)

        self.__channel_index = laserInfo.managerProperties['channel_index']
        self.__isBinary = laserInfo.managerProperties['isBinary']
        self.illumination_source = laserInfo.managerProperties['illumination_source']
        self.R=0
        self.G=0
        self.B=0

        self.enabled = False
        
        super().__init__(laserInfo, name, isBinary=self.__isBinary, valueUnits='mW', valueDecimals=0)
        
        

    def setEnabled(self, enabled):
        """Turn on (N) or off (F) laser emission"""
        
        self.enabled = enabled
        self._rs232manager._squid.set_illumination_led_matrix(illumination_source=self.illumination_source,
                                                              r=self.R*self.enabled,
                                                              g=self.G*self.enabled,
                                                              b=self.B*self.enabled)
       

    def setValue(self, power):
        """Handles output power.
        Sends a RS232 command to the laser specifying the new intensity.
        """
        self.power = power
        self.R=power
        self.G=power
        self.B=power
    
        if self.enabled:
            self._rs232manager._squid.set_illumination_led_matrix(illumination_source=self.illumination_source,
                                                            r=self.R,
                                                            g=self.G,
                                                            b=self.B)



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
