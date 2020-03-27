# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 16:41:57 2020

@author: _Xavi
"""
import numpy as np
class MasterController():
    def __init__(self):
        print('init master controller')
        self.stagePos = [0, 0, 0]

    def moveStage(self, axis, dist):
        self.stagePos[axis] += dist
        return self.stagePos[axis]
        
    def getImage(self):
        im = 20 + np.zeros((20, 20))
        return im
        
    def addItemTovb(self, plot):
        print('Item added to viewbox')
        
    def removeItemFromvb(self, plot):
        print('Item removed from viewbox')
        
    def getImageSize(self):
        return [500, 500]