# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:16:06 2020

@author: _Xavi
"""
from model import instruments

class TempestaModel():
    
    def __init__(self):
        self.cameras = instruments.Cameras(0)
