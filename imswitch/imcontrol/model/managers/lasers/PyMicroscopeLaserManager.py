from .LaserManager import LaserManager
from imswitch.imcommon.model import initLogger

class PyMicroscopeLaserManager(LaserManager):
    """ Generic LaserManager for laser handlers supported by Python Microscope.

    Manager properties:

    - ``pyMicroscopeDriver`` -- string describing the Python Microscope
        object to initialize; requires to specify the module
        and the class name, e.g. ``toptica.TopticaiBeam``
    - ``digitalPorts`` -- string describing the COM port
        to connect to, e.g. ``["COM4"]``
    """
    def __init__(self, laserInfo, name, **_lowLevelManager) -> None:
        self.__logger = initLogger(self, instanceName=name)
        self.__port = laserInfo.managerProperties["digitalPorts"]
        self.__driver = str(laserInfo.managerProperties["pyMicroscopeDriver"])

        # we need to import the proper class from python microscope
        # split the pyMicroscopeDriver
        driver = self.__driver.split(".")
        laserClass = __import__("microscope.lights." + driver[0], fromlist=driver[1])

        # we have imported the class, now we build the object
        self.__laser = getattr(laserClass, driver[1])(self.__port)
        self.__logger.info(f"[{self.__port}] {self.__driver} initialized. ")
        super().__init__(laserInfo, name, isBinary=False, valueUnits='mW', valueDecimals=1)
        self.__maxPower = float(laserInfo.valueRangeMax)
    
    def setEnabled(self, enabled: bool) -> None:
        (self.__laser.enable() if enabled else self.__laser.disable())
    
    def setValue(self, value) -> None:
        # laser power is handled as percentage
        # so we divide for the max power to obtain
        # the actual percentage to which we set
        # the output power
        self.__laser.power = float(value) / self.__maxPower
    
    def finalize(self) -> None:
        self.__logger.info(f"[{self.__port}] {self.__driver} closed.")
        self.__laser.shutdown()