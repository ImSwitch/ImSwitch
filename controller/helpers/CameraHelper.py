# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 16:37:09 2020

@author: _Xavi
"""
import numpy as np
from pyqtgraph.Qt import QtCore
from time import sleep

class SingleCameraHelper(QtCore.QObject):
    """SingleCameraHelper deals with the Hamamatsu parameters and frame extraction
    for a single camera."""

    updateImageSignal = QtCore.pyqtSignal(np.ndarray, bool)

    def __init__(self, camera, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__camera = camera

        self.__frameStart = (0, 0)
        self.__binning = 1
        self.__shape = (self.__camera.getPropertyValue('image_height')[0],
                        self.__camera.getPropertyValue('image_width')[0])
        self.__fullShape = self.__shape
        self.__image = np.array([])
        self.__model = self.__camera.camera_model.decode("utf-8")

    @property
    def model(self):
        return self.__model

    @property
    def binning(self):
        return self.__binning

    @property
    def frameStart(self):
        return self.__frameStart

    @property
    def shape(self):
        return self.__shape

    @property
    def fullShape(self):
        return self.__fullShape

    @property
    def image(self):
        return self.__image

    def _startAcquisition(self):
        self.__camera.startAcquisition()
        sleep(0.3)

    def _stopAcquisition(self):
        self.__camera.stopAcquisition()

    def changeParameter(self, function):
        """ This method is used to change those camera properties that need
        the camera to be idle to be able to be adjusted.
        """
        try:
            function()
        except:
            self._stopAcquisition()
            function()
            self._startAcquisition()

    def updateLatestFrame(self, init):
        self.__image = self.__camera.getLast()
        self.updateImageSignal.emit(self.__image, init)

    def getChunk(self):
        return self.__camera.getFrames()

    def updateCameraIndices(self):
        self.__camera.updateIndices()

    def setExposure(self, time):
        self.__camera.setPropertyValue('exposure_time', time)

    def getTimings(self):
        return (self.__camera.getPropertyValue('exposure_time')[0],
                self.__camera.getPropertyValue('internal_frame_interval')[0],
                self.__camera.getPropertyValue('timing_readout_time')[0],
                self.__camera.getPropertyValue('internal_frame_rate')[0])

    def cropOrca(self, hpos, vpos, hsize, vsize):
        """Method to crop the frame read out by Orcaflash. """
        self.__camera.setPropertyValue('subarray_vpos', 0)
        self.__camera.setPropertyValue('subarray_hpos', 0)
        self.__camera.setPropertyValue('subarray_vsize', 2304)
        self.__camera.setPropertyValue('subarray_hsize', 2304)
        
        self.__camera.setPropertyValue('subarray_vsize', vsize)
        self.__camera.setPropertyValue('subarray_hsize', hsize)
        self.__camera.setPropertyValue('subarray_vpos', vpos)
        self.__camera.setPropertyValue('subarray_hpos', hpos)
        

        # This should be the only place where self.frameStart is changed
        self.__frameStart = (vpos, hpos)
        # Only place self.shapes is changed
        self.__shape = (vsize, hsize)

    def changeTriggerSource(self, source):
        if source == 'Internal trigger':
            self.changeParameter(
                lambda: self.__camera.setPropertyValue('trigger_source', 1)
            )

        elif source == 'External "Start-trigger"':
            self.changeParameter(
                lambda: self.__camera.setPropertyValue('trigger_source', 2)
            )
            self.changeParameter(
                lambda: self.__camera.setPropertyValue('trigger_mode', 6)
            )

        elif source == 'External "frame-trigger"':
            self.changeParameter(
                lambda: self.__camera.setPropertyValue('trigger_source', 2)
            )
            self.changeParameter(
                lambda: self.__camera.setPropertyValue('trigger_mode', 1)
            )

    def setBinning(self, binning):
        binning = str(binning)
        binstring = binning + 'x' + binning
        coded = binstring.encode('ascii')

        self.changeParameter(
            lambda: self.__camera.setPropertyValue('binning', coded)
        )

        self.__binning = int(binning)


class CameraHelper(QtCore.QObject):
    """CameraHelper is an interface for dealing with SingleCameraHelpers"""

    updateImageSignal = QtCore.pyqtSignal(np.ndarray, bool)

    def __init__(self, commChannel, cameras, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__commChannel = commChannel

        self.__singleCameraHelpers = {}
        self.__currentCameraName = None
        for cameraName, camera in cameras.items():
            self.__singleCameraHelpers[cameraName] = SingleCameraHelper(camera)

            self.__singleCameraHelpers[cameraName].updateImageSignal.connect(
                lambda image, init, cameraName=cameraName: self.updateImageSignal.emit(
                    image, init
                ) if cameraName == self.__currentCameraName else None
            )

            if self.__currentCameraName is None:
                self.__currentCameraName = cameraName

        # A timer will collect the new frame and update it through the communication channel
        self.__lvWorker = LVWorker(self)
        self.__thread = QtCore.QThread()
        self.__lvWorker.moveToThread(self.__thread)
        self.__thread.started.connect(self.__lvWorker.run)

    def getCurrentCameraName(self):
        return self.__currentCameraName

    def getCurrentCamera(self):
        return self.__singleCameraHelpers[self.__currentCameraName]

    def setCurrentCamera(self, cameraName):
        self.__currentCameraName = cameraName
        self.__commChannel.cameraSwitched.emit(cameraName)
        self.execOnCurrent(lambda c: c.updateLatestFrame(True))

    def execOn(self, cameraName, func):
        """ Executes a function on a specific camera and returns the result. """
        return func(self.__singleCameraHelpers[cameraName])

    def execOnCurrent(self, func):
        """ Executes a function on the current camera and returns the result. """
        return self.execOn(self.__currentCameraName, func)

    def execOnAll(self, func):
        """ Executes a function on all cameras and returns the results. """
        return {cameraName: func(singleCameraHelper)
                for cameraName, singleCameraHelper in self.__singleCameraHelpers.items()}

    def startAcquisition(self):
        self.execOnAll(lambda c: c._startAcquisition())
        self.__thread.start()

    def stopAcquisition(self):
        self.__thread.quit()
        self.__thread.wait()
        self.execOnAll(lambda c: c._stopAcquisition())
        self.__commChannel.acquisitionStopped.emit()


class LVWorker(QtCore.QObject):
    updateSignal = QtCore.pyqtSignal()

    def __init__(self, cameraHelper, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__cameraHelper = cameraHelper   

    def run(self):
        self.__cameraHelper.execOnAll(lambda c: c.updateLatestFrame(False))
        self.vtimer = QtCore.QTimer()
        self.vtimer.timeout.connect(
            lambda: self.__cameraHelper.execOnAll(lambda c: c.updateLatestFrame(True))
        )
        self.vtimer.start(100)
