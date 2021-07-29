import importlib

from imswitch.imcommon.model import pythontools


class LantzLaser:
    def __new__(cls, iName, ports):
        if len(ports) < 1:
            raise ValueError('LantzLaser requires at least one port, none passed')

        lasers = []
        for port in ports:
            laser = getLaser(iName, port)
            lasers.append(laser)

        return lasers[0] if len(ports) == 1 else LinkedLantzLaser(lasers)


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
        if item == 'lasers':
            return super().__getattribute__(item)  # Prevent infinite recursion on lasers object

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
        if key == 'lasers':
            super().__setattr__(key, value)  # Prevent infinite recursion on lasers object

        for laser in self.lasers:
            setattr(laser, key, value)


def getLaser(iName, port):
    pName, driverName = iName.rsplit('.', 1)

    try:
        # Try our included drivers first
        package = importlib.import_module(
            pythontools.joinModulePath('imswitch.imcontrol.model.lantzdrivers', pName)
        )
        driver = getattr(package, driverName)
        laser = driver(port)
        laser.initialize()
    except Exception as e1:
        driverNotFound = isinstance(e1, ModuleNotFoundError) or isinstance(e1, AttributeError)

        try:
            # If that fails, try to load the driver from lantz
            package = importlib.import_module(
                pythontools.joinModulePath('lantz.drivers', pName)
            )
            driver = getattr(package, driverName)
            laser = driver(port)
            laser.initialize()
        except Exception as e2:
            if driverNotFound:
                driverNotFound = (isinstance(e2, ModuleNotFoundError) or
                                  isinstance(e2, AttributeError))

            if driverNotFound:
                print(f'No lantz driver found matching "{iName}" for laser, loading mocker')
            else:
                if not isinstance(e1, ModuleNotFoundError) or isinstance(e1, AttributeError):
                    errorDetails = str(e1)
                else:
                    errorDetails = str(e2)

                print(f'Failed to initialize lantz driver "{iName}" for laser, loading mocker'
                      f' (error details: {errorDetails})')

            try:
                # If that also fails, try loading a mock driver
                package = importlib.import_module(
                    pythontools.joinModulePath('imswitch.imcontrol.model.lantzdrivers_mock.', pName)
                )
                driver = getattr(package, driverName)
                laser = driver(port)
                laser.initialize()
            except Exception as e3:
                if isinstance(e3, ModuleNotFoundError) or isinstance(e3, AttributeError):
                    print(f'No mocker found matching "{iName}"')
                else:
                    print(f'Failed to initialize mocker for "{iName}"')

                if driverNotFound:
                    raise NoSuchDriverError(f'No lantz driver found matching "{iName}"')
                else:
                    raise DriverLoadError(f'Failed to initialize lantz driver "{iName}"')

    return laser


class NoSuchDriverError(Exception):
    """ Exception raised when the specified driver is not found. """

    def __init__(self, message):
        self.message = message


class DriverLoadError(Exception):
    """ Exception raised when the specified driver fails to be initialized. """

    def __init__(self, message):
        self.message = message


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
