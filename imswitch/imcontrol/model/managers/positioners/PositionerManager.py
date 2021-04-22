from abc import ABC, abstractmethod


class PositionerManager(ABC):
    """ Abstract class for a manager for controlling positioners. Intended to
    be extended for each type of positioner. """

    @abstractmethod
    def __init__(self, positionerInfo, name, initialPosition):
        self._positionerInfo = positionerInfo
        self._position = initialPosition

        self.__name = name

        self.__axes = positionerInfo.axes
        self.__forPositioning = positionerInfo.forPositioning
        self.__forScanning = positionerInfo.forScanning
        if not positionerInfo.forPositioning and not positionerInfo.forScanning:
            raise ValueError('At least one of forPositioning and forScanning must be set in'
                             ' PositionerInfo.')

    @property
    def name(self):
        return self.__name

    @property
    def position(self):
        return self._position

    @property
    def axes(self):
        return self.__axes

    @property
    def forPositioning(self):
        return self.__forPositioning

    @property
    def forScanning(self):
        return self.__forScanning

    @abstractmethod
    def move(self, dist, axis):
        """ Moves the positioner by the specified distance and returns the new
        position. Derived classes will update the position field manually. If
        the positioner controls multiple axes, the axis must be specified. """
        pass

    @abstractmethod
    def setPosition(self, position, axis):
        """ Adjusts the positioner to the specified position and returns the
        new position. Derived classes will update the position field manually.
        If the positioner controls multiple axes, the axis must be specified.
        """
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

