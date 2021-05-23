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

    def finalize(self):
        for laser in self.lasers:
            laser.finalize()

    def __getattr__(self, item):
        value = getattr(self.lasers[0], item)
        if callable(value):
            return lambda *args, **kwargs: [getattr(laser, item)(*args, **kwargs)
                                            for laser in self.lasers]
        else:
            for laser in self.lasers:
                valueInLaser = getattr(laser, item)
                if valueInLaser != value:
                    raise ValueError(f'Laser {laser.idn} value {item} is {valueInLaser} while laser'
                                     f' {self.lasers[0]} value {item} is {value}')

            return value

    def __setattr__(self, key, value):
        for laser in self.lasers:
            setattr(laser, key, value)


def getDriver(iName):
    pName, driverName = iName.rsplit('.', 1)

    try:
        # Try our included drivers first
        package = importlib.import_module('imswitch.imcontrol.model.drivers.' + pName)
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
