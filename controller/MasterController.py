# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 16:41:57 2020

@author: _Xavi
"""
import numpy as np
from threading import Timer, Thread

class MyTimer(Timer):
    def __init__(self, time, function):
        super().__init__(time, self.run)
        self.stop = False
        self.function = function
        
    def run(self):
        while not self.stop:
            self.function()
    
    def stop(self):
        self.stop = True
        
class MyThread(Thread):
    def __init__(self, function):
        super().__init__()
        self.stop = False
        self.function = function
        
    def run(self):
        while not self.stop:
            self.function()
    
    def stop(self):
        self.stop = True
            
class CameraHelper():
    def __init__(self, cameras, updateImage):
        self.cameras = cameras
        self.updateImage = updateImage
        
    def startAcquisition(self):
        c = self.cameras[0]
        c.setPropertyValue('readout_speed', 3)
        c.setPropertyValue('trigger_global_exposure', 5)
        c.setPropertyValue(
                'trigger_active', 2)
        c.setPropertyValue('trigger_polarity', 2)
        c.setPropertyValue('exposure_time', 0.01)
        c.setPropertyValue('trigger_source', 1)
        c.setPropertyValue('subarray_vpos', 0)
        c.setPropertyValue('subarray_hpos', 0)
        c.setPropertyValue('subarray_vsize', 2048)
        c.setPropertyValue('subarray_hsize', 2048)
        
        c.startAcquisition()
        self.timer = MyTimer(0.1, self.updateLatestFrame)
        self.timer.start()
#        
    def stopAcquisition(self):
        self.cameras[0].stopAcquisition()
#        
#    def changeParameter(self):
#        
    def updateLatestFrame(self):
        hcData = self.cameras[0].getLast()
        size = hcData[1]
        frame = hcData[0].getData()
        self.image = np.reshape(
            frame, (size), 'F')
        self.updateImage(self.image)


        
class MasterController():
    
    def __init__(self, model, updateImage):
        print('init master controller')
        self.model = model
        self.stagePos = [0, 0, 0]
        self.updateImage = updateImage
        self.cameraHelper = CameraHelper(self.model.cameras, self.updateImage)
        
    def startLiveview(self):
        self.cameraHelper.startAcquisition()
        
    def stopLiveview(self):
        self.cameraHelper.stopAcquisition()
        
    def moveStage(self, axis, dist):
        self.stagePos[axis] += dist
        return self.stagePos[axis]
        
    def getImage(self):
        im = 20 + np.zeros((20, 20))
        return im
        
    def getImageSize(self):
        return [500, 500]
        
    def toggleLaser(self, enable, laser):
        print('Change enabler of laser '+ str(laser) + ' to ' + str(enable))
        
    def changePower(self, magnitude, laser):
        print('Change power of laser '+ str(laser) + ' to ' + str(magnitude))
        
    def digitalMod(self, digital, powers, laser):
        print('Digital modulation for laser '+ str(laser) + ' set to ' + str(digital))
        
