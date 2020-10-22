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


class MasterController():
    # This class will handle the communication between software and hardware, using the Helpers for each hardware set.
    def __init__(self, model, comm_channel):
        print('init master controller')
        self.__model = model
        self.__comm_channel = comm_channel
        self.cameraHelper = CameraHelper(self.__comm_channel, self.__model.cameras)
        self.recordingHelper = RecordingHelper(self.__comm_channel, self.cameraHelper)
        self.nidaqHelper = NidaqHelper()
        self.scanHelper = ScanHelper()  # Make sure compatibility
        self.laserHelper = LaserHelper(self.__model.lasers)
