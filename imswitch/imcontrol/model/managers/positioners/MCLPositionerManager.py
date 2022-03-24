from MadCityLabs import MicroDriveHandler
from imswitch.imcommon.model import initLogger
from .PositionerManager import PositionerManager
from typing import Dict

class MCLPositionerManager(PositionerManager):
    """ PositionerManager for Mad City Labs drivers.

    Manager properties:
    - ``type`` -- string value: "MicroDrive" or "NanoDrive" supported
    - ``dllPath`` -- string containing the absolute path to the DLL
    """

    def __init__(self, positionerInfo, name: str, initialPosition: Dict[str, float]):
        self.__logger = initLogger(self, instanceName=name)
        self.__driver = None
        posType = positionerInfo.managerProperties["type"]

        if len(self.axes) != 3:
            raise RuntimeError("")

        if posType == "MicroDrive":
            self.__driver = MicroDriveHandler(positionerInfo.managerProperties["dllPath"], positionerInfo.axes)
        elif posType == "NanoDrive":
            # todo: support NanoDrive
            pass
        else:
            raise RuntimeError(f"Unsupported positioner type {posType}")
        super().__init__(positionerInfo, name, initialPosition)

    def move(self, dist: float, axis: str):
        self.__driver.setPosition(self.position[axis] + dist, axis)
        self.position[axis] += dist
    
    def setPosition(self, position: float, axis: str):
        # todo: this is incorrect, fix
        self.__driver.setPosition(position, axis)
        self.position[axis] = position