"""
Created on Thu Jan 13 10:23:00 2021

@author: jonatanalvelid
"""
from imswitch.imcommon.model import initLogger


class RS232Manager:
    """ A general-purpose RS232 manager that together with a general-purpose
    RS232Driver interface can handle an arbitrary RS232 communication channel,
    with all the standard serial communication protocol parameters as defined
    in the hardware control configuration.

    Manager properties:

    - ``port``
    - ``encoding``
    - ``recv_termination``
    - ``send_termination``
    - ``baudrate``
    - ``bytesize``
    - ``parity``
    - ``stopbits``
    - ``rtscts``
    - ``dsrdtr``
    - ``xonxoff``
    """

    def __init__(self, rs232Info, name, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        self._settings = rs232Info.managerProperties
        self._name = name
        self._port = rs232Info.managerProperties['port']
        self._rs232port = self._getRS232port(self._port, self._settings)

    def send(self, arg: str) -> str:
        """ Sends the specified command to the RS232 device and returns a
        string encoded from the received bytes. """
        return self._rs232port.query(arg)

    def finalize(self):
        self._rs232port.close()

    def _getRS232port(self, port, settings):
        try:
            from imswitch.imcontrol.model.interfaces.RS232Driver import generateDriverClass
            DriverClass = generateDriverClass(settings)
            rs232port = DriverClass(port)
            rs232port.initialize()
            return rs232port
        except Exception:
            self.__logger.warning('Initializing mock RS232 port')
            from imswitch.imcontrol.model.interfaces.RS232Driver_mock import MockRS232Driver
            return MockRS232Driver(port, settings)


# Copyright (C) 2020, 2021 TestaLab
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
