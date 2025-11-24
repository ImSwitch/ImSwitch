import time

import numpy as np
from imswitch.imcommon.model import initLogger
from .LaserManager import LaserManager


class MPBLaserManager(LaserManager):
    def __init__(self, laserInfo, name, **kwargs):
        self.__logger = initLogger(self, instanceName=name)
        self._rs232manager = kwargs['rs232sManager']._subManagers[laserInfo.managerProperties['rs232device']]
        self.__logger.debug(f'Laser 775, SN: {self._rs232manager.query("GETSN")}')

        self.__power_setting = 1  # To change power with python (1) or knob (0) -> not functional currently
        self.__mode = 1  # Constant current (0) or constant power (1) mode
        self.__triggerMode = 0  # Trigger: internal (0) --> not functional currently

        self.check_that_laser_is_in_APC_mode()

        # find out min max powers, the command gives them back in such a format: 'F >99 3050'
        self.__min_max_powers = [int(val) for val in self._rs232manager.query("GETPOWERSETPTLIM 0").split('>')[1].split(' ')]
        assert(len(self.__min_max_powers) == 2)
        self.__logger.debug(f"Min Power setting: {self.__min_max_powers[0]} mW,"
                            f" Max Power setting: {self.__min_max_powers[1]} mW")

        self.setPowerSetting(self.__power_setting)
        self.setTriggerSource(self.__triggerMode)
        self.setMode(self.__mode)
        self.__enabled = True
        self.setEnabled(self.__enabled)

        super().__init__(laserInfo, name, isBinary=False, valueUnits='mW', valueDecimals=0)

    def setEnabled(self, enabled):
        """Turn on (1) or off (0) laser emission"""
        if enabled:
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
        power = np.max([self.__min_max_powers[0],power])
        power = np.min([self.__min_max_powers[1],power])

        cmd = "SETPOWER 0 " + str(power)
        self._rs232manager.query(cmd)
        #self.__logger.debug(f"Laser Power set to: {power}")
        #time.sleep(1) # --> laser needs a moment
        #self.__logger.debug(f"Laser Power is: {self.getValue()}")

    def getValue(self):
        return [self._rs232manager.query("POWER 0"), self._rs232manager.query("POWER 1"), self._rs232manager.query("POWER 2"), self._rs232manager.query("POWER 3")]

    def setDigitalMod(self, digital, initialValue):
        pass

    def setPowerSetting(self, power_setting):
        # """Power can be changed via this interface (1), or manual knob (0)"""
        # self.__power_setting = power_setting
        pass # --> Laser output control is handled in AOM controller for some reason, so doesnt make sense to have it here again

    def setTriggerSource(self, source):
         """Internal frequency generator (0)
         External trigger source for adjustable trigger level (1), Tr-1 In
         External trigger source for TTL trigger (2), Tr-2 In
         """
         pass  #TODO

    def setMode(self, mode):
        """Constant current mode (0) or constant power mode (1)"""
        cmd = "POWERENABLE " + str(mode)

        self._rs232manager.query(cmd)

    def check_that_laser_is_in_APC_mode(self):
        # Laser can be in APC (power mW controlled) and ACC (diode current controlled) mode
        # Setpower commands will not work in ACC mode and for some reason will just be ignored
        # So we'll check if it's the right mode and otherwise switch, which required awkward steps for some
        # --> switching the laser off, changing mode and switching on again ...

        ans = self._rs232manager.query("GETPOWERENABLE")
        if ans != 'D >1':
            self._rs232manager.query("SETLDENABLE 0")
            self._rs232manager.query("POWERENABLE 1") # switch on APC mode
            self._rs232manager.query("SETLDENABLE 1")

        self.__logger.debug(f"Laser successfully started in APC mode? "
                            f"{(self._rs232manager.query('GETPOWERENABLE') == 'D >1')}")


