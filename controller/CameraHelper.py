# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 16:37:09 2020

@author: _Xavi
"""
from pyqtgraph.Qt import QtCore
#import time

class CameraHelper():
    # CameraHelper deals with the Hamamatsu parameters and frame extraction
    def __init__(self, comm_channel, cameras):
        self.__cameras = cameras
        self.__comm_channel = comm_channel

        
        # A timer will collect the new frame and update it through the communication channel
        self.__lvWorker = LVWorker(self)
        self.__thread = QtCore.QThread()
        self.__lvWorker.moveToThread(self.__thread)
        self.__thread.started.connect(self.__lvWorker.run)
        
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
        self.__model = self.__cameras[0].camera_model.decode("utf-8")
        
    @property
    def model(self):
        return self.__model
        
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
        self.updateLatestFrame(False)
        self.__thread.start()
        
    def stopAcquisition(self):
        self.__thread.quit()
        self.__thread.wait()
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

    def updateLatestFrame(self, init=True):
        self.__image = self.__cameras[0].getLast()
        self.__comm_channel.updateImage(init)
        
    def getChunk(self):
        return self.__cameras[0].getFrames()
        
    def updateCameraIndices(self):
        self.__cameras[0].updateIndices()
        
    def setExposure(self, time):
        self.__cameras[0].setPropertyValue('exposure_time', time)
        return self.getTimings()
        
    def getTimings(self):
        return [self.__cameras[0].getPropertyValue('exposure_time')[0], self.__cameras[0].getPropertyValue('internal_frame_interval')[0], self.__cameras[0].getPropertyValue('timing_readout_time')[0], self.__cameras[0].getPropertyValue('internal_frame_rate')[0]]

                
    def cropOrca(self, hpos, vpos, hsize, vsize):
        """Method to crop the frame read out by Orcaflash. """
        self.__cameras[0].setPropertyValue('subarray_vpos', 0)
        self.__cameras[0].setPropertyValue('subarray_hpos', 0)
        self.__cameras[0].setPropertyValue('subarray_vsize', 2048)
        self.__cameras[0].setPropertyValue('subarray_hsize', 2048)
        
        if not (hpos == 0 and vpos == 0 and hsize == 2048 and vsize == 2048):
            self.__cameras[0].setPropertyValue('subarray_vsize', vsize)
            self.__cameras[0].setPropertyValue('subarray_hsize', hsize)
            self.__cameras[0].setPropertyValue('subarray_vpos', vpos)
            self.__cameras[0].setPropertyValue('subarray_hpos', hpos)

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
        
class LVWorker(QtCore.QObject):

    def __init__(self, cameraHelper, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__cameraHelper = cameraHelper

    def run(self):
        self.vtimer = QtCore.QTimer()
        self.vtimer.timeout.connect(self.__cameraHelper.updateLatestFrame)
        self.vtimer.start(30)
            

           