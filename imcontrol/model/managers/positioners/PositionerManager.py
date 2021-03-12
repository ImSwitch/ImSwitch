from abc import ABC, abstractmethod


class PositionerManager(ABC):
    @abstractmethod
    def __init__(self, name, initialPosition):
        self.__name = name
        self._position = initialPosition

    @property
    def name(self):
        return self.__name

    @property
    def position(self):
        return self._position

    @abstractmethod
    def move(self, dist):
        """Moves the positioner by the specified distance and returns the new
        position. Derived classes will update the position field manually."""
        pass

    @abstractmethod
    def setPosition(self, position):
        """Adjusts the positioner to the specified position and returns the new
        position. Derived classes will update the position field manually."""
        pass

    def finalize(self):
        """ Close/cleanup positioner. """
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

