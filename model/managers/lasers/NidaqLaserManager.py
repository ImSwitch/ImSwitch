# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 16:41:57 2020

@author: _Xavi
"""
from .LaserManager import LaserManager


class NidaqLaserManager(LaserManager):
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
