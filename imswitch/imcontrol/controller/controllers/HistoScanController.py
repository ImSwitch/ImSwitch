import json
import os

import numpy as np
import time
import tifffile as tif
import threading
from datetime import datetime
import cv2

from imswitch.imcommon.model import dirtools, initLogger, APIExport
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex, Timer
import time

from ..basecontrollers import LiveUpdatedController

#import NanoImagingPack as nip

class HistoScanController(LiveUpdatedController):
    """Linked to HistoScanWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self)

        # HistoScan parameters
        self.nImages = 0
        self.timePeriod = 60 # seconds
        self.zStackEnabled = False
        self.zStackMin = 0
        self.zStackMax = 0
        self.zStackStep = 0

        # store old values
        self.LEDValueOld = 0
        self.LEDValue = 0
        
        # stage-related variables
        self.speed = 10000
        self.positionMoveManual = 1000

        self.HistoScanFilename = ""

        self.updateRate=2
        self.pixelsizeZ=10
        self.tUnshake = .1
        
        
        
        # physical coordinates (temporarily)
        self.stepsizeX = 1
        self.stepsizeY = 1
        self.offsetX = 100  # distance between center of the brightfield and the ESP32 preview camera (X)
        self.offsetY = 100  # distance between center of the brightfield and the ESP32 preview camera (Y)
        self.currentPositionX = 0
        self.currentPositionY = 0
        
        # brightfield camera parameters
        self.camPixelsize = 1 # µm
        self.camPixNumX = 1000
        self.camPixNumY = 1000
        self.camOverlap = 0.3 # 30% overlap of tiles
        
        # preview camera parameters
        self.camPreviewPixelsize = 100
        self.camPreviewPixNumX = self._widget.canvas.height()
        self.camPreviewPixNumY = self._widget.canvas.width()
        

        if self._setupInfo.HistoScan is None:
            self._widget.replaceWithError('HistoScan is not configured in your setup file.')
            return

        # Connect HistoScanWidget signals
        self._widget.HistoScanStartButton.clicked.connect(self.startHistoScan)
        self._widget.HistoScanStopButton.clicked.connect(self.stopHistoScan)
        self._widget.HistoScanShowLastButton.clicked.connect(self.showLast)
        
        self._widget.HistoScanMoveUpButton.clicked.connect(self.moveUp)
        self._widget.HistoScanMoveDownButton.clicked.connect(self.moveDown)
        self._widget.HistoScanMoveLeftButton.clicked.connect(self.moveLeft)
        self._widget.HistoScanMoveRightButton.clicked.connect(self.moveRight)
        
        self._widget.HistoCamLEDButton.clicked.connect(self.toggleLED)
        self._widget.HistoSnapPreviewButton.clicked.connect(self.snapPreview)
        self._widget.HistoFillHolesButton.clicked.connect(self.fillHoles)
        self._widget.HistoUndoButton.clicked.connect(self.undoSelection)
                
        self._widget.sigSliderLEDValueChanged.connect(self.valueLEDChanged)
        
        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]

        # select illumination sources
        self.leds = []
        allIlluNames = self._master.lasersManager.getAllDeviceNames()
        for iDevice in allIlluNames:
            if iDevice.find("LED")>=0:
                self.leds.append(self._master.lasersManager[iDevice])

        # select stage
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]

        self.isHistoScanrunning = False
        self._widget.HistoScanShowLastButton.setEnabled(False)
        
        # setup gui limits
        if len(self.leds) >= 1: self._widget.sliderLED.setMaximum(self.leds[0]._LaserManager__valueRangeMax)

        # get the camera object
        self._camera = self._master.detectorsManager["PreviewCamera"]
        
    
    
        # Steps for the Histoscanner 
        

        
    def fillHoles(self):
        # fill holes in the selection
        self._widget.canvas.fillHoles()

    def undoSelection(self):
        # recover the previous selection
        self._widget.canvas.undoSelection()
        

    def startHistoScan(self):
        # initilaze setup
        # this is not a thread!
        self._widget.HistoScanStartButton.setEnabled(False)
        
        self._widget.setInformationLabel("Starting HistoScan...")

        # get parameters from GUI
        self.zStackMin, self.zStackax, self.zStackStep, self.zStackEnabled = self._widget.getZStackValues()
        self.HistoScanFilename = self._widget.getFilename()
        self.HistoScanDate = datetime.now().strftime("%Y_%m_%d-%I-%M-%S_%p")

        self.doScan()
            

    
    def stopHistoScan(self):
        self.isHistoScanrunning = False

        self._widget.setInformationLabel("Stopping HistoScan...")
        self._widget.HistoScanStartButton.setEnabled(True)
        try:
            del self.HistoScanThread
        except:
            pass

        self._widget.setInformationLabel("Done wit timelapse...")

    def showLast(self):
        try:
            self._widget.setImage(self.LastStackLEDArrayLast, colormap="gray", name="Brightfield",pixelsizeZ=self.pixelsizeZ)
        except  Exception as e:
            self._logger.error(e)

    def displayStack(self, im):
        """ Displays the image in the view. """
        self._widget.setImage(im)

    def doScan(self):
        # 0. initailize pixelsize (low-res and highres) and stage stepsize 
        # TODO: RETRIEVE PROPER COORDINATES THROUGH GUI AND SETTINGS
        
        # 1. Move to initial position on sample
        
        # 2. Take low-res, arge FOv image
        if len(self._widget.canvas.getCoordinateList()) <= 0:
            self._logger.debug("No selection was made..")
            return
        
        # 3. Get Annotaitons from sample selection and bring them to real world coordinates
        allPreviewCoordinatesToScan = np.array(self._widget.canvas.getCoordinateList())
        
        # translate coordinates into bitmap coordinates
        scanRegion = np.zeros((self.camPreviewPixNumX, self.camPreviewPixNumY))
        scanRegion[allPreviewCoordinatesToScan[:,0], allPreviewCoordinatesToScan[:,1]] = 1
        
        # compute FOV ratios between two cameras 
        scanRatioX = (self.camPreviewPixNumX*self.camPreviewPixelsize)/(self.camPixNumX*self.camPixelsize*(1-self.camOverlap))
        scanRatioY = (self.camPreviewPixNumY*self.camPreviewPixelsize)/(self.camPixNumY*self.camPixelsize*(1-self.camOverlap))
        
        # compute necessary tiles for the large FOV to scan - a bit hacky
        nKernel = self._widget.canvas.penwidth
        kernel =  np.ones((nKernel,nKernel)) 
        # binary coordinates (without physical units ) of the scan region
        scanRegionMicroscsope = cv2.resize(cv2.filter2D(np.uint8(scanRegion*1), -1, kernel), None, fx = 1/scanRatioX, fy = 1/scanRatioY, interpolation = cv2.INTER_CUBIC)>1
        
        # overlay the scan region on the low-res image
        lowResCoordinatesMap = cv2.resize(1.*scanRegionMicroscsope, None, fx = scanRatioX, fy = scanRatioY, interpolation = cv2.INTER_CUBIC)
        # TODO: NOT WORKING self._widget.canvas.overlayImage(lowResCoordinatesMap, alpha=0.5)
        
        # => each pixel in the scan region is now a square of size scanRatioX*scanRatioY pixels in the large FOV
        # compute cordinates of the miroscope stage and export list of coordinates
        
        # 4. Compute coordinates for high-res image / tiles 
        coordinateList = np.array(np.where(scanRegionMicroscsope==1)).T*(self.camPixNumX*self.camPixelsize,self.camPixNumY*self.camPixelsize) # each row is one FOV
        
        if len(coordinateList) <= 0:
            self._logger.debug("No selection was made..")
            self._widget.HistoScanStartButton.setEnabled(True)
            self._widget.setInformationLabel("No selection was made..")
            return

        # 6. TODO: Sort list for faster acquisition
        
        # this should decouple the hardware-related actions from the GUI
        self.isHistoScanrunning = True
        self.HistoScanThread = threading.Thread(target=self.doScanThread, args=(coordinateList,), daemon=True)
        self.HistoScanThread.start()

    def doAutofocus(self, params):
        self._logger.info("Autofocusing...")
        isRunInBackground = False
        self._commChannel.sigAutoFocus.emit(int(params["valueRange"]), int(params["valueSteps"], isRunInBackground))
        
    def doScanThread(self, coordinateList):
        # store initial stage position
        initialPosition = (self.stages.get_abs(axis=1),self.stages.get_abs(axis=2))

        # reserve and free space for displayed stacks
        self.LastStackLED = []
            
        for iPos in range(len(coordinateList)):
            # move to location
            self._widget.setInformationLabel("Moving to : " + str(coordinateList[iPos,:]) + " µm ")
            self.stages.move(value=coordinateList[iPos,:], axis="XY", speed=(self.speed,self.speed), is_absolute=True, is_blocking=True, timeout=5)
            #self.stages.move(value=coordinateList[iPos,0], axis="X", speed=(self.speed), is_absolute=True, is_blocking=True)
            #self.stages.move(value=coordinateList[iPos,1], axis="Y", speed=(self.speed), is_absolute=True, is_blocking=True)
            
            # want to do autofocus?
            autofocusParams = self._widget.getAutofocusValues()
            if self._widget.isAutofocus() and np.mod(self.nImages, int(autofocusParams['valuePeriod'])) == 0:
                self._widget.setInformationLabel("Autofocusing...")
                self.doAutofocus(autofocusParams)
            
            # turn on illumination # TODO: ensure it's the right light source!    
            zstackParams = self._widget.getZStackValues()
            self._logger.debug("Take image")
            time.sleep(0.2) # antishake
            self.takeImageIlluStack(xycoords = coordinateList[iPos,:], intensity=self.LEDValue, zstackParams=zstackParams)

        # move stage back to origine
        self.stages.move(value=initialPosition, axis="XY", speed=(self.speed,self.speed), is_absolute=True, is_blocking=True, timeout=5)
        
        # done with scan
        self._widget.setInformationLabel("Done")
        self._widget.HistoScanStartButton.setEnabled(True)
        self.isHistoScanrunning = False
        self.LastStackLEDArrayLast = np.array(self.LastStackLED)
        self._widget.HistoScanShowLastButton.setEnabled(True)


    def takeImageIlluStack(self, xycoords, intensity, zstackParams=None):
        self._logger.debug("Take image: " + str(xycoords) + " - " + str(intensity))
        fileExtension = 'tif'

        # sync with camera frame
        time.sleep(.15)

        if zstackParams[-1]:
            # perform a z-stack
            stepsCounter = 0
            backlash=0
            try: # only relevant for UC2 stuff
                self.stages.setEnabled(is_enabled=True)
            except:
                pass

            self.stages.move(value=zstackParams[0], axis="Z", is_absolute=False, is_blocking=True)
            for iZ in np.arange(zstackParams[0], zstackParams[1], zstackParams[2]):
                stepsCounter += zstackParams[2]
                self.stages.move(value=zstackParams[2], axis="Z", is_absolute=False, is_blocking=True)
                filePath = self.getSaveFilePath(date=self.HistoScanDate, filename=f'{self.HistoScanFilename}_X{xycoords[0]}_Y{xycoords[1]}_Z_{stepsCounter}', extension=fileExtension)
                
                # turn on illuminationn
                self.leds[0].setValue(intensity)
                self.leds[0].setEnabled(True)
                time.sleep(self.tUnshake) # unshake
                lastFrame = self.detector.getLatestFrame()
                self.leds[0].setEnabled(False)
                
                # write out filepath
                self._logger.debug(filePath)
                tif.imwrite(filePath, lastFrame, append=True)

                # store frames for displaying
                self.LastStackLED.append(lastFrame.copy())
            self.stages.setEnabled(is_enabled=False)
            self.stages.move(value=-(zstackParams[1]+backlash), axis="Z", is_absolute=False, is_blocking=True)

        else:
            # turn on illuminationn
            self.leds[0].setValue(intensity)
            self.leds[0].setEnabled(True)

            filePath = self.getSaveFilePath(date=self.HistoScanDate, filename=f'{self.HistoScanFilename}_X{xycoords[0]}_Y{xycoords[1]}', extension=fileExtension)
            lastFrame = self.detector.getLatestFrame()
            self._logger.debug(filePath)
            tif.imwrite(filePath, lastFrame)
            # store frames for displaying
            self.LastStackLED.append(lastFrame.copy())
            self.leds[0].setEnabled(False)


    def valueLEDChanged(self, value):
        self.LEDValue = value
        self._widget.HistoScanLabelLED.setText('Intensity (LED):'+str(value))
        if len(self.leds):
            self.leds[0].setEnabled(True)
            self.leds[0].setValue(self.LEDValue)
            
    def __del__(self):
        self.imageComputationThread.quit()
        self.imageComputationThread.wait()

    def getSaveFilePath(self, date, filename, extension):
        mFilename =  f"{date}_{filename}.{extension}"
        dirPath  = os.path.join(dirtools.UserFileDirs.Root, 'recordings', date)

        newPath = os.path.join(dirPath,mFilename)

        if not os.path.exists(dirPath):
            os.makedirs(dirPath)


        return newPath

    
    def moveUp(self):
        # move stage in Y direction
        self.stages.move(value=self.positionMoveManual, axis="Y", is_absolute=False, is_blocking=True)
        
    def moveDown(self):
        self.stages.move(value=-self.positionMoveManual, axis="Y", is_absolute=False, is_blocking=True)
        
    def moveLeft(self):
        self.stages.move(value=self.positionMoveManual, axis="X", is_absolute=False, is_blocking=True)

    def moveRight(self):
        self.stages.move(value=-self.positionMoveManual, axis="X", is_absolute=False, is_blocking=True)
        
    def snapPreview(self):
        self._logger.info("Snap preview...")
        self.previewImage = self._camera.getLatestFrame()
        self._widget.canvas.setImage(self.previewImage)
        
    def toggleLED(self):
        if self._widget.HistoCamLEDButton.isChecked():
            self._logger.info("LED on")
            self._camera.setCameraLED(255)
        else:
            self._logger.info("LED off")
            self._camera.setCameraLED(0)
            
    def setLED(self, value):
        self._logger.info("Setting LED...")
        self._camera.setLED(value)

    
    
class mTimer(object):
    def __init__(self, waittime, mFunc) -> None:
        self.waittime = waittime
        self.starttime = time.time()
        self.running = False
        self.isStop = False
        self.mFunc = mFunc
        
    def start(self):
        self.starttime = time.time()
        self.running = True
        
        ticker = threading.Event( daemon=True)
        self.waittimeLoop=0 # make sure first run runs immediately
        while not ticker.wait(self.waittimeLoop) and self.isStop==False:
            self.waittimeLoop = self.waittime
            self.mFunc()
        self.running = False
        
    def stop(self):
        self.running = False
        self.isStop = True


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
