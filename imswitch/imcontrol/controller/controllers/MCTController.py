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
import pyqtgraph.ptime as ptime

from ..basecontrollers import LiveUpdatedController

#import NanoImagingPack as nip

class MCTController(LiveUpdatedController):
    """Linked to MCTWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self)

        # mct parameters
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
        self.MCTFilename = ""

        self.updateRate=2

        self.pixelsizeZ=10

        self.tUnshake = .1

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
        self._widget.sigSliderLEDValueChanged.connect(self.valueLEDChanged)

        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]

        # select lasers
        allLaserNames = self._master.lasersManager.getAllDeviceNames()
        self.lasers = []
        for iDevice in allLaserNames:
            if iDevice.find("Laser")>=0:
                self.lasers.append(self._master.lasersManager[iDevice])

        self.leds = []
        for iDevice in allLaserNames:
            if iDevice.find("LED")>=0:
                self.leds.append(self._master.lasersManager[iDevice])

        if len(self._master.LEDMatrixsManager.getAllDeviceNames())>0:
            self.illu = self._master.LEDMatrixsManager[self._master.LEDMatrixsManager.getAllDeviceNames()[0]]
        else:
            self.illu = []

        # select stage
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]

        self.isMCTrunning = False
        self._widget.mctShowLastButton.setEnabled(False)

    def initFilter(self):
        self._widget.setNImages("Initializing filter position...")
        if len(self.lasers)>0:
            self.lasers[0].initFilter()

    def startMCT(self):
        # initilaze setup
        # this is not a thread!
        self._widget.mctStartButton.setEnabled(False)

        if not self.isMCTrunning and (self.Laser1Value>0 or self.Laser2Value>0 or self.LEDValue>0):
            self.nImages = 0
            self._widget.setNImages("Starting timelapse...")
            self.switchOffIllumination()
            if len(self.lasers)>0:
                self.lasers[0].initFilter()

            # get parameters from GUI
            self.zStackMin, self.zStackax, self.zStackStep, self.zStackEnabled = self._widget.getZStackValues()
            self.timePeriod, self.nDuration = self._widget.getTimelapseValues()
            self.MCTFilename = self._widget.getFilename()
            self.MCTDate = datetime.now().strftime("%Y_%m_%d-%I-%M-%S_%p")

            # store old values for later
            if len(self.lasers)>0:
                self.Laser1ValueOld = self.lasers[0].power
            if len(self.lasers)>1:
                self.Laser2ValueOld = self.lasers[1].power
            if len(self.leds)>1:
                self.LEDValueOld = self.leds[0].power

            # reserve space for the stack
            self._widget.mctShowLastButton.setEnabled(False)

            # initiliazing the update scheme for pulling pressure measurement values
            self.timer = Timer()
            self.timer.timeout.connect(self.takeTimelapse())
            self.timer.start(self.timePeriod*1000)
            self.startTime = ptime.time()

        else:

            self.isMCTrunning = False
            self._widget.mctStartButton.setEnabled(True)



    def stopMCT(self):
        self.isMCTrunning = False

        self._widget.setNImages("Stopping timelapse...")

        self._widget.mctStartButton.setEnabled(True)
        try:
            del self.timer
        except:
            pass

        try:
            del self.MCTThread
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
        if not self.isMCTrunning:
            try:
                # make sure there is no exisiting thrad
                del self.MCTThread
            except:
                pass

            # stop measurement once done
            if self.nDuration < self.nImages:
                self.timer.stop()
                self.isMCTrunning = False
                self._widget.mctStartButton.setEnabled(True)
                return

            # this should decouple the hardware-related actions from the GUI - but it doesn't
            self.isMCTrunning = True
            self.MCTThread = threading.Thread(target=self.takeTimelapseThread, daemon=True)
            self.MCTThread.start()


    def takeTimelapseThread(self):
        # this wil run i nthe background
        self._logger.debug("Take image")
        zstackParams = self._widget.getZStackValues()
        # reserve and free space for displayed stacks
        self.LastStackLaser1 = []
        self.LastStackLaser2 = []
        self.LastStackLED = []

        if self.Laser1Value>0:
            self.takeImageIllu(illuMode = "Laser1", intensity=self.Laser1Value, zstackParams=zstackParams)
        if self.Laser2Value>0:
            self.takeImageIllu(illuMode = "Laser2", intensity=self.Laser2Value, zstackParams=zstackParams)
        if self.LEDValue>0:
            self.takeImageIllu(illuMode = "Brightfield", intensity=self.LEDValue, zstackParams=zstackParams)

        self.nImages += 1
        self._widget.setNImages(self.nImages)

        self.isMCTrunning = False

        self.LastStackLaser1ArrayLast = np.array(self.LastStackLaser1)
        self.LastStackLaser2ArrayLast = np.array(self.LastStackLaser2)
        self.LastStackLEDArrayLast = np.array(self.LastStackLED)

        self._widget.mctShowLastButton.setEnabled(True)


    def takeImageIllu(self, illuMode, intensity, zstackParams=None):
        self._logger.debug("Take image:" + illuMode + str(intensity))
        fileExtension = 'tif'
        if illuMode == "Laser1" and len(self.lasers)>0:
            self.lasers[0].setValue(intensity)
            self.lasers[0].setEnabled(True)

        if illuMode == "Laser2" and len(self.lasers)>1:
            self.lasers[1].setValue(intensity)
            self.lasers[1].setEnabled(True)

        if illuMode == "Brightfield":
            try:
                if intensity > 255: intensity=255
                if intensity < 0: intensity=0
                if len(self.leds)>0:
                    self.leds[0].setValue(intensity)
                    self.leds[0].setEnabled(True)
            except:
                pass

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
                filePath = self.getSaveFilePath(date=self.MCTDate, filename=f'{self.MCTFilename}_{illuMode}_Z_{stepsCounter}', extension=fileExtension)
                time.sleep(self.tUnshake) # unshake
                lastFrame = self.detector.getLatestFrame()
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
            filePath = self.getSaveFilePath(date=self.MCTDate, filename=f'{self.MCTFilename}_{illuMode}', extension=fileExtension)
            lastFrame = self.detector.getLatestFrame()
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
            self.lasers[1].setValue(0)
            time.sleep(0.1)
        if len(self.leds)>0:
            self.illu.setAll((0,0,0))


    def valueLaser1Changed(self, value):
        self.Laser1Value= value
        if len(self.lasers)>0:
            self.lasers[0].setValue(self.Laser1Value)

    def valueLaser2Changed(self, value):
        self.Laser2Value = value
        if len(self.lasers)>1:
            self.lasers[1].setValue(self.Laser2Value)

    def valueLEDChanged(self, value):
        self.LEDValue= value
        if len(self.leds):
            self.illu.setAll((self.LEDValue,self.LEDValue,self.LEDValue))

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
