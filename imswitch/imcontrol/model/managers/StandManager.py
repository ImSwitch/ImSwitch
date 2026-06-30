from imswitch.imcommon.model import initLogger
from imswitch.imcommon.model import pythontools
from abc import ABC
import importlib


_MANAGER_ALIASES = {
    "LeicaDMIManager": "LeicaDMIStandManager",
}


class StandManager(ABC):
    """ StandManager interface for dealing with microscope stand managers. """
    def __init__(self, deviceInfo, **lowLevelManagers):
        self.__logger = initLogger(self)
        self._subManager = None
        currentPackage = '.'.join(__name__.split('.')[:-1])
        if deviceInfo:
            try:
                managerName = self._resolveManagerName(deviceInfo.managerName)
                package = importlib.import_module(
                        pythontools.joinModulePath(f'{currentPackage}.{"stands"}', managerName))
                manager = getattr(package, managerName)
                self._subManager = manager(deviceInfo, **lowLevelManagers)
            except Exception as e:
                self.__logger.error(
                    f'Failed to load stand manager {deviceInfo.managerName}: {e}'
                )

    def _resolveManagerName(self, managerName):
        resolvedName = _MANAGER_ALIASES.get(managerName, managerName)
        if resolvedName != managerName:
            self.__logger.warning(
                f'Stand manager name {managerName} is deprecated; using {resolvedName}.'
            )
        return resolvedName

    def isConnected(self):
        if self._subManager is None:
            return False

        isConnected = getattr(self._subManager, 'isConnected', None)
        if isConnected is None:
            return True

        return bool(isConnected())

    def motCorrPos(self, position):
        return self._delegate('motCorrPos', position)

    def _delegate(self, attrName, *args, **kwargs):
        if self._subManager is None:
            self.__logger.warning(
                f'Cannot run stand command {attrName}: no stand manager is available.'
            )
            return None

        return getattr(self._subManager, attrName)(*args, **kwargs)

    def __getattr__(self, attrName):
        subManager = self.__dict__.get('_subManager', None)
        if subManager is not None:
            return getattr(subManager, attrName)
        raise AttributeError(attrName)


# Copyright (C) 2020-2023 ImSwitch developers
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
