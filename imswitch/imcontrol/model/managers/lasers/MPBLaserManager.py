import numpy as np
from imswitch.imcommon.model import initLogger
from .LaserManager import LaserManager


class MPBLaserManager(LaserManager):
    def __init__(self, laserInfo, name, **kwargs):
        self.__logger = initLogger(self, instanceName=name)
        self._isMock = False

        try:
            self._rs232manager = kwargs['rs232sManager']._subManagers[
                laserInfo.managerProperties['rs232device']
            ]
            self.__logger.debug(f'Laser 775, SN: {self._rs232manager.query("GETSN")}')

            self.__mode = 1  # APC (constant power)
            self.__triggerMode = 0  # internal

            self.check_that_laser_is_in_APC_mode()

            # Response format: 'F >99 3050'
            raw = self._rs232manager.query("GETPOWERSETPTLIM 0")
            self.__min_max_powers = [int(v) for v in raw.split('>')[1].split()]
            assert len(self.__min_max_powers) == 2
            self.__logger.debug(
                f"Power limits: {self.__min_max_powers[0]}–{self.__min_max_powers[1]} mW"
            )

            self.setTriggerSource(self.__triggerMode)
            self.setMode(self.__mode)
            self.setEnabled(False)

        except Exception as e:
            self._isMock = True
            self.__min_max_powers = [0, 1000]  # fallback for UI
            self.__logger.warning(f'MPB laser not available, entering mock mode: {e}')

        super().__init__(laserInfo, name, isBinary=False, valueUnits='mW', valueDecimals=0)

    def setEnabled(self, enabled):
        if self._isMock:
            return
        self._rs232manager.query(f"SETLDENABLE {int(enabled)}")

    def setValue(self, power):
        if self._isMock:
            return
        if power <= 0:
            self.setEnabled(False)
            return
        power = int(np.clip(power, self.__min_max_powers[0], self.__min_max_powers[1]))
        self._rs232manager.query(f"SETPOWER 0 {power}")

    def getValue(self):
        if self._isMock:
            return 0
        # Channel 0 = forward power monitor (what the laser is actually emitting)
        return self._rs232manager.query("POWER 0")

    def setMode(self, mode):
        if self._isMock:
            return
        self._rs232manager.query(f"POWERENABLE {mode}")

    def setTriggerSource(self, source):
        pass  # TODO

    def setDigitalMod(self, digital, initialValue):
        pass

    def check_that_laser_is_in_APC_mode(self):
        ans = self._rs232manager.query("GETPOWERENABLE")
        if ans != 'D >1':
            self._rs232manager.query("SETLDENABLE 0")
            self._rs232manager.query("POWERENABLE 1")
            self._rs232manager.query("SETLDENABLE 1")
        self.__logger.debug(
            f"APC mode confirmed: {self._rs232manager.query('GETPOWERENABLE') == 'D >1'}"
        )