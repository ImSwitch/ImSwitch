# -*- coding: utf-8 -*-
"""
Created on Wed Apr  1 15:18:49 2020

@author: Testa4
"""
import numpy as np
from model import mockers

import importlib

class Laser(object):

    def __new__(cls, iName, *args):
        try:
            pName, driverName = iName.rsplit('.', 1)
            package = importlib.import_module('lantz.drivers.legacy.' + pName)
            driver = getattr(package, driverName)
            laser = driver(*args)
            laser.initialize()
            return laser

        except:
            return mockers.MockLaser()


class LinkedLaserCheck(object):

    def __new__(cls, iName, ports):
        try:
            pName, driverName = iName.rsplit('.', 1)
            package = importlib.import_module('lantz.drivers.legacy.' + pName)
            driver = getattr(package, driverName)
            laser0 = driver(ports[0])
            laser0.initialize()
            laser1 = driver(ports[1])
            laser1.initialize()
            return LinkedLaser([laser0, laser1])

        except:
            return mockers.MockLaser()


class LinkedLaser(object):

    def __init__(self, lasers):
        self.lasers = lasers

    @property
    def idn(self):
        return 'Linked Lasers' + self.lasers[0].idn + self.lasers[1].idn

    @property
    def autostart(self):
        return self.lasers[0].autostart

    @autostart.setter
    def autostart(self, value):
        self.lasers[0].autostart = self.lasers[1].autostart = value

    @property
    def enabled(self):
        return self.lasers[0].enabled

    @enabled.setter
    def enabled(self, value):
        self.lasers[0].enabled = self.lasers[1].enabled = value

    @property
    def power(self):
        return self.lasers[0].power + self.lasers[1].power

    @property
    def power_sp(self):
        return self.lasers[0].power_sp + self.lasers[1].power_sp

    @power_sp.setter
    def power_sp(self, value):
        self.lasers[0].power_sp = self.lasers[1].power_sp = 0.5*value

    @property
    def digital_mod(self):
        return self.lasers[0].digital_mod

    @digital_mod.setter
    def digital_mod(self, value):
        self.lasers[0].digital_mod = self.lasers[1].digital_mod = value

    @property
    def mod_mode(self):
        return [self.lasers[0].mod_mode, self.lasers[1].mod_mode]

    def enter_mod_mode(self):
        [self.lasers[i].enter_mod_mode() for i in [0, 1]]

    def changeEdit(self):
        [self.lasers[i].changeEdit() for i in [0, 1]]

    def query(self, value):
        [self.lasers[i].query(value) for i in [0, 1]]

    @property
    def power_mod(self):
        """Laser modulated power (mW).
        """
        return self.lasers[0].power_mod + self.lasers[1].power_mod

    @power_mod.setter
    def power_mod(self, value):
        self.lasers[0].power_mod = self.lasers[1].power_mod = 0.5*value

    def finalize(self):
        self.lasers[0].finalize()
        self.lasers[1].finalize()

class Cameras(object):
    """ Buffer class for testing whether the camera is connected. If it's not,
    it returns a dummy class for program testing. """
#TODO:
    """This was originally (by federico) called from tormenta.py using a "with" call, as with the Lasers. But
    accoring to litterature, "with" should be used with classes having __enter__ and __exit functions defined. 
    For some reason this particular class gives "Error: class is missing __exit__ fcn" (or similar)
    Maybe it could be rewritten using __enter__  __exit__. 
    http://effbot.org/zone/python-with-statement.htm
    Although I believe that design is more suitable for funcions that are 
    called alot or environments that are used alot."""


    def __new__(cls, *args, **kwargs):
        cameras = []
        try:     
            import model.hamamatsu as hm
            for i in np.arange(hm.n_cameras):
                print('Trying to import camera', i)
                cameras.append(hm.HamamatsuCameraMR(i))
                print('Initialized Hamamatsu Camera Object, model: ', cameras[i].camera_model)
            return cameras

        except:
            print('Initializing Mock Hamamatsu')
            return [mockers.MockHamamatsu()]
