# -*- coding: utf-8 -*-
"""
Created on Fri Jan 08 14:00:00 2021

@author: jonatanalvelid
"""

import numpy as np

from .DetectorManager import (
    DetectorManager, DetectorNumberParameter, DetectorListParameter
)
from framework import Signal, SignalInterface, Thread, Worker

class APDManager(DetectorManager):

    # TODO: use the same manager for the PMT, with the type of detector as an argument. NidaqPointDetectorManager
    def __init__(self, APDInfo, name, nidaqManager, **_kwargs):
        model = 0
        self.__name = name
        self._image = np.array([])

        #for propertyName, propertyValue in webcamInfo.managerProperties['tis'].items():
        #    self._camera.setPropertyValue(propertyName, propertyValue)

        fullShape = (0, 0)

        # Prepare parameters
        parameters = {}
        self._nidaqManager = nidaqManager
        self._nidaqManager.scanStartSignal.connect(lambda nL, nP: self.startScan(nL, nP))
        super().__init__(name, fullShape, [1], model, parameters)

    def startScan(self, nLines, nPixels):
        if self.acquisition:
            self._scanWorker = ScanWorker(self, nLines, nPixels)
            self._scanThread = Thread()
            self._scanWorker.moveToThread(self._scanThread)
            self._scanThread.started.connect(self._scanWorker.run)
            self._scanWorker.scanning = True
            self._scanWorker.newLine.connect(lambda line: self.updateImage(line))
            self._scanThread.start()
    
    def startAcquisition(self):
        self.acquisition = True

    def stopAcquisition(self):
        self._scanWorker.scanning = False
        self._scanThread.quit()
        self._scanThread.wait()
    

    def getLatestFrame(self):
        return self._image

    def updateImage(self, line):
        print('update image')

    def setParameter(self, name, value):
        pass

    def getParameter(self, name):
       pass

    def setBinning(self, binning):
        super().setBinning(binning)
    
    def getChunk(self):
        pass

    def flushBuffers(self):
        pass

    def pixelSize(self):
        pass

    def crop(self, hpos, vpos, hsize, vsize):
        pass

    def show_dialog(self):
        "Manager: open camera settings dialog mock."
        pass

class ScanWorker(Worker):
    newLine = Signal(np.ndarray)
    def __init__(self, manager, nLines, nPixels):
        super().__init__()
        self._name = manager.__name
        manager._nidaqManager.startInputTask(self.name, 'ci')
        self._manager = manager
        self._nLines = nLines
        self._nPixels = nPixels

    def run(self):
        lineCounter = 0
        lastValue = 0
        while lineCounter < self._nLines:
            if self.scanning:
                data = self._manager._nidaqManager.readInputTask(self._name, self._nPixels)
                # galvo-sensor-data reading
                subtractionArray = np.concatenate(([lastValue],data[:-1]))
                lastValue = data[-1]
                data = data - subtractionArray  # Now apd_data is an array contains at each position the number of counts at this position
                line = np.absolute(data[0:len(data) // 2])
                # TODO: Line_from_sine from old code, probably have to read galvo-sensor-data
                newLine.emit(line)
                lineCounter = lineCounter + 1
            else:
                self.close()
        
    def close(self):
        self.manager.nidaqManager.stopInputTask(self._name)
