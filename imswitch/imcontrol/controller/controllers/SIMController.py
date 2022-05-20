import json
import os

import numpy as np
import time 

from imswitch.imcommon.model import dirtools, initLogger, APIExport
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex, Timer

from ..basecontrollers import LiveUpdatedController

import NanoImagingPack as nip

from napari_sim_processor.convSimProcessor import ConvSimProcessor
from napari_sim_processor.hexSimProcessor import HexSimProcessor

class SIMController(LiveUpdatedController):
    """Linked to SIMWidget."""
    
    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        self.it=0
        self.updateRate=5

        
        self.simDir = os.path.join(dirtools.UserFileDirs.Root, 'imcontrol_sim')
        if not os.path.exists(self.simDir):
            os.makedirs(self.simDir)

        if self._setupInfo.sim is None:
            self._widget.replaceWithError('SIM is not configured in your setup file.')
            return

        self._widget.initSIMDisplay(self._setupInfo.sim.monitorIdx)
        # self.loadPreset(self._defaultPreset)

        # Connect CommunicationChannel signals
        self._commChannel.sigSIMMaskUpdated.connect(self.displayMask)

        # Connect SIMWidget signals
        self._widget.controlPanel.saveButton.clicked.connect(self.saveParams)
        self._widget.controlPanel.loadButton.clicked.connect(self.loadParams)

        self._widget.applyChangesButton.clicked.connect(self.applyParams)
        self._widget.startSIMAcquisition.clicked.connect(self.startSIM)
        self._widget.stopSIMAcquisition.clicked.connect(self.stopSIM)
        self._widget.sigSIMDisplayToggled.connect(self.toggleSIMDisplay)
        self._widget.sigSIMMonitorChanged.connect(self.monitorChanged)
        self._widget.sigPatternID.connect(self.patternIDChanged)
        
        # sim parameters
        self.patternID = 0
        self.nRotations = 3
        self.nPhases = 3
        self.allFrames = []
        
        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]
        
        # setup worker/background thread
        self.imageComputationWorker = self.SIMProcessorWorker(self.detector, self.simPatternByID,self.nPhases,self.nRotations)
        self.imageComputationWorker.sigSIMProcessorImageComputed.connect(self.displayImage)
        
        self.imageComputationThread = Thread()
        self.imageComputationWorker.moveToThread(self.imageComputationThread)
        self.sigImageReceived.connect(self.imageComputationWorker.computeSIMImage)
        self.imageComputationThread.start()

        # Initial SIM display
        self._commChannel.sigUpdateImage.connect(self.update)

        # show placeholder pattern
        initPattern = self._master.simManager.allPatterns[self.patternID]
        self._widget.updateSIMDisplay(initPattern)


    def __del__(self):
        self.imageComputationThread.quit()
        self.imageComputationThread.wait()

    def toggleSIMDisplay(self, enabled):
        self._widget.setSIMDisplayVisible(enabled)

    def monitorChanged(self, monitor):
        self._widget.setSIMDisplayMonitor(monitor)
        
    def patternIDChanged(self, patternID):
        self.patternID = patternID

    def displayMask(self, image):
        self._widget.updateSIMDisplay(image)

    
    def update(self, detectorName, im, init, isCurrentDetector):
        """ Update with new detector frame. """
        if not isCurrentDetector or not self.active:
            return

                
        if self.it >= self.updateRate:
            self.it = 0

            # dispaly sim pattern
            if(self._master.simManager.isSimulation):
                iPhi = self.patternID%self.nPhases
                iRot = self.patternID//self.nRotations
                self.setIlluPatternByID(iRot, iPhi)
            else:
                pass
            
            # this does not correlate with simulated patterns! 
            self.__logger.debug(self.patternID)   
            self.simPatternByID(self.patternID)
            self.allFrames.append(im)
            
            # wait for frame to be displayed? 
            time.sleep(.1)
            self.patternID+=1
            
            # if all patterns are acquired => reconstruct
            if self.patternID>=(self.nRotations*self.nPhases):
                # process the frames and display
                allFramesNP = np.array(self.allFrames)
                self.imageComputationWorker.prepareForNewSIMStack(allFramesNP)
                self.sigImageReceived.emit()

                from datetime import datetime
                date = datetime. now(). strftime("%Y_%m_%d-%I-%M-%S_%p")
                import tifffile as tif
                tif.imsave(f"filename_{date}.tif", allFramesNP)

                self.patternID=0
                self.allFrames = []

        else:
            self.it += 1

    def setIlluPatternByID(self, iRot, iPhi):
        self.detector.setIlluPatternByID(iRot, iPhi)

    def displayImage(self, im):
        """ Displays the image in the view. """
        self._widget.setImage(im)

    def saveParams(self):
        pass

    def loadParams(self):
        pass
    
    def applyParams(self):
        currentPattern = self._master.simManager.allPatterns[self.patternID]
        self.updateDisplayImage(currentPattern)
 
    def startSIM(self):
        self.active = True
        self.patternID = 0        
        self.iReconstructed = 0
        self.imageComputationWorker.setNumReconstructed(numReconstructed=self.iReconstructed)
 
    def stopSIM(self):
        self.active = False
        self.it = 0
        #self.imageComputationWorker.stopSIMacquisition()
 
    def updateDisplayImage(self, image):
        image = np.fliplr(image.transpose())
        self._widget.img.setImage(image, autoLevels=True, autoDownsample=False)
        self._widget.updateSIMDisplay(image)
        # self._logger.debug("Updated displayed image")

    @APIExport(runOnUIThread=True)
    def simPatternByID(self, patternID):
        currentPattern = self._master.simManager.allPatterns[patternID]
        self.updateDisplayImage(currentPattern)
        return currentPattern
   
    class SIMProcessorWorker(Worker):
        sigSIMProcessorImageComputed = Signal(np.ndarray)
        
        def __init__(self, detector, displayFct, nPhases=3, nRotations=3):
            super().__init__()

            self._logger = initLogger(self, tryInheritParent=False)
            self._numQueuedImages = 0
            self.isRunning = False
            self.displayFct = displayFct
            self.detector = detector
            self.nPhases=nPhases
            self.nRotations=nRotations
            
            self.iReconstructed = 0
            
            self._numQueuedImages = 0
            self._numQueuedImagesMutex = Mutex()
            
            # initilaize the reconstructor
            self.processor = SIMProcessor()

        def setNumReconstructed(self, numReconstructed=0):
            self.iReconstructed = numReconstructed
            
        def computeSIMImage(self):
            """ Compute SIM of an image stack. """
            try:
                if self._numQueuedImages > 1:
                    return  # Skip this frame in order to catch up
                
                # Simulate SIM Stack
                #self._image = self.processor.simSimulator(Nx=512, Ny=512, Nrot=3, Nphi=3)
                
                # initialize the model 
                if self.iReconstructed == 0:
                    self.processor.setReconstructor()
                    self.processor.calibrate(self._image)
                SIMframe = self.processor.reconstruct(self._image)
                self.sigSIMProcessorImageComputed.emit(np.array(SIMframe))

                self.iReconstructed += 1

            finally:
                self._numQueuedImagesMutex.lock()
                self._numQueuedImages -= 1
                self._numQueuedImagesMutex.unlock()

        def prepareForNewSIMStack(self, image):
            """ Must always be called before the worker receives a new image. """
            self._image = image
            self._numQueuedImagesMutex.lock()
            self._numQueuedImages += 1
            self._numQueuedImagesMutex.unlock()
            


