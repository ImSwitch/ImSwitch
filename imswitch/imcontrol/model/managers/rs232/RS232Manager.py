"""
Created on Thu Jan 13 10:23:00 2021

@author: jonatanalvelid
"""


class RS232Manager:
    """General RS232Manager."""
    def __init__(self, rs232Info, name, **kwargs):
        self._settings = rs232Info.managerProperties
        self._name = name
        self._port = rs232Info.managerProperties['port']
        self._rs232port = getRS232port(self._port, self._settings)

    def send(self, arg):
        return self._rs232port.query(arg)

    def finalize(self):
        self._rs232port.close()


def getRS232port(port, settings):
    try:
        from imswitch.imcontrol.model.interfaces.RS232Driver import RS232Driver, generateDriverClass
        DriverClass = generateDriverClass(settings)
        rs232port = DriverClass(port)
        rs232port.initialize()
        return rs232port
    except:
        print('Initializing mock RS232 port')
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
