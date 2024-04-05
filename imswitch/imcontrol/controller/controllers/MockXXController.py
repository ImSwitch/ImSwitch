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

from ..basecontrollers import ImConWidgetController

#import NanoImagingPack as nip

class MockXXController(ImConWidgetController):
    """Linked to MockXXWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self)

        # MockXX parameters
        self.nImagesTaken = 0
        self.timePeriod = 60 # seconds
        self.zStackEnabled = False
        self.zStackMin = 0
        self.zStackMax = 0
        self.zStackStep = 0

        # xy
        self.xyScanEnabled = False
        self.xScanMin = 0
        self.xScanMax = 0
        self.xScanStep = 0
        self.yScanMin = 0
        self.yScanMax = 0
        self.yScanStep = 0

        # store old values
        self.Laser1ValueOld = 0
        self.Laser2ValueOld = 0
        self.LEDValueOld = 0

        self.Laser1Value = 0
        self.Laser2Value = 0
        self.LEDValue = 0
        self.MockXXFilename = ""

        self.pixelsize=(10,1,1) # zxy

        self.tUnshake = .15

        if self._setupInfo.MockXX is None:
            self._widget.replaceWithError('MockXX is not configured in your setup file.')
            return

        # Connect MockXXWidget signals
        self._widget.MockXXStartButton.clicked.connect(self.startMockXX)
        self._widget.MockXXStopButton.clicked.connect(self.stopMockXX)
        self._widget.MockXXShowLastButton.clicked.connect(self.showLast)
        
        self._widget.sigSliderLaser1ValueChanged.connect(self.valueLaser1Changed)
        self._widget.sigSliderLaser2ValueChanged.connect(self.valueLaser2Changed)
        self._widget.sigSliderLEDValueChanged.connect(self.valueLEDChanged)

        # connect XY Stagescanning live update  https://github.com/napari/napari/issues/1110
        self.sigImageReceived.connect(self.displayImage)

        # autofocus related
        self.isAutofocusRunning = False
        self._commChannel.sigAutoFocusRunning.connect(self.setAutoFocusIsRunning)

        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]
        self.detector.startAcquisition()

        # select lasers
        allLaserNames = self._master.lasersManager.getAllDeviceNames()
        self.lasers = []
        for iDevice in allLaserNames:
            if iDevice.lower().find("laser")>=0 or iDevice.lower().find("led"):
                self.lasers.append(self._master.lasersManager[iDevice])

        # TODO: misleading we have LEDs and LED Matrices here...
        self.leds = []
        for iDevice in allLaserNames:
            if iDevice.find("LED")>=0:
                self.leds.append(self._master.lasersManager[iDevice])

        '''
        if len(self._master.LEDMatrixsManager.getAllDeviceNames())>0:
            self.illu = self._master.LEDMatrixsManager[self._master.LEDMatrixsManager.getAllDeviceNames()[0]]
        else:
            self.illu = []
        '''
        # select stage
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]

        self.isMockXXrunning = False
        self._widget.MockXXShowLastButton.setEnabled(False)

        # setup gui limits
        if len(self.lasers) >= 1: self._widget.sliderLaser1.setMaximum(self.lasers[0]._LaserManager__valueRangeMax)
        if len(self.lasers) >= 2: self._widget.sliderLaser2.setMaximum(self.lasers[1]._LaserManager__valueRangeMax)
        if len(self.leds) >= 1: self._widget.sliderLED.setMaximum(self.leds[0]._LaserManager__valueRangeMax)

        # setup gui text
        if len(self.lasers) >= 1: self._widget.sliderLaser1.setMaximum(self.lasers[0]._LaserManager__valueRangeMax)
        if len(self.lasers) >= 2: self._widget.sliderLaser2.setMaximum(self.lasers[1]._LaserManager__valueRangeMax)
        if len(self.leds) >= 1: self._widget.sliderLED.setMaximum(self.leds[0]._LaserManager__valueRangeMax)

        # suggest limits for tiled scan with 20% overlay
        try:
            self.pixelSize = self.detector.pixelSizeUm
            overlap = 0.8 # %20 overlap between ROIs
            self.Nx, self.Ny = self.detector._camera.SensorWidth, self.detector._camera.SensorHeight
            self.optDx = int(self.Nx* self.pixelSize[1]*overlap) # dx
            self.optDy = int(self.Ny* self.pixelSize[2]*overlap) # dy
            self._widget.MockXXValueXsteps.setText(str(self.optDx))
            self._widget.MockXXValueYsteps.setText(str(self.optDy))

        except Exception as e:
            self._logger.error(e)


    def startMockXX(self):
        # initilaze setup
        # this is not a thread!
        self._widget.MockXXStartButton.setEnabled(False)

        # don't show any message
        self._master.UC2ConfigManager.setDebug(False)

        # start the timelapse
        if not self.isMockXXrunning and (self.Laser1Value>0 or self.Laser2Value>0 or self.LEDValue>0):
            self.nImagesTaken = 0
            self._widget.setMessageGUI("Starting timelapse...")
            self.switchOffIllumination()

            # get parameters from GUI
            self.zStackMin, self.zStackMax, self.zStackStep, self.zStackEnabled = self._widget.getZStackValues()
            self.xScanMin, self.xScanMax, self.xScanStep, self.yScanMin, self.yScanMax, self.yScanStep, self.xyScanEnabled = self._widget.getXYScanValues()

            self.timePeriod, self.nImagesToCapture = self._widget.getTimelapseValues()
            self.MockXXFilename = self._widget.getFilename()
            self.MockXXDate = datetime.now().strftime("%Y_%m_%d-%I-%M-%S_%p")

            # store old values for later
            if len(self.lasers)>0:
                self.Laser1ValueOld = self.lasers[0].power
            if len(self.lasers)>1:
                self.Laser2ValueOld = self.lasers[1].power
            if len(self.leds)>0:
                self.LEDValueOld = self.leds[0].power

            # reserve space for the stack
            self._widget.MockXXShowLastButton.setEnabled(False)

            # start the timelapse - otherwise we have to wait for the first run after timePeriod to take place..
            self.takeTimelapse(self.timePeriod)

            '''
            self.timer = mTimer(self.timePeriod, self.takeTimelapse)
            self.timer.start()
            '''

        else:
            self.isMockXXrunning = False
            self._widget.MockXXStartButton.setEnabled(True)


    def stopMockXX(self):
        self.isMockXXrunning = False

        self._widget.setMessageGUI("Stopping timelapse...")

        self._widget.MockXXStartButton.setEnabled(True)

        # go back to initial position
        try:
            if self.xyScanEnabled:
                self.stages.move(value=(self.initialPosition[0], self.initialPosition[1]), axis="XY", is_absolute=True, is_blocking=True)
        except:
            pass

        # delete any existing timer
        try:
            del self.timer
        except:
            pass

        # delete any existing thread
        try:
            del self.MockXXThread
        except:
            pass

        self._widget.setMessageGUI("Done wit timelapse...")

        # store old values for later
        if len(self.lasers)>0:
            self.lasers[0].setValue(self.Laser1ValueOld)
        if len(self.lasers)>1:
            self.lasers[1].setValue(self.Laser2ValueOld)
        if len(self.leds)>0:
            self.leds[0].setValue(self.LEDValueOld)

    def showLast(self, isCleanStack=False):
        #  isCleanStack=False => subtract backgroudn or not
        if hasattr(self, "LastStackLaser1ArrayLast"):
            try:
                #subtract background and normalize stack
                if isCleanStack: LastStackLaser1ArrayLast = self.cleanStack(self.LastStackLaser1ArrayLast)
                else: LastStackLaser1ArrayLast = self.LastStackLaser1ArrayLast
                self._widget.setImage(LastStackLaser1ArrayLast, colormap="green", name="GFP",pixelsize=self.pixelsize)
            except  Exception as e:
                self._logger.error(e)

        if hasattr(self, "LastStackLaser2ArrayLast"):
            try:
                if isCleanStack: LastStackLaser2ArrayLast = self.cleanStack(self.LastStackLaser2ArrayLast)
                else: LastStackLaser2ArrayLast = self.LastStackLaser2ArrayLast
                self._widget.setImage(LastStackLaser2ArrayLast, colormap="red", name="SiR",pixelsize=self.pixelsize)
            except Exception as e:
                self._logger.error(e)

        if hasattr(self, "LastStackLEDArrayLast"):
            try:
                if isCleanStack: LastStackLEDArrayLast = self.cleanStack(self.LastStackLEDArrayLast)
                else: LastStackLEDArrayLast = self.LastStackLEDArrayLast
                self._widget.setImage(LastStackLEDArrayLast, colormap="gray", name="Brightfield",pixelsize=self.pixelsize)
            except  Exception as e:
                self._logger.error(e)

    def cleanStack(self, input):
        import NanoImagingPack as nip
        mBackground = nip.gaussf(np.mean(input,0),10)
        moutput = input/mBackground
        mFluctuations = np.mean(moutput, (1,2))
        moutput /= np.expand_dims(np.expand_dims(mFluctuations,-1),-1)
        return np.uint8(moutput)

    def displayStack(self, im):
        """ Displays the image in the view. """
        self._widget.setImage(im)

    def takeTimelapse(self, tperiod):
        # this is called periodically by the timer
        if not self.isMockXXrunning:
            try:
                # make sure there is no exisiting thrad
                del self.MockXXThread
            except:
                pass

            # this should decouple the hardware-related actions from the GUI
            self.isMockXXrunning = True
            self.MockXXThread = threading.Thread(target=self.takeTimelapseThread, args=(tperiod, ), daemon=True)
            self.MockXXThread.start()

    def doAutofocus(self, params):
        self._logger.info("Autofocusing...")
        self._widget.setMessageGUI("Autofocusing...")
        self._commChannel.sigAutoFocus.emit(int(params["valueRange"]), int(params["valueSteps"]))
        self.isAutofocusRunning = True

        while self.isAutofocusRunning:
            time.sleep(0.1)
            if not self.isAutofocusRunning:
                self._logger.info("Autofocusing done.")
                return


    def takeTimelapseThread(self, tperiod = 1):
        # this wil run i nthe background
        self.timeLast = 0
        
        # get current position
        currentPositions = self.stages.getPosition()
        self.initialPosition = (currentPositions["X"], currentPositions["Y"])
        self.initialPositionZ = currentPositions["Z"]

        # run as long as the MockXX is active
        while(self.isMockXXrunning):

            # stop measurement once done
            if self.nImagesTaken >= self.nImagesToCapture:
                self.isMockXXrunning = False
                self._logger.debug("Done with timelapse")
                self._widget.MockXXStartButton.setEnabled(True)
                break

            # initialize a run
            if time.time() - self.timeLast >= (tperiod):

                # run an event
                self.timeLast = time.time() # makes sure that the period is measured from launch to launch
                self._logger.debug("Take image")
                # reserve and free space for displayed stacks
                self.LastStackLaser1 = []
                self.LastStackLaser2 = []
                self.LastStackLED = []


                # set  speed
                self.stages.setSpeed(speed=10000, axis="X")
                self.stages.setSpeed(speed=10000, axis="Y")
                self.stages.setSpeed(speed=1000, axis="Z")

                try:
                    # want to do autofocus?
                    autofocusParams = self._widget.getAutofocusValues()
                    
                    if self._widget.isAutofocus() and np.mod(self.nImagesTaken, int(autofocusParams['valuePeriod'])) == 0:
                        self._widget.setMessageGUI("Autofocusing...")
                        # turn on illuimination
                        if autofocusParams['illuMethod']=="Laser1":
                            self.lasers[0].setValue(self.Laser1Value)
                            self.lasers[0].setEnabled(True)
                            time.sleep(.05)
                        elif autofocusParams['illuMethod']=="Laser2":
                            self.lasers[1].setValue(self.Laser2Value)
                            self.lasers[1].setEnabled(True)
                            time.sleep(.05)
                        elif autofocusParams['illuMethod']=="LED":
                            self.leds[0].setValue(self.LEDValue)
                            self.leds[0].setEnabled(True)
                            time.sleep(.05)

                        self.doAutofocus(autofocusParams)

                    #increase iterator in case something fails during frame acquisition => avoid forever loop
                    self.nImagesTaken += 1

                    # acquire one xyzc scan
                    self.acquireScan(timestamp=self.nImagesTaken)
                   
                    self._widget.setMessageGUI(self.nImagesTaken)

                    # sneak images into arrays for displaying stack
                    if self.zStackEnabled and not self.xyScanEnabled:
                        self.LastStackLaser1ArrayLast = np.array(self.LastStackLaser1)
                        self.LastStackLaser2ArrayLast = np.array(self.LastStackLaser2)
                        self.LastStackLEDArrayLast = np.array(self.LastStackLED)

                        self._widget.MockXXShowLastButton.setEnabled(True)

                except Exception as e:
                    self._logger.error("Thread closes with Error: "+str(e))
                    # close the controller ina nice way
                    pass

            # pause to not overwhelm the CPU
            time.sleep(0.1)



    def acquireScan(self, timestamp=0):
        fileExtension = 'tif'

        # precompute steps for xy scan
        # snake scan
        if self.xyScanEnabled:
            xyScanStepsAbsolute = []
            xyScanIndices = []
            # we snake over y
            fwdpath = np.arange(self.yScanMin, self.yScanMax, self.yScanStep)
            bwdpath = np.flip(fwdpath)
            # we increase linearly over x
            for indexX, ix in enumerate(np.arange(self.xScanMin, self.xScanMax, self.xScanStep)):
                if indexX%2==0:
                    for indexY, iy in enumerate(fwdpath):
                        xyScanStepsAbsolute.append([ix, iy])
                else:
                    for indexY, iy in enumerate(bwdpath):
                        xyScanStepsAbsolute.append([ix, iy])
            
            # reserve space for tiled image
            downScaleFactor = 4
            nTilesX = int(np.ceil((self.xScanMax-self.xScanMin)/self.xScanStep))
            nTilesY = int(np.ceil((self.yScanMax-self.yScanMin)/self.yScanStep))
            imageDimensions = self.detector.getLatestFrame().shape
            imageDimensionsDownscaled = (imageDimensions[1]//downScaleFactor, imageDimensions[0]//downScaleFactor) # Y/X
            tiledImageDimensions = (nTilesX*imageDimensions[1]//downScaleFactor, nTilesY*imageDimensions[0]//downScaleFactor)
            self.tiledImage = np.zeros(tiledImageDimensions)

        else:
            xyScanStepsAbsolute = [[0,0]]
            self.xScanMin = 0
            self.xScanMax = 0
            self.yScanMin = 0
            self.yScanMax = 0

        
        # precompute steps for z scan
        if self.zStackEnabled:
            zStepsAbsolute =  np.arange(self.zStackMin, self.zStackMax, self.zStackStep) + self.initialPositionZ
        else:
            zStepsAbsolute = [self.initialPositionZ]


        # in case something is not connected we want to reconnect! 
        # TODO: This should go into some function outside the MockXX!!!
        if not ("IDENTIFIER_NAME" in self._master.UC2ConfigManager.ESP32.state.get_state() and self._master.UC2ConfigManager.ESP32.state.get_state()["IDENTIFIER_NAME"] == "uc2-esp"):
            mThread = threading.Thread(target=self._master.UC2ConfigManager.initSerial)
            mThread.start()
            mThread.join()

        # initialize xyz coordinates
        if self.xyScanEnabled:
            self.stages.move(value=(self.xScanMin+self.initialPosition[0],self.yScanMin+self.initialPosition[1]), axis="XY", is_absolute=True, is_blocking=True)

        # initialize iterator
        imageIndex = 0
        self._widget.gridLayer = None
        # iterate over all xy coordinates iteratively

        # if we only have one light-source, keep it on during scanning
        if (self.Laser1Value>0 + self.Laser2Value>0 + self.LEDValue>0)>1:
            turnOffIlluInBetween = True
        else:
            turnOffIlluInBetween = False
            
        for ipos, iXYPos in enumerate(xyScanStepsAbsolute):
            if not self.isMockXXrunning:
                break
            # move to xy position is necessary
            if self.xyScanEnabled:
                self.stages.move(value=(iXYPos[0]+self.initialPosition[0],iXYPos[1]+self.initialPosition[1]), axis="XY", is_absolute=True, is_blocking=True)
            # measure framenumber and check if it has been renewed after stage has stopped => avoid motion blur!
            nFrameSyncWait = 5
            if hasattr(self.detector, "getFrameNumber"):
                frameNumber = self.detector.getFrameNumber()
            else:
                frameNumber = -nFrameSyncWait



            # perform a z-stack
            for iZ in zStepsAbsolute:
                # move to each position
                if self.zStackEnabled:
                    self.stages.move(value=iZ, axis="Z", is_absolute=True, is_blocking=True)
                    time.sleep(self.tUnshake) # unshake
                
                # capture image for every illumination
                if self.Laser1Value>0 and len(self.lasers)>0:
                    filePath = self.getSaveFilePath(date=self.MockXXDate,
                                timestamp=timestamp,
                                filename=f'{self.MockXXFilename}_Laser1_i_{imageIndex}_Z_{iZ}_X_{xyScanStepsAbsolute[ipos][0]}_Y_{xyScanStepsAbsolute[ipos][1]}',
                                extension=fileExtension)
                    self.lasers[0].setValue(self.Laser1Value)
                    self.lasers[0].setEnabled(True)
                    time.sleep(.05)
                    lastFrame = self.detector.getLatestFrame()
                    # wait for frame after next frame to appear. Avoid motion blurring
                    #while self.detector.getFrameNumber()<(frameNumber+nFrameSyncWait):time.sleep(0.05)
                    #TODO: USE self._master.recordingManager.snap()
                    tif.imwrite(filePath, lastFrame, append=True)
                    if turnOffIlluInBetween: self.lasers[0].setEnabled(False)
                    self.LastStackLaser1.append(lastFrame.copy())

                if self.Laser2Value>0 and len(self.lasers)>0:
                    filePath = self.getSaveFilePath(date=self.MockXXDate,
                                timestamp=timestamp,
                                filename=f'{self.MockXXFilename}_Laser2_i_{imageIndex}_Z_{iZ}_X_{xyScanStepsAbsolute[ipos][0]}_Y_{xyScanStepsAbsolute[ipos][1]}',
                                extension=fileExtension)
                    self.lasers[1].setValue(self.Laser2Value)
                    self.lasers[1].setEnabled(True)
                    time.sleep(.05)
                    lastFrame = self.detector.getLatestFrame()
                    tif.imwrite(filePath, lastFrame, append=True)
                    if turnOffIlluInBetween: self.lasers[1].setEnabled(False)
                    self.LastStackLaser2.append(lastFrame.copy())

                if self.LEDValue>0 and len(self.leds)>0:
                    filePath = self.getSaveFilePath(date=self.MockXXDate,
                                timestamp=timestamp,
                                filename=f'{self.MockXXFilename}_LED_i_{imageIndex}_Z_{iZ}_X_{xyScanStepsAbsolute[ipos][0]}_Y_{xyScanStepsAbsolute[ipos][1]}',
                                extension=fileExtension)
                    try:
                        if self.LEDValue > 255: self.LEDValue=255
                        if self.LEDValue < 0: self.LEDValue=0
                        if len(self.leds)>0:
                            self.leds[0].setValue(self.LEDValue)
                            self.leds[0].setEnabled(True)
                        time.sleep(.1)
                        lastFrame = self.detector.getLatestFrame()
                        tif.imwrite(filePath, lastFrame, append=True)
                        if turnOffIlluInBetween: self.leds[0].setEnabled(False)
                        self.LastStackLED.append(lastFrame.copy())
                    except:
                        pass


                imageIndex += 1

            # reduce backlash => increase chance to endup at the same position
            if self.zStackEnabled:
                self.stages.move(value=(self.initialPositionZ), axis="Z", is_absolute=True, is_blocking=True)

            if self.xyScanEnabled:
                # lets try to visualize each slice in napari
                # def setImage(self, im, colormap="gray", name="", pixelsize=(1,1,1)):
                # construct the tiled image
                iX = int(np.floor((iXYPos[0]-self.xScanMin) // self.xScanStep))
                iY = int(np.floor((iXYPos[1]-self.yScanMin) // self.yScanStep))
                # handle rgb => turn to mono for now
                if len(lastFrame.shape)>2:
                    lastFrame = np.uint16(np.mean(lastFrame, 0))
                # add tile to large canvas
                lastFrameScaled = cv2.resize(lastFrame, None, fx = 1/downScaleFactor, fy = 1/downScaleFactor, interpolation = cv2.INTER_NEAREST)
                try:
                    self.tiledImage[int(iY*imageDimensionsDownscaled[1]):int(iY*imageDimensionsDownscaled[1]+imageDimensionsDownscaled[1]),
                        int(iX*imageDimensionsDownscaled[0]):int(iX*imageDimensionsDownscaled[0]+imageDimensionsDownscaled[0])] = lastFrameScaled
                except Exception as e:
                    self._logger.error(e)
                    self._logger.error("Failed to parse a frame into the tiledImage array")
                self.sigImageReceived.emit() # => displays image


        # initialize xy coordinates
        if self.xyScanEnabled:
            self.stages.move(value=(self.initialPosition[0], self.initialPosition[1]), axis="XY", is_absolute=True, is_blocking=True)
        if self.zStackEnabled:
            self.stages.move(value=(self.initialPositionZ), axis="Z", is_absolute=True, is_blocking=True)

        # ensure all illus are off
        self.switchOffIllumination()

        # disable motors to prevent overheating 
        self.stages.enalbeMotors(enable=False)

    def switchOffIllumination(self):
        # switch off all illu sources
        for lasers in self.lasers:
            lasers.setEnabled(False)
            #lasers.setValue(0)
            time.sleep(0.1)
        if len(self.leds)>0:
            self.leds[0].setValue(0)
            #self.illu.setAll((0,0,0))

    def valueLaser1Changed(self, value):
        self.Laser1Value= value
        self._widget.MockXXLabelLaser1.setText('Intensity (Laser 1):'+str(value))
        if not self.lasers[0].enabled: self.lasers[0].setEnabled(1)
        if len(self.lasers)>0:self.lasers[0].setValue(self.Laser1Value)
        if self.lasers[1].power: self.lasers[1].setValue(0)

    def valueLaser2Changed(self, value):
        self.Laser2Value = value
        self._widget.MockXXLabelLaser2.setText('Intensity (Laser 2):'+str(value))
        if not self.lasers[1].enabled: self.lasers[1].setEnabled(1)
        if len(self.lasers)>1: self.lasers[1].setValue(self.Laser2Value)
        if self.lasers[0].power: self.lasers[0].setValue(0)

    def valueLEDChanged(self, value):
        self.LEDValue= value
        self._widget.MockXXLabelLED.setText('Intensity (LED):'+str(value))
        if len(self.leds) and not self.leds[0].enabled: self.leds[0].setEnabled(1)
        if len(self.leds): self.leds[0].setValue(self.LEDValue, getReturn=False)
        #if len(self.leds): self.illu.setAll(state=(1,1,1), intensity=(self.LEDValue,self.LEDValue,self.LEDValue))

    def __del__(self):
        self.imageComputationThread.quit()
        self.imageComputationThread.wait()

    def getSaveFilePath(self, date, timestamp, filename, extension):
        mFilename =  f"{date}_{filename}.{extension}"
        dirPath  = os.path.join(dirtools.UserFileDirs.Root, 'recordings', date, "t"+str(timestamp))

        newPath = os.path.join(dirPath,mFilename)

        if not os.path.exists(dirPath):
            os.makedirs(dirPath)

        return newPath

    def setAutoFocusIsRunning(self, isRunning):
        # this is set by the AutofocusController once the AF is finished/initiated
        self.isAutofocusRunning = isRunning

    def displayImage(self):
        # a bit weird, but we cannot update outside the main thread
        name = "tilescanning"
        self._widget.setImage(np.uint16(self.tiledImage), colormap="gray", name=name, pixelsize=(1,1), translation=(0,0))




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


# Copyright (C) 2020-2023 ImSwitch developers
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