'''#####################################
# SIM PROCESSOR
#####################################'''

class SIMProcessor(object):
    
    def __init__(self):
        '''
        setup parameters
        '''
        self.mFile = "/Users/bene/Dropbox/Dokumente/Promotion/PROJECTS/MicronController/PYTHON/NAPARI-SIM-PROCESSOR/DATA/SIMdata_2019-11-05_15-21-42.tiff"
        self.phases_number = 3
        self.angles_number = 3
        self.magnification = 60
        self.NA = 1.05
        self.n = 1.33
        self.wavelength = 0.57
        self.pixelsize = 6.5
        self.dz= 0.55
        self.alpha = 0.5
        self.beta = 0.98
        self.w = 0.2
        self.eta = 0.65
        self.group = 30
        self.use_phases = True
        self.find_carrier = True
        self.pixelsize = 6.5
        self.isCalibrated = False
        self.use_phases =  True
        self.use_torch = False
        
        '''
        initialize
        '''

        # load images
        #import tifffile as tif
        #mImages = tif.imread(self.mFile)


        # set model
        #h = HexSimProcessor(); #
        self.h = ConvSimProcessor()
        self.k_shape = (3,1)

        # setup
        self.h.debug = False
        self.setReconstructor() 
        self.kx_input = np.zeros(self.k_shape, dtype=np.single)
        self.ky_input = np.zeros(self.k_shape, dtype=np.single)
        self.p_input = np.zeros(self.k_shape, dtype=np.single)
        self.ampl_input = np.zeros(self.k_shape, dtype=np.single)
        
    
    def setReconstructor(self):
        '''
        Sets the attributes of the Processor
        Executed frequently, upon update of several settings
        '''
       
        self.h.usePhases = self.use_phases
        self.h.magnification = self.magnification
        self.h.NA = self.NA
        self.h.n = self.n
        self.h.wavelength = self.wavelength
        self.h.pixelsize = self.pixelsize
        self.h.alpha = self.alpha
        self.h.beta = self.beta
        self.h.w = self.w
        self.h.eta = self.eta
        if not self.find_carrier:
            self.h.kx = self.kx_input
            self.h.ky = self.ky_input
        
    def get_current_stack_for_calibration(self,data):
        '''
        Returns the 4D raw image (angles,phases,y,x) stack at the z value selected in the viewer  
        '''
        if(0):
            data = np.expand_dims(np.expand_dims(data, 0), 0)
            dshape = data.shape # TODO: Hardcoded ...data.shape
            zidx = 0
            delta = group // 2
            remainer = group % 2
            zmin = max(zidx-delta,0)
            zmax = min(zidx+delta+remainer,dshape[2])
            new_delta = zmax-zmin
            data = data[...,zmin:zmax,:,:]
            phases_angles = phases_number*angles_number
            rdata = data.reshape(phases_angles, new_delta, dshape[-2],dshape[-1])            
            cal_stack = np.swapaxes(rdata, 0, 1).reshape((phases_angles * new_delta, dshape[-2],dshape[-1]))
        return data


    def calibrate(self, imRaw):
        '''
        calibration
        '''
        
        #imRaw = get_current_stack_for_calibration(mImages)         
        if self.use_torch:
            self.h.calibrate_pytorch(imRaw,self.find_carrier)
        else:
            self.h.calibrate(imRaw,self.find_carrier)
        self.isCalibrated = True
        if self.find_carrier: # store the value found   
            self.kx_input = self.h.kx  
            self.ky_input = self.h.ky
            self.p_input = self.h.p
            self.ampl_input = self.h.ampl 
    

    def reconstruct(self, currentImage):
        '''
        reconstruction
        '''
        assert self.isCalibrated, 'SIM processor not calibrated, unable to perform SIM reconstruction'
        dshape= currentImage.shape
        phases_angles = self.phases_number*self.angles_number
        rdata = currentImage.reshape(phases_angles, dshape[-2],dshape[-1])
        if self.use_torch:
            imageSIM = self.h.reconstruct_pytorch(rdata.astype(np.float32)) #TODO:this is left after conversion from torch
        else:
            imageSIM = self.h.reconstruct_rfftw(rdata)
            
        return imageSIM
        
    def simSimulator(self, Nx=512, Ny=512, Nrot=3, Nphi=3):
        Isample = np.zeros((Nx,Ny))
        Isample[np.random.random(Isample.shape)>0.999]=1
        

        allImages = []
        for iRot in range(Nrot):
            for iPhi in range(Nphi):
                IGrating = 1+np.sin(((iRot/Nrot)*nip.xx((Nx,Ny))+(Nrot-iRot)/Nrot*nip.yy((Nx,Ny)))*np.pi/2+np.pi*iPhi/Nphi)
                allImages.append(nip.gaussf(IGrating*Isample,3))
                
        allImages=np.array(allImages)
        allImages-=np.min(allImages)
        allImages/=np.max(allImages)
        return allImages



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
