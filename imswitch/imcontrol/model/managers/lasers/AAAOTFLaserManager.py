from .LaserManager import LaserManager


class AAAOTFLaserManager(LaserManager):
    """ LaserManager for controlling one channel of an AA Opto-Electronic
    acousto-optic modulator/tunable filter through RS232 communication.

    Available manager properties:

    - ``rs232device`` -- name of the defined rs232 communication channel
      through which the communication should take place
    - ``channel`` -- index of the channel in the acousto-optic device that
      should be controlled (indexing starts at 1)
    """

    def __init__(self, laserInfo, name, **kwargs):
        print(type(laserInfo))
        self._channel = int(laserInfo.managerProperties['channel'])
        self._rs232manager = kwargs['rs232sManager'][laserInfo.managerProperties['rs232device']]

        self.blankingOn()
        self.internalControl()

        super().__init__(
            laserInfo, name, isBinary=False, isDigital=True, valueUnits='arb'
        )

    def setEnabled(self, enabled):
        """Turn on (1) or off (0) laser emission"""
        if enabled==True:
            value = 1
        else:
            value = 0
        cmd = 'L' + str(self._channel) + 'O' + str(value)
        self._rs232manager.send(cmd)

    def setValue(self, power):
        """Handles output power.
        Sends a RS232 command to the laser specifying the new intensity.
        """        
        valueaotf = round(power)  # assuming input value is [0,1023]
        cmd = 'L' + str(self._channel) + 'P' + str(valueaotf)
        self._rs232manager.send(cmd)

    def blankingOn(self):
        """Switch on the blanking of all the channels"""
        cmd = 'L0' + 'I1' + 'O1'
        self._rs232manager.send(cmd)

    def internalControl(self):
        """Switch the channel to external control"""
        cmd = 'L' + str(self._channel) + 'I1'
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
