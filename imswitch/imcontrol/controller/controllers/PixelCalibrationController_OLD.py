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

#import NanoImagingPack as nip


class PixelCalibrationController(LiveUpdatedController):
    """Linked to PixelCalibrationWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self)

        # Connect PixelCalibrationWidget signals
        #self._widget.PixelCalibrationLabelInfo.clicked.connect()
        self._widget.PixelCalibrationSnapPreviewButton.clicked.connect(self.snapPreview)
        self._widget.PixelCalibrationUndoButton.clicked.connect(self.undoSelection)
        self._widget.PixelCalibrationCalibrateButton.clicked.connect(self.startPixelCalibration)
        self._widget.PixelCalibrationStageCalibrationButton.clicked.connect(self.stageCalibration)
        
        self._widget.PixelCalibrationPixelSizeButton.clicked.connect(self.setPixelSize)
        self.pixelSize=500 # defaul FIXME: Load from json?

        # select detectors # TODO: Bad practice, but how can we access the pixelsize then?
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]


    def undoSelection(self):
        # recover the previous selection
        self._widget.canvas.undoSelection()
        
    def snapPreview(self):
        self._logger.info("Snap preview...")
        previewImage = self._master.detectorsManager.execOnCurrent(lambda c: c.getLatestFrame())
        self._widget.setImage(previewImage)
        self._widget.addPointLayer()
        
    def startPixelCalibration(self):
        # initilaze setup
        # this is not a thread!
        
        csm_extension = CSMExtension(self)
        csm_extension.calibrate_xy()
        
        knownDistance = self._widget.getKnownDistance()
        try:
            self.lastTwoPoints = self._widget.viewer.layers["Pixelcalibration Points"].data[-2:,]
            dx = self.lastTwoPoints[1,0]-self.lastTwoPoints[0,0]
            dy = self.lastTwoPoints[1,1]-self.lastTwoPoints[0,1]
            dr = np.sqrt(dx**2+dy**2)
            pixelSize = knownDistance/dr
            self._widget.setInformationLabel(str(pixelSize)+" µm")
            self.detector.setPixelSizeUm(pixelSize*1e-3) # convert from nm to um
        except:
            pass 

    def setPixelSize(self):
        # returns nm from textedit
        self.pixelSize = self._widget.getPixelSizeTextEdit()
        self._widget.setInformationLabel(str(self.pixelSize)+" µm")
        #try setting it in the camera parameters
        try:
            self.detector.setPixelSizeUm(self.pixelSize*1e-3) # convert from nm to um
            self._widget.setInformationLabel(str(self.pixelSize)+" µm")
        except Exception as e:
            self._logger.error("Could not set pixel size in camera parameters")
            self._logger.error(e)
            self._widget.setInformationLabel("Could not set pixel size in camera parameters")
        
    def stageCalibration(self):
        stageCalibrationT = threading.Thread(target=self.stageCalibrationThread, args=())
        stageCalibrationT.start()
        
    def stageCalibrationThread(self, stageName=None, scanMax=100, scanMin=-100, scanStep = 50, rescalingFac=10.0, gridScan=True):
        # we assume we have a structured sample in focus
        # the sample is moved around and the deltas are measured
        # everything has to be inside a thread

        # get current position
        if stageName is None:
            stageName = self._master.positionersManager.getAllDeviceNames()[0]
        currentPositions = self._master.positionersManager.execOn(stageName, lambda c: c.getPosition())
        self.initialPosition = (currentPositions["X"], currentPositions["Y"])
        self.initialPosiionZ = currentPositions["Z"]
        
        # snake scan
        
        if gridScan:
            xyScanStepsAbsolute = []
            fwdpath = np.arange(scanMin, scanMax, scanStep)
            bwdpath = np.flip(fwdpath)
            for indexX, ix in enumerate(np.arange(scanMin, scanMax, scanStep)): 
                if indexX%2==0:
                    for indexY, iy in enumerate(fwdpath):
                        xyScanStepsAbsolute.append([ix, iy])
                else:
                    for indexY, iy in enumerate(bwdpath):
                        xyScanStepsAbsolute.append([ix, iy])
            xyScanStepsAbsolute = np.array(xyScanStepsAbsolute)    
        else:
            # avoid grid pattern to be detected as same locations => random positions
            xyScanStepsAbsolute = np.random.randint(scanMin, scanMax, (10,2))

        # initialize xy coordinates
        value = xyScanStepsAbsolute[0,0] + self.initialPosition[0], xyScanStepsAbsolute[0,1] + self.initialPosition[1]
        self._master.positionersManager.execOn(stageName, lambda c: c.move(value=value[0], axis="X", is_absolute=True, is_blocking=True))
        self._master.positionersManager.execOn(stageName, lambda c: c.move(value=value[1], axis="Y", is_absolute=True, is_blocking=True))
        # store images
        allPosImages = []
        for ipos, iXYPos in enumerate(xyScanStepsAbsolute):
            
            # move to xy position is necessary
            value = iXYPos[0]+self.initialPosition[0],iXYPos[1]+self.initialPosition[1]
            self._master.positionersManager.execOn(stageName, lambda c: c.move(value=value, axis="XY", is_absolute=True, is_blocking=True))
            #TODO: do we move to the correct positions?
            # antishake
            time.sleep(0.5)
            lastFrame = self.detector.getLatestFrame()
            allPosImages.append(lastFrame)
        
        # reinitialize xy coordinates
        value = self.initialPosition[0], self.initialPosition[1]
        self._master.positionersManager.execOn(stageName, lambda c: c.move(value=value[0], axis="X", is_absolute=True, is_blocking=True))
        self._master.positionersManager.execOn(stageName, lambda c: c.move(value=value[1], axis="Y", is_absolute=True, is_blocking=True))
        # process the slices and compute their relative distances in pixels
        # compute shift between images relative to zeroth image
        self._logger.info("Starting to compute relative displacements from the first image")
        allShiftsComputed = []
        for iImage in range(len(allPosImages)):
            image1 = cv2.cvtColor(allPosImages[0], cv2.COLOR_BGR2GRAY)
            image2 = cv2.cvtColor(allPosImages[iImage], cv2.COLOR_BGR2GRAY)
            
            # downscaling will reduce accuracy, but will speed up computation
            image1 = cv2.resize(image1, dsize=None, dst=None, fx=1/rescalingFac, fy=1/rescalingFac)
            image2 = cv2.resize(image2, dsize=None, dst=None, fx=1/rescalingFac, fy=1/rescalingFac)

            shift, error, diffphase = phase_cross_correlation(image1, image2)
            shift *=rescalingFac
            self._logger.info("Shift w.r.t. 0 is:"+str(shift))
            allShiftsComputed.append((shift[0],shift[1]))
            
        # compute averrage shifts according to scan grid 
        # compare measured shift with shift given by the array of random coordinats
        allShiftsPlanned = np.array(xyScanStepsAbsolute)
        allShiftsPlanned -= np.min(allShiftsPlanned,0)
        allShiftsComputed = np.array(allShiftsComputed)

        # compute differencs
        nShiftX = (self.xScanMax-self.xScanMin)//self.xScanStep
        nShiftY = (self.yScanMax-self.yScanMin)//self.yScanStep

        # determine the axis and swap if necessary (e.g. swap axis (y,x))
        dReal = np.abs(allShiftsPlanned-np.roll(allShiftsPlanned,-1,0))
        dMeasured = np.abs(allShiftsComputed-np.roll(allShiftsComputed,-1,0))
        xAxisReal = np.argmin(np.mean(dReal,0))
        xAxisMeasured = np.argmin(np.mean(dMeasured,0))
        if xAxisReal != xAxisMeasured:
            xAxisMeasured = np.transposes(xAxisMeasured, (1,0))
        
        # stepsize => real motion / stepsize 
        stepSizeStage = (dMeasured*self.pixelSize)/dReal
        stepSizeStage[stepSizeStage == np.inf] = 0
        stepSizeStage = np.nan_to_num(stepSizeStage, nan=0.)
        stepSizeStage = stepSizeStage[np.where(stepSizeStage>0)]
        stepSizeStageDim = np.mean(stepSizeStage)
        stepSizeStageVar = np.var(stepSizeStage)

        self._logger.debug("Stage pixel size: "+str(stepSizeStageDim)+"nm/step")
        self._widget.setInformationLabel("Stage pixel size: "+str(stepSizeStageDim)+" nm/step")

        # Set in setup info
        name="test"
        self._setupInfo.setPositionerPreset(name, self.makePreset())
        configfiletools.saveSetupInfo(configfiletools.loadOptions()[0], self._setupInfo)





import logging
import time
import numpy as np
import PIL
import io
import os
import json
from collections import namedtuple

from camera_stage_mapping.camera_stage_calibration_1d import calibrate_backlash_1d, image_to_stage_displacement_from_1d

from camera_stage_mapping.camera_stage_tracker import Tracker
from camera_stage_mapping.closed_loop_move import closed_loop_move, closed_loop_scan
from camera_stage_mapping.scan_coords_times import ordered_spiral



CSM_DATAFILE_NAME = "csm_calibration.json"
#CSM_DATAFILE_PATH = data_file_path(CSM_DATAFILE_NAME)

MoveHistory = namedtuple("MoveHistory", ["times", "stage_positions"])
class LoggingMoveWrapper():
    """Wrap a move function, and maintain a log position/time.
    
    This class is callable, so it doesn't change the signature
    of the function it wraps - it just makes it possible to get
    a list of all the moves we've made, and how long they took.
    
    Said list is intended to be useful for calibrating the stage
    so we can estimate how long moves will take.
    """
    def __init__(self, move_function):
        self._move_function = move_function
        self._current_position = None
        self.clear_history()

    def __call__(self, new_position, *args, **kwargs):
        """Move to a new position, and record it"""
        self._history.append((time.time(), self._current_position))
        self._move_function(new_position, *args, **kwargs)
        self._current_position = new_position
        self._history.append((time.time(), self._current_position))

    @property
    def history(self):
        """The history, as a numpy array of times and another of positions"""
        times = np.array([t for t, p in self._history])
        positions = np.array([p for t, p in self._history])
        return MoveHistory(times, positions)

    def clear_history(self):
        """Reset our history to be an empty list"""
        self._history = []


class CSMExtension(object):
    """
    Use the camera as an encoder, so we can relate camera and stage coordinates
    """

    def __init__(self, parent):
        self._parent = parent 
    
    
    def update_settings(self, settings):
        """Update the stored extension settings dictionary"""
        pass 
    def get_settings(self):
        """Retrieve the settings for this extension"""
        return {}
    
    def camera_stage_functions(self):
        """Return functions that allow us to interface with the microscope"""
        grab_image = self._parent.detector.getLatestFrame
        
        def getPositionList():
            posDict = self._parent._master.positionersManager[self._parent._master.positionersManager.getAllDeviceNames()[0]].getPosition()
            return (posDict["X"], posDict["Y"], posDict["Z"])
        
        def movePosition(posList):
            stage = self._parent._master.positionersManager[self._parent._master.positionersManager.getAllDeviceNames()[0]]
            stage.move(value=posList[0], axis="X", is_absolute=True, is_blocking=True)
            stage.move(value=posList[1], axis="Y", is_absolute=True, is_blocking=True)
            if len(posList)>2:
                stage.move(value=posList[2], axis="Z", is_absolute=True, is_blocking=True)
            
        get_position = getPositionList
        move = movePosition
        wait = time.sleep(0.1)

        return grab_image, get_position, move, wait

    def calibrate_1d(self, direction):
        """Move a microscope's stage in 1D, and figure out the relationship with the camera"""
        grab_image, get_position, move, wait = self.camera_stage_functions()
        move = LoggingMoveWrapper(move)  # log positions and times for stage calibration

        tracker = Tracker(grab_image, get_position, settle=wait)

        result = calibrate_backlash_1d(tracker, move, direction)
        result["move_history"] = move.history
        return result

    def calibrate_xy(self):
        """Move the microscope's stage in X and Y, to calibrate its relationship to the camera"""
        self._parent._logger.info("Calibrating X axis:")
        cal_x = self.calibrate_1d(np.array([1, 0, 0]))
        self._parent._logger.info("Calibrating Y axis:")
        cal_y = self.calibrate_1d(np.array([0, 1, 0]))
        
        # Combine X and Y calibrations to make a 2D calibration
        cal_xy = image_to_stage_displacement_from_1d([cal_x, cal_y])
        self.update_settings(cal_xy)

        data = {
            "camera_stage_mapping_calibration": cal_xy,
            "linear_calibration_x": cal_x,
            "linear_calibration_y": cal_y,
        }


        return data

    @property
    def image_to_stage_displacement_matrix(self):
        """A 2x2 matrix that converts displacement in image coordinates to stage coordinates."""
        try:
            settings = self.get_settings()
            return settings["image_to_stage_displacement"]
        except KeyError:
            raise ValueError("The microscope has not yet been calibrated.")

    def move_in_image_coordinates(self, displacement_in_pixels):
        """Move by a given number of pixels on the camera"""
        p = np.array(displacement_in_pixels)
        relative_move = np.dot(p, self.image_to_stage_displacement_matrix)
        self.microscope.stage.move_rel([relative_move[0], relative_move[1], 0])

    def closed_loop_move_in_image_coordinates(self, displacement_in_pixels, **kwargs):
        """Move by a given number of pixels on the camera, using the camera as an encoder."""
        grab_image, get_position, move, wait = self.camera_stage_functions()

        tracker = Tracker(grab_image, get_position, settle=wait)
        tracker.acquire_template()
        closed_loop_move(tracker, self.move_in_image_coordinates, displacement_in_pixels, **kwargs)

    def closed_loop_scan(self, scan_path, **kwargs):
        """Perform closed-loop moves to each point defined in scan_path.

        This returns a generator, which will move the stage to each point in
        ``scan_path``, then yield ``i, pos`` where ``i``
        is the index of the scan point, and ``pos`` is the estimated position
        in pixels relative to the starting point.  To use it properly, you 
        should iterate over it, for example::
        
            for i, pos in csm_extension.closed_loop_scan(scan_path):
                capture_image(f"image_{i}.jpg")

        ``scan_path`` should be an Nx2 numpy array defining
        the points to visit in pixels relative to the current position.

        If an exception occurs during the scan, we automatically return to the
        starting point.  Keyword arguments are passed to 
        ``closed_loop_move.closed_loop_scan``.
        """
        grab_image, get_position, move, wait = self.camera_stage_functions()

        tracker = Tracker(grab_image, get_position, settle=wait)
        tracker.acquire_template()

        return closed_loop_scan(tracker, self.move_in_image_coordinates, move, np.array(scan_path), **kwargs)


    def test_closed_loop_spiral_scan(self, step_size, N, **kwargs):
        """Move the microscope in a spiral scan, and return the positions."""
        scan_path = ordered_spiral(0,0, N, *step_size)

        for i, pos in self.closed_loop_scan(np.array(scan_path), **kwargs):
            pass



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
