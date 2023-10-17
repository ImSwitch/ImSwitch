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


class FocusLockController(ImConWidgetController):
    """Linked to FocusLockWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self)

        if self._setupInfo.focusLock is None:
            return

        self.camera = self._setupInfo.focusLock.camera
        self.positioner = self._setupInfo.focusLock.positioner
        self.updateFreq = self._setupInfo.focusLock.updateFreq
        if self.updateFreq is None:
            self.updateFreq = 10
        self.cropFrame = (self._setupInfo.focusLock.frameCropx,
                          self._setupInfo.focusLock.frameCropy,
                          self._setupInfo.focusLock.frameCropw,
                          self._setupInfo.focusLock.frameCroph)
        
        if self.cropFrame[0] is not None:
            self._master.detectorsManager[self.camera].crop(*self.cropFrame)
        self._widget.setKp(self._setupInfo.focusLock.piKp)
        self._widget.setKi(self._setupInfo.focusLock.piKi)
        try:
            self.focusLockMetric = self._setupInfo.focusLockMetric
        except:
            self.focusLockMetric = "JPG"

        # Connect FocusLockWidget buttons
        self._widget.kpEdit.textChanged.connect(self.unlockFocus)
        self._widget.kiEdit.textChanged.connect(self.unlockFocus)

        self._widget.lockButton.clicked.connect(self.toggleFocus)
        self._widget.camDialogButton.clicked.connect(self.cameraDialog)
        self._widget.focusCalibButton.clicked.connect(self.focusCalibrationStart)
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
        self.focusTime = 1000 / self.updateFreq  # focus signal update interval (ms)
        self.zStepLimLo = 0
        self.aboutToLockDiffMax = 0.4
        self.lockPosition = 0
        self.currentPosition = 0
        self.lastPosition = 0
        self.buffer = 40
        self.currPoint = 0
        self.setPointData = np.zeros(self.buffer)
        self.timeData = np.zeros(self.buffer)

        self._master.detectorsManager[self.camera].startAcquisition()
        self.__processDataThread = ProcessDataThread(self)
        self.__focusCalibThread = FocusCalibThread(self)
        self.__processDataThread.setFocusLockMetric(self.focusLockMetric)

        self.timer = Timer()
        self.timer.timeout.connect(self.update)
        self.timer.start(int(self.focusTime))
        self.startTime = perf_counter()

    def __del__(self):
        self.__processDataThread.quit()
        self.__processDataThread.wait()
        self.__focusCalibThread.quit()
        self.__focusCalibThread.wait()
        self.ESP32Camera.stopStreaming()
        if hasattr(super(), '__del__'):
            super().__del__()

    def unlockFocus(self):
        if self.locked:
            self.locked = False
            self._widget.lockButton.setChecked(False)
            self._widget.focusPlot.removeItem(self._widget.focusLockGraph.lineLock)

    def toggleFocus(self):
        self.aboutToLock = False
        if self._widget.lockButton.isChecked():
            zpos = self._master.positionersManager[self.positioner].get_abs()
            self.lockFocus(zpos)
            self._widget.lockButton.setText('Unlock')
        else:
            self.unlockFocus()
            self._widget.lockButton.setText('Lock')

    def cameraDialog(self):
        if not self.isESP32: self._master.detectorsManager[self.camera].openPropertiesDialog()

    def setGain(self, gain):
        self.ESP32Camera.setGain(gain)

    def setExposureTime(self, exposureTime):
        self.ESP32Camera.setExposureTime(exposureTime)
        
    def focusCalibrationStart(self):
        self.__focusCalibThread.start()

    def showCalibrationCurve(self):
        self._widget.showCalibrationCurve(self.__focusCalibThread.getData())

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
            value_move = self.updatePI()
            if self.noStepVar and abs(value_move) > 0.002:
                self._master.positionersManager[self.positioner].move(value_move, 0)
        elif self.aboutToLock:
           self.aboutToLockUpdate()
        # udpate graphics
        self.updateSetPointData()
        self._widget.camImg.setImage(img)
        if self.currPoint < self.buffer:
            self._widget.focusPlotCurve.setData(self.timeData[1:self.currPoint],
                                                self.setPointData[1:self.currPoint])
        else:
            self._widget.focusPlotCurve.setData(self.timeData, self.setPointData)
    
    def aboutToLockUpdate(self):
        self.aboutToLockDataPoints = np.roll(self.aboutToLockDataPoints,1)
        self.aboutToLockDataPoints[0] = self.setPointSignal
        averageDiff = np.std(self.aboutToLockDataPoints)
        if averageDiff < self.aboutToLockDiffMax:
            zpos = self._master.positionersManager[self.positioner].get_abs()
            self.lockFocus(zpos)
            self.aboutToLock = False

    def updateSetPointData(self):
        if self.currPoint < self.buffer:
            self.setPointData[self.currPoint] = self.setPointSignal
            self.timeData[self.currPoint] = perf_counter() - self.startTime
        else:
            self.setPointData = np.roll(self.setPointData, -1)
            self.setPointData[-1] = self.setPointSignal
            self.timeData = np.roll(self.timeData, -1)
            self.timeData[-1] = perf_counter() - self.startTime
        self.currPoint += 1

    def updatePI(self):
        if not self.noStepVar:
            self.noStepVar = True
        self.currentPosition = self._master.positionersManager[self.positioner].get_abs()
        self.stepDistance = np.abs(self.currentPosition - self.lastPosition)
        distance = self.currentPosition - self.lockPosition
        move = self.pi.update(self.setPointSignal)
        self.lastPosition = self.currentPosition

        if abs(distance) > 5 or abs(move) > 3:
            self._logger.warning(f'Safety unlocking! Distance to lock: {distance:.3f}, current move step: {move:.3f}.')
            self.unlockFocus()
        elif self.zStackVar:
            if self.stepDistance > self.zStepLimLo:
                self.unlockFocus()
                self.aboutToLockDataPoints = np.zeros(5)
                self.aboutToLock = True
                self.noStepVar = False
        return move

    def lockFocus(self, zpos):
        if not self.locked:
            kp = float(self._widget.kpEdit.text())
            ki = float(self._widget.kiEdit.text())
            self.pi = PI(self.setPointSignal, 0.001, kp, ki)
            self.lockPosition = zpos
            self.locked = True
            self._widget.focusLockGraph.lineLock = self._widget.focusPlot.addLine(
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
        self.focusLockMetric = None
        

    def grabCameraFrame(self):
        detectorManager = self._controller._master.detectorsManager[self._controller.camera]
        self.latestimg = detectorManager.getLatestFrame()
            
        # 1.5 swap axes of frame (depending on setup, make this a variable in the json)
        if self._controller._setupInfo.focusLock.swapImageAxes:
            self.latestimg = np.swapaxes(self.latestimg,0,1)
        return self.latestimg
    
    def setFocusLockMetric(self, focuslockMetric):
        self.focusLockMetric = focuslockMetric

    def update(self, twoFociVar):

        if self._controller._master.detectorsManager[self._controller.camera].model == "ESP32SerialCamera":
            imagearraygf = ndi.filters.gaussian_filter(self.latestimg, 5)
            # mBackground = np.mean(mStack, (0)) #np.ones(mStack.shape[1:])# 
            mBackground = ndi.filters.gaussian_filter(self.latestimg,15)
            mFrame = imagearraygf/mBackground # mStack/mBackground
            massCenterGlobal=np.max(np.mean(mFrame**2, 1))/np.max(np.mean(mFrame**2, 0))
            
        else:
            if self.focusLockMetric == "JPG":

                def extract(marray, crop_size):
                    center_x, center_y = marray.shape[1] // 2, marray.shape[0] // 2

                    # Calculate the starting and ending indices for cropping
                    x_start = center_x - crop_size // 2
                    x_end = x_start + crop_size
                    y_start = center_y - crop_size // 2
                    y_end = y_start + crop_size

                    # Crop the center region
                    return marray[y_start:y_end, x_start:x_end]
                imagearraygf = extract(self.latestimg, 512)
                is_success, buffer = cv2.imencode(".jpg", imagearraygf, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                # Check if encoding was successful
                if is_success:
                    # Get the size of the JPEG image
                    focusquality = len(buffer)
                else:
                    focusquality = 0
                    print("Failed to encode image")
                massCenterGlobal = focusquality
            else:
                # Gaussian filter the image, to remove noise and so on, to get a better center estimate
                imagearraygf = ndi.filters.gaussian_filter(self.latestimg, 7)

                # Update the focus signal
                if twoFociVar:
                        allmaxcoords = peak_local_max(imagearraygf, min_distance=60)
                        size = allmaxcoords.shape
                        maxvals = np.zeros(size[0])
                        maxvalpos = np.zeros(2)
                        for n in range(0, size[0]):
                            if imagearraygf[allmaxcoords[n][0], allmaxcoords[n][1]] > maxvals[0]:
                                if imagearraygf[allmaxcoords[n][0], allmaxcoords[n][1]] > maxvals[1]:
                                    tempval = maxvals[1]
                                    maxvals[0] = tempval
                                    maxvals[1] = imagearraygf[allmaxcoords[n][0], allmaxcoords[n][1]]
                                    tempval = maxvalpos[1]
                                    maxvalpos[0] = tempval
                                    maxvalpos[1] = n
                                else:
                                    maxvals[0] = imagearraygf[allmaxcoords[n][0], allmaxcoords[n][1]]
                                    maxvalpos[0] = n
                        xcenter = allmaxcoords[maxvalpos[0]][0]
                        ycenter = allmaxcoords[maxvalpos[0]][1]
                        if allmaxcoords[maxvalpos[1]][1] < ycenter:
                            xcenter = allmaxcoords[maxvalpos[1]][0]
                            ycenter = allmaxcoords[maxvalpos[1]][1]
                        centercoords2 = np.array([xcenter, ycenter])
                else:
                    centercoords = np.where(imagearraygf == np.array(imagearraygf.max()))
                    centercoords2 = np.array([centercoords[0][0], centercoords[1][0]])

                subsizey = 50
                subsizex = 50
                xlow = max(0, (centercoords2[0] - subsizex))
                xhigh = min(1024, (centercoords2[0] + subsizex))
                ylow = max(0, (centercoords2[1] - subsizey))
                yhigh = min(1280, (centercoords2[1] + subsizey))

                imagearraygfsub = imagearraygf[xlow:xhigh, ylow:yhigh]
                massCenter = np.array(ndi.measurements.center_of_mass(imagearraygfsub))
                # add the information about where the center of the subarray is
                massCenterGlobal = massCenter[1] + centercoords2[1]  # - subsizey - self.sensorSize[1] / 2
        return massCenterGlobal


class FocusCalibThread(Thread):
    def __init__(self, controller, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._controller = controller

    def run(self):
        self.signalData = []
        self.positionData = []
        self.fromVal = float(self._controller._widget.calibFromEdit.text())
        self.toVal = float(self._controller._widget.calibToEdit.text())
        self.scan_list = np.round(np.linspace(self.fromVal, self.toVal, 20), 2)
        for z in self.scan_list:
            self._controller._master.positionersManager[self._controller.positioner].setPosition(z, 0)
            time.sleep(0.5)
            self.focusCalibSignal = self._controller.setPointSignal
            self.signalData.append(self.focusCalibSignal)
            self.positionData.append(self._controller._master.positionersManager[self._controller.positioner].get_abs())
        self.poly = np.polyfit(self.positionData, self.signalData, 1)
        self.calibrationResult = np.around(self.poly, 4)
        self.show()

    def show(self):
        cal_nm = np.round(1000 / self.poly[0], 1)
        calText = f'1 px --> {cal_nm} nm'
        self._controller._widget.calibrationDisplay.setText(calText)

    def getData(self):
        data = {
            'signalData': self.signalData,
            'positionData': self.positionData,
            'poly': self.poly
        }
        return data


class PI:
    """Simple implementation of a discrete PI controller.
    Taken from http://code.activestate.com/recipes/577231-discrete-pid-controller/
    Author: Federico Barabas"""
    def __init__(self, setPoint, multiplier=1, kp=0, ki=0):
        self._kp = multiplier * kp
        self._ki = multiplier * ki
        self._setPoint = setPoint
        self.multiplier = multiplier
        self.error = 0.0
        self._started = False

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
        return self.out

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

