# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 16:41:57 2020

@author: _Xavi
"""
from model import (
    DetectorsManager, LasersManager, NidaqManager, PositionersManager, RecordingManager, ScanManager
)


class MasterController:
    # This class will handle the communication between software and hardware, using the managers for each hardware set.
    def __init__(self, setupInfo, commChannel):
        print('init master controller')
        self.__setupInfo = setupInfo
        self.__commChannel = commChannel

        # Init managers
        self.detectorsManager = DetectorsManager(self.__setupInfo.detectors, updatePeriod=100)
        self.recordingManager = RecordingManager(self.detectorsManager)
        self.nidaqManager = NidaqManager(self.__setupInfo)
        self.scanManager = ScanManager(self.__setupInfo)  # Make sure compatibility
        self.lasersManager = LasersManager(self.__setupInfo.lasers, nidaqManager=self.nidaqManager)
        self.positionersManager = PositionersManager(self.__setupInfo.positioners,
                                                     nidaqManager=self.nidaqManager)

        # Connect signals
        self.detectorsManager.acquisitionStarted.connect(self.__commChannel.acquisitionStarted)
        self.detectorsManager.acquisitionStopped.connect(self.__commChannel.acquisitionStopped)
        self.detectorsManager.detectorSwitched.connect(self.__commChannel.detectorSwitched)
        self.detectorsManager.imageUpdated.connect(self.__commChannel.updateImage)

        self.recordingManager.recordingEnded.connect(self.__commChannel.endRecording)
        self.recordingManager.recordingFrameNumUpdated.connect(self.__commChannel.updateRecFrameNum)
        self.recordingManager.recordingTimeUpdated.connect(self.__commChannel.updateRecTime)
