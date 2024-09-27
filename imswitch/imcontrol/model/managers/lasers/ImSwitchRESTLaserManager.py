from imswitch.imcommon.model import initLogger
from .LaserManager import LaserManager
import numpy as np

class ImSwitchRESTLaserManager(LaserManager):
    """ LaserManager for controlling lasers via a REST API.
    Each LaserManager instance controls one laser.

    Manager properties:

    - ``rest_device`` -- name of the REST API communication channel through which the communication should take place.
    """

    def __init__(self, laserInfo, name, **lowLevelManagers):
        super().__init__(laserInfo, name, isBinary=False, valueUnits='mW', valueDecimals=0)
        self._rs232manager = lowLevelManagers['rs232sManager'][laserInfo.managerProperties['rs232device']]
        self._imswitch_client = self._rs232manager._imswitch_client
        self.laser_names = self._imswitch_client.lasersManager.getLaserNames()
        self.channel_index = laserInfo.managerProperties['channel_index']
        self._laser_manager = self._imswitch_client.lasersManager
        self.power = 0
        self.wavelength = laserInfo.wavelength
        self.laser_name = laserInfo.managerProperties['laser_name']
        self.enabled = False
        self.setEnabled(self.enabled)
        self.__logger = initLogger(self, instanceName=name)

    def setEnabled(self, enabled, getReturn=False):
        """Turn on or off laser emission."""
        self.enabled = enabled
        self._laser_manager.setLaserActive(self.laser_names[self.channel_index], active=self.enabled)

    def setValue(self, power, getReturn=False):
        """Sets the output power of the laser."""
        self.power = power
        if self.enabled:
            self._laser_manager.setLaserValue(self.laser_names[self.channel_index], value=self.power)

