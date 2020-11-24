# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:08:33 2020

@author: _Xavi
"""
import numpy as np
from pyqtgraph.Qt import QtCore, QtGui


class CommunicationChannel(QtCore.QObject):
    """
    Communication Channel is a class that handles the communication between Master Controller
    and Widgets, or between Widgets.
    """

    updateImage = QtCore.pyqtSignal(np.ndarray, bool)  # (image, init)

    acquisitionStopped = QtCore.pyqtSignal()

    adjustFrame = QtCore.pyqtSignal(int, int)  # (width, height)

    cameraSwitched = QtCore.pyqtSignal(str)  # (cameraName)

    gridToggle = QtCore.pyqtSignal()

    crosshairToggle = QtCore.pyqtSignal()

    addItemTovb = QtCore.pyqtSignal(QtGui.QGraphicsItem)  # (item)

    removeItemFromvb = QtCore.pyqtSignal(QtGui.QGraphicsItem)  # (item)

    endRecording = QtCore.pyqtSignal()

    updateRecFrameNumber = QtCore.pyqtSignal(int)  # (frameNumber)

    updateRecTime = QtCore.pyqtSignal(int)  # (recTime)

    prepareScan = QtCore.pyqtSignal()

    endScan = QtCore.pyqtSignal()

    moveZstage = QtCore.pyqtSignal(int)  # (step)

    def __init__(self, main, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
