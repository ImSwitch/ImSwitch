from lantz import Feat
from lantz import Driver
from lantz import Q_


class Cobolt0601_f2(Driver):

    def __init__(self, *args, **kwargs):
        super().__init__()

        self.mW = Q_(1, 'mW')

        self.enabled = False
        self.power_sp = 0 * self.mW
        self._digMod = False

    @property
    def idn(self):
        return 'Simulated laser'

    @property
    def status(self):
        """Current device status
        """
        return 'Simulated laser status'

    # ENABLE LASER
    @property
    def enabled(self):
        """Method for turning on the laser
        """
        return self.enabled_state

    @enabled.setter
    def enabled(self, value):
        self.enabled_state = value

    # LASER'S CONTROL MODE AND SET POINT

    @property
    def power_sp(self):
        """To handle output power set point (mW) in APC Mode
        """
        return self.power_setpoint

    @power_sp.setter
    def power_sp(self, value):
        self.power_setpoint = value

    # LASER'S CURRENT STATUS

    @property
    def power(self):
        """To get the laser emission power (mW)
        """
        return 55555 * self.mW

    def enter_mod_mode(self):
        self._digMod = True

    @property
    def digital_mod(self):
        """digital modulation enable state
        """
        return self._digMod

    @digital_mod.setter
    def digital_mod(self, value):
        self._digMod = value

    @property
    def mod_mode(self):
        """Returns the current operating mode
        """
        return 0

    @Feat(units='mW')
    def power_mod(self):
        return 0

    @power_mod.setter
    def power_mod(self, value):
        pass

    def query(self, text):
        return 0


# Copyright (C) 2017 Federico Barabas
# This file is part of Tormenta.
#
# Tormenta is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tormenta is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
