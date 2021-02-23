# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:08:33 2020

@author: _Xavi
"""
import numpy as np
from imcommon.framework import Signal, SignalInterface
from imcommon.model import SharedAttributes


class CommunicationChannel(SignalInterface):
    """
    Communication Channel is a class that handles the communication between Master Controller
    and Widgets, or between Widgets.
    """

    sigUpdateImage = Signal(np.ndarray, bool)  # (image, init)

    sigAcquisitionStarted = Signal()

    sigAcquisitionStopped = Signal()

    sigAdjustFrame = Signal(int, int)  # (width, height)

    sigDetectorSwitched = Signal(str, str)  # (newDetectorName, oldDetectorName)

    sigGridToggled = Signal(bool)  # (enabled)

    sigCrosshairToggled = Signal(bool)  # (enabled)

    sigAddItemToVb = Signal(object)  # (item)

    sigRemoveItemFromVb = Signal(object)  # (item)

    sigRecordingEnded = Signal()

    sigUpdateRecFrameNum = Signal(int)  # (frameNumber)

    sigUpdateRecTime = Signal(int)  # (recTime)

    sigPrepareScan = Signal()

    sigScanEnded = Signal()

    sigMoveZStage = Signal(float)  # (step)

    @property
    def sharedAttrs(self):
        return self.__sharedAttrs

    def __init__(self, main):
        super().__init__()
        self.__main = main
        self.__sharedAttrs = SharedAttributes()

    def getROIdata(self, image, ROI):
        return self.__main.imageController.getROIdata(image, ROI)

    def getCenterROI(self):
        # Returns the center of the VB to align the ROI
        return self.__main.imageController.getCenterROI()

    def getCamAttrs(self):
        return self.__main.settingsController.getCamAttrs()

    def getScanStageAttrs(self):
        return self.__main.scanController.getScanStageAttrs()

    def getScanTTLAttrs(self):
        return self.__main.scanController.getScanTTLAttrs()

    def getDimsScan(self):
        return self.__main.scanController.getDimsScan()

    def getStartPos(self):
        return self.__main.positionerController.getPos()
