# -*- coding: utf-8 -*-
"""
Created on Wed Jan 13 10:35:00 2021

@author: jonatanalvelid
"""

import numpy as np
from .LaserManager import LaserManager


class AAAOTFLaserManager(LaserManager):
    def __init__(self, laserInfo, name, **kwargs):
        print(type(laserInfo))
        self._channel = int(laserInfo.managerProperties['channel'])
        self._rs232manager = kwargs['rs232sManager']._subManagers[laserInfo.managerProperties['rs232device']]

        self.blankingOn()
        self.internalControl()

        super().__init__(
            name, isBinary=False, isDigital=True, wavelength=laserInfo.wavelength,
            valueRangeMin=laserInfo.valueRangeMin, valueRangeMax=laserInfo.valueRangeMax,
            valueUnits='arb', valueRangeStep=laserInfo.valueRangeStep
        )

    def setEnabled(self, enabled):
        """Turn on (1) or off (0) laser emission"""
        if enabled==True:
            value = 1
        else:
            value = 0
        cmd = 'L' + str(self._channel) + 'O' + str(value)
        self._rs232manager.send(cmd)

    def setValue(self, power):
        """Handles output power.
        Sends a RS232 command to the laser specifying the new intensity.
        """        
        valueaotf = round(power)  # assuming input value is [0,1023]
        cmd = 'L' + str(self._channel) + 'P' + str(valueaotf)
        self._rs232manager.send(cmd)

    def setDigitalMod(self, digital, initialValue):
        pass

    def blankingOn(self):
        """Switch on the blanking of all the channels"""
        cmd = 'L0' + 'I1' + 'O1'
        self._rs232manager.send(cmd)

    def internalControl(self):
        """Switch the channel to external control"""
        cmd = 'L' + str(self._channel) + 'I1'
        self._rs232manager.send(cmd)
