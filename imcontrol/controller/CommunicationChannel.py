import numpy as np
from imcommon.framework import Signal, SignalInterface
from imcommon.model import SharedAttributes


class CommunicationChannel(SignalInterface):
    """
    Communication Channel is a class that handles the communication between Master Controller
    and Widgets, or between Widgets.
    """

    sigUpdateImage = Signal(str, np.ndarray, bool, bool)  # (detectorName, image, init, isCurrentDetector)

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


# Copyright (C) 2020, 2021 TestaLab
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
