from imswitch.imcommon.model import initLogger
from .LaserManager import LaserManager
import numpy as np

class VirtualLaserManager(LaserManager):
    """ LaserManager for controlling LEDs and LAsers connected to an
    ESP32 exposing a REST API
    Each LaserManager instance controls one LED.

    Manager properties:

    - ``rs232device`` -- name of the defined rs232 communication channel
      through which the communication should take place

    """

    def __init__(self, laserInfo, name, **lowLevelManagers):
        super().__init__(laserInfo, name, isBinary=False, valueUnits='mW', valueDecimals=0)
        try:
            self.VirtualMicroscope = lowLevelManagers["rs232sManager"]["VirtualMicroscope"]
        except:
            return
        # assign the camera from the Virtual Microscope
        self._laser = self.VirtualMicroscope._illuminator

        self.__logger = initLogger(self, instanceName=name)
        self.channel_index = laserInfo.managerProperties['channel_index']

        # set the laser to 0
        self.power = 0
        self.enabled = False
        self.setEnabled(self.enabled)

    def setEnabled(self, enabled,  getReturn=True):
        """Turn on (N) or off (F) laser emission"""
        self.enabled = enabled
        self._laser.set_intensity(self.channel_index, int(self.power*self.enabled))

    def setValue(self, power, getReturn=True):
        """Handles output power.
        Sends a RS232 command to the laser specifying the new intensity.
        """
        self.power = power
        if self.enabled:
            self._laser.set_intensity(self.channel_index,
                                    int(self.power))


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
