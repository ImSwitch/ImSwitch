# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 16:41:57 2020

@author: _Xavi
"""
import numpy as np
from pyqtgraph.Qt import QtCore

class CameraHelper():
    def __init__(self, comm_channel, cameras):
        self.cameras = cameras
        self.comm_channel = comm_channel
        self.time = 100
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateLatestFrame)
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
        
    def startAcquisition(self):
        self.timer.start(self.time)
        self.cameras[0].startAcquisition()  
        
    def stopAcquisition(self):
        self.timer.stop()
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
        self.comm_channel.updateImage(self.image)

#class NidaqHelper():
#    
#    def __init__(self, ):
#        import nidaqmx
#        self.deviceInfo = [['488 Exc', 1, [0, 247, 255]],
#                           ['405', 2, [130, 0, 200]],
#                           ['488 OFF', 3, [0, 247, 255]],
#                           ['Camera', 4, [255, 255, 255]]]
#    def __createDOTask(self):
#    def __createAOTask(self):
#        
#    def setDigital(self, target, enable):
#    def setAnalog(self, target, voltage):
#
#    def runScan(self, analog_targets, digital_targets, analog_signals, digital_signals):
#    def runContinuous(self, digital_targets, digital_signals):

        
class MasterController():
    
    def __init__(self, model, comm_channel):
        print('init master controller')
        self.model = model
        self.stagePos = [0, 0, 0]
        self.comm_channel = comm_channel
        self.cameraHelper = CameraHelper(self.comm_channel, self.model.cameras)
        
        
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
        
