from .LaserManager import LaserManager


class AAAOTFLaserManager(LaserManager):
    """ LaserManager for controlling one channel of an AA Opto-Electronic
    acousto-optic modulator/tunable filter through RS232 communication.

    Manager properties:

    - ``rs232device`` -- name of the defined rs232 communication channel
      through which the communication should take place
    - ``channel`` -- index of the channel in the acousto-optic device that
      should be controlled (indexing starts at 1)
    - ``toggleTrueExternal`` -- bool describing if the channel setting
      should use internal (False) or external (True) setting to be able
      to modify the laser power through ImSwitch. Default: False/null
    - ``ttlToggling`` -- bool describing if the channel should default to
      an extrenal control after setting a power value, to allow fast ttl
      toggling from another source. 
    """

    def __init__(self, laserInfo, name, **lowLevelManagers):
        self._channel = int(laserInfo.managerProperties['channel'])
        self._rs232manager = lowLevelManagers['rs232sManager'][
            laserInfo.managerProperties['rs232device']
        ]
        if 'toggleTrueExternal' in laserInfo.managerProperties:
            self._toggleTrueExternal = laserInfo.managerProperties['toggleTrueExternal']
        else:
            self._toggleTrueExternal = False
        if 'ttlToggling' in laserInfo.managerProperties:
            self._ttlToggling = laserInfo.managerProperties['ttlToggling']
        else:
            self._ttlToggling = False

        if self._toggleTrueExternal:
            if self._ttlToggling:
                #self.blankingOnInternal()
                self.internalControl()
            else:
                #self.blankingOnInternal()
                self.externalControl()
        else:
            if self._ttlToggling:
                #self.blankingOnExternal()
                self.externalControl()
            else:
                #self.blankingOnInternal()
                self.internalControl()

        super().__init__(laserInfo, name, isBinary=False, valueUnits='arb', valueDecimals=0)

    def setEnabled(self, enabled):
        """Turn on (1) or off (0) laser emission"""
        if enabled:
            value = 1
        else:
            value = 0
        cmd = 'L' + str(self._channel) + 'O' + str(value)
        if self._ttlToggling:
            if self._toggleTrueExternal:
                self.externalControl()
            else:
                self.internalControl()
        _ = self._rs232manager.query(cmd)
        if self._ttlToggling:
            if self._toggleTrueExternal:
                self.internalControl()
            else:
                self.externalControl()

    def setValue(self, power):
        """Handles output power.
        Sends a RS232 command to the laser specifying the new intensity.
        """
        valueaotf = round(power)
        cmd = 'L' + str(self._channel) + 'P' + str(valueaotf)
        if self._ttlToggling:
            if self._toggleTrueExternal:
                self.externalControl()
            else:
                self.internalControl()
        _ = self._rs232manager.query(cmd)
        if self._ttlToggling:
            if self._toggleTrueExternal:
                self.internalControl()
            else:
                self.externalControl()

    #def blankingOnInternal(self):
    #    """Switch on the blanking of the channel, internal"""
    #    cmd = 'L' + str(self._channel) + 'O0'
    #    self._rs232manager.write(cmd)

    #def blankingOnExternal(self):
    #    """Switch on the blanking of the channel, external"""
    #    cmd = 'L' + str(self._channel) + 'O0'
    #    self._rs232manager.write(cmd)

    def internalControl(self):
        """Switch the channel to internal control"""
        cmd = 'L' + str(self._channel) + 'I1' + 'O0'
        _ = self._rs232manager.query(cmd)

    def externalControl(self):
        """Switch the channel to external control"""
        cmd = 'L' + str(self._channel) + 'I0'
        _ = self._rs232manager.query(cmd)


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
