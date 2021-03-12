from .LaserManager import LaserManager


class NidaqAOLaserManager(LaserManager):
    def __init__(self, laserInfo, name, **kwargs):
        self._nidaqManager = kwargs['nidaqManager']

        super().__init__(
            name, isBinary=laserInfo.analogChannel is None, isDigital=False,
            wavelength=laserInfo.wavelength,
            valueRangeMin=laserInfo.valueRangeMin, valueRangeMax=laserInfo.valueRangeMax,
            valueUnits='V'
        )

    def setEnabled(self, enabled):
        self._nidaqManager.setDigital(self.name, enabled)

    def setValue(self, voltage):
        if self.isBinary:
            return

        self._nidaqManager.setAnalog(
            target=self.name, voltage=voltage,
            min_val=self.valueRangeMin, max_val=self.valueRangeMax
        )

    def setDigitalMod(self, digital, initialValue):
        pass

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