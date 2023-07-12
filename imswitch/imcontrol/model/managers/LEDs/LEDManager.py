from abc import ABC, abstractmethod

from typing import Union


class LEDManager(ABC):
    """ Abstract base class for managers that control LEDs. Each type of
    LED corresponds to a manager derived from this class. """

    @abstractmethod
    def __init__(self, ledInfo, name: str, isBinary: bool, valueUnits: str,
                 valueDecimals: int) -> None:
        """
        Args:
            ledInfo: See setup file documentation.
            name: The unique name that the device is identified with in the
              setup file.
            isBinary: Whether the LED can only be turned on and off, and its
              value cannot be changed.
            valueUnits: The units of the LED value, e.g. "mW" or "V".
            valueDecimals: How many decimals are accepted in the LED value.
        """
        self._ledInfo = ledInfo
        self.__name = name
        self.__isBinary = isBinary
        self.__valueRangeMin = ledInfo.valueRangeMin
        self.__valueRangeMax = ledInfo.valueRangeMax
        self.__valueRangeStep = ledInfo.valueRangeStep
        self.__valueUnits = valueUnits
        self.__valueDecimals = valueDecimals

    @property
    def name(self) -> str:
        """ Unique LED name, defined in the LED's setup info. """
        return self.__name

    @property
    def isBinary(self) -> bool:
        """ Whether the LED can only be turned on and off, and its value
        cannot be changed. """
        return self.__isBinary

    @property
    def valueRangeMin(self) -> float:
        """ The minimum value that the laser can be set to. """
        return self.__valueRangeMin

    @property
    def valueRangeMax(self) -> float:
        """ The maximum value that the laser can be set to. """
        return self.__valueRangeMax

    @property
    def valueRangeStep(self) -> float:
        """ The default step size of the value range that the laser can be set
        to. """
        return self.__valueRangeStep

    @property
    def valueUnits(self) -> str:
        """ The units of the laser value, e.g. "mW" or "V". """
        return self.__valueUnits

    @property
    def valueDecimals(self):
        """ How many decimals are accepted in the laser value. """
        return self.__valueDecimals

    @abstractmethod
    def setEnabled(self, enabled: bool) -> None:
        """ Sets whether the laser is enabled. """
        pass

    @abstractmethod
    def setValue(self, value: Union[int, float]) -> None:
        """ Sets the value of the laser. """
        pass

    def setScanModeActive(self, active: bool) -> None:
        """ Sets whether the laser should be in scan mode (if the laser
        supports it). """
        pass

    def finalize(self) -> None:
        """ Close/cleanup laser. """
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
