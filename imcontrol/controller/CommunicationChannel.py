import numpy as np
from imcommon.framework import Signal, SignalInterface
from imcommon.model import SharedAttributes


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

# Copyright (C) 2020, 2021 Staffan Al-Kadhimi, Xavier Casas, Andreas Boden
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
