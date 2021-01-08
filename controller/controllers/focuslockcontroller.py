# -*- coding: utf-8 -*-
"""
Created on Fri Jan 08 16:53:00 2021

@author: jonatanalvelid
"""

import pickle
import time
import threading

import numpy as np

from framework import Signal, Thread, Worker
from pyqtgraph.Qt import QtCore
from .basecontrollers import WidgetController
from model.managers.SLMManager import MaskMode, Direction, MaskChoice
from skimage.feature import peak_local_max
import pyqtgraph.ptime as ptime
import scipy.ndimage as ndi


class FocusLockController(WidgetController):
    """Linked to FocusLockWidget."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.loadPreset(self._defaultPreset)
        #self.scansPerS = self._setupInfo.focusLock.scansPerS
        self.scansPerS = 10

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
        self.focusTime = 1000 / self.scansPerS  # time between focus signal updates in ms
        self.initialZ = 0
        self.currentZ = 0
        self.lastZ = 0
        self.lockingData = np.zeros(7)
        self.__processDataThread = ProcessDataThread()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self._master.focusLockManager.focusTime)

    def unlockFocus(self):
        if self.locked:
            self.locked = False
            self._widget.lockButton.setChecked(False)
            self._widget.focusLockGraph.plot.removeItem(self._widget.focusLockGraph.lineLock)
    
    def toggleFocus(self):
        if self._widget.lockButton.isChecked():
            absz = self._master.piezozHelper.get_abs()
            self.lockFocus(np.float(self._widget.kpEdit.text()), np.float(self._widget.kiEdit.text()), absz)
            self._widget.lockButton.setText('Unlock')
        else:
            self.unlockFocus()
            self._widget.lockButton.setText('Lock')
        print("Controller: Toggle focus: unlock if locked, lock if unlocked. Also: change text on the lockButton.")

    def cameraDialog(self):
        self._master.cameraHelper.show_dialog()
        print("Controller: Open camera settings dialog.")

    def moveZ(self):
        print("Controller: Potentially connect this to moving the z-piezo, or otherwise take care of that only in the positioning widget and remove this button. Can still keep the text and update with a signal to the current Z-position.")

    def focusCalibrationStart(self):
        print("Controller: Start focus calibration thread and calibrate.")

    def showCalibrationCurve(self):
        print("Controller: Show calibration curve.")

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
        #1 Grab camera frame through cameraHelper
        img = self._master.cameraHelper.grab_image()
        #2 Pass camera frame and get back focusSignalPosition from ProcessDataThread
        self.setPointSignal = self.__processDataThread.update(img)
        #3 Update PI with the new setPointSignal and get back the distance to move, send to
        # update the PI control
        if self.locked:
            value_move = self.updatePI()
            if self.noStepVar and abs(out) > 0.002:
                self.zstepupdate = self.zstepupdate + 1
                self.z.move_relZ(out * self.um)
            self._master.piezozHelper.move_rel(value_move)
        #elif self.aboutToLock:
        #    self.lockingPI()
        #4 Send updated position to z-piezo
        #5 Update image and focusSignalPosition in FocusLockWidget
        self._widget.webcamGraph.update(self.image)
        self._widget.focusLockGraph.update(self.setPointSignal)

    #def lockingPI(self):
    #    self.lockingData[:-1] = self.lockingData[1:]
    #    self.lockingData[-1] = self.setPointSignal
    #    averageDiff = np.std(self.lockingData)
    #    if averageDiff < 0.4:
    #        absz = self._master.piezozHelper.get_abs()
    #        self.lockFocus(np.float(self._widget.kpEdit.text()), np.float(self._widget.kiEdit.text()), absz)
    #        self.aboutToLock = False

    def updatePI(self):
        if not self.noStepVar:
            self.noStepVar = True
        self.currentZ = self._master.piezozHelper.get_abs()
        distance = self.currentZ - self.initialZ
        #self.stepDistance = self.currentZ - self.lastZ
        out = self.PI.update(self.setPointSignal)
        self.lastZ = self.currentZ

        if abs(distance) > 5 or abs(out) > 3:
            print('Safety unlocking!')
            self.unlockFocus()
        
        return out

#        elif self.zStackVar and self.zstepupdate > 15:
#            if self.stepDistance > self.stepDistLow * self.um and self.stepDistance < self.stepDistHigh * self.um:
#                self.unlockFocus()
#                self.dataPoints = np.zeros(5)
#                self.averageDiff = 10
#                self.aboutToLock = True
#                self.t0 = time.time()
#                self.zsteptime = self.t0-self.t1
#                self.t1 = self.t0
#                self.noStepVar = False
        #if self.noStepVar and abs(out) > 0.002:
        #    self.zstepupdate = self.zstepupdate + 1
        #    self.z.move_relZ(out * self.um)
    #def loadPreset(self, preset):
    #    print('Loaded default focus lock settings.')

    #def initLock(self):
    #    if not self.locked:
    #        self.setPoint = self.processDataThread.focusSignal
    #        self.focusLockGraph.line = self.focusLockGraph.plot.addLine(
    #                                                y=self.setPoint, pen='r')
    #        self.PI = pi.PI(self.setPoint, 0.001,
    #                        np.float(self.kpEdit.text()),
    #                        np.float(self.kiEdit.text()))
    #        self.initialZ = self.z.absZ
    #        self.locked = True
    #        self.stepDistLow = 0.001 * np.float(self.zStepFromEdit.text())
    #        self.stepDistHigh = 0.001 * np.float(self.zStepToEdit.text())

    def lockFocus(self, kp, ki, absz):
        if not self.locked:
            self.setPointSignal = self.__processDataThread.focusSignal
            self.pi = pi.PI(self.setPoint, 0.001, kp, ki)
            self.initialZ = absz
            self.locked = True
            self._widget.focusLockGraph.lineLock = self._widget.focusLockGraph.plot.addLine(y=self.setPointSignal, pen='r')
        print("Manager: lock focus")

    def focusCalibrationStart(self):
        print("Manager: starting focus calibration thread")


class ProcessDataThread(QtCore.QThread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # set the camera
        #self.webcam = self.focusWidget.webcam
        # self.ws = {'vsub': 4, 'hsub': 4,
        #            'top': None, 'bot': None,
        #            'exposure_time': 10}
        # self.image = self.webcam.grab_image(vsub=self.ws['vsub'],
        #                                     hsub=self.ws['hsub'],
        #                                     top=self.ws['top'],
        #                                     bot=self.ws['bot'],
        #                                     exposure_time=self.ws[
        #                                     'exposure_time'])
        #self.image = self.webcam.grab_image()

        #self.sensorSize = np.array(self.image.shape)
        # print(self.sensorSize) #= (1024,1280)

        self.focusSignal = 0

    def update(self, img):
        self.updateFocusSignal(img)
        return self.focusSignal

    def updateFocusSignal(self, img):
        # update the focus signal
        print('Updating focus signal...')
        try:
            # self.image = self.webcam.grab_image(vsub=self.ws['vsub'],
            #                                     hsub=self.ws['hsub'],
            #                                     top=self.ws['top'],
            #                                     bot=self.ws['bot'])
#            then = time.time()
            self.image = self.webcam.grab_image()
#            now = time.time()
#            print("Focus: Whole grab image took:", now-then, "seconds.")
            # print("")
        except:
            print("No image grabbed.")
            pass
        imagearray = self.image
        imagearray = imagearray[0:1024,730:830]
        imagearray = np.swapaxes(imagearray,0,1)      # Swap matrix axes, after having turned the camera 90deg
        # imagearraygf = imagearray
        imagearraygf = ndi.filters.gaussian_filter(imagearray,7)     # Gaussian filter the image, to remove noise and so on, to get a better center estimate

        if self.focusWidget.twoFociVar:
            allmaxcoords = peak_local_max(imagearraygf, min_distance=60)
#            print(allmaxcoords)
            size = allmaxcoords.shape
            maxvals = np.zeros(size[0])
            maxvalpos = np.zeros(2)
            for n in range(0,size[0]):
                if imagearraygf[allmaxcoords[n][0],allmaxcoords[n][1]] > maxvals[0]:
                    if imagearraygf[allmaxcoords[n][0],allmaxcoords[n][1]] > maxvals[1]:
                        tempval = maxvals[1]
                        maxvals[0] = tempval
                        maxvals[1] = imagearraygf[allmaxcoords[n][0],allmaxcoords[n][1]]
                        tempval = maxvalpos[1]
                        maxvalpos[0] = tempval
                        maxvalpos[1] = n
                    else:
                        maxvals[0] = imagearraygf[allmaxcoords[n][0],allmaxcoords[n][1]]
                        maxvalpos[0] = n
            xcenter = allmaxcoords[maxvalpos[0]][0]
            ycenter = allmaxcoords[maxvalpos[0]][1]
            if allmaxcoords[maxvalpos[1]][1] < ycenter:
                xcenter = allmaxcoords[maxvalpos[1]][0]
                ycenter = allmaxcoords[maxvalpos[1]][1]
            centercoords2 = np.array([xcenter,ycenter])
        else:
            centercoords = np.where(imagearraygf == np.array(imagearraygf.max()))
            centercoords2 = np.array([centercoords[0][0],centercoords[1][0]])
            
        subsizey = 50
        subsizex = 50
        xlow = max(0,(centercoords2[0]-subsizex))
        xhigh = min(1024,(centercoords2[0]+subsizex))
        ylow = max(0,(centercoords2[1]-subsizey))
        yhigh = min(1280,(centercoords2[1]+subsizey))
        #print(xlow)
        #print(xhigh)
        #print(ylow)
        #print(yhigh)
        imagearraygfsub = imagearraygf[xlow:xhigh,ylow:yhigh]
        #imagearraygfsub = imagearraygf[xlow:xhigh,:]
        #imagearraygfsubtest = imagearraygf
        #zeroindices = np.zeros(imagearray.shape)
        #zeroindices[xlow:xhigh,ylow:yhigh] = 1
        #imagearraygfsubtest = np.multiply(imagearraygfsubtest,zeroindices)
        self.image = imagearraygf
        #print(centercoords2[1])
        self.massCenter = np.array(ndi.measurements.center_of_mass(imagearraygfsub))
        #self.massCenter2 = np.array(ndi.measurements.center_of_mass(imagearraygfsubtest))
        # self.massCenterGlobal[0] = self.massCenter[0] #+ centercoords2[0] #- subsizex - self.sensorSize[0] / 2     #add the information about where the center of the subarray is
        self.massCenterGlobal = self.massCenter[1] + centercoords2[1] #- subsizey - self.sensorSize[1] / 2     #add the information about where the center of the subarray is
#        print(self.massCenter[1])
#        print(self.massCenterGlobal)
#        print(centercoords2[1])
#        print('')
        #print(self.massCenter2[1])
        #print('')
        self.focusSignal = self.massCenterGlobal


class FocusCalibThread(QtCore.QThread):
    def __init__(self, focusWidget, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.z = focusWidget.z
        self.focusWidget = focusWidget  # mainwidget será FocusLockWidget
        self.um = Q_(1, 'micrometer')

    def run(self):
        self.signalData = []
        self.positionData = []
        self.start = np.float(self.focusWidget.CalibFromEdit.text())
        self.end = np.float(self.focusWidget.CalibToEdit.text())
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
        calText = '1 px --> {} nm'.format(np.round(1000/cal, 1))
        self.focusWidget.calibrationDisplay.setText(calText)
        d = [self.positionData, self.calibrationResult[::-1]]
        self.savedCalibData = [self.positionData,
                               self.signalData,
                               np.polynomial.polynomial.polyval(d[0], d[1])]
        np.savetxt('calibrationcurves.txt', self.savedCalibData)


class PI(object):
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

