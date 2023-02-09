from imswitch.imcommon.model import initLogger
from imswitch.imcommon.model import pythontools
from abc import ABC
import importlib


class StandManager(ABC):
    """ StandManager interface for dealing with microscope stand managers. """
    def __init__(self, deviceInfo, **lowLevelManagers):
        self.__logger = initLogger(self)
        self._subManager = None
        currentPackage = '.'.join(__name__.split('.')[:-1])
        if deviceInfo:
            # Create sub-manager
            try:
                package = importlib.import_module(
                    pythontools.joinModulePath(f'{currentPackage}.{"stands"}',deviceInfo.managerName))
                manager = getattr(package, deviceInfo.managerName)
                self._subManager = manager(deviceInfo, **lowLevelManagers)
            except:
                self.__logger.error(f'Failed to load LeicaDMIManager (not provided due to NDA). Loading mocker.')
                package = importlib.import_module(
                    pythontools.joinModulePath(f'{currentPackage}.{"stands"}',f'{deviceInfo.managerName}_mock'))
                manager = getattr(package, f'Mock{deviceInfo.managerName}')
                self._subManager = manager(deviceInfo, **lowLevelManagers)

    def motCorrPos(self, position):
        self._subManager.motCorrPos(position)


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