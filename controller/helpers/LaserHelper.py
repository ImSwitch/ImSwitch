# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 16:41:57 2020

@author: _Xavi
"""
from lantz import Q_


class LaserHelper:
    def __init__(self, laserInfos, fullDigitalLasers, nidaqHelper):
        self.__fullDigitalLasers = fullDigitalLasers
        self.__laserInfos = laserInfos
        self.__nidaqHelper = nidaqHelper

    def setEnabled(self, laserName, enable):
        if self.__laserInfos[laserName].isFullDigital():
            self.__fullDigitalLasers[laserName].enabled = enable
        else:
            self.__nidaqHelper.setDigital(laserName, enable)

    def changeVoltage(self, laserName, voltage):
        laserInfo = self.__laserInfos[laserName]
        if not laserInfo.isAotf():
            raise ValueError('Passed laser was not aotf')

        self.__nidaqHelper.setAnalog(
            target=laserName, voltage=voltage,
            min_val=laserInfo.valueRangeMin, max_val=laserInfo.valueRangeMax
        )

    def changePower(self, laserName, power, dig):
        laserInfo = self.__laserInfos[laserName]
        if laserInfo.isAotf():
            raise ValueError('Passed laser was aotf')

        if laserInfo.isBinary():
            return

        if dig:
            self.__fullDigitalLasers[laserName].power_mod = power * Q_(1, 'mW')
        else:
            self.__fullDigitalLasers[laserName].power_sp = power * Q_(1, 'mW')

    def digitalMod(self, laserName, digital, power):
        if self.__laserInfos[laserName].isBinary():
            return

        laser = self.__fullDigitalLasers[laserName]
        if digital:
            laser.enter_mod_mode()
            laser.power_mod = power * Q_(1, 'mW')
            print('Entered digital modulation mode with power :', power)
            print('Modulation mode is: ', laser.mod_mode)
        else:
            laser.digital_mod = False
            laser.query('cp')
            print('Exited digital modulation mode')
