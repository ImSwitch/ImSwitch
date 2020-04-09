# -*- coding: utf-8 -*-
"""
Created on Sun Dec 28 13:25:27 2014

@author: federico
"""

import importlib
import model.mockers as mockers
import numpy as np
import nidaqmx


class Laser(object):

    def __new__(cls, iName, *args):
        try:
            pName, driverName = iName.rsplit('.', 1)
            package = importlib.import_module('lantz.drivers.legacy.' + pName)
            driver = getattr(package, driverName)
            laser = driver(*args)
            laser.initialize()
            return driver(*args)

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
        return self.lasers[0].digital_mode

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


class LaserTTL(object):
    def __init__(self, line):
        self.line = line
        # Nidaq task
        self.aotask = nidaqmx.Task('AOTF_voltage')
        self.aotask.ao_channels.add_ao_voltage_chan('Dev1/ao3', min_val = 0, max_val = 5)
        self._digital_mod = False
        
        self._power = 0
        self.enabled = False
        

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        try:
            self.dotask
        except:
            self.dotask = nidaqmx.Task('dotaskEnableTTL')
            self.dotask.do_channels.add_do_chan(
                lines='Dev1/port0/line%s' % self.line,
                name_to_assign_to_lines='chan')

            self.dotask.timing.cfg_samp_clk_timing(
               source=r'100kHzTimeBase',
               rate=100000,
               sample_mode=nidaqmx.constants.AcquisitionType.FINITE)
            
        if value:
            self.dotask.write(np.ones(100, dtype=bool), auto_start=True)
            self.dotask.wait_until_done()
            self.dotask.stop()
        else:
            self.dotask.write(np.zeros(100, dtype=bool), auto_start=True)
            self.dotask.wait_until_done()
            self.dotask.stop()

        self._enabled = value
        
    @property
    def power(self):
        return self._power
        
    @power.setter
    def power(self, value):
        self.analog(value)
        
    def analog(self, value):
        self.aotask.write(value)
        
    @property
    def digital_mod(self):
        return self._digital_mod

    @digital_mod.setter
    def digital_mod(self, value):
        self._digital_mod = value
        if value:
            print('Closing task in LaserTTL')
            self.dotask.close()
        else:
            self.dotask = nidaqmx.Task('dotaskEnableTTL')
            self.dotask.do_channels.add_do_chan(
                lines='Dev1/port0/line%s' % self.line,
                name_to_assign_to_lines='chan')

            self.dotask.timing.cfg_samp_clk_timing(
               source=r'100kHzTimeBase',
               rate=100000,
               sample_mode=nidaqmx.constants.AcquisitionType.FINITE)

    def enter_mod_mode(self):
        pass

    def query(self, value):
        pass


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
            import hamamatsu.hamamatsu_camera_Testa as hm
            for i in np.arange(hm.n_cameras):
                print('Trying to import camera', i)
                cameras.append(hm.HamamatsuCameraMR(i))
                print('Initialized Hamamatsu Camera Object, model: ', cameras[i].camera_model)
            return cameras

        except:
            print('Initializing Mock Hamamatsu')
            return [mockers.MockHamamatsu()]


class PZT(object):

    def __new__(cls, port, *args):
        try:
            from lantz.drivers.piezosystemjena.nv401 import nv401
            inst = nv401.via_serial(port)
            inst.initialize()
            inst.position
            return inst
        except:
            return mockers.MockPZT()


class Webcam(object):

    def __new__(cls):
        try:
            from instrumental.drivers.cameras.uc480 import UC480_Camera
            webcam = UC480_Camera()
        except:
            webcam = mockers.MockWebcam()
        return webcam
