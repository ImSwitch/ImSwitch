# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 16:41:57 2020

@author: _Xavi
"""
import numpy as np
from pyqtgraph.Qt import QtCore

class MasterController():
    # This class will handle the communication between software and hardware, using the Helpers for each hardware set.
    def __init__(self, model, comm_channel):
        print('init master controller')
        self.__model = model
        self.stagePos = [0, 0, 0]
        self.__comm_channel = comm_channel
        self.cameraHelper = CameraHelper(self.__comm_channel, self.__model.cameras)
    
        
    def moveStage(self, axis, dist):
        self.stagePos[axis] += dist
        return self.stagePos[axis]
        
    def toggleLaser(self, enable, laser):
        print('Change enabler of laser '+ str(laser) + ' to ' + str(enable))
        
    def changePower(self, magnitude, laser):
        print('Change power of laser '+ str(laser) + ' to ' + str(magnitude))
        
    def digitalMod(self, digital, powers, laser):
        print('Digital modulation for laser '+ str(laser) + ' set to ' + str(digital))
        
class CameraHelper():
    # CameraHelper deals with the Hamamatsu parameters and frame extraction
    def __init__(self, comm_channel, cameras):
        self.__cameras = cameras
        self.__comm_channel = comm_channel
        self.__time = 100
        
        # A timer will collect the new frame and update it through the communication channel
        self.__timer = QtCore.QTimer()
        self.__timer.timeout.connect(self.__updateLatestFrame) 
        self.__cameras[0].setPropertyValue('readout_speed', 3)
        self.__cameras[0].setPropertyValue('trigger_global_exposure', 5)
        self.__cameras[0].setPropertyValue(
                'trigger_active', 2)
        self.__cameras[0].setPropertyValue('trigger_polarity', 2)
        self.__cameras[0].setPropertyValue('exposure_time', 0.01)
        self.__cameras[0].setPropertyValue('trigger_source', 1)
        self.__cameras[0].setPropertyValue('subarray_vpos', 0)
        self.__cameras[0].setPropertyValue('subarray_hpos', 0)
        self.__cameras[0].setPropertyValue('subarray_vsize', 2048)
        self.__cameras[0].setPropertyValue('subarray_hsize', 2048)
        self.__frameStart = (0, 0)
        self.__shapes = (self.__cameras[0].getPropertyValue('image_height')[0], self.__cameras[0].getPropertyValue('image_width')[0])
        self.__image = []

        
    @property
    def frameStart(self):
        return self.__frameStart
    
    @property
    def shapes(self):
        return self.__shapes
        
    @property
    def image(self):
        return self.__image
        
    def startAcquisition(self):
        self.__cameras[0].startAcquisition()
        self.__updateLatestFrame(False)
        self.__timer.start(self.__time)
        
    def stopAcquisition(self):
        self.__timer.stop()
        self.__cameras[0].stopAcquisition()
        
    def changeParameter(self, function):
            """ This method is used to change those camera properties that need
            the camera to be idle to be able to be adjusted.
            """
            try:
                function()
            except BaseException:
                self.stopAcquisition()
                function()
                self.startAcquisition()  

    def __updateLatestFrame(self, init=True):
        hcData = self.__cameras[0].getLast()
        size = hcData[1]
        frame = hcData[0].getData()
        self.__image = np.reshape(
            frame, (size), 'F')
        self.__comm_channel.updateImage(init)
        
    def setExposure(self, time):
        self.__cameras[0].setPropertyValue('exposure_time', time)
        return self.getTimings()
        
    def getTimings(self):
        return [self.__cameras[0].getPropertyValue('exposure_time')[0], self.__cameras[0].getPropertyValue('internal_frame_interval')[0], self.__cameras[0].getPropertyValue('timing_readout_time')[0], self.__cameras[0].getPropertyValue('internal_frame_rate')[0]]

                
    def cropOrca(self, hpos, vpos, hsize, vsize):
        """Method to crop the frame read out by Orcaflash. """
        self.stopAcquisition()
        self.__cameras[0].setPropertyValue('subarray_vpos', 0)
        self.__cameras[0].setPropertyValue('subarray_hpos', 0)
        self.__cameras[0].setPropertyValue('subarray_vsize', 2048)
        self.__cameras[0].setPropertyValue('subarray_hsize', 2048)
        
        if not (hpos == 0 and vpos == 0 and hsize == 2048 and vsize == 2048):
            self.__cameras[0].setPropertyValue('subarray_vsize', vsize)
            self.__cameras[0].setPropertyValue('subarray_hsize', hsize)
            self.__cameras[0].setPropertyValue('subarray_vpos', vpos)
            self.__cameras[0].setPropertyValue('subarray_hpos', hpos)
            
        self.startAcquisition()
        # This should be the only place where self.frameStart is changed
        self.__frameStart = (hpos, vpos)
        # Only place self.shapes is changed
        self.__shapes = (hsize, vsize)
            
    def changeTriggerSource(self, source):
        if source == 'Internal trigger':
            self.changeParameter(
                lambda: self.__cameras[0].setPropertyValue(
                    'trigger_source', 1))

        elif source == 'External "Start-trigger"':
            self.changeParameter(
                lambda: self.__cameras[0].setPropertyValue(
                    'trigger_source', 2))
            self.changeParameter(
                lambda: self.__cameras[0].setPropertyValue(
                    'trigger_mode', 6))

        elif source == 'External "frame-trigger"':
            self.changeParameter(
                lambda: self.__cameras[0].setPropertyValue(
                    'trigger_source', 2))
            self.changeParameter(
                lambda: self.__cameras[0].setPropertyValue(
                    'trigger_mode', 1))
            
    def setBinning(self, binning):    
        binning = str(binning)
        binstring = binning + 'x' + binning
        coded = binstring.encode('ascii')
    
        self.changeParameter(
           lambda: self.__cameras[0].setPropertyValue('binning', coded))
 
        
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

        

        
