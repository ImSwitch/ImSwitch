import time
import cv2 
import numpy as np
from time import perf_counter
import scipy.ndimage as ndi
from skimage.feature import peak_local_max

import numpy as np
import matplotlib.pyplot as plt
import tifffile as tif
import serial
import time
import serial.tools.list_ports
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import base64
import io
import serial.tools.list_ports
import threading

from imswitch.imcommon.framework import Thread, Timer
from imswitch.imcommon.model import initLogger
from ..basecontrollers import ImConWidgetController


class FOVLockController(ImConWidgetController):
    """Linked to FOVLockWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self)

        if self._setupInfo.fovLock is None:
            return

        self.camera = self._setupInfo.fovLock.camera
        self.positioner = self._setupInfo.fovLock.positioner
        self.updateFreq = self._setupInfo.fovLock.updateFreq
        if self.updateFreq is None:
            self.updateFreq = 1
        self.cropFrame = (self._setupInfo.fovLock.frameCropx,
                          self._setupInfo.fovLock.frameCropy,
                          self._setupInfo.fovLock.frameCropw,
                          self._setupInfo.fovLock.frameCroph)
        
        if self.cropFrame[0] is not None:
            self._master.detectorsManager[self.camera].crop(*self.cropFrame)
        self._widget.setKp(self._setupInfo.fovLock.piKp)
        self._widget.setKi(self._setupInfo.fovLock.piKi)
        try:
            self.fovLockMetric = self._setupInfo.fovLockMetric
        except:
            self.fovLockMetric = "JPG"

        # Connect FOVLockWidget buttons
        self._widget.kpEdit.textChanged.connect(self.unlockFOV)
        self._widget.kiEdit.textChanged.connect(self.unlockFOV)

        self._widget.lockButton.clicked.connect(self.toggleFOV)
        self._widget.camDialogButton.clicked.connect(self.cameraDialog)
        self._widget.fovCalibButton.clicked.connect(self.fovCalibrationStart)
        self._widget.calibCurveButton.clicked.connect(self.showCalibrationCurve)

        self._widget.zStackBox.stateChanged.connect(self.zStackVarChange)
        self._widget.twoFociBox.stateChanged.connect(self.twoFociVarChange)
        
        self._widget.sigSliderExpTValueChanged.connect(self.setExposureTime)
        self._widget.sigSliderGainValueChanged.connect(self.setGain)


        self.setPointSignal = 0
        self.locked = False
        self.aboutToLock = False
        self.zStackVar = False
        self.twoFociVar = False
        self.noStepVar = True
        self.fovTime = 1000 / self.updateFreq  # fov signal update interval (ms)
        self.zStepLimLo = 0
        self.aboutToLockDiffMax = 0.4
        self.lockPosition = 0
        self.currentPosition = 0
        self.lastPosition = 0
        self.buffer = 40
        self.currPoint = 0
        self.setPointDataX = np.zeros(self.buffer)
        self.setPointDataY = np.zeros(self.buffer)
        self.timeData = np.zeros(self.buffer)

        self._master.detectorsManager[self.camera].startAcquisition()
        self.__processDataThread = ProcessDataThread(self)
        self.__fovCalibThread = FOVCalibThread(self)
        self.__processDataThread.setFOVLockMetric(self.fovLockMetric)

        self.timer = Timer()
        self.timer.timeout.connect(self.update)
        self.timer.start(int(self.fovTime))
        self.startTime = perf_counter()

    def __del__(self):
        self.__processDataThread.quit()
        self.__processDataThread.wait()
        self.__fovCalibThread.quit()
        self.__fovCalibThread.wait()
        self.ESP32Camera.stopStreaming()
        if hasattr(super(), '__del__'):
            super().__del__()

    def unlockFOV(self):
        if self.locked:
            self.locked = False
            self._widget.lockButton.setChecked(False)
            self._widget.fovPlot.removeItem(self._widget.fovLockGraph.lineLock)

    def toggleFOV(self):
        self.aboutToLock = False
        if self._widget.lockButton.isChecked():
            positions = self._master.positionersManager[self.positioner].getPosition()
            self.lockFOV(positions)
            self._widget.lockButton.setText('Unlock')
        else:
            self.unlockFOV()
            self._widget.lockButton.setText('Lock')

    def cameraDialog(self):
        if not self.isESP32: self._master.detectorsManager[self.camera].openPropertiesDialog()

    def setGain(self, gain):
        self.ESP32Camera.setGain(gain)

    def setExposureTime(self, exposureTime):
        self.ESP32Camera.setExposureTime(exposureTime)
        
    def fovCalibrationStart(self):
        self.__fovCalibThread.startThread()

    def showCalibrationCurve(self):
        self._widget.showCalibrationCurve(self.__fovCalibThread.getData())

    def zStackVarChange(self):
        if self.zStackVar:
            self.zStackVar = False
        else:
            self.zStackVar = True

    def twoFociVarChange(self):
        if self.twoFociVar:
            self.twoFociVar = False
        else:
            self.twoFociVar = True

    def update(self):
        # get data
        img = self.__processDataThread.grabCameraFrame()
        self.setPointSignal = self.__processDataThread.update(self.twoFociVar)
        
        # move
        if self.locked:
            '''
            compute the value to move the positioner
            '''
            
            value_move = self.updatePI()
            if self.noStepVar and abs(value_move) > 0.002:
                self._master.positionersManager[self.positioner].move(value_move, 0)
        elif self.aboutToLock:
           self.aboutToLockUpdate()
        # udpate graphics
        self.updateSetPointData()
        self._widget.camImg.setImage(img)
        if self.currPoint < self.buffer:
            self._widget.fovPlotCurveX.setData(self.timeData[1:self.currPoint],
                                                self.setPointDataX[1:self.currPoint])
            self._widget.fovPlotCurveY.setData(self.timeData[1:self.currPoint],
                                                self.setPointDataY[1:self.currPoint])
        else:
            self._widget.fovPlotCurveX.setData(self.timeData, self.setPointDataX)
            self._widget.fovPlotCurveY.setData(self.timeData, self.setPointDataY)
    
    def aboutToLockUpdate(self):
        self.aboutToLockDataPoints = np.roll(self.aboutToLockDataPoints,1)
        self.aboutToLockDataPoints[0] = self.setPointSignal
        averageDiff = np.std(self.aboutToLockDataPoints)
        if averageDiff < self.aboutToLockDiffMax:
            zpos = self._master.positionersManager[self.positioner].get_abs()
            self.lockFOV(zpos)
            self.aboutToLock = False

    def updateSetPointData(self):
        if self.currPoint < self.buffer:
            self.setPointDataX[self.currPoint] = self.setPointSignal[0][0]
            self.setPointDataY[self.currPoint] = self.setPointSignal[0][1]
            self.timeData[self.currPoint] = perf_counter() - self.startTime
        else:
            self.setPointDataX = np.roll(self.setPointDataX, -1)
            self.setPointDataY = np.roll(self.setPointDataY, -1)
            self.setPointDataX[-1] = self.setPointSignal[0][0]
            self.setPointDataY[-1] = self.setPointSignal[0][1]
            self.timeData = np.roll(self.timeData, -1)
            self.timeData[-1] = perf_counter() - self.startTime
        self.currPoint += 1

    def updatePI(self):
        if not self.noStepVar:
            self.noStepVar = True
        self.currentPosition = self._master.positionersManager[self.positioner].getposition()
        self.stepDistance = np.abs(self.currentPosition - self.lastPosition)
        distance = self.currentPosition - self.lockPosition
        
        move = self.pi.update(self.setPointSignal)
        self.lastPosition = self.currentPosition

        if abs(distance) > 5 or abs(move) > 3:
            self._logger.warning(f'Safety unlocking! Distance to lock: {distance:.3f}, current move step: {move:.3f}.')
            self.unlockFOV()
        elif self.zStackVar:
            if self.stepDistance > self.zStepLimLo:
                self.unlockFOV()
                self.aboutToLockDataPoints = np.zeros(5)
                self.aboutToLock = True
                self.noStepVar = False

        return move

    def lockFOV(self, zpos):
        if not self.locked:
            self.__processDataThread.setInitialFrame()
            kp = float(self._widget.kpEdit.text())
            ki = float(self._widget.kiEdit.text())
            avg_pixel_per_step = self.__fovCalibThread.getData()
            self.pi = PI(self.setPointSignal, 0.001, kp, ki, avg_pixel_per_step)
            self.lockPosition = zpos
            self.locked = True
            self._widget.fovLockGraph.lineLock = self._widget.fovPlot.addLine(
                y=self.setPointSignal, pen='r'
            )
            self._widget.lockButton.setChecked(True)
            self.updateZStepLimits()

    def updateZStepLimits(self):
        self.zStepLimLo = 0.001 * float(self._widget.zStepFromEdit.text())


class ProcessDataThread(Thread):
    def __init__(self, controller, *args, **kwargs):
        self._controller = controller
        super().__init__(*args, **kwargs)
        self.fovLockMetric = None
        self.latestimg = None
        self.lastimg = None
        
    def setInitialFrame(self):
        detectorManager = self._controller._master.detectorsManager[self._controller.camera]
        self.latestimg = detectorManager.getLatestFrame()
        self.lastimg = self.latestimg.copy()
        return self.lastimg

    def grabCameraFrame(self):
        detectorManager = self._controller._master.detectorsManager[self._controller.camera]
        self.latestimg = detectorManager.getLatestFrame()
            
        # 1.5 swap axes of frame (depending on setup, make this a variable in the json)
        if self._controller._setupInfo.fovLock.swapImageAxes:
            self.latestimg = np.swapaxes(self.latestimg,0,1)
        return self.latestimg
    
    def setFOVLockMetric(self, fovlockMetric):
        self.fovLockMetric = fovlockMetric

    def update(self, twoFociVar):
        def extract(marray, crop_size):
            center_x, center_y = marray.shape[1] // 2, marray.shape[0] // 2

            # Calculate the starting and ending indices for cropping
            x_start = center_x - crop_size // 2
            x_end = x_start + crop_size
            y_start = center_y - crop_size // 2
            y_end = y_start + crop_size

            # Crop the center region
            return marray[y_start:y_end, x_start:x_end]


        self.latestimg = extract(self.latestimg, 512)
        # Load images
        if self.lastimg is None:
            self.lastimg = self.latestimg.copy()

        if 0:
            pixelShift = self.find_shift_feature_based(self.lastimg, self.latestimg)
            print(f"Shift (Feature-Based): {shift_feature_based}")
        elif 1:
            img1 = np.float32(self.lastimg)
            img2 = np.float32(self.latestimg)

            # Compute cross correlation
            (pixelShiftX, pixelShiftY), pixelShift = cv2.phaseCorrelate(img1, img2)
        else:
            pixelShift = 0

        return (pixelShiftX, pixelShiftY), pixelShift 


    def find_shift_feature_based(self, image1, image2):
        # Initialize ORB detector
        orb = cv2.ORB_create()

        # Find the keypoints and descriptors with ORB
        kp1, des1 = orb.detectAndCompute(image1, None)
        kp2, des2 = orb.detectAndCompute(image2, None)

        # Match features.
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = matcher.match(des1, des2)

        # Extract location of good matches
        points1 = np.zeros((len(matches), 2), dtype=np.float32)
        points2 = np.zeros_like(points1)

        for i, match in enumerate(matches):
            points1[i, :] = kp1[match.queryIdx].pt
            points2[i, :] = kp2[match.trainIdx].pt

        # Find shift
        shift = np.mean(points2 - points1, axis=0)
        return shift



class FOVCalibThread(object):
    def __init__(self, controller, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._controller = controller

        self.detectorManager = self._controller._master.detectorsManager[self._controller.camera]
        self.positioner = self._controller._master.positionersManager[self._controller.positioner]
        self.initial_position = None
        self.latestimg = None
        self.avg_pixel_per_step = 1
        
    def move_stage(self, steps, axis = "X", isAbsolute = False):
        self.positioner.move(value=steps, axis=axis, is_absolute=isAbsolute, is_blocking=True)

    def capture_image(self):
        self.latestimg = self.detectorManager.getLatestFrame()
        return self.latestimg

    def calculate_pixel_shift(self, img1, img2):
        self._controller._logger.info('Calculating pixel shift')
        (pixelShiftX, pixelShiftY), pixelShift = cv2.phaseCorrelate(np.float32(img1), np.float32(img2))    
        self._controller._logger.info('Done')
        return pixelShiftX, pixelShiftY
    
    def startThread(self):
        import threading
        self.mThread = threading.Thread(target=self.runCalibration)
        self.mThread.start()
    
    def runCalibration(self):
        self._controller._logger.info('Starting FOV calibration')
        self.signalData = []
        self.positionData = []
        self.fromVal = float(self._controller._widget.calibFromEdit.text())
        self.toVal = float(self._controller._widget.calibToEdit.text())
        self.scan_list = np.round(np.linspace(self.fromVal, self.toVal, 20), 2)
        initial_position = self.positioner.getPosition()['X']
        
        pixel_displacements = []
        self._controller._logger.info(self.scan_list)
        steps = 0
        step = self.fromVal
        for iStep in range(10):
            self._controller._logger.info('Moving stage to %s' % step)
            self.move_stage(step, isAbsolute=False)  # Move the stage
            time.sleep(0.5) # let settle
            self._controller._logger.info('Capturing image')
            moved_image = self.capture_image()
            if len(moved_image.shape)==3:
                moved_image = np.mean(moved_image, -1)
            if iStep > 0:
                # Calculate pixel displacement here.
                # This function should be defined based on how you can compare images.
                self._controller._logger.info('Calculating pixel shift')
                (pixel_shiftX, pixel_shiftY) = self.calculate_pixel_shift(self.last_image, moved_image)
                pixel_displacements.append((pixel_shiftX/step, pixel_shiftY/step))
                self._controller._logger.info('PixelShift: %s / %s', str(pixel_shiftX/step), str(pixel_shiftY/step))
            steps += step
            self.last_image = moved_image.copy()  # Capture initial position
        # Return to the zero position
        self.move_stage(initial_position, isAbsolute=True)

        # Calculate average pixel-per-step
        self.avg_pixel_per_step = np.mean(np.array(pixel_displacements), 0)
        self.avg_pixel_per_step = np.round(self.avg_pixel_per_step, 1)
        self.show(self.avg_pixel_per_step)

    def show(self, step_to_pixel):
        # limit to one decimal
        calText = f'1 px --> {step_to_pixel} steps'
        self._controller._logger.info(calText)
        self._controller._widget.calibrationDisplay.setText(calText)

    def getData(self):
        return self.avg_pixel_per_step


class PI:
    """Simple implementation of a discrete PI controller.
    Taken from http://code.activestate.com/recipes/577231-discrete-pid-controller/
    Author: Federico Barabas"""
    def __init__(self, setPoint, multiplier=1, kp=0, ki=0, avg_pixel_per_step=1):
        self._kp = multiplier * kp
        self._ki = multiplier * ki
        self._setPoint = setPoint
        self.multiplier = multiplier
        self.error = 0.0
        self._started = False
        self.avg_pixel_per_step = avg_pixel_per_step

    def update(self, currentValue):
        """ Calculate PI output value for given reference input and feedback.
        Using the iterative formula to avoid integrative part building. """
        self.error = self.setPoint - currentValue
        if self.started:
            self.dError = self.error - self.lastError
            self.out = self.out + self.kp * self.dError + self.ki * self.error
        else:
            # This only runs in the first step
            self.out = self.kp * self.error
            self.started = True
        self.lastError = self.error
        return self.out*self.avg_pixel_per_stepgithu
    

    def restart(self):
        self.started = False

    @property
    def started(self):
        return self._started

    @started.setter
    def started(self, value):
        self._started = value

    @property
    def setPoint(self):
        return self._setPoint

    @setPoint.setter
    def setPoint(self, value):
        self._setPoint = value

    @property
    def kp(self):
        return self._kp

    @kp.setter
    def kp(self, value):
        self._kp = value

    @property
    def ki(self):
        return self._ki

    @ki.setter
    def ki(self, value):
        self._ki = value
        






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

