from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model.interfaces import LantzLaser
from .LaserManager import LaserManager


class LantzLaserManager(LaserManager):
    """ Base LaserManager for lasers that are fully digitally controlled using
    drivers available through Lantz.

    Manager properties:

    - ``digitalPorts`` -- a string array containing the COM ports to connect
      to, e.g. ``["COM4"]``
    """

    def __init__(self, laserInfo, name, isBinary, valueUnits, valueDecimals, driver,
                 **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        ports = laserInfo.managerProperties['digitalPorts']

        # Init laser
        self._laser = LantzLaser(driver, ports)
        self._numLasers = len(ports)
        self.__logger.info(f'Initialized laser, model: {self._laser.idn}')

        super().__init__(laserInfo, name, isBinary=isBinary, valueUnits=valueUnits,
                         valueDecimals=valueDecimals)

    def finalize(self):
        self._laser.finalize()


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
