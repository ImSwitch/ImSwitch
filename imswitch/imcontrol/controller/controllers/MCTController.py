import json
import os

import numpy as np
import time 
import tifffile as tif

from imswitch.imcommon.model import dirtools, initLogger, APIExport
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex, Timer
import pyqtgraph.ptime as ptime

from ..basecontrollers import LiveUpdatedController

#import NanoImagingPack as nip

class MCTController(LiveUpdatedController):
    """Linked to MCTWidget."""
    
    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        
        # mct parameters
        self.nImages = 0
        self.timePeriod = 60 # seconds
        self.zStackEnabled = False
        self.zStackMin = 0
        self.zStackMax = 0
        self.zStackStep = 0
        self.brightfieldEnabeld = False
        
        self.Laser1Value = 0
        self.Laser2Value = 0
        self.MCTFilename = ""
        
        self.updateRate=2
        
        if self._setupInfo.mct is None:
            self._widget.replaceWithError('MCT is not configured in your setup file.')
            return

        # Connect MCTWidget signals      
        self._widget.mctStartButton.clicked.connect(self.startMCT)
        self._widget.mctStopButton.clicked.connect(self.stopMCT)
        self._widget.mctShowLastButton.clicked.connect(self.showLast)
        self._widget.mctInitFilterButton.clicked.connect(self.initFilter)

        
        
        self._widget.sigSliderLaser1ValueChanged.connect(self.valueLaser1Changed)
        self._widget.sigSliderLaser2ValueChanged.connect(self.valueLaser2Changed)
        

        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]

        # select lasers
        allLaserNames = self._master.lasersManager.getAllDeviceNames()
        self.lasers = []
        for iDevice in allLaserNames:
            if iDevice.find("Laser")>=0:
                self.lasers.append(self._master.lasersManager[iDevice])
        
        # select stage
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]

        # setup worker/background thread
        self.imageComputationWorker = self.MCTProcessorWorker()
        #self.imageComputationWorker.sigMCTProcessorImageComputed.connect(self.displayImage)
        
        self.imageComputationThread = Thread()
        self.imageComputationWorker.moveToThread(self.imageComputationThread)
        self.sigImageReceived.connect(self.imageComputationWorker.computeMCTImage)
        self.imageComputationThread.start()

        # Initial MCT display
        self._commChannel.sigUpdateImage.connect(self.update)
        #self.displayMask(self._master.mctManager.maskCombined)

        self.isMCTrunning = False
        
    def initFilter(self):
        self._widget.setNImages("Initializing filter position...")
        self.lasers[0].initFilter()


    def startMCT(self):
        
        self.nImages = 0
        
        self._widget.setNImages("Starting timelapse...")

        self.lasers[0].initFilter()

        self.zStackMin, self.zStackax, self.zStackStep, self.zStackEnabled = self._widget.getZStackValues()
        self.timePeriod = self._widget.getTimelapseValues()
        self.MCTFilename = self._widget.getFilename()
        self.brightfieldEnabeld = self._widget.getBrightfieldEnabled()
        self.isMCTrunning = True
        
        # initiliazing the update scheme for pulling pressure measurement values
        self.timer = Timer()
        self.timer.timeout.connect(self.takeTimelapse)
        self.timer.start(self.timePeriod*1000)
        self.startTime = ptime.time()
    
    def stopMCT(self):
        self.isMCTrunning = False
        del self.timer
            
    def showLast(self):
        pass
    
    def takeTimelapse(self):
        if self.isMCTrunning:
            self.__logger.debug("Take image")
            zstackParams = self._widget.getZStackValues()

            if self.Laser1Value>0:
                self.takeImageIllu(illuMode = "Laser1", intensity=self.Laser1Value, zstackParams=zstackParams)
            if self.Laser2Value>0:
                self.takeImageIllu(illuMode = "Laser2", intensity=self.Laser1Value, zstackParams=zstackParams)
            if self.brightfieldEnabeld:
                self.takeImageIllu(illuMode = "Brightfield", intensity=1)
                    
            self.nImages += 1
            self._widget.setNImages(self.nImages)
                
        
    def takeImageIllu(self, illuMode, intensity, zstackParams=None):
        self._logger.debug("Take image:" + illuMode + str(intensity))
        fileExtension = 'tif'
        if illuMode == "Laser1":
            self.lasers[0].setValue(self.Laser1Value)
            self.lasers[0].setEnabled(True)
        if illuMode == "Laser2":
            self.lasers[1].setValue(self.Laser2Value)
            self.lasers[1].setEnabled(True)
        if illuMode == "Brightfield":
            self.lasers[2].setValue(self.Laser1Value)
            self.lasers[2].setEnabled(True)
        
        if zstackParams[-1]:
            # perform a z-stack
            stepsCounter = 0
            for iZ in np.arange(zstackParams[0], zstackParams[1], zstackParams[2]):
                stepsCounter += zstackParams[2]
                self.stages.move(value=iZ, axis="Z", is_absolute=False, is_blocking=True)
                filePath = self.getSaveFilePath(f'{self.MCTFilename}_N_{illuMode}_Z_{stepsCounter}.{fileExtension}')
                time.sleep(0.1) # unshake
                tif.imwrite(filePath, self.detector.getLatestFrame())
            self.stages.move(value=-stepsCounter, axis="Z", is_absolute=True, is_blocking=True)

        else:
            filePath = self.getSaveFilePath(f'{self.MCTFilename}_{illuMode}.{fileExtension}')
            tif.imwrite(filePath, self.detector.getLatestFrame())

        for lasers in self.lasers:
            lasers.setEnabled(False)
        
            
    
    def valueLaser1Changed(self, value):
        self.Laser1Value= value
        #self.lasers[0].setEnabled(True)
        self.lasers[0].setValue(self.Laser1Value)

    def valueLaser2Changed(self, value):
        self.Laser2Value= value
        self.lasers[1].setValue(self.Laser2Value)

                
    def __del__(self):
        self.imageComputationThread.quit()
        self.imageComputationThread.wait()
 
    def update(self, detectorName, im, init, isCurrentDetector):
        """ Update with new detector frame. """
        '''
        if not isCurrentDetector or not self.active:
            return
                
        if self.it >= self.updateRate:
            self.it = 0

            # dispaly mct pattern
            if(isSimulation):
                iPhi = self.patternID%self.nPhases
                iRot = self.patternID//self.nRotations
                self.setIlluPatternByID(iRot, iPhi)
            else:
                pass
            
            # this does not correlate with mctulated patterns!    
            self.mctPatternByID(self.patternID)
            self.allFrames.append(im)
            
            # wait for frame to be displayed? 
            time.sleep(.1)
            self.patternID+=1
            
            # if all patterns are acquired => reconstruct
            if self.patternID>=(self.nRotations*self.nPhases):
                # process the frames and display
                allFramesNP = np.array(self.allFrames)
                self.imageComputationWorker.prepareForNewMCTStack(allFramesNP)
                self.sigImageReceived.emit()
                
                self.patternID=0
                self.allFrames = []

        else:
            self.it += 1
        '''
        pass
    
    def getSaveFilePath(self, path, allowOverwriteDisk=False, allowOverwriteMem=False):
        newPath = path
        numExisting = 0

        def existsFunc(pathToCheck):
            if not allowOverwriteDisk and os.path.exists(pathToCheck):
                return True
            return False

        while existsFunc(newPath):
            numExisting += 1
            pathWithoutExt, pathExt = os.path.splitext(path)
            newPath = f'{pathWithoutExt}_{numExisting}{pathExt}'
        return newPath

    @APIExport(runOnUIThread=True)
    def mctPatternByID(self, patternID):
        currentPattern = self._master.mctManager.allPatterns[patternID]
        self.updateDisplayImage(currentPattern)
        return currentPattern
   
    class MCTProcessorWorker(Worker):
        sigMCTProcessorImageComputed = Signal(np.ndarray)
        
        def __init__(self):
            super().__init__()

            self._logger = initLogger(self, tryInheritParent=False)
            self._numQueuedImages = 0
            self.isRunning = False           
            self.iReconstructed = 0
            
            self._numQueuedImages = 0
            self._numQueuedImagesMutex = Mutex()
            
            # initilaize the reconstructor
            #self.processor = MCTProcessor()

        def setNumReconstructed(self, numReconstructed=0):
            self.iReconstructed = numReconstructed
            
        def computeMCTImage(self):
            """ Compute MCT of an image stack. """
            try:
                if self._numQueuedImages > 1:
                    return  # Skip this frame in order to catch up
                
                # Simulate MCT Stack
                #self._image = self.processor.mctSimulator(Nx=512, Ny=512, Nrot=3, Nphi=3)
                
                # initialize the model 
                '''
                if self.iReconstructed == 0:
                    #self.processor.setReconstructor()
                    #self.processor.calibrate(self._image)
                MCTframe = self.processor.reconstruct(self._image)
                self.sigMCTProcessorImageComputed.emit(np.array(MCTframe))

                self.iReconstructed += 1
                '''
            finally:
                self._numQueuedImagesMutex.lock()
                self._numQueuedImages -= 1
                self._numQueuedImagesMutex.unlock()

        def prepareForNewMCTStack(self, image):
            """ Must always be called before the worker receives a new image. """
            self._image = image
            self._numQueuedImagesMutex.lock()
            self._numQueuedImages += 1
            self._numQueuedImagesMutex.unlock()
            


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
