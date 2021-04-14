import importlib
from abc import ABC, abstractmethod


class MultiManager(ABC):
    """ Abstract class for a manager used to control a group of sub-managers.
    Intended to be extended for each type of manager. """

    @abstractmethod
    def __init__(self, managedDeviceInfos, subManagersPackage, **kwargs):
        self._subManagers = {}
        currentPackage = '.'.join(__name__.split('.')[:-1])
        for managedDeviceName, managedDeviceInfo in managedDeviceInfos.items():
            # Create sub-manager
            package = importlib.import_module(
                f'{currentPackage}.{subManagersPackage}.{managedDeviceInfo.managerName}'
            )
            manager = getattr(package, managedDeviceInfo.managerName)
            self._subManagers[managedDeviceName] = manager(
                managedDeviceInfo, managedDeviceName, **kwargs)

    def hasDevices(self):
        """ Returns whether this manager manages any devices. """
        return len(self._subManagers) > 0

    def getAllDeviceNames(self):
        """ Returns the names of all managed devices. """
        return list(self._subManagers.keys())

    def execOn(self, managedDeviceName, func):
        """ Executes a function on a specific sub-manager and returns the result. """
        self._validateManagedDeviceName(managedDeviceName)
        return func(self._subManagers[managedDeviceName])

    def execOnAll(self, func):
        """ Executes a function on all sub-managers and returns the results. """
        return {managedDeviceName: func(subManager)
                for managedDeviceName, subManager in self._subManagers.items()}

    def finalize(self):
        """ Close/cleanup sub-managers. """
        for subManager in self._subManagers.values():
            if hasattr(subManager, 'finalize') and callable(subManager.finalize):
                subManager.finalize()

    def _validateManagedDeviceName(self, managedDeviceName):
        """ Raises an error if the specified device is not managed by this
        manager. """
        if managedDeviceName not in self._subManagers:
            raise NoSuchSubManagerError(f'Device "{managedDeviceName}" does not exist or is not'
                                        f' managed by this {self.__class__.__name__}.')

    def __getitem__(self, key):
        return self._subManagers[key]

    def __iter__(self):
        yield from self._subManagers.items()


class NoSuchSubManagerError(RuntimeError):
    """ Error raised when a function related to a sub-manager is called if the
    sub-manager is not managed by the MultiManager. """
    pass


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
