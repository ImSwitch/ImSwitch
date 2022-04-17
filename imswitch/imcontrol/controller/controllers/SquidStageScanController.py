import numpy as np
import NanoImagingPack as nip
import time
import threading

from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex
from imswitch.imcontrol.view import guitools
from imswitch.imcommon.model import initLogger
from ..basecontrollers import LiveUpdatedController


class SquidStageScanController(LiveUpdatedController):
    """ Linked to SquidStageScanWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self, tryInheritParent=False)
        
        # Prepare image computation worker
        self.imageComputationWorker = self.SquidStageScanImageComputationWorker()
        self.imageComputationWorker.setCoordinates((1,2,3,4))
        self.imageComputationWorker.setPixelsize(1.)
        self.imageComputationWorker.sigSquidStageScanImageComputed.connect(self.displayImage)
   
        self.imageComputationThread = Thread()
        self.imageComputationWorker.moveToThread(self.imageComputationThread)
        self.sigImageReceived.connect(self.imageComputationWorker.computeSquidStageScanImage)
        self.imageComputationThread.start()

        # Connect CommunicationChannel signals
        self._commChannel.sigUpdateImage.connect(self.update)

        # Connect SquidStageScanWidget signals
        
        
        # connect camera and stage
        self.cameraName = self._master.detectorsManager.getAllDeviceNames()[0]
        self.camera = self._master.detectorsManager[self.cameraName]
        
        self.positionerName = self._master.positionersManager.getAllDeviceNames()[0]
        self.positioner = self._master.positionersManager[self.positionerName]

        # Connect buttons
        self.isScanRunning = False
        self.isHoming = False
        self.isHomed = False
        self._widget.btnStart.clicked.connect(self.startScan)
        self._widget.btnHome.clicked.connect(self.startHoming)
        
        self.stageCoordinates(self._widget.getCoordinates())
        self.pixelSize(self._widget.getPixelsize())
        self.coordinates = (0,0,0,0)
        
    def __del__(self):
        self.imageComputationThread.quit()
        self.imageComputationThread.wait()        
        if hasattr(super(), '__del__'):
            super().__del__()
            
    def startHoming(self):
        self._logger.debug("Start Homing")
        self.imageComputationWorker.startHoming(self.positioner)
        
    def startScan(self):
        # Update values
        self.stageCoordinates(self._widget.getCoordinates())
        self.pixelSize(self._widget.getPixelsize())

        # start/stop scan
        if not self.isScanRunning:
            self._logger.debug("Start Scanning")
            self.imageComputationWorker.startScan(self.positioner,self.camera,self.coordinates, self.pixelsize)
            self.isScanRunning = True
        else:
            self._logger.debug("Stop Scanning")
            self.imageComputationWorker.stopScan(self.positioner)
            self.isScanRunning = False
    
    def stageCoordinates(self, coordinates):
        self._logger.debug("Coordinates: "+str(coordinates))
        self.coordinates = np.float32(coordinates)
        
    def pixelSize(self, pixelsize):
        self._logger.debug("pixelsize: "+str(pixelsize))
        self.pixelsize = pixelsize

    def displayImage(self, im):
        """ Displays the image in the view. """
        self._widget.setImage(im)
        
    '''
    def update(self, detectorName, im, init, isCurrentDetector):
        """ Update with new detector frame. """
        if not isCurrentDetector or not self.active:
            return

        if self.it == self.updateRate:
            self.it = 0
            self.imageComputationWorker.prepareForNewImage(im)
            self.sigImageReceived.emit()
        else:
            self.it += 1

    def changeRate(self, updateRate):
        """ Change update rate. """
        self.updateRate = updateRate
        self.it = 0
    '''

    class SquidStageScanImageComputationWorker(Worker):
        sigSquidStageScanImageComputed = Signal(np.ndarray)

        def __init__(self):
            super().__init__()
            
            self._logger = initLogger(self, tryInheritParent=False)
            self._numQueuedImages = 0
            self._numQueuedImagesMutex = Mutex()
            self.pixelsize = 1
            self.stopScan = False
            self.intensityMap = []

        def computeSquidStageScanImage(self):
            """ Compute SquidStageScan of an image. """
            pass
        
        def imageComputationThread(self):
            pass

        def startHoming(self, positioner):
            positioner.homing()
            self.isHomed = False
            while(positioner.is_busy()):
                time.sleep(.1)
                # wait until we arrive at the home position
            self.isHomed = True

        def startScan(self, positioner, detector, coordinates, pixelsize):
            self.intensityMap = []
            self.stopScan = False
            xmin,xmax,ymin,ymax = coordinates[0],coordinates[1],coordinates[2],coordinates[3] # * not working?
            self.currentPosition = positioner.getPosition() # xyz
            # detector determine 
            # detector.width
            detector.startAcquisition()
            NPixelY = detector.shape[-1]
            fovY = float(pixelsize)*NPixelY
            NPixelY = 1000
            NScansY = int((ymax-ymin)//int(fovY))

            mCoordY = 0            
            for iScan in range(NScansY):
                # we want to scan the entire FOV spanned by min/max x/y 
                # snake scan
                
                # move as fast as you can
                positioner.move(mCoordY,"Y")
                if iScan%2:
                    mCoordX = xmin
                else:
                    mCoordX = xmax
                positioner.move(mCoordX,"X")
                self._logger.debug("X/Y: "+str((mCoordX,mCoordY)))
                
                while positioner.is_busy:
                    # capture images and assign them to xy locations
                    # while the stage is scanning at fullspeed
                    if self.stopScan:
                        break
                    mMeanImage = np.mean(detector.getLatestFrame())
                    mPos = positioner.getPosition()
                    self.intensityMap.append((mMeanImage, mPos))

                mCoordY += (fovY)
                
            positioner.homing()

        def stopScan(self):
            self.stopScan = True

            
            
            
        '''
            try:
                if self._numQueuedImages > 1:
                    return  # Skip this frame in order to catch up
                SquidStageScanrecon = np.flip(np.abs(self.reconSquidStageScan(self._image, PSFpara=self.PSFpara, N_subroi=1024, pixelsize=self.pixelsize, dz=self.dz)),1)
                
                self.sigSquidStageScanImageComputed.emit(np.array(SquidStageScanrecon))
            finally:
                self._numQueuedImagesMutex.lock()
                self._numQueuedImages -= 1
                self._numQueuedImagesMutex.unlock()
        

        def prepareForNewImage(self, image):
            """ Must always be called before the worker receives a new image. """
            self._image = image
            self._numQueuedImagesMutex.lock()
            self._numQueuedImages += 1
            self._numQueuedImagesMutex.unlock()
            '''

        def setPixelsize(self, dz):
            self.dz = dz
        
        def setCoordinates(self, pixelsize):
            self.pixelsize = pixelsize


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
