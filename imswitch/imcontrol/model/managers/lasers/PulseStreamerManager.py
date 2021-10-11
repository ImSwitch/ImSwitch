"""
Created on Mon Oct 11 09:48:00 2021

@author: jacopoabramo
"""

from pulsestreamer.sequence import OutputState
from imswitch.imcommon.model import initLogger
from pulsestreamer import PulseStreamer, findPulseStreamers
from .LaserManager import LaserManager

class PulseStreamerManager(LaserManager):
    """ LaserManager for controlling Pulse Streamer 8/2 from Swabian Instruments.

    Manager properties:

    - ``streamer_ip``   -- streamer IP address
    - ``channel_index`` -- streamer digital output (0 to 7)
    """

    def __init__(self, laserInfo, name):
        self._logger = initLogger(self, instanceName=name)

        self._ip_hostname    = laserInfo.managerProperties['streamer_ip']
        self._channel_index  = laserInfo.managerProperties['channel_index']
        self._pulse_streamer = PulseStreamer(ip_hostname=self._ip_hostname)

        super().__init__(laserInfo, name, isBinary=True, valueUnits="V", valueDecimals=1)

    def setEnabled(self, enabled):
        if enabled:
            self._pulse_streamer.constant(OutputState([self._channel_index]))
        else:
            self._pulse_streamer.constant(OutputState.ZERO())

    def setValue(self, value):
        # todo: how to implement?
        pass

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
