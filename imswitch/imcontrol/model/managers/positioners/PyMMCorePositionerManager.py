from pprint import pprint
from .PositionerManager import PositionerManager
from ..PyMMCoreManager import PyMMCoreManager # only for type hinting
from imswitch.imcommon.model import initLogger

class PyMMCorePositionerManager(PositionerManager):
    """ PositionerManager for control of a stage controlled by MMCore, using pymmcore.

    Manager properties:

    - ``module`` -- name of the MM module referenced
    - ``device`` -- name of the MM device described in the module 
    - ``stageType`` -- either "single" or "double" (for single-axis stage or double-axis stage)
    - ``speedProperty`` (optional) -- name of the property indicating the stage speed
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
            self.speed =  float(self.__coreManager.getProperty(self.__name, self.__speedProp))
        else:
            # assuming device has no speed
            self.speed = 0.0
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
    
    def setSpeed(self, speed: float) -> None:
        # check if speed property exists
        if self.__speedProp is not None:
            self.__coreManager.setProperty(self.__name, self.__speedProp, speed)
    
    def move(self, dist: float, axis: str) -> None:
        self.setPosition(self._position[axis] + dist, axis)
    
    def finalize(self) -> None:
        self.__logger.info(f"Closing {self.__name}")
        self.__coreManager.unloadDevice(self.__name)