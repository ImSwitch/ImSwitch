# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 16:41:57 2020

@author: _Xavi
"""
from lantz import Q_


class LaserHelper:
    def __init__(self, lasers, laserInfos):
        self.__lasers = lasers
        self.laserInfos = laserInfos

    def toggleLaser(self, enable, laser):
        self.__lasers[laser].enabled = enable

    def changePower(self, power, laser, dig):
        if dig:
            self.__lasers[laser].power_mod = power * Q_(1, 'mW')
        else:
            self.__lasers[laser].power_sp = power * Q_(1, 'mW')

    def digitalMod(self, digital, power, laser):
        laser = self.__lasers[laser]
        if digital:
            laser.enter_mod_mode()
            laser.power_mod = power * Q_(1, 'mW')
            print('Entered digital modulation mode with power :', power)
            print('Modulation mode is: ', laser.mod_mode)
        else:
            laser.digital_mod = False
            laser.query('cp')
            print('Exited digital modulation mode')
