from .LaserManager import LaserManager
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.controller import CommunicationChannel

class NidaqLaserManager(LaserManager):
    """ LaserManager for analog-value NI-DAQ-controlled lasers.

    Manager properties: None
    """

    def __init__(self, laserInfo, name, **lowLevelManagers):

        self._nidaqManager = lowLevelManagers['nidaqManager']
        self.__logger = initLogger(self, tryInheritParent=True)
        super().__init__(laserInfo, name, isBinary=laserInfo.getAnalogChannel() is None,
                         valueUnits='V', valueDecimals=2)

    def setEnabled(self, enabled):
        try:
            self._nidaqManager.setDigital(self.name, enabled)
        except:
            self.__logger.error("Error trying to enable laser.")

    def setValue(self, voltage, enabled=True, for_scanning=False):
        if self.isBinary:
            return
        if for_scanning and not enabled:
            voltage = 0
        try:
            self._nidaqManager.setAnalog(
                target=self.name, voltage=voltage,
                min_val=self.valueRangeMin, max_val=self.valueRangeMax
            )
        except:
            self.__logger.error("Error trying to set value to laser.")

    def setScanModeActive(self, active, enabled=True):
        if active:
            self.setEnabled(False)
        # if laser was enable before the scan, it is enabled again. Value set to 0 first so that it does not get enabled
        # before laser preset is applied
        elif enabled:
            self.setValue(0, True)
            self.setEnabled(True)




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
