# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:08:33 2020

@author: _Xavi
"""
import numpy as np
from imcommon.framework import Signal, SignalInterface


class CommunicationChannel(SignalInterface):
    """
    Communication Channel is a class that handles the communication between Master Controller
    and Widgets, or between Widgets.
    """

    updateImage = Signal(np.ndarray, bool)  # (image, init)

    acquisitionStarted = Signal()

    acquisitionStopped = Signal()

    adjustFrame = Signal(int, int)  # (width, height)

    detectorSwitched = Signal(str, str)  # (newDetectorName, oldDetectorName)

    gridToggle = Signal()

    crosshairToggle = Signal()

    addItemTovb = Signal(object)  # (item)

    removeItemFromvb = Signal(object)  # (item)

    endRecording = Signal()

    updateRecFrameNum = Signal(int)  # (frameNumber)

    updateRecTime = Signal(int)  # (recTime)

    prepareScan = Signal()

    endScan = Signal()

    moveZstage = Signal(float)  # (step)

    def __init__(self, main):
        super().__init__()
        self.__main = main

    def getROIdata(self, image, ROI):
        return self.__main.imageController.getROIdata(image, ROI)

    def getCenterROI(self):
        # Returns the center of the VB to align the ROI
        return self.__main.imageController.getCenterROI()

    def getCamAttrs(self):
        return self.__main.settingsController.getCamAttrs()

    def getScanAttrs(self):
        return self.__main.scanController.getScanAttrs()

    def getDimsScan(self):
        return self.__main.scanController.getDimsScan()

    def getStartPos(self):
        return self.__main.positionerController.getPos()
