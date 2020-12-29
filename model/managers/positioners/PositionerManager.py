from abc import abstractmethod


class PositionerManager:
    @abstractmethod
    def __init__(self, name, initialPosition):
        super().__init__()
        self._name = name
        self._position = initialPosition

    @property
    def name(self):
        return self._name

    @property
    def position(self):
        return self._position

    @abstractmethod
    def move(self, dist):
        """Moves the positioner by the specified distance and returns the new position. Derived
        classes will update the position field manually."""
        pass

    @abstractmethod
    def setPosition(self, position):
        """Adjusts the positioner to the specified position and returns the new position. Derived
        classes will update the position field manually."""
        pass
