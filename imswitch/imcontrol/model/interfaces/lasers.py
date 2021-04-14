import importlib

from .lasers_mock import MockLaser


class LantzLaser:
    def __new__(cls, iName, ports):
        try:
            if len(ports) < 1:
                raise ValueError('LantzLaser requires at least one port, none passed')

            driver = getDriver(iName)

            lasers = []
            for port in ports:
                laser = driver(port)
                laser.initialize()
                lasers.append(laser)

            return lasers[0] if len(ports) == 1 else LinkedLantzLaser(lasers)
        except:
            return MockLaser()


class LinkedLantzLaser:
    def __init__(self, lasers):
        if len(lasers) < 1:
            raise ValueError('LinkedLantzLaser requires at least one laser, none passed')

        self.lasers = lasers

    @property
    def idn(self):
        return 'Linked Lasers ' + ' '.join([str(laser.idn) for laser in self.lasers])

    @property
    def autostart(self):
        value = self.lasers[0].autostart
        for laser in self.lasers:
            if laser.autostart != value:
                raise ValueError(f'Laser {laser.idn} autostart state is {laser.autostart} while laser'
                                 f' {self.lasers[0]} autostart state is {value}')

        return value

    @autostart.setter
    def autostart(self, value):
        for laser in self.lasers:
            laser.autostart = value

    @property
    def enabled(self):
        value = self.lasers[0].enabled
        for laser in self.lasers:
            if laser.enabled != value:
                raise ValueError(f'Laser {laser.idn} enabled state is {laser.enabled} while laser'
                                 f' {self.lasers[0]} enabled state is {value}')

        return value

    @enabled.setter
    def enabled(self, value):
        for laser in self.lasers:
            laser.enabled = value

    @property
    def power(self):
        return sum([laser.power for laser in self.lasers])

    @property
    def power_sp(self):
        return sum([laser.power_sp for laser in self.lasers])

    @power_sp.setter
    def power_sp(self, value):
        for laser in self.lasers:
            laser.power_sp = value / len(self.lasers)

    @property
    def digital_mod(self):
        value = self.lasers[0].digital_mod
        for laser in self.lasers:
            if laser.digital_mod != value:
                raise ValueError(f'Laser {laser.idn} digital_mod state is {laser.digital_mod} while'
                                 f' laser {self.lasers[0]} digital_mod state is {value}')

        return value

    @digital_mod.setter
    def digital_mod(self, value):
        for laser in self.lasers:
            laser.digital_mod = value

    @property
    def mod_mode(self):
        return [laser.mod_mode for laser in self.lasers]

    def enter_mod_mode(self):
        for laser in self.lasers:
            laser.enter_mod_mode()

    def changeEdit(self):
        for laser in self.lasers:
            laser.changeEdit()

    def query(self, value):
        for laser in self.lasers:
            laser.query(value)

    @property
    def power_mod(self):
        """Laser modulated power (mW).
        """
        return sum([laser.power_mod for laser in self.lasers])

    @power_mod.setter
    def power_mod(self, value):
        for laser in self.lasers:
            laser.power_mod = value / len(self.lasers)

    def finalize(self):
        for laser in self.lasers:
            laser.finalize()


def getDriver(iName):
    pName, driverName = iName.rsplit('.', 1)

    try:
        # Try our included drivers first
        package = importlib.import_module('imcontrol.model.drivers.' + pName)
        driver = getattr(package, driverName)
    except ModuleNotFoundError or AttributeError:
        # If that fails, try to load the driver from lantz
        package = importlib.import_module('lantz.drivers.' + pName)
        driver = getattr(package, driverName)

    return driver


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
