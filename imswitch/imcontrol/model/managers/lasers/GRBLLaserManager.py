from .LaserManager import LaserManager


class GRBLLaserManager(LaserManager):
    """ LaserManager for controlling one channel of an AA Opto-Electronic
    acousto-optic modulator/tunable filter through RS232 communication.

    Manager properties:

    - ``rs232device`` -- name of the defined rs232 communication channel
      through which the communication should take place
    - ``channel`` -- index of the channel in the acousto-optic device that
      should be controlled (indexing starts at 1)
    """

    def __init__(self, laserInfo, name, **lowLevelManagers):
        self._rs232manager = lowLevelManagers['rs232sManager'][
            laserInfo.managerProperties['rs232device']
        ]
        self.channel = laserInfo.managerProperties['channel']
        self.laserval = 0
        self.enabled = False
        super().__init__(laserInfo, name, isBinary=False, valueUnits='arb', valueDecimals=0)
        self._rs232manager._board.set_laser_intensity(self.enabled*self.laserval)

    def setEnabled(self, enabled):
        """Turn on (1) or off (0) laser emission"""
        self.enabled = enabled 
        if self.channel == "LASER":
          self._rs232manager._board.set_laser_intensity(enabled*self.laserval)
        else:
          self._rs232manager._board.set_led(self.enabled*self.laserval)
              
    def setValue(self, power):
        """Handles output power.
        Sends a RS232 command to the laser specifying the new intensity.
        """
        self.laserval = round(power)  # assuming input value is [0,1023]
        if self.channel == "LASER":
          self._rs232manager._board.set_laser_intensity(self.enabled*self.laserval)
        else:
          self._rs232manager._board.set_led(self.enabled*self.laserval)


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
