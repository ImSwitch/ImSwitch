# -*- coding: utf-8 -*-
"""
Created on Wed Apr  1 15:18:49 2020

@author: Testa4
"""
import numpy as np
from model import mockers

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
