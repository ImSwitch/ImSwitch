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
