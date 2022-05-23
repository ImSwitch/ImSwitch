from turtle import position
from .PositionerManager import PositionerManager
from ..PyMMCoreManager import PyMMCoreManager # only for type hinting
from imswitch.imcommon.model import initLogger
from typing import Dict

class PyMMCorePositionerManager(PositionerManager):
    """ PositionerManager for control of a stage controlled by MMCore, using pymmcore.

    Manager properties:

    - ``module`` -- name of the MM module referenced
    - ``device`` -- name of the MM device described in the module 
    - ``stageType`` -- either "single" or "double" (for single-axis stage or double-axis stage)
    - ``speed`` -- positioner maximum speed
    """

    def __init__(self, positionerInfo, name: str, **lowLevelManagers):

        self.__name = name
        self.__logger = initLogger(self)
        self.__stageType = positionerInfo.managerProperties["stageType"]
        # only combination of double axis stages allowed is X-Y
        if self.__stageType == "double":
            if len(positionerInfo.axes) != 2:
                raise ValueError(f"Declared axis number not correct. Must be 2 ([\"X\", \"Y\"]), instead is {len(positionerInfo.axes)}")
            elif positionerInfo.axes != ["X", "Y"]:
                raise ValueError(f"Declared axis names incorrect. Must be [\"X\", \"Y\"], instead is {positionerInfo.axes}")

        # type assignment useful for type hinting
        self.__coreManager: PyMMCoreManager = lowLevelManagers["pymmcManager"]

        module = positionerInfo.managerProperties["module"]
        device = positionerInfo.managerProperties["device"]
        self.speed = positionerInfo.managerProperties["speed"] 

        self.__logger.info(f"Trying to load positioner: {name}.{module}.{device} ...")

        devInfo = (name, module, device)
        self.__coreManager.loadPositioner(devInfo)
        self.__logger.info(f"... done!")

        initialPosition = {
            axis: self.__coreManager.getStagePosition(name, self.__stageType, axis) 
            for axis in positionerInfo.axes
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
        self.setPosition(self._position[axis] + dist, axis)
    
    def finalize(self) -> None:
        self.__logger.info(f"Closing {self.__name}")
        self.__coreManager.unloadPositioner(self.__name)