from abc import ABC, abstractmethod

from typing import Dict, List


class StateSelectorManager(ABC):
    """ Abstract base class for managers that change states for a device"""

    @abstractmethod
    def __init__(self, stateselectorInfo, name: str):
        self._stateselectorInfo = stateselectorInfo
        self.__name = name

        self.__selectors = stateselectorInfo.selectors

    @property
    def name(self) -> str:
        return self.__name


    @property
    def selectors(self) -> List[str]:
        return self.__selectors

    @property
    def managername(self) -> str:
        return self.__managername


    @abstractmethod
    def move(self, dist: float, axis: str):
        """ Moves the selector position"""
        pass

    def finalize(self) -> None:
        """ Close/cleanup stateselector. """
        pass