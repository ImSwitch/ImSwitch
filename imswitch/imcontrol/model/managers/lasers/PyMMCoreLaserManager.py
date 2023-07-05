from typing import Union
from imswitch.imcontrol.model.managers.PyMMCoreManager import PyMMCoreManager
from imswitch.imcommon.model import initLogger
from .LaserManager import LaserManager

class PyMMCoreLaserManager(LaserManager):
    """ Generic LaserManager for laser handlers supported by the Micro-Manager core.

    Manager properties:

    - ``binary`` -- boolean; `True` if the device has only ON/OFF status, `False` if it has a power level
    - ``powerPropertyName`` -- name of the device property dedicated to control power level (discarded if ``binary`` is `True`)
    """
    def __init__(self, laserInfo, name, **lowLevelManagers) -> None:

        self.__logger = initLogger(self, instanceName=name)
        self.__coreManager: PyMMCoreManager = lowLevelManagers["pymmcManager"]

        module = laserInfo.managerProperties["module"]
        device = laserInfo.managerProperties["device"]
        self.__coreManager.loadDevice((name, module, device))

        self.__powerPropertyLabel = None
        isBinary = laserInfo.managerProperties["binary"]
        if not isBinary:
            self.__powerPropertyLabel = laserInfo.managerProperties["powerPropertyName"]

        super().__init__(laserInfo, name, isBinary=isBinary, valueUnits='mW', valueDecimals=1)
    
    def setEnabled(self, enabled: bool) -> None:
        self.__coreManager.setShutterStatus(self.name, enabled)
    
    def setValue(self, value: Union[int, float]) -> None:
        self.__coreManager.setProperty(self.name, self.__powerPropertyLabel, value)