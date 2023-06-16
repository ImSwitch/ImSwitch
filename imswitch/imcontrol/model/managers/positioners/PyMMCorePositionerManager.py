from .PositionerManager import PositionerManager
from ..PyMMCoreManager import PyMMCoreManager # only for type hinting
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model.SetupInfo import SetupInfo
from imswitch.imcontrol.model.configfiletools import (
    loadOptions, 
    loadSetupInfo,
    saveSetupInfo
)

class PyMMCorePositionerManager(PositionerManager):
    """ PositionerManager for control of a stage controlled by the Micro-Manager core, using pymmcore.

    Manager properties:
    - ``module`` -- name of the MM module referenced
    - ``device`` -- name of the MM device described in the module 
    - ``stageType`` -- either "single" or "double" (for single-axis stage or double-axis stage)
    - ``speedProperty`` (optional) -- name of the property indicating the stage speed
    """

    def __init__(self, positionerInfo, name: str, **lowLevelManagers):

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
        try:
            self.__speedProp = positionerInfo.managerProperties["speedProperty"]
        except:
            self.__speedProp = None

        self.__logger.info(f"Loading {name}.{module}.{device} ...")

        devInfo = (name, module, device)
        self.__coreManager.loadDevice(devInfo)

        # can be read only after device is loaded and initialized
        # some device may not have a speed property...
        if self.__speedProp is not None:
            self.speed =  float(self.__coreManager.getProperty(name, self.__speedProp))
        else:
            # assuming device has no speed
            self.speed = 0.0
        self.__logger.info(f"... done!")
        
        initialPosition = {
            axis : self.__coreManager.getStagePosition(name, axis) for axis in positionerInfo.axes
        }
        
        # we need to make sure that the origin position is set again at startup
        # so that it's correctly shown on the positioner's GUI widget;
        # usually (but not tested) Micro-Manager's device adapters for positioners do not store the last origin
        # after reboot when these are considered focus devices (i.e. MCL NanoDrive)
        if any(value != 0 for value in initialPosition.values()):
            initialPosition = self.__coreManager.setStageOrigin(name, self.__stageType, positionerInfo.axes)                 
        super().__init__(positionerInfo, name, initialPosition)
    
    def setPosition(self, position: float, axis: str) -> None:
        try:
            oldPosition = self.position[axis]
            self._position[axis] = position
            self._position = self.__coreManager.setStagePosition(
                label=self.name,
                stageType=self.__stageType,
                axis=axis,
                positions=self.position,
                isAbsolute=True
            )
        except RuntimeError as e:
            self.__logger.error(f"Invalid position requested ({self.name} -> ({axis} : {position}): MMCore response: {e}")
            self._position[axis] = oldPosition
    
    def setSpeed(self, speed: float) -> None:
        # check if speed property exists
        if self.__speedProp is not None:
            self.__coreManager.setProperty(self.name, self.__speedProp, speed)
    
    def move(self, dist: float, axis: str) -> None:
        movement = { ax : 0 for ax in self.axes }
        movement[axis] = dist
        try:
            self._position = self.__coreManager.setStagePosition(
                label=self.name,
                stageType=self.__stageType,
                axis=axis,
                positions=movement,
                isAbsolute=False
            )
        except RuntimeError as e:
            self.__logger.error(f"Invalid movement requested ({self.name} -> ({axis} : {dist}): MMCore response: {e}")
    
    def setOrigin(self, axis: str):
        self._position = self.__coreManager.setStageOrigin(self.name, self.__stageType, self.axes)
    
    def finalize(self) -> None:
        self.__logger.info(f"Closing {self.name}.")
        self.__coreManager.unloadDevice(self.name)