"""
Created on Thu Jan 13 10:23:00 2021

@author: jonatanalvelid
"""
from imswitch.imcommon.model import initLogger
import imswitch.imcontrol.model.interfaces.grbldriver as grbldriver


class GRBLManager:
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
        try:
            self.is_home = rs232Info.managerProperties['is_home']
        except:
            self.is_home = False 
             
        
        self._board = grbldriver.GrblDriver(self._port)

        # init the stage
        self._board.write_global_config()
        self._board.write_all_settings()
        #self.board.verify_settings()
        self._board.reset_stage()
        if self.is_home:
            self._board.home()

    def send(self, arg: str) -> str:
        """ Sends the specified command to the RS232 device and returns a
        string encoded from the received bytes. """
        return self._board._write(arg)

    def finalize(self):
        self.self._board.close()


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
