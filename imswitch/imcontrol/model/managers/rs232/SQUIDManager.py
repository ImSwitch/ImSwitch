from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model.interfaces.squid import SQUID

class SQUIDManager:

    def __init__(self, rs232Info, name, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)
        self._settings = rs232Info.managerProperties
        self._name = name

        try:
            self._serialport = rs232Info.managerProperties['serialport']
        except:
            self._serialport = None

        # initialize the SQUID board 
        try:
            self._squid = SQUID(port=self._serialport)
        except Exception as e:
            self.__logger.debug("No Arduino found, switching back to Simulation")
            from imswitch.imcontrol.model.interfaces.squid import Microcontroller_Simulation
            self._squid = Microcontroller_Simulation()
        
    def send(self, arg: str) -> str:
        """ Sends the specified command to the RS232 device and returns a
        string encoded from the received bytes. """
        self._squid.post_json(arg)
        
    def finalize(self):
        self._squid.close() 


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
