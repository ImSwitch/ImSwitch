"""
Created on Mon Oct 11 09:48:00 2021

@author: jacopoabramo
"""

from imswitch.imcommon.model import initLogger
from .LaserManager import LaserManager

class PulseStreamerLaserManager(LaserManager):
    """ LaserManager for controlling Pulse Streamer 8/2 from Swabian Instruments.

    Manager properties:

    - ``digitalChannel`` -- streamer digital output (0 to 7)
    - ``analogChannel"   -- streamer analog output (0 to 1)
    """

    def __init__(self, laserInfo, name, **lowLevelManagers):
        self._logger = initLogger(self, instanceName=name)
        self._pulseStreamerManager = lowLevelManagers["pulseStreamerManager"]
        self._digitalChannels = laserInfo.managerProperties["digitalChannels"]
        self._analogChannels = laserInfo.managerProperties["analogChannels"]
        

        super().__init__(laserInfo, name, isBinary=self._analogChannels is None, valueUnits="V", valueDecimals=1)

    def setEnabled(self, enabled):
        """Turns ON/OFF the digital channel handled by the manager.
        """
        self._pulseStreamerManager.setDigital(self._digitalChannels, enabled)

    def setValue(self, voltage):
        """Sets the output voltage of the analog channel selected by the manager.
        """
        self._pulseStreamerManager.setAnalog(
            channel=self._analogChannels, voltage=voltage,
            min_val=self.valueRangeMin, max_val=self.valueRangeMax
        )

# Copyright (C) 2021 Eggeling Group
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