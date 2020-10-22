# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:16:06 2020

@author: _Xavi
"""
from model import instruments


class TempestaModel():

    def __init__(self):
        self.cameras = instruments.Cameras(0)
        cobolt = 'cobolt.cobolt0601.Cobolt0601_f2'
        offlaser = instruments.LinkedLaserCheck(cobolt, ['COM4', 'COM7'])
        actlaser = instruments.Laser(cobolt, 'COM10')
        self.lasers = {'405': actlaser, '488': offlaser}
        self.initLaser(self.lasers['405'])
        self.initLaser(self.lasers['488'])

    def initLaser(self, laser):
        print(laser.idn)
        laser.digital_mod = False
        laser.enabled = False
        laser.digital_mod = True
        laser.autostart = False
        laser.autostart = False
