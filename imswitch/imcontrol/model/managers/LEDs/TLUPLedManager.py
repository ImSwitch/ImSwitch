from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model.managers.LEDs.LEDManager import LEDManager
from imswitch.imcontrol.model.interfaces.tlupled import getLED


class TLUPLedManager(LEDManager):
    """ LaserManager for controlling a Thorlabs UpLed LED

    Manager properties:
    """

    def __init__(self, ledInfo, name, **lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)
        self._led = getLED()
        self.__device_index = ledInfo.managerProperties['device_index']
        self.enabled = False
        super().__init__(ledInfo, name, isBinary=False, valueUnits='A', valueDecimals=3)
        self.__logger.info(f'Initialized LED, model: {self._led.name}')


    def setEnabled(self, enabled):
        """Turn on (N) or off (F) LED emission"""
        if enabled:
            self._led.switch_on()
        else:
            self._led.switch_off()
        self.enabled = enabled

    def setModulationEnabled(self, enabled: bool) -> None:
        """ Sets wether the LED frequency modulation is enabled. """
        if enabled:
            self._led.switch_on()
        else:
            self._led.switch_off()

    def setValue(self, value):
        """Handles output current.
        """
        self._led.current_setpoint = value

    def getValue(self):
        return self._led.current_setpoint



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
