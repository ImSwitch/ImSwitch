from .PositionerManager import PositionerManager
from ..PyMMCoreManager import PyMMCoreManager # only for type hinting
from typing import Dict

class PyMMCorePositionerManager(PositionerManager):
    """ PositionerManager for control of a stage controlled by MMCore, using pymmcore.

    Manager properties:

    - ``module`` -- name of the MM module referenced
    - ``device`` -- name of the MM device described in the module 
    - ``stageType`` -- either "single" or "double" (for single-axis stage or double-axis stage)
    """

    def __init__(self, positionerInfo, name: str, **lowLevelManagers):

        self.__stageType = positionerInfo.managerProperties["stageType"]
        # only combination of double axis stages allowed is X-Y
        if self.__stageType == "double":
            if len(positionerInfo.axis):
                raise ValueError("Declared axis number not correct. Must be 2 ([\"X\", \"Y\"])")
            elif positionerInfo.axis[0] != "X" or positionerInfo.axis[1] != "Y":
                raise ValueError("Declared axis names incorrect. Must be [\"X\", \"Y\"]")

        # type assignment useful for type hinting
        self.__coreManager: PyMMCoreManager = lowLevelManagers["pymmcManager"]

        devInfo = tuple(
            name, 
            positionerInfo.managerProperties["module"], 
            positionerInfo.managerProperties["device"]
        )

        self.__coreManager.loadPositioner(devInfo)

        initialPosition = {
            axis: self.__coreManager.getStagePosition(name, self.__stageType, axis) 
            for axis in positionerInfo.axis
        }
        super().__init__(positionerInfo, name, initialPosition)
    
    def setPosition(self, position: float, axis: str) -> None:
        self._position[axis] = position
        self._position = self.__coreManager.setStagePosition(
            self.name,
            self.__stageType,
            axis,
            self.position
        )
    
    def move(self, dist: float, axis: str) -> None:
        self.setPosition(self.setPosition(self._position[axis] + dist, axis))