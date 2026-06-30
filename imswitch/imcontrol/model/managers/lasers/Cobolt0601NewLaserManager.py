from imswitch.imcommon.model import initLogger
from .PyCoboltManager import list_lasers
from .PyCoboltManager import Cobolt06
from .PyCoboltMock import MockCobolt06
from .LaserManager import LaserManager
import traceback


class Cobolt0601NewLaserManager(LaserManager):
    """ LaserManager for Cobolt 06-01 lasers. Uses digital modulation mode when
    scanning. Does currently not support DPL type lasers.

    Manager properties:

    - ``digitalPorts`` -- a string array containing the COM ports to connect
      to, e.g. ``["COM4"]``
    """

    def __init__(self, laserInfo, name, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        # TODO: Find good fix for this missing attribute _laserInfo

        self._port = laserInfo.managerProperties['digitalPorts'][0]
        # self._ttlLine = laserInfo.managerProperties['digitalLine']
        self.__logger.debug(f'Initializing Cobolt0601 laser (name: {name}) on port {self._port}')
        self._is_DPL = False
        self._digitalMod = True
        self._isMock = False
        self._checkKeyOnFirstEnable = False
        self.powerQ = 0
        if 'DPL' in name:
            self._is_DPL = True
        try:
            # self._laser = CoboltLaser(port=self._port)
            self._laser = Cobolt06(port=self._port)

            # start up by turning on modulation power -> laser is off
            self._laser.constant_current(0)
            # check mode of laser
            mode = self._laser.get_mode()
            # mode = 1

        except Exception as exc:
            self.__logger.warning(
                f'Failed to initialize Cobolt0601 laser (name: {name}) on port {self._port},'
                f' loading mock: {exc}'
            )
            # self.__logger.debug(f'Cobolt0601 initialization traceback: {traceback.format_exc()}')
            self._isMock = True
            self._laser = MockCobolt06(port=self._port)
            self._laser.constant_current(0)
            mode = self._laser.get_mode()

        self._digitalMod = False

        # self.__logger.debug(f'Laser mode is: {mode}, might have to turn the key.')
        super().__init__(laserInfo, name, isBinary=False, valueUnits='mW', valueDecimals=0)
        self._checkKeyOnFirstEnable = not self._isMock

        if not self._laser.is_on():
            try:
                self._laser.turn_on() # turn on laser
                self.setEnabled(False) # pause emission
                self.__logger.debug(f'Laser {name} turned on, mode {mode} - emission paused.')
            except Exception:
                err = traceback.format_exc()
                self.__logger.warning(f'Laser {name} could not be turned on: {err}')
    
    def finalize(self):
        """ Turn off laser """
        try:
            if self._laser.is_on():
                self._laser.turn_off() # turn on laser
        except Exception:
            err = traceback.format_exc()
            self.__logger.warning(f'Laser could not be turned off properly: {err}.')

    def setEnabled(self, enabled):  # toggle laser on or off
        if enabled:  # laser is toggled on
            self._laser.resume_emission()
            self._laser.constant_power()  # set laser to constant power mode
        else:

            self._laser.pause_emission()
            #self._laser.constant_current(0)  # If laser should be disabled, turn off by setting scanmode to active -> modulation mode

    def setValue(self, power, enabled=True, for_scanning=False):
        power = int(power)
        self.powerQ = power
        if self._digitalMod:
            if power ==0:
                self._laser.current_modulation_mode()
                self._laser.set_modulation_current(0.1)
                self.__logger.debug(f'Modulation current in setValue is: {self._laser.get_modulation_current()}')

            else :
                self._laser.power_modulation_mode()
                self._laser.set_modulation_power(power)
                self.__logger.debug(f'Modulation power in setValue is: {self._laser.get_modulation_power()}')
        else:
            self._laser.set_power(power)
            self.__logger.debug(f'Set power to: {power}')

    def setScanModeActive(self, active,enabled=True):
        if active == False:  # Come back to values set before scan
            self._digitalMod = False
            self._laser.constant_power()  # If laser should be disabled, turn off by setting scanmode to active -> modulation mode
            self.__logger.debug('Exited digital modulation mode')
        else:
            if self.powerQ == 0: #To be sure the laser doesn't emit
                self._laser.current_modulation_mode()
                self._laser.set_modulation_current(0.1)
            else:
                self._laser.power_modulation_mode()
                self.__logger.debug(f'Modulation power is: {self._laser.get_modulation_power()}')
                self._laser.set_modulation_power(self.powerQ)
                self.__logger.debug(f'Modulation power is: {self._laser.get_modulation_power()}')


            # self.setModulationPower(powerQ)
            # powerQ = self._laser.power_sp * self._numLasers

            self.__logger.debug('Entered digital modulation mode')
            self.__logger.debug(f'Modulation mode is: {self._laser.get_modulation_state()}')
        self._digitalMod = active
        # TODO
        # this is needed when imswitch is handling the scan
        # for now, arduino is handling the scanning
        # once the camera is not exposing the laser will not be on whilst digital modulation is set
        pass

    def setModulationEnabled(self, enabled):
        if enabled:
            self._laser.power_modulation_mode(digital_enabled=True)
        else:
            self._laser.power_modulation_mode(digital_enabled=False)

    def setModulationPower(self, power):
        power = int(power)
        self._laser.set_modulation_power(power)
        self.__logger.debug(f'Set modulation power to: {power}')

    def getModulationPower(self):
        return self._laser.get_modulation_power()

    def getAllDeviceNames(self):  # wonder where thats needed
        if self._isMock:
            devices = [self._port]
        else:
            devices = list_lasers()
        self.__logger.debug(f'Available devices: {devices}')
        return devices

    def consumeOnEnableWarning(self):
        if not self._checkKeyOnFirstEnable:
            return None

        self._checkKeyOnFirstEnable = False
        state = self._getLaserState()
        if self._isWaitingForKey(state):
            return (
                f'Laser "{self.name}" is waiting for the key. Turn the laser key on before'
                f' enabling emission.'
            )

        if state is None:
            return (
                f'ImSwitch could not verify the current key state for laser "{self.name}".'
                f' Make sure the laser key is turned on before enabling emission.'
            )

        return None

    def _getLaserState(self):
        try:
            return self._laser.get_state()
        except Exception:
            self.__logger.debug(f'Could not read Cobolt0601 laser state: {traceback.format_exc()}')
            return None

    def _isWaitingForKey(self, state):
        state = str(state).strip().lower()
        return state in ('1', 'autostartwaitingforkeyon') or 'waitingforkey' in state

# Copyright (C) 2020-2021 ImSwitch developers
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
