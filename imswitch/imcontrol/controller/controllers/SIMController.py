    
import json
import os

import numpy as np
import time
import threading
from datetime import datetime
import tifffile as tif

from imswitch.imcommon.model import dirtools, initLogger, APIExport
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex, Timer

from ..basecontrollers import LiveUpdatedController

import os
import time
import numpy as np
from pathlib import Path
import tifffile

try:
    import mcsim
    ismcSIM=True
except:
    ismcSIM=False

if ismcSIM:
    try:
        import cupy as cp
        from mcsim.analysis import sim_reconstruction as sim
        isGPU = True
    except:
        print("GPU not available")
        import numpy as cp 
        from mcsim.analysis import sim_reconstruction as sim
        isGPU = False

try:
    import NanoImagingPack as nip
    isNIP = True
except:
    isNIP = False


try:
    from napari_sim_processor.convSimProcessor import ConvSimProcessor
    from napari_sim_processor.hexSimProcessor import HexSimProcessor
    isSIM = True
    
except:
    isSIM = False

try:
    import torch
    isPytorch = True
except:
    isPytorch = False

isDEBUG = False

class SIMController(ImConWidgetController):
    """Linked to SIMWidget."""

    sigImageReceived = Signal()
    sigSIMProcessorImageComputed = Signal(np.ndarray)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self)
        self.nSyncCameraSLM = 1  # 5 frames will be captured before a frame is retrieved from buffer for prcoessing 
        self.iSyncCameraSLM = 0 # counter for syncCameraSLM

        # switch to detect if a recording is in progress
        self.isRecording = False
        
        # we can switch between mcSIM and napari
        self.reconstructionMethod = "napari" # or "mcSIM"

        # save directory of the reconstructed frames
        self.simDir = os.path.join(dirtools.UserFileDirs.Root, 'imcontrol_sim')
        if not os.path.exists(self.simDir):
            os.makedirs(self.simDir)

        # load config file
        if self._setupInfo.sim is None:
            self._widget.replaceWithError('SIM is not configured in your setup file.')
            return

        # initialize external dispaly (if available => id = 2?)
        self._widget.initSIMDisplay(self._setupInfo.sim.monitorIdx)
        # self.loadPreset(self._defaultPreset)

        # Connect CommunicationChannel signals
        self._commChannel.sigSIMMaskUpdated.connect(self.displayMask)

        # Connect SIMWidget signals
        #self._widget.controlPanel.saveButton.clicked.connect(self.saveParams)
        #self._widget.controlPanel.loadButton.clicked.connect(self.loadParams)

        #self._widget.applyChangesButton.clicked.connect(self.applyParams)
        self._widget.startSIMAcquisition.clicked.connect(self.startSIM)
        self._widget.isRecordingButton.clicked.connect(self.toggleRecording)
        self._widget.stopSIMAcquisition.clicked.connect(self.stopSIM)
        #self._widget.sigSIMDisplayToggled.connect(self.toggleSIMDisplay)
        #self._widget.sigSIMMonitorChanged.connect(self.monitorChanged)
        #self._widget.sigPatternID.connect(self.patternIDChanged)

        # sim parameters
        self.patternID = 0
        self.nRotations = 3
        self.nPhases = 3

        # se    ect lasers
        allLaserNames = self._master.lasersManager.getAllDeviceNames()
        self.lasers = []
        for iDevice in allLaserNames:
            if iDevice.lower().find("laser")>=0 or iDevice.lower().find("led"):
                self.lasers.append(self._master.lasersManager[iDevice])


        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]

        # show placeholder pattern
        initPattern = self._master.simManager.allPatterns[self.patternID]
        self._widget.updateSIMDisplay(initPattern)

        # activate hamamatsu slm if necessary
        if self._master.simManager.isHamamatsuSLM:
            self.IS_HAMAMATSU = True
            self.initHamamatsuSLM()
        else:
            self.IS_HAMAMATSU = False

        # enable display of SIM pattern by default 
        self.toggleSIMDisplay(enabled=True)

        # initialize SIM processor
        self.processor = SIMProcessor()
        
        # connect the reconstructed image to the displayer
        self.sigSIMProcessorImageComputed.connect(self.displayImage)
        



    def initHamamatsuSLM(self):
        self.hamamatsuslm = nip.HAMAMATSU_SLM() # FIXME: Add parameters
        #def __init__(self, dll_path = None, OVERDRIVE = None, use_corr_pattern = None, wavelength = None, corr_pattern_path = None):
        allPatterns = self._master.simManager.allPatterns[self.patternID]
        for im_number, im in enumerate(allPatterns):
            self.hamamatsuslm.send_dat(im, im_number)

    def __del__(self):
        self.imageComputationThread.quit()
        self.imageComputationThread.wait()

    def toggleSIMDisplay(self, enabled=True):
        self._widget.setSIMDisplayVisible(enabled)

    def monitorChanged(self, monitor):
        self._widget.setSIMDisplayMonitor(monitor)

    def patternIDChanged(self, patternID):
        self.patternID = patternID

    def displayMask(self, image):
        self._widget.updateSIMDisplay(image)

    def setIlluPatternByID(self, iRot, iPhi):
        self.detector.setIlluPatternByID(iRot, iPhi)

    def displayImage(self, im):
        """ Displays the image in the view. """
        self._widget.setImage(im, name="SIM Reconstruction")

    def saveParams(self):
        pass

    def loadParams(self):
        pass

    def applyParams(self):
        currentPattern = self._master.simManager.allPatterns[self.patternID]
        self.updateDisplayImage(currentPattern)

    def startSIM(self):
        # start live processing => every frame is captured by the update() function. It also handles the pattern addressing
        self.iReconstructed = 0
        #  Start acquisition if not started already
        self._master.detectorsManager.startAcquisition(liveView=False)
        
        # reset the pattern iterator
        self.nSyncCameraSLM = self._widget.getFrameSyncVal()

        self.active = True
        self.simThread = threading.Thread(target=self.performSIMExperimentThread, args=(), daemon=True)
        self.simThread.start()
        self._widget.startSIMAcquisition.setEnabled(False)
        
    def toggleRecording(self):
        self.isRecording = not self.isRecording
        if self.isRecording:
            self._widget.isRecordingButton.setText("Stop Recording")
        else:
            self._widget.isRecordingButton.setText("Start Recording")

    def stopSIM(self):
        # stop live processing 
        self.active = False
        self._master.detectorsManager.startAcquisition(liveView=True)
        self.simThread.join()
        self._widget.startSIMAcquisition.setEnabled(True)
        
    def updateDisplayImage(self, image):
        image = np.fliplr(image.transpose())
        self._widget.img.setImage(image, autoLevels=True, autoDownsample=False)
        self._widget.updateSIMDisplay(image)
        # self._logger.debug("Updated displayed image")

    @APIExport(runOnUIThread=True)
    def simPatternByID(self, patternID):
        try:
            currentPattern = self._master.simManager.allPatterns[patternID]
            self.updateDisplayImage(currentPattern)
            return currentPattern
        except Exception as e:
            self._logger.error(e)
            
    def performSIMExperimentThread(self):
        """ 
        Iterate over all SIM patterns, display them and acquire images 
        """     
        SIMstack = []
        self.patternID = 0
        self.isReconstructing = False
        while self.active:
            # 1 display the pattern
            self.simPatternByID(self.patternID)    
            
            # 2 grab a frame 
            frame = self.detector.getLatestFrame()
            SIMstack.append(frame)
            
            # 3 add the frame to the list 
            if len(SIMstack)>=(self.nRotations*self.nPhases):
                # We will collect N*M images and process them with the SIM processor
                # process the frames and display
                self.patternID = 0
                if not self.isReconstructing:
                    self.isReconstructing=True
                    self.mReconstructionThread = threading.Thread(target=self.reconstructSIMStack, args=(SIMstack.copy(),), daemon=True)
                    self.mReconstructionThread.start()
                SIMstack = []
                
            self.patternID+=1
        
    def reconstructSIMStack(self, imageStack):
        '''
        reconstruct the image stack asychronously
        '''
        self.allFramesNP = np.array(imageStack)
        self.allFramesList = imageStack
        if self.isRecording:
            date = datetime. now(). strftime("%Y_%m_%d-%I-%M-%S_%p")
            mFilename = f"filename_{date}.tif"
            # TODO: implement this as a qeue
            threading.Thread(target=self.saveImageInBackground, args=(self.allFramesNP,mFilename,), daemon=True).start()
            # FIXME: This is not how we should do it, but how can we tell the compute SimImage to process the images in background?!
        
        # compute image
        # initialize the model
        self._logger.debug("Processing frames")
        if not self.processor.getIsCalibrated():
            self.processor.setReconstructor()
            self.processor.calibrate(self.allFramesNP)
        SIMframe = self.processor.reconstruct(self.allFramesNP)
        self.sigSIMProcessorImageComputed.emit(np.array(SIMframe))

        self.iReconstructed += 1
        self.isReconstructing = False

    def saveImageInBackground(self, image, filename):
        tif.imsave(filename, image)
        self._logger.debug("Saving file: "+filename)

        '''
                     # capture image for every illumination
                if self.Laser1Value>0 and len(self.lasers)>0:
                    filePath = self.getSaveFilePath(date=self.MCTDate,
                                timestamp=timestamp,
                                filename=f'{self.MCTFilename}_Laser1_i_{imageIndex}_Z_{iZ}_X_{xyScanStepsAbsolute[ipos][0]}_Y_{xyScanStepsAbsolute[ipos][1]}',
                                extension=fileExtension)
                    self.lasers[0].setValue(self.Laser1Value)
                    self.lasers[0].setEnabled(True)
                    lastFrame = self.detector.getLatestFrame()
                    tif.imwrite(filePath, lastFrame, append=True)
                    self.lasers[0].setEnabled(False)
                    self.LastStackLaser1.append(lastFrame.copy())

                if self.Laser2Value>0 and len(self.lasers)>0:
                    filePath = self.getSaveFilePath(date=self.MCTDate,
                                timestamp=timestamp,
                                filename=f'{self.MCTFilename}_Laser2_i_{imageIndex}_Z_{iZ}_X_{xyScanStepsAbsolute[ipos][0]}_Y_{xyScanStepsAbsolute[ipos][1]}',
                                extension=fileExtension)
                    self.lasers[1].setValue(self.Laser2Value)
                    self.lasers[1].setEnabled(True)
                    lastFrame = self.detector.getLatestFrame()
                    tif.imwrite(filePath, lastFrame, append=True)
                    self.lasers[1].setEnabled(False)
                    self.LastStackLaser2.append(lastFrame.copy())
        '''
            
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
        self.use_torch = isPytorch
        
        # initialize logger
        self._logger = initLogger(self, tryInheritParent=False)

        # switch for the different reconstruction algorithms
        self.reconstructionMethod = "napari"

        '''
        initialize
        '''

        # load images
        #import tifffile as tif
        #mImages = tif.imread(self.mFile)


        # set model
        #h = HexSimProcessor(); #
        if isSIM:
            self.h = ConvSimProcessor()
            self.k_shape = (3,1)
        else:
            self._logger.error("Please install napari sim! pip install napari-sim-processor")

        # setup
        self.h.debug = False
        self.setReconstructor()
        self.kx_input = np.zeros(self.k_shape, dtype=np.single)
        self.ky_input = np.zeros(self.k_shape, dtype=np.single)
        self.p_input = np.zeros(self.k_shape, dtype=np.single)
        self.ampl_input = np.zeros(self.k_shape, dtype=np.single)
        
        # set up the GPU for mcSIM
        if isGPU:
            # GPU memory usage
            mempool = cp.get_default_memory_pool()
            pinned_mempool = cp.get_default_pinned_memory_pool()
            memory_start = mempool.used_bytes()


    def setReconstructionMethod(self, method):
        self.reconstructionMethod = method

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
        self._logger.error("get_current_stack_for_calibration not implemented yet")
        '''
        Returns the 4D raw image (angles,phases,y,x) stack at the z value selected in the viewer

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
        '''
        return data


    def calibrate(self, imRaw):
        '''
        calibration
        '''
        self._logger.debug("Starting to calibrate the stack")
        if self.reconstructionMethod == "napari":
            #imRaw = get_current_stack_for_calibration(mImages)
            if self.use_torch:
                self.h.calibrate_pytorch(imRaw, self.find_carrier)
            else:
                self.h.calibrate(imRaw, self.find_carrier)
            self.isCalibrated = True
            if self.find_carrier: # store the value found
                self.kx_input = self.h.kx
                self.ky_input = self.h.ky
                self.p_input = self.h.p
                self.ampl_input = self.h.ampl
            self._logger.debug("Done calibrating the stack")
        elif self.reconstructionMethod == "mcSIM":
            """
            test running SIM reconstruction at full speed on GPU
            """
                        # physical parameters
            na = 1.3 # numerical aperture
            dxy = 0.065 # um
            wavelength = 0.488 # um


            # ############################
            # for the first image, estimate the SIM parameters
            # this step is slow, can take ~1-2 minutes
            # ############################
            print("running initial reconstruction with full parameter estimation")
            imgset = sim.SimImageSet({"pixel_size": dxy,
                                    "na": na,
                                    "wavelength": wavelength},
                                    imRaw,
                                    otf=None,
                                    wiener_parameter=0.3,
                                    frq_estimation_mode="band-correlation",
                                    # frq_guess=frqs_gt, # todo: can add frequency guesses for more reliable fitting
                                    phase_estimation_mode="wicker-iterative",
                                    phases_guess=np.array([[0, 2*np.pi / 3, 4 * np.pi / 3],
                                                            [0, 2*np.pi / 3, 4 * np.pi / 3],
                                                            [0, 2*np.pi / 3, 4 * np.pi / 3]]),
                                    combine_bands_mode="fairSIM",
                                    fmax_exclude_band0=0.4,
                                    normalize_histograms=False,
                                    background=100,
                                    gain=2,
                                    use_gpu=True)
            
            # this included parameter estimation
            imgset.reconstruct()
            # extract estimated parameters
            self.mcSIMfrqs = imgset.frqs
            self.mcSIMphases = imgset.phases - np.expand_dims(imgset.phase_corrections, axis=1)
            self.mcSIMmod_depths = imgset.mod_depths
            self.mcSIMotf = imgset.otf

            # clear GPU memory
            imgset.delete()
            
    def getIsCalibrated(self):
        return self.isCalibrated

    def reconstruct(self, currentImage):
        '''
        reconstruction
        '''
        if self.reconstructionMethod == "napari":
            # we use the napari reconstruction method   
            self._logger.debug("reconstructing the stack with napari") 
            assert self.isCalibrated, 'SIM processor not calibrated, unable to perform SIM reconstruction'
            
            dshape= currentImage.shape
            phases_angles = self.phases_number*self.angles_number
            rdata = currentImage[:phases_angles, :, :].reshape(phases_angles, dshape[-2],dshape[-1])
            if self.use_torch:
                imageSIM = self.h.reconstruct_pytorch(rdata.astype(np.float32)) #TODO:this is left after conversion from torch
            else:
                imageSIM = self.h.reconstruct_rfftw(rdata)

            return imageSIM
        
        elif self.reconstructionMethod == "mcSIM":
            """
            test running SIM reconstruction at full speed on GPU
            """

            '''
            # load images
            root_dir = os.path.join(Path(__file__).resolve().parent, 'data')
            fname_data = os.path.join(root_dir, "synthetic_microtubules_512.tif")
            imgs = tifffile.imread(fname_data)
            '''
            self._logger.debug("reconstructing the stack with mcsim") 

            imgset_next = sim.SimImageSet({"pixel_size": self.dxy,
                                        "na": self.na,
                                        "wavelength": self.wavelength},
                                        currentImage,
                                        otf=self.mcSIMotf,
                                        wiener_parameter=0.3,
                                        frq_estimation_mode="fixed",
                                        frq_guess=self.mcSIMfrqs,
                                        phase_estimation_mode="fixed",
                                        phases_guess=self.mcSIMphases,
                                        combine_bands_mode="fairSIM",
                                        mod_depths_guess=self.mcSIMmod_depths,
                                        use_fixed_mod_depths=True,
                                        fmax_exclude_band0=0.4,
                                        normalize_histograms=False,
                                        background=100,
                                        gain=2,
                                        use_gpu=True,
                                        print_to_terminal=False)

            imgset_next.reconstruct()
            imageSIM = imgset_next.sim_sr.compute()
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
