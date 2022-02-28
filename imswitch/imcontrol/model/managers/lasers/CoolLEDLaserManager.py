from imswitch.imcommon.model import initLogger
from .LaserManager import LaserManager


class CoolLEDLaserManager(LaserManager):
    """ LaserManager for controlling the LEDs from CoolLED. Each LaserManager
    instance controls one LED.

    Manager properties:

    - ``rs232device`` -- name of the defined rs232 communication channel
      through which the communication should take place
    - ``channel_index`` -- laser channel (A to H)
    """

    def __init__(self, laserInfo, name, **lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        self._rs232manager = lowLevelManagers['rs232sManager'][
            laserInfo.managerProperties['rs232device']
        ]
        self.__channel_index = laserInfo.managerProperties['channel_index']
        self.__digital_mod = False

        super().__init__(laserInfo, name, isBinary=False, valueUnits='mW', valueDecimals=0)

    def setEnabled(self, enabled):
        """Turn on (N) or off (F) laser emission"""
        if enabled:
            value = "N"
        else:
            value = "F"
        cmd = "C" + self.__channel_index + value
        self._rs232manager.query(cmd)

    def setValue(self, power):
        """Handles output power.
        Sends a RS232 command to the laser specifying the new intensity.
        """
        cmd = "C" + self.__channel_index + "IX" + "{0:03.0f}".format(power)
        self.__logger.debug(cmd)
        self._rs232manager.query(cmd)


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
