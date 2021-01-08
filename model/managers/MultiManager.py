import importlib
from abc import ABC, abstractmethod


class MultiManager(ABC):
    @abstractmethod
    def __init__(self, managedDeviceInfos, subManagersPackage, **kwargs):
        self._subManagers = {}
        for managedDeviceName, managedDeviceInfo in managedDeviceInfos.items():
            # Create sub-manager
            package = importlib.import_module(
                f'model.managers.{subManagersPackage}.{managedDeviceInfo.managerName}'
            )
            manager = getattr(package, managedDeviceInfo.managerName)
            self._subManagers[managedDeviceName] = manager(
                managedDeviceInfo, managedDeviceName, **kwargs
            )

    def execOn(self, managedDeviceName, func):
        """ Executes a function on a specific sub-manager and returns the result. """
        self._validateManagedDeviceName(managedDeviceName)
        return func(self._subManagers[managedDeviceName])

    def execOnAll(self, func):
        """ Executes a function on all sub-managers and returns the results. """
        return {managedDeviceName: func(subManager)
                for managedDeviceName, subManager in self._subManagers.items()}

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
