# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 16:41:57 2020

@author: _Xavi
"""
from .helpers.CameraHelper import CameraHelper
from .helpers.LaserHelper import LaserHelper
from .helpers.NidaqHelper import NidaqHelper
from .helpers.RecordingHelper import RecordingHelper
from .helpers.ScanHelper import ScanHelper


class MasterController:
    # This class will handle the communication between software and hardware, using the Helpers for each hardware set.
    def __init__(self, model, commChannel):
        print('init master controller')
        self.__model = model
        self.__commChannel = commChannel

        # Init helpers
        self.cameraHelper = CameraHelper(self.__commChannel, self.__model.cameras)
        self.recordingHelper = RecordingHelper(self.__commChannel, self.cameraHelper)
        self.nidaqHelper = NidaqHelper(self.__model.setupInfo)
        self.scanHelper = ScanHelper(self.__model.setupInfo)  # Make sure compatibility
        self.laserHelper = LaserHelper(self.__model.setupInfo.lasers, self.__model.lasers,
                                       self.nidaqHelper)

        # Connect signals
        self.cameraHelper.updateImageSignal.connect(self.__commChannel.updateImage)
