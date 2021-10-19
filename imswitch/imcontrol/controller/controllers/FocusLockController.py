import time

import numpy as np
import pyqtgraph.ptime as ptime
import scipy.ndimage as ndi
from lantz import Q_
from skimage.feature import peak_local_max

from imswitch.imcommon.framework import Thread, Timer
from imswitch.imcommon.model import initLogger
from ..basecontrollers import ImConWidgetController


class FocusLockController(ImConWidgetController):
    """Linked to FocusLockWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        if self._setupInfo.focusLock is None:
            return

        self.camera = self._setupInfo.focusLock.camera
        self.positioner = self._setupInfo.focusLock.positioner
        self.updateFreq = self._setupInfo.focusLock.updateFreq
        self.cropFrame = (self._setupInfo.focusLock.frameCropx,
                          self._setupInfo.focusLock.frameCropy,
                          self._setupInfo.focusLock.frameCropw,
                          self._setupInfo.focusLock.frameCroph)
        self._master.detectorsManager[self.camera].crop(*self.cropFrame)

        # Connect FocusLockWidget buttons
        self._widget.kpEdit.textChanged.connect(self.unlockFocus)
        self._widget.kiEdit.textChanged.connect(self.unlockFocus)

        self._widget.lockButton.clicked.connect(self.toggleFocus)
        self._widget.camDialogButton.clicked.connect(self.cameraDialog)
        self._widget.positionSetButton.clicked.connect(self.moveZ)
        self._widget.focusCalibButton.clicked.connect(self.focusCalibrationStart)
        self._widget.calibCurveButton.clicked.connect(self.showCalibrationCurve)

        self._widget.zStackBox.stateChanged.connect(self.zStackVarChange)
        self._widget.twoFociBox.stateChanged.connect(self.twoFociVarChange)

        self.setPointSignal = 0
        self.locked = False
        self.aboutToLock = False
        self.zStackVar = False
        self.twoFociVar = False
        self.noStepVar = True
        self.focusTime = 1000 / self.updateFreq  # time between focus signal updates in ms
        self.lockPosition = 0
        self.currentPosition = 0
        self.lastZ = 0
        self.buffer = 40
        self.currPoint = 0
        self.setPointData = np.zeros(self.buffer)
        self.timeData = np.zeros(self.buffer)
        self.lockingData = np.zeros(7)

        self._master.detectorsManager[self.camera].startAcquisition()
        self.__processDataThread = ProcessDataThread(self)

        self.timer = Timer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self.focusTime)
        self.startTime = ptime.time()

    def __del__(self):
        self.__processDataThread.quit()
        self.__processDataThread.wait()
        if hasattr(super(), '__del__'):
            super().__del__()

    def unlockFocus(self):
        if self.locked:
            self.locked = False
            self._widget.lockButton.setChecked(False)
            self._widget.focusPlot.removeItem(self._widget.focusLockGraph.lineLock)

    def toggleFocus(self):
        if self._widget.lockButton.isChecked():
            absz = self._master.positionersManager[self.positioner].get_abs()
            self.lockFocus(float(self._widget.kpEdit.text()),
                           float(self._widget.kiEdit.text()),
                           absz)
            self._widget.lockButton.setText('Unlock')
        else:
            self.unlockFocus()
            self._widget.lockButton.setText('Lock')

    def cameraDialog(self):
        self._master.detectorsManager[self.camera].openPropertiesDialog()
        self.__logger.debug('Open camera settings dialog')

    def moveZ(self):
        abspos = float(self._widget.positionEdit.text())
        self._master.positionersManager[self.positioner].setPosition(abspos, 0)
        self.__logger.debug(f'Move Z-piezo to absolute position {abspos} um')

    def focusCalibrationStart(self):
        self.__logger.debug('Start focus calibration thread and calibrate')

    def showCalibrationCurve(self):
        self.__logger.debug('Show calibration curve')

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

    # Update focus lock
    def update(self):
        # 1 Grab camera frame
        img = self.__processDataThread.grabCameraFrame()
        # 2 Pass camera frame and get back focusSignalPosition from ProcessDataThread
        self.setPointSignal = self.__processDataThread.update(self.twoFociVar)
        # 3 Update PI with the new setPointSignal and get back the distance to move, send to
        # update the PI control, and then send the move-distance to the z-piezo
        if self.locked:
            value_move = self.updatePI()
            if self.noStepVar and abs(value_move) > 0.002:
                # self.zstepupdate = self.zstepupdate + 1
                self._master.positionersManager[self.positioner].move(value_move, 0)
        # elif self.aboutToLock:
        #    self.lockingPI()
        # 4 Update image and focusSignalPosition in FocusLockWidget
        self.updateSetPointData()
        self._widget.camImg.setImage(img)
        if self.currPoint < self.buffer:
            self._widget.focusPlotCurve.setData(self.timeData[1:self.currPoint],
                                                self.setPointData[1:self.currPoint])
        else:
            self._widget.focusPlotCurve.setData(self.timeData, self.setPointData)

    def updateSetPointData(self):
        if self.currPoint < self.buffer:
            self.setPointData[self.currPoint] = self.setPointSignal
            self.timeData[self.currPoint] = ptime.time() - self.startTime
        else:
            self.setPointData[:-1] = self.setPointData[1:]
            self.setPointData[-1] = self.setPointSignal
            self.timeData[:-1] = self.timeData[1:]
            self.timeData[-1] = ptime.time() - self.startTime
        self.currPoint += 1

    def updatePI(self):
        if not self.noStepVar:
            self.noStepVar = True
        self.currentPosition = self._master.positionersManager[self.positioner].get_abs()
        distance = self.currentPosition - self.lockPosition
        move = self.pi.update(self.setPointSignal)
        self.lastZ = self.currentPosition

        if abs(distance) > 5 or abs(move) > 3:
            self.__logger.debug(f'Safety unlocking! Distance: {distance}, move: {move}.')
            self.unlockFocus()

        return move

    def lockFocus(self, kp, ki, absz):
        if not self.locked:
            self.pi = PI(self.setPointSignal, 0.001, kp, ki)
            self.lockPosition = absz
            self.locked = True
            self._widget.focusLockGraph.lineLock = self._widget.focusPlot.addLine(
                y=self.setPointSignal, pen='r'
            )


class ProcessDataThread(Thread):
    def __init__(self, controller, *args, **kwargs):
        self._controller = controller
        super().__init__(*args, **kwargs)

    def grabCameraFrame(self):
        detectorManager = self._controller._master.detectorsManager[self._controller.camera]
        self.latestimg = detectorManager.getLatestFrame()
        return self.latestimg

    def update(self, twoFociVar):
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
    def __init__(self, focusWidget, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.z = focusWidget.z
        self.focusWidget = focusWidget  # mainwidget será FocusLockWidget
        self.um = Q_(1, 'micrometer')

    def run(self):
        self.signalData = []
        self.positionData = []
        self.start = float(self.focusWidget.CalibFromEdit.text())
        self.end = float(self.focusWidget.CalibToEdit.text())
        self.scan_list = np.round(np.linspace(self.start, self.end, 20), 2)
        for x in self.scan_list:
            self.z.move_absZ(x * self.um)
            time.sleep(0.5)
            self.focusCalibSignal = \
                self.focusWidget.processDataThread.focusSignal
            self.signalData.append(self.focusCalibSignal)
            self.positionData.append(self.z.absZ.magnitude)

        self.poly = np.polyfit(self.positionData, self.signalData, 1)
        self.calibrationResult = np.around(self.poly, 4)
        self.export()

    def export(self):
        np.savetxt('calibration.txt', self.calibrationResult)
        cal = self.poly[0]
        calText = '1 px --> {} nm'.format(np.round(1000 / cal, 1))
        self.focusWidget.calibrationDisplay.setText(calText)
        d = [self.positionData, self.calibrationResult[::-1]]
        self.savedCalibData = [self.positionData,
                               self.signalData,
                               np.polynomial.polynomial.polyval(d[0], d[1])]
        np.savetxt('calibrationcurves.txt', self.savedCalibData)


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
        """
        Calculate PID output value for given reference input and feedback.
        I'm using the iterative formula to avoid integrative part building.
        ki, kp > 0
        """
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
