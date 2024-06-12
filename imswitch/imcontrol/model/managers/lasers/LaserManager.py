from abc import ABC, abstractmethod

from typing import Union


class LaserManager(ABC):
    """ Abstract base class for managers that control lasers. Each type of
    laser corresponds to a manager derived from this class. """

    @abstractmethod
    def __init__(self, laserInfo, name: str, isBinary: bool, valueUnits: str,
                 valueDecimals: int, isModulated: bool = False) -> None:
        """
        Args:
            laserInfo: See setup file documentation.
            name: The unique name that the device is identified with in the
              setup file.
            isBinary: Whether the laser can only be turned on and off, and its
              value cannot be changed.
            valueUnits: The units of the laser value, e.g. "mW" or "V".
            valueDecimals: How many decimals are accepted in the laser value.
            isModulated: Whether the laser can be frequency modulated.
        """
        self._laserInfo = laserInfo
        self.__name = name
        self.__isBinary = isBinary
        self.__wavelength = laserInfo.wavelength
        self.__valueRangeMin = laserInfo.valueRangeMin
        self.__valueRangeMax = laserInfo.valueRangeMax
        self.__valueRangeStep = laserInfo.valueRangeStep
        self.__valueUnits = valueUnits
        self.__valueDecimals = valueDecimals
        self.__isModulated = isModulated
        if isModulated:
            self.__freqRangeMin = laserInfo.freqRangeMin
            self.__freqRangeMax = laserInfo.freqRangeMax
            self.__freqRangeInit = laserInfo.freqRangeInit
        else:
            self.__freqRangeMin = None
            self.__freqRangeMax = None
            self.__freqRangeInit = None

    @property
    def name(self) -> str:
        """ Unique laser name, defined in the laser's setup info. """
        return self.__name

    @property
    def isBinary(self) -> bool:
        """ Whether the laser can only be turned on and off, and its value
        cannot be changed. """
        return self.__isBinary

    @property
    def wavelength(self) -> int:
        """ The wavelength of the laser. """
        return self.__wavelength

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
    
    @property
    def isModulated(self) -> bool:
        """ Whether the laser supports frequency modulation."""
        return self.__isModulated

    @property
    def freqRangeMin(self) -> int:
        """ The minimum frequency of the laser modulation. """
        return self.__freqRangeMin
    
    @property
    def freqRangeMax(self) -> int:
        """ The maximum frequency of the laser modulation. """
        return self.__freqRangeMax
    
    @property
    def freqRangeInit(self) -> int:
        """ The initial frequency of the laser modulation. """
        return self.__freqRangeInit

    @abstractmethod
    def setEnabled(self, enabled: bool) -> None:
        """ Sets whether the laser is enabled. """
        pass

    @abstractmethod
    def setValue(self, value: Union[int, float]) -> None:
        """ Sets the value of the laser. """
        pass

    def setModulationEnabled(self, enabled: bool) -> None:
        """ Sets wether the laser frequency modulation is enabled. """
        pass

    def setModulationFrequency(self, frequency: int) -> None:
        """ Sets the laser modulation frequency. """
        pass
    
    def setModulationDutyCycle(self, dutyCycle: int) -> None:
        """ Sets the laser modulation duty cycle. """

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
