from lantz import Q_

from imcontrol.model.interfaces import FullDigitalLaser
from .LaserManager import LaserManager


class FullDigitalLaserManager(LaserManager):
    def __init__(self, laserInfo, name, **_kwargs):
        self._digitalMod = False

        # Init laser
        self._laser = FullDigitalLaser(laserInfo.managerProperties['digitalDriver'],
                                       laserInfo.managerProperties['digitalPorts'])
        print(self._laser.idn)
        self._laser.digital_mod = False
        self._laser.enabled = False
        # self._laser.digital_mod = True  # TODO: What's the point of this?
        self._laser.autostart = False
        # self._laser.autostart = False  # TODO: What's the point of this?

        super().__init__(
            name, isBinary=False, isDigital=True, wavelength=laserInfo.wavelength,
            valueRangeMin=laserInfo.valueRangeMin, valueRangeMax=laserInfo.valueRangeMax,
            valueUnits='mW'
        )

    def setEnabled(self, enabled):
        self._laser.enabled = enabled

    def setValue(self, power):
        power = int(power)
        if self._digitalMod:
            self._laser.power_mod = power * Q_(1, 'mW')
        else:
            self._laser.power_sp = power * Q_(1, 'mW')

    def setDigitalMod(self, digital, initialPower):
        if digital:
            self._laser.enter_mod_mode()
            self._laser.power_mod = initialPower * Q_(1, 'mW')
            print('Entered digital modulation mode with power :', initialPower)
            print('Modulation mode is: ', self._laser.mod_mode)
        else:
            self._laser.digital_mod = False
            self._laser.query('cp')
            print('Exited digital modulation mode')
        self._digitalMod = digital
		
    def finalize(self):
        self._laser.finalize()
 
# Copyright (C) 2020, 2021 Staffan Al-Kadhimi, Xavier Casas, Andreas Boden
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
