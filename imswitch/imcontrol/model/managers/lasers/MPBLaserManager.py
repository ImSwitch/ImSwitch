import numpy as np
from imswitch.imcommon.model import initLogger
from .LaserManager import LaserManager


class MPBLaserManager(LaserManager):
    def __init__(self, laserInfo, name, **kwargs):
        self.__logger = initLogger(self, instanceName=name)
        self._rs232manager = kwargs['rs232sManager']._subManagers[laserInfo.managerProperties['rs232device']]
        self.__logger.debug(f'Laser 775')
        cmd5 = "GETSN"
        self.__logger.debug(f'Commande envoyee{self._rs232manager.query(cmd5)}')
        
        self.__power_setting = 1  # To change power with python (1) or knob (0)
        self.__mode = 0  # Constant current (1) or constant power (0) mode
        self.__triggerMode = 0  # Trigger: internal (0)

        self.setPowerSetting(self.__power_setting)
        # self.setTriggerSource(self.__triggerMode)
        self.setMode(self.__mode)        

        super().__init__(laserInfo, name, isBinary=False, valueUnits='mW', valueDecimals=0)

    def setEnabled(self, enabled):
        """Turn on (1) or off (0) laser emission"""
        if enabled==True:
            value = 1
        else:
            value = 0
        cmd = "SETLDENABLE " + str(int(value))
        self._rs232manager.query(cmd)

    def setValue(self, power):
        """Handles output power.
        Sends a RS232 command to the laser specifying the new intensity.
        """        
        if(self.__power_setting != 1):
            print("Knob mode: impossible to change power.")
            return
        power = round(np.max([0,power])/1000, 3)  # Conversion from mW to W and round
        cmd = "SETPOWER " + str(power)
        self._rs232manager.query(cmd)

    def setDigitalMod(self, digital, initialValue):
        pass

    def setPowerSetting(self, power_setting):
        # """Power can be changed via this interface (1), or manual knob (0)"""
        # cmd = "lps=" + str(power_setting)
        # self._rs232manager.query(cmd)
        pass

    # def setTriggerSource(self, source):
    #     """Internal frequency generator (0)
    #     External trigger source for adjustable trigger level (1), Tr-1 In
    #     External trigger source for TTL trigger (2), Tr-2 In
    #     """
    #     cmd = "lts=" + str(source)
    #     self._rs232manager.query(cmd)

    def setMode(self, mode):
        """Constant current mode (0) or constant power mode (1)"""
        cmd = "POWERENABLE " + str(mode)

        self._rs232manager.query(cmd)
