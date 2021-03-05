from abc import ABC, abstractmethod


class LaserManager(ABC):
    @abstractmethod
    def __init__(self, name, isBinary, isDigital, wavelength,
                 valueRangeMin, valueRangeMax, valueUnits):
        self.__name = name
        self.__isBinary = isBinary
        self.__isDigital = isDigital
        self.__wavelength = wavelength
        self.__valueRangeMin = valueRangeMin
        self.__valueRangeMax = valueRangeMax
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
    def valueUnits(self):
        """The units of the laser value, e.g. "mW" or "V"."""
        return self.__valueUnits

    @abstractmethod
    def setEnabled(self, enabled):
        """Sets whether the laser is enabled."""
        pass

    @abstractmethod
    def setDigitalMod(self, digital, initialValue):
        """Sets whether the laser is in digital modulation mode. Does nothing
        if the laser doesn't support this mode."""
        pass

    @abstractmethod
    def setValue(self, value):
        pass

    def finalize(self):
        """ Close/cleanup laser. """
        pass
