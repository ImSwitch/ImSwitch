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

class ISMController(LiveUpdatedController):
    """Linked to ISMWidget."""
    
    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self)
        
        # ISM parameters
        self.nImages = 0

        # store old values
        self.Laser1ValueOld = 0        
        self.Laser1Value = 0
        
        self.ISMFilename = ""
        
        self.updateRate=2

        self.tUnshake = .1
        
        if self._setupInfo.ism is None:
            self._widget.replaceWithError('ISM is not configured in your setup file.')
            return

        
        # Connect ISMWidget signals      
        self._widget.ISMStartButton.clicked.connect(self.startISM)
        self._widget.ISMStopButton.clicked.connect(self.stopISM)
        self._widget.ISMShowLastButton.clicked.connect(self.showLast)
        self._widget.ISMShowSinglePatternButton.clicked.connect(self.initFilter)

        self._widget.sigSliderLaser1ValueChanged.connect(self.valueLaser1Changed)
        
        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]

        # select lasers
        LaserName = self._master.lasersManager.getAllDeviceNames()[0]
        self.laser = self._master.lasersManager[LaserName]

        # select stage
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]

        self.isISMrunning = False
        
        self._widget.ISMShowLastButton.setEnabled(False)


    def getISMFrame(self, nFrame=0):
        # try pattern
        nPixels = 256
        nUnitCell = 16
        unitCell = np.zeros((nUnitCell,nUnitCell))
        iX = nFrame//nUnitCell
        iY = nFrame%nUnitCell
        unitCell[iX,iY]=1
        ismPattern = np.matlib.repmat(unitCell, int(nPixels//nUnitCell), int(nPixels//nUnitCell))
        ismPatternIndex =  np.where(ismPattern.flatten()>0)[0]
        return ismPatternIndex
        
    def initFilter(self):
        ismPatternIndex = self.getISMFrame(nFrame=0)
        self.laser.sendScannerPattern(ismPatternIndex, scannernFrames=1,
            scannerLaserVal=32000,
            scannerExposure=500, scannerDelay=500)
        self._widget.setText("Displaying standard pattern")
        
    def startISM(self):
        # initilaze setup
        # this is not a thread!
        self._widget.ISMStartButton.setEnabled(False)
            
        if not self.isISMrunning and self.Laser1Value>0:
            self.nImages = 0
            self._widget.setText("Starting ISM...")
            self.switchOffIllumination()

            # get parameters from GUI
            #self.zStackMin, self.zStackax, self.zStackStep, self.zStackEnabled = self._widget.getZStackValues()
            #self.timePeriod, self.nDuration = self._widget.getTimelapseValues()
            self.ISMFilename = self._widget.getFilename()
            self.ISMDate = datetime.now().strftime("%Y_%m_%d-%I-%M-%S_%p")

            # store old values for later
            self.Laser1ValueOld = self.lasers[0].power            
            
            # reserve space for the stack
            self._widget.ISMShowLastButton.setEnabled(False)

            # Initiate ISM Imaging
        
            try:
                # make sure there is no exisiting thrad 
                del self.ISMThread
            except:
                pass
                
            # this should decouple the hardware-related actions from the GUI - but it doesn't 
            self.isISMrunning = True
            self.ISMThread = threading.Thread(target=self.takeISMImageThread, args=(), daemon=True)
            self.ISMThread.start()
        else:            
            self.isISMrunning = False
            self._widget.ISMStartButton.setEnabled(True)


    def stopISM(self):
        self.isISMrunning = False
        
        self._widget.setText("Stopping timelapse...")

        self._widget.ISMStartButton.setEnabled(True)
        try:
            del self.timer
        except:
            pass

        try:
            del self.ISMThread
        except:
            pass
        
        self._widget.setText("Done wit timelapse...")
    
        # store old values for later
        self.lasers[0].setValue(self.Laser1ValueOld)            


    def showLast(self):
        try:
            self._widget.setImage(self.LastStackLaser1ArrayLast, colormap="green", name="GFP")
        except  Exception as e:
            self._logger.error(e)

        try:
            self._widget.setImage(self.LastStackLaser2ArrayLast, colormap="red", name="Red")
        except Exception as e:
            self._logger.error(e)
            
        try:
            self._widget.setImage(self.LastStackLEDArrayLast, colormap="gray", name="Brightfield")
        except  Exception as e:
            self._logger.error(e)

    def displayStack(self, im):
        """ Displays the image in the view. """
        self._widget.setImage(im)


            
        
    def takeISMImageThread(self):
        # this wil run i nthe background
        self._logger.debug("Take ISM images")
        
        # reserve and free space for displayed stacks
        self.LastStackLaser1 = []
        
        for iISMimage in range(16*16):
            # 1: Display ISM Frame
            ismPatternIndex = self.getISMFrame(nFrame=iISMimage)
            self._widget.setText("Displaying pattern # "+str(iISMimage))
            self.laser.sendScannerPattern(ismPatternIndex, scannernFrames=10,
                scannerLaserVal=32000,
                scannerExposure=500, scannerDelay=500, isBlocking=False)
            filePath = self.getSaveFilePath(date=self.ISMDate, filename=f'{self.ISMFilename}_{iISMimage}', extension=".tif")
            time.sleep(self.tUnshake) # wait for display
            lastFrame = self.detector.getLatestFrame()
            self.LastStackLaser1.append(lastFrame)
            tif.imwrite(filePath, lastFrame, append=True)

            self.nImages += 1
            self._widget.setText(self.nImages)

        self.isISMrunning = False

        self.LastStackLaser1ArrayLast = np.array(self.LastStackLaser1)
        self._widget.ISMShowLastButton.setEnabled(True)
        self._widget.ISMStartButton.setEnabled(True)
        

    def switchOffIllumination(self):
        # switch off all illu sources
        for lasers in self.lasers:
            lasers.setEnabled(False)
            self.lasers[1].setValue(0)
            time.sleep(0.1)
        try:
            self.illu.setAll((0,0,0))
        except:
            pass

        
    def valueLaser1Changed(self, value):
        self.Laser1Value= value
        #self.lasers[0].setEnabled(True)
        self.lasers[0].setValue(self.Laser1Value)

    def valueLaser2Changed(self, value):
        self.Laser2Value= value
        self.lasers[1].setValue(self.Laser2Value)

    def valueLEDChanged(self, value):
        self.LEDValue= value
        self.lasers[1].setValue(self.LEDValue)
                
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
