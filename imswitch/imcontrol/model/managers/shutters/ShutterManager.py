from abc import ABC, abstractmethod

from typing import Union


class ShutterManager(ABC):
    """ Abstract base class for managers that control shutter. Each type of
    shutter corresponds to a manager derived from this class. """

    @abstractmethod
    def __init__(self, shutterInfo, name: str) -> None:
        """
        Args:
            shutterInfo: See setup file documentation.
            name: The unique name that the device is identified with in the
              setup file.
        """
        self._shutterInfo = shutterInfo
        self.__name = name

    @property
    def name(self) -> str:
        """ Unique shutter name, defined in the shutter's setup info. """
        return self.__name

    @abstractmethod
    def setEnabled(self, enabled: bool) -> None:
        """ Sets whether the shutter is enabled. """
        pass

    def setScanModeActive(self, active: bool) -> None:
        """ Sets whether the shutter should be in scan mode (if the shutter
        supports it). """
        pass

    def finalize(self) -> None:
        """ Close/cleanup shutter. """
        pass


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
