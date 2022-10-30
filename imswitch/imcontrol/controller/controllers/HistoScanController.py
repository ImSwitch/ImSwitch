import json
import os

import numpy as np
import time
import tifffile as tif
import threading
from datetime import datetime


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
        self.Laser1ValueOld = 0
        self.Laser2ValueOld = 0
        self.LEDValueOld = 0

        self.Laser1Value = 0
        self.Laser2Value = 0
        self.LEDValue = 0
        self.HistoScanFilename = ""

        self.updateRate=2

        self.pixelsizeZ=10

        self.tUnshake = .1

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
        
        self._widget.sigSliderLEDValueChanged.connect(self.valueLEDChanged)
        
        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]

        self.leds = []
        allLaserNames = self._master.lasersManager.getAllDeviceNames()
        for iDevice in allLaserNames:
            if iDevice.find("LED")>=0:
                self.leds.append(self._master.lasersManager[iDevice])

        if len(self._master.LEDMatrixsManager.getAllDeviceNames())>0:
            self.illu = self._master.LEDMatrixsManager[self._master.LEDMatrixsManager.getAllDeviceNames()[0]]
        else:
            self.illu = []

        # select stage
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]

        self.isHistoScanrunning = False
        self._widget.HistoScanShowLastButton.setEnabled(False)
        
        # setup gui limits
        if len(self.leds) >= 1: self._widget.sliderLED.setMaximum(self.leds[0]._LaserManager__valueRangeMax)

        # get the camera object
        self._camera = self._master.detectorsManager["PreviewCamera"]
        
    
    
        # Steps for the Histoscanner 
        
        # 0. initailize pixelsize (low-res and highres) and stage stepsize 
        
        # 1. Move to initial position on sample
        
        # 2. Take low-res, arge FOv image
        
        # 3. Annotate Sample region in Canvas
        
        # 4. Compute coordinates for high-res image / tiles 
        
        # 5. move to first tile and take image
        
        # 6. iterate over all tiles and take images
        
        # 7. visualize images/current position in canvas
        
        
        

    def startHistoScan(self):
        # initilaze setup
        # this is not a thread!
        self._widget.HistoScanStartButton.setEnabled(False)

        if not self.isHistoScanrunning and (self.Laser1Value>0 or self.Laser2Value>0 or self.LEDValue>0):
            self.nImages = 0
            self._widget.setNImages("Starting timelapse...")
            self.switchOffIllumination()
            if len(self.lasers)>0:
                self.lasers[0].initFilter()

            # get parameters from GUI
            self.zStackMin, self.zStackax, self.zStackStep, self.zStackEnabled = self._widget.getZStackValues()
            self.timePeriod, self.nDuration = self._widget.getTimelapseValues()
            self.HistoScanFilename = self._widget.getFilename()
            self.HistoScanDate = datetime.now().strftime("%Y_%m_%d-%I-%M-%S_%p")

            # store old values for later
            if len(self.lasers)>0:
                self.Laser1ValueOld = self.lasers[0].power
            if len(self.lasers)>1:
                self.Laser2ValueOld = self.lasers[1].power
            if len(self.leds)>1:
                self.LEDValueOld = self.leds[0].power

            # reserve space for the stack
            self._widget.HistoScanShowLastButton.setEnabled(False)

            # FIXME: This is a hack to make sure the image is displayed correctly
            # we start it first and then in a loop 
            self.takeTimelapse()
            
            # start the timelapse - otherwise we have to wait for the first run after timePeriod to take place..
            self.timer = Timer()
            self.timer.timeout.connect(lambda: self.takeTimelapse())
            self.timer.start(self.timePeriod*1000)
            self.startTime = time.time()
            '''       
            self.timer = mTimer(self.timePeriod, self.takeTimelapse)
            self.timer.start()
            '''
            
        else:
            self.isHistoScanrunning = False
            self._widget.HistoScanStartButton.setEnabled(True)

    
    def stopHistoScan(self):
        self.isHistoScanrunning = False

        self._widget.setNImages("Stopping timelapse...")

        self._widget.HistoScanStartButton.setEnabled(True)
        try:
            del self.timer
        except:
            pass

        try:
            del self.HistoScanThread
        except:
            pass

        self._widget.setNImages("Done wit timelapse...")

        # store old values for later
        if len(self.lasers)>0:
            self.lasers[0].setValue(self.Laser1ValueOld)
        if len(self.lasers)>1:
            self.lasers[1].setValue(self.Laser2ValueOld)
        if len(self.leds)>0:
            self.leds[0].setValue(self.LEDValueOld)

    def showLast(self):

        try:
            self._widget.setImage(self.LastStackLaser1ArrayLast, colormap="green", name="GFP",pixelsizeZ=self.pixelsizeZ)
        except  Exception as e:
            self._logger.error(e)

        try:
            self._widget.setImage(self.LastStackLaser2ArrayLast, colormap="red", name="Red",pixelsizeZ=self.pixelsizeZ)
        except Exception as e:
            self._logger.error(e)

        try:
            self._widget.setImage(self.LastStackLEDArrayLast, colormap="gray", name="Brightfield",pixelsizeZ=self.pixelsizeZ)
        except  Exception as e:
            self._logger.error(e)

    def displayStack(self, im):
        """ Displays the image in the view. """
        self._widget.setImage(im)

    def takeTimelapse(self):
        # this is called periodically by the timer
        if not self.isHistoScanrunning:
            try:
                # make sure there is no exisiting thrad
                del self.HistoScanThread
            except:
                pass

            # stop measurement once done
            if self.nDuration <= self.nImages:
                self.isHistoScanrunning = False
                self._widget.HistoScanStartButton.setEnabled(True)
                self.timer.stop()
                return

            # this should decouple the hardware-related actions from the GUI
            self.isHistoScanrunning = True
            self.HistoScanThread = threading.Thread(target=self.takeTimelapseThread, args=(), daemon=True)
            self.HistoScanThread.start()

    def doAutofocus(self, params):
        self._logger.info("Autofocusing...")
        isRunInBackground = False
        self._commChannel.sigAutoFocus.emit(int(params["valueRange"]), int(params["valueSteps"], isRunInBackground))

    def takeTimelapseThread(self):
        # this wil run i nthe background
        self._logger.debug("Take image")
        zstackParams = self._widget.getZStackValues()
        # reserve and free space for displayed stacks
        self.LastStackLaser1 = []
        self.LastStackLaser2 = []
        self.LastStackLED = []
        
        # want to do autofocus?
        autofocusParams = self._widget.getAutofocusValues()
        if self._widget.isAutofocus() and np.mod(self.nImages, int(autofocusParams['valuePeriod'])) == 0:
            self._widget.setNImages("Autofocusing...")
            self.doAutofocus(autofocusParams)
            


        if self.Laser1Value>0:
            self.takeImageIllu(illuMode = "Laser1", intensity=self.Laser1Value, timestamp=self.nImages, zstackParams=zstackParams)
        if self.Laser2Value>0:
            self.takeImageIllu(illuMode = "Laser2", intensity=self.Laser2Value, timestamp=self.nImages, zstackParams=zstackParams)
        if self.LEDValue>0:
            self.takeImageIllu(illuMode = "Brightfield", intensity=self.LEDValue, timestamp=self.nImages, zstackParams=zstackParams)

        self.nImages += 1
        self._widget.setNImages(self.nImages)

        self.isHistoScanrunning = False

        self.LastStackLaser1ArrayLast = np.array(self.LastStackLaser1)
        self.LastStackLaser2ArrayLast = np.array(self.LastStackLaser2)
        self.LastStackLEDArrayLast = np.array(self.LastStackLED)

        self._widget.HistoScanShowLastButton.setEnabled(True)


    def takeImageIllu(self, illuMode, intensity, timestamp=0, zstackParams=None):
        self._logger.debug("Take image: " + illuMode + " - " + str(intensity))
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
                filePath = self.getSaveFilePath(date=self.HistoScanDate, filename=f'{self.HistoScanFilename}_{illuMode}_t_{timestamp}_Z_{stepsCounter}', extension=fileExtension)
                
                # turn on illuminationn
                if illuMode == "Laser1" and len(self.lasers)>0:
                    self.lasers[0].setValue(intensity)
                    self.lasers[0].setEnabled(True)
                elif illuMode == "Laser2" and len(self.lasers)>1:
                    self.lasers[1].setValue(intensity)
                    self.lasers[1].setEnabled(True)
                elif illuMode == "Brightfield":
                    try:
                        if intensity > 255: intensity=255
                        if intensity < 0: intensity=0
                        if len(self.leds)>0:
                            self.leds[0].setValue(intensity)
                            self.leds[0].setEnabled(True)
                    except:
                        pass
                time.sleep(self.tUnshake) # unshake
                lastFrame = self.detector.getLatestFrame()
                self.switchOffIllumination()
                self._logger.debug(filePath)
                tif.imwrite(filePath, lastFrame, append=True)

                # store frames for displaying
                if illuMode == "Laser1":
                    self.LastStackLaser1.append(lastFrame.copy())
                if illuMode == "Laser2":
                    self.LastStackLaser2.append(lastFrame.copy())
                if illuMode == "Brightfield":
                    self.LastStackLED.append(lastFrame.copy())
            self.stages.setEnabled(is_enabled=False)
            self.stages.move(value=-(zstackParams[1]+backlash), axis="Z", is_absolute=False, is_blocking=True)

        else:
            # turn on illuminationn
            if illuMode == "Laser1" and len(self.lasers)>0:
                self.lasers[0].setValue(intensity)
                self.lasers[0].setEnabled(True)
            elif illuMode == "Laser2" and len(self.lasers)>1:
                self.lasers[1].setValue(intensity)
                self.lasers[1].setEnabled(True)
            elif illuMode == "Brightfield":
                try:
                    if intensity > 255: intensity=255
                    if intensity < 0: intensity=0
                    if len(self.leds)>0:
                        self.leds[0].setValue(intensity)
                        self.leds[0].setEnabled(True)
                except:
                    pass
            filePath = self.getSaveFilePath(date=self.HistoScanDate, filename=f'{self.HistoScanFilename}_{illuMode}_t_{timestamp}', extension=fileExtension)
            lastFrame = self.detector.getLatestFrame()
            self._logger.debug(filePath)
            tif.imwrite(filePath, lastFrame)
            # store frames for displaying
            if illuMode == "Laser1":
                self.LastStackLaser1.append(lastFrame.copy())
            if illuMode == "Laser2":
                self.LastStackLaser2.append(lastFrame.copy())
            if illuMode == "Brightfield":
                self.LastStackLED.append(lastFrame.copy())

        self.switchOffIllumination()


    def switchOffIllumination(self):
        # switch off all illu sources
        for lasers in self.lasers:
            lasers.setEnabled(False)
            lasers.setValue(0)
            time.sleep(0.1)
        if len(self.leds)>0:
            self.illu.setAll((0,0,0))


    def valueLaser1Changed(self, value):
        self.Laser1Value= value
        self._widget.HistoScanLabelLaser1.setText('Intensity (Laser 1):'+str(value)) 
        if len(self.lasers)>0:
            self.lasers[0].setValue(self.Laser1Value)

    def valueLaser2Changed(self, value):
        self.Laser2Value = value
        self._widget.HistoScanLabelLaser2.setText('Intensity (Laser 2):'+str(value))
        if len(self.lasers)>1:
            self.lasers[1].setValue(self.Laser2Value)

    def valueLEDChanged(self, value):
        self.LEDValue= value
        self._widget.HistoScanLabelLED.setText('Intensity (LED):'+str(value))
        if len(self.leds):
            self.illu.setAll(state=(1,1,1), intensity=(self.LEDValue,self.LEDValue,self.LEDValue))

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
        self._logger.info("Moving up...")
        
    def moveDown(self):
        self._logger.info("Moving down...")

    def moveLeft(self):
        self._logger.info("Moving left...")

    def moveRight(self):
        self._logger.info("Moving right...")
        
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
