# -*- coding: utf-8 -*-
"""
Created on Thu Jan 07 11:42:00 2021

@author: jonatanalvelid
"""

import time
import threading

import numpy as np

import scipy.ndimage as ndi
import pyqtgraph.ptime as ptime
from skimage.feature import peak_local_max
from pyqtgraph.Qt import QtCore


class FocusLockHelper:
    """Manager for the focus lock."""
    def __init__(self, focusLockInfo):       
        self.setPointSignal = 0
        self.locked = False
        self.aboutToLock = False
        self.zStackVar = False
        self.twoFociVar = False
        self.noStepVar = True
        self.focusTime = 1000 / focusLockInfo.scansPerS  # time between focus signal updates in ms
        self.initialZ = 0
        self.currentZ = 0
        self.lastZ = 0
        self.lockingData = np.zeros(7)
        self.__processDataThread = ProcessDataThread()

    def unlockFocus(self):
        #if self
        print("Manager: unlocking focus")

    def lockFocus(self, kp, ki, absz):
        if not self.locked:
            self.setPointSignal = self.__processDataThread.focusSignal
            self.pi = pi.PI(self.setPoint, 0.001, kp, ki)
            self.initialZ = absz
            self.locked = True
        print("Manager: lock focus")
        return self.setPointSignal

    def toggleFocus(self):
        self.aboutToLock = False
        print("Manager: toggling focus")

    def focusCalibrationStart(self):
        print("Manager: starting focus calibration thread")


class ProcessDataThread(QtCore.QThread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # set the camera
        self.webcam = self.focusWidget.webcam
        # self.ws = {'vsub': 4, 'hsub': 4,
        #            'top': None, 'bot': None,
        #            'exposure_time': 10}
        # self.image = self.webcam.grab_image(vsub=self.ws['vsub'],
        #                                     hsub=self.ws['hsub'],
        #                                     top=self.ws['top'],
        #                                     bot=self.ws['bot'],
        #                                     exposure_time=self.ws[
        #                                     'exposure_time'])
        self.image = self.webcam.grab_image()

        self.sensorSize = np.array(self.image.shape)
        # print(self.sensorSize) #= (1024,1280)

        self.focusSignal = 0

    def update(self, img):
        self.updateFocusSignal(img)
        # self.focusWidget.webcamGraph.update(self.image)  # DO THIS IN FOCUSLOCKHELPER INSTEAD
        # self.focusWidget.focusLockGraph.update(self.focusSignal)  # DO THIS IN FOCUSLOCKHELPER INSTEAD
        return self.focusSignal
        # update the PI control
        if self.focusWidget.locked:
            self.focusWidget.updatePI()
        elif self.focusWidget.aboutToLock:
            self.focusWidget.lockingPI()

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
