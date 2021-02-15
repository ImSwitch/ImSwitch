# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:08:33 2020

@author: _Xavi
"""
import copy
import numpy as np

from framework import Signal, SignalInterface
from .SharedAttributes import SharedAttributes


class CommunicationChannel(SignalInterface):
    """
    Communication Channel is a class that handles the communication between Master Controller
    and Widgets, or between Widgets.
    """

    updateImage = Signal(str, np.ndarray, bool)  # (detectorName, image, init)

    acquisitionStarted = Signal()

    acquisitionStopped = Signal()

    adjustFrame = Signal(int, int)  # (width, height)

    detectorSwitched = Signal(list, list)  # (newDetectorNames, oldDetectorNames)

    gridToggle = Signal(bool)  # (enabled)

    crosshairToggle = Signal(bool)  # (enabled)

    addItemTovb = Signal(object)  # (item)

    removeItemFromvb = Signal(object)  # (item)

    endRecording = Signal()

    updateRecFrameNum = Signal(int)  # (frameNumber)

    updateRecTime = Signal(int)  # (recTime)

    prepareScan = Signal()

    endScan = Signal()

    moveZstage = Signal(float)  # (step)

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
