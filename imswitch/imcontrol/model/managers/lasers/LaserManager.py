from abc import ABC, abstractmethod


class LaserManager(ABC):
    """ Abstract class for a manager for controlling lasers. Intended to be
    extended for each type of laser. """

    @abstractmethod
    def __init__(self, laserInfo, name, isBinary, isDigital, valueUnits):
        self._laserInfo = laserInfo
        self.__name = name
        self.__isBinary = isBinary
        self.__isDigital = isDigital
        self.__wavelength = laserInfo.wavelength
        self.__valueRangeMin = laserInfo.valueRangeMin
        self.__valueRangeMax = laserInfo.valueRangeMax
        self.__valueRangeStep = laserInfo.valueRangeStep
        self.__valueUnits = valueUnits

    @property
    def name(self):
        return self.__name

    @property
    def isBinary(self):
        """Whether the laser can only be turned on and off, and its value
        cannot be changed."""
        return self.__isBinary

    @property
    def isDigital(self):
        """Whether the laser is digital."""
        return self.__isDigital

    @property
    def wavelength(self):
        return self.__wavelength

    @property
    def valueRangeMin(self):
        """The minimum value that the laser can be set to."""
        return self.__valueRangeMin

    @property
    def valueRangeMax(self):
        """The maximum value that the laser can be set to."""
        return self.__valueRangeMax

    @property
    def valueRangeStep(self):
        """The step of the value range that the laser can be set to."""
        return self.__valueRangeStep

    @property
    def valueUnits(self):
        """The units of the laser value, e.g. "mW" or "V"."""
        return self.__valueUnits

    @abstractmethod
    def setEnabled(self, enabled):
        """Sets whether the laser is enabled."""
        pass

    @abstractmethod
    def setValue(self, value):
        pass

    def setScanModeActive(self, active):
        """Sets whether the laser should be in scan mode (if supported)."""
        pass

    def finalize(self):
        """ Close/cleanup laser. """
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

