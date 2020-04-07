# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 16:41:57 2020

@author: _Xavi
"""
from controller.CameraHelper import CameraHelper

class MasterController():
    # This class will handle the communication between software and hardware, using the Helpers for each hardware set.
    def __init__(self, model, comm_channel):
        print('init master controller')
        self.__model = model
        self.stagePos = [0, 0, 0]
        self.__comm_channel = comm_channel
        self.cameraHelper = CameraHelper(self.__comm_channel, self.__model.cameras)
       # self.scanHelper = ScanHelper()  #Make sure compatibility  
    def moveStage(self, axis, dist):
        self.stagePos[axis] += dist
        return self.stagePos[axis]
        
    def toggleLaser(self, enable, laser):
        print('Change enabler of laser '+ str(laser) + ' to ' + str(enable))
        
    def changePower(self, magnitude, laser):
        print('Change power of laser '+ str(laser) + ' to ' + str(magnitude))
        
    def digitalMod(self, digital, powers, laser):
        print('Digital modulation for laser '+ str(laser) + ' set to ' + str(digital))
