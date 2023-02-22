import json
import os

import numpy as np
import time
import tifffile as tif
import threading
from datetime import datetime
import threading
import cv2
from skimage.registration import phase_cross_correlation
from imswitch.imcommon.model import dirtools, initLogger, APIExport
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex, Timer
from imswitch.imcontrol.model import configfiletools
import time

from ..basecontrollers import LiveUpdatedController


# import NanoImagingPack as nip


class PixelCalibrationController(LiveUpdatedController):
    """Linked to PixelCalibrationWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self)

        # Connect PixelCalibrationWidget signals
        # self._widget.PixelCalibrationLabelInfo.clicked.connect()
        self._widget.PixelCalibrationSnapPreviewButton.clicked.connect(self.snapPreview)
        self._widget.PixelCalibrationUndoButton.clicked.connect(self.undoSelection)
        self._widget.PixelCalibrationCalibrateButton.clicked.connect(self.startPixelCalibration)
        self._widget.PixelCalibrationStageCalibrationButton.clicked.connect(self.stageCalibration)

        self._widget.PixelCalibrationPixelSizeButton.clicked.connect(self.setPixelSize)
        self.pixelSize = 500  # defaul FIXME: Load from json?

        # select detectors # TODO: Bad practice, but how can we access the pixelsize then?
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]

    def undoSelection(self):
        # recover the previous selection
        self._widget.canvas.undoSelection()

    def snapPreview(self):
        self._logger.info("Snap preview...")
        self.previewImage = self._master.detectorsManager.execOnCurrent(lambda c: c.getLatestFrame())
        self._widget.canvas.setImage(self.previewImage)

    def startPixelCalibration(self):
        # initilaze setup
        # this is not a thread!
        self.pixelSize = self._widget.getPixelSize()
        self._widget.setInformationLabel(str(self.pixelSize) + " µm")

    def setPixelSize(self):
        # returns nm from textedit
        self.pixelSize = self._widget.getPixelSizeTextEdit()

        # try setting it in the camera parameters
        try:
            self.detector.setPixelSizeUm(self.pixelSize * 1e-3)  # convert from nm to um
            self._widget.setInformationLabel(str(self.pixelSize) + " µm")
        except Exception as e:
            self._logger.error("Could not set pixel size in camera parameters")
            self._logger.error(e)
            self._widget.setInformationLabel("Could not set pixel size in camera parameters")

    def stageCalibration(self):
        stageCalibrationT = threading.Thread(target=self.stageCalibrationThread, args=())
        stageCalibrationT.start()

    def stageCalibrationThread(self):
        # we assume we have a structured sample in focus
        # the sample is moved around and the deltas are measured
        # everything has to be inside a thread

        # get current position
        stage_name = self._master.positionersManager.getAllDeviceNames()[0]
        currentPositions = self._master.positionersManager.execOn(stage_name, lambda c: c.getPosition())
        self.initialPosition = (currentPositions["X"], currentPositions["Y"])
        self.initialPosiionZ = currentPositions["Z"]

        # define scan parameters
        self.xScanMin = -40
        self.xScanMax = 40
        self.yScanMin = -40
        self.yScanMax = 40
        self.xScanStep = 15
        self.yScanStep = 15

        # snake scan
        if 0:
            xyScanStepsAbsolute = []
            fwdpath = np.arange(self.xScanMin, self.xScanMax, self.xScanStep)
            bwdpath = np.flip(fwdpath)
            for indexX, ix in enumerate(np.arange(self.xScanMin, self.xScanMax, self.yScanStep)):
                if indexX % 2 == 0:
                    for indexY, iy in enumerate(fwdpath):
                        xyScanStepsAbsolute.append([ix, iy])
                else:
                    for indexY, iy in enumerate(bwdpath):
                        xyScanStepsAbsolute.append([ix, iy])
        else:
            # avoid grid pattern to be detected as same locations => random positions
            xyScanStepsAbsolute = np.random.randint(self.xScanMin, self.xScanMax, (10, 2))

        # initialize xy coordinates
        value = xyScanStepsAbsolute[0, 0] + self.initialPosition[0], xyScanStepsAbsolute[0, 1] + self.initialPosition[1]
        self._master.positionersManager.execOn(stage_name, lambda c: c.move(value=value, axis="XY", is_absolute=True,
                                                                            is_blocking=True))

        # store images
        allPosImages = []
        for ipos, iXYPos in enumerate(xyScanStepsAbsolute):
            # move to xy position is necessary
            value = iXYPos[0] + self.initialPosition[0], iXYPos[1] + self.initialPosition[1]
            self._master.positionersManager.execOn(stage_name,
                                                   lambda c: c.move(value=value, axis="XY", is_absolute=True,
                                                                    is_blocking=True))
            # TODO: do we move to the correct positions?
            # antishake
            time.sleep(0.5)
            lastFrame = self.detector.getLatestFrame()
            allPosImages.append(lastFrame)

        # reinitialize xy coordinates
        value = self.initialPosition[0], self.initialPosition[1]
        self._master.positionersManager.execOn(stage_name, lambda c: c.move(value=value, axis="XY", is_absolute=True,
                                                                            is_blocking=True))

        # process the slices and compute their relative distances in pixels
        # compute shift between images relative to zeroth image
        self._logger.info("Starting to compute relative displacements from the first image")
        allShifts = []
        for iImage in range(len(allPosImages)):
            image1 = np.mean(allPosImages[0], -1)
            image2 = np.mean(allPosImages[iImage], -1)
            rescalingFac = 10.
            # downscaling will reduce accuracy, but will speed up computation
            image1 = cv2.resize(image1, dsize=None, dst=None, fx=1 / rescalingFac, fy=1 / rescalingFac)
            image2 = cv2.resize(image2, dsize=None, dst=None, fx=1 / rescalingFac, fy=1 / rescalingFac)

            shift, error, diffphase = phase_cross_correlation(image1, image2)
            shift *= rescalingFac
            self._logger.info("Shift w.r.t. 0 is:" + str(shift))
            allShifts.append((shift[0], shift[1]))

        # compute averrage shifts according to scan grid
        # compare measured shift with shift given by the array of random coordinats
        xyScanStepsAbsolute
        allShifts
        shiftReal = np.array(xyScanStepsAbsolute)
        shiftReal -= np.min(shiftReal, 0)
        shiftMeasured = np.array(allShifts)

        # whiten the data

        # compute differencs
        nShiftX = (self.xScanMax - self.xScanMin) // self.xScanStep
        nShiftY = (self.yScanMax - self.yScanMin) // self.yScanStep

        dReal = np.abs(shiftReal - np.roll(shiftReal, -1, 0))
        dMeasured = np.abs(shiftMeasured - np.roll(shiftMeasured, -1, 0))

        # determine the axis
        xAxisReal = np.argmin(np.mean(dReal, 0))
        xAxisMeasured = np.argmin(np.mean(dMeasured, 0))

        # swap axis (y,x)
        if xAxisReal != xAxisMeasured:
            xAxisMeasured = np.transposes(xAxisMeasured, (1, 0))

        # stepsize => real motion / stepsize
        stepSizeStage = (dMeasured * self.pixelSize) / dReal
        stepSizeStage[stepSizeStage == np.inf] = 0
        stepSizeStage = np.nan_to_num(stepSizeStage, nan=0.)
        stepSizeStage = stepSizeStage[np.where(stepSizeStage > 0)]
        stepSizeStageDim = np.mean(stepSizeStage)
        stepSizeStageVar = np.var(stepSizeStage)

        self._logger.debug("Stage pixel size: " + str(stepSizeStageDim) + "nm/step")
        self._widget.setInformationLabel("Stage pixel size: " + str(stepSizeStageDim) + " nm/step")

        # Set in setup info
        name = "test"
        self._setupInfo.setPositionerPreset(name, self.makePreset())
        configfiletools.saveSetupInfo(configfiletools.loadOptions()[0], self._setupInfo)

# Copyright (C) 2020-2021 ImSwitch developers
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