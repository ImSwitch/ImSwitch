from lantz import Q_

from .LantzLaserManager import LantzLaserManager


class CoboltLaserManager(LantzLaserManager):
    """ LaserManager for Cobolt lasers that are fully digitally controlled
    using drivers available through Lantz. Uses digital modulation mode when
    scanning.

    Available manager properties: Same as LantzLaserManager.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._digitalMod = False

        self._laser.digital_mod = False
        self._laser.enabled = False
        self._laser.autostart = False

    def setEnabled(self, enabled):
        self._laser.enabled = enabled

    def setValue(self, power):
        power = int(power)
        if self._digitalMod:
            self._setModPower(power * Q_(1, 'mW'))
        else:
            self._setBasicPower(power * Q_(1, 'mW'))

    def setScanModeActive(self, active):
        if active:
            powerQ = self._laser.power_sp * self._numLasers
            self._laser.enter_mod_mode()
            self._setModPower(powerQ)
            print(f'Entered digital modulation mode')
            print(f'Modulation mode is: {self._laser.mod_mode}')
        else:
            self._laser.digital_mod = False
            self._laser.query('cp')
            print('Exited digital modulation mode')

        self._digitalMod = active

    def _setBasicPower(self, power):
        self._laser.power_sp = power / self._numLasers

    def _setModPower(self, power):
        self._laser.power_mod = power / self._numLasers
        print(f'Set digital modulation mode power to: {power}')


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
