import requests
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

import imswitch

from datetime import datetime

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
else:
    isGPU = False
    
try:
    import NanoImagingPack as nip
    isNIP = True
except:
    isNIP = False
    


try:
    from napari_sim_processor.processors.convSimProcessor import ConvSimProcessor
    from napari_sim_processor.processors.hexSimProcessor import HexSimProcessor
    isSIM = True
    
except:
    isSIM = False

try:
    # FIXME: This does not pass pytests!
    import torch
    isPytorch = True
except:
    isPytorch = False

isDEBUG = False

class SIMController(ImConWidgetController):
    """Linked to SIMWidget."""

    sigImageReceived = Signal(np.ndarray, str)
    sigSIMProcessorImageComputed = Signal(np.ndarray, str)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self)
        self.IS_FASTAPISIM=False
        self.IS_HAMAMATSU=False
        # switch to detect if a recording is in progress
        self.isRecording = False
        self.isRecordReconstruction = False

        # Laser flag
        self.LaserWL = 0
 
        self.simFrameVal = 0
        self.nsimFrameSyncVal = 1 

        # Choose which laser will be recorded
        self.is488 = True
        self.is635 = True

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

        # connect live update  https://github.com/napari/napari/issues/1110
        self.sigImageReceived.connect(self.displayImage)      
        
        # select lasers
        allLaserNames = self._master.lasersManager.getAllDeviceNames()
        self.lasers = []
        for iDevice in allLaserNames:
            if iDevice.lower().find("laser")>=0 or iDevice.lower().find("led"):
                self.lasers.append(self._master.lasersManager[iDevice])
        
        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]

        # select positioner
        self.positioner = self._master.positionersManager['ESP32Stage']
        
        # setup the SIM processors
        sim_parameters = SIMParameters()
        self.SimProcessorLaser1 = SIMProcessor(self, sim_parameters, wavelength=sim_parameters.wavelength_1)
        self.SimProcessorLaser2 = SIMProcessor(self, sim_parameters, wavelength=sim_parameters.wavelength_2)

        # Connect CommunicationChannel signals
        self.sigSIMProcessorImageComputed.connect(self.displayImage)
        
        self.initFastAPISIM(self._master.simManager.fastAPISIMParams)
        
        if imswitch.IS_HEADLESS:
            return
        self._widget.start_button.clicked.connect(self.startSIM)
        self._widget.stop_button.clicked.connect(self.stopSIM)
        
        #self._widget.is488LaserButton.clicked.connect(self.toggle488Laser)
        #self._widget.is635LaserButton.clicked.connect(self.toggle635Laser)
        self._widget.checkbox_record_raw.stateChanged.connect(self.toggleRecording)
        self._widget.checkbox_record_reconstruction.stateChanged.connect(self.toggleRecordReconstruction)
        #self._widget.sigPatternID.connect(self.patternIDChanged)
        self._widget.number_dropdown.currentIndexChanged.connect(self.patternIDChanged)
        #self._widget.checkbox_reconstruction.stateChanged.connect(self.toggleRecording)
        # read parameters from the widget
        self._widget.start_timelapse_button.clicked.connect(self.startTimelapse)
        self._widget.start_zstack_button.clicked.connect(self.startZstack)

    def toggleRecording(self):
        self.isRecording = not self.isRecording
        if not self.isRecording:
            self.isActive = False
            
    def toggleRecordReconstruction(self):
        self.isRecordReconstruction = not self.isRecordReconstruction
        if not self.isRecordReconstruction:
            self.isActive = False
        
    
        
    def initFastAPISIM(self, params):
        self.fastAPISIMParams = params
        self.IS_FASTAPISIM = True
        
        # Usage example
        host = self.fastAPISIMParams["host"]
        port = self.fastAPISIMParams["port"]
        tWaitSequence = self.fastAPISIMParams["tWaitSquence"]

        if tWaitSequence is None:
            tWaitSequence = 0.1
        if host is None:
            host = "169.254.165.4"
        if port is None:
            port = 8000
        
        self.SIMClient = SIMClient(URL=host, PORT=port)
        self.SIMClient.set_pause(tWaitSequence)
                

    def initHamamatsuSLM(self):
        self.hamamatsuslm = nip.HAMAMATSU_SLM() # FIXME: Add parameters
        #def __init__(self, dll_path = None, OVERDRIVE = None, use_corr_pattern = None, wavelength = None, corr_pattern_path = None):
        allPatterns = self._master.simManager.allPatterns[self.patternID]
        for im_number, im in enumerate(allPatterns):
            self.hamamatsuslm.send_dat(im, im_number)

    def __del__(self):
        pass
        #self.imageComputationThread.quit()
        #self.imageComputationThread.wait()

    def toggleSIMDisplay(self, enabled=True):
        self._widget.setSIMDisplayVisible(enabled)

    def monitorChanged(self, monitor):
        self._widget.setSIMDisplayMonitor(monitor)

    def patternIDChanged(self, patternID):
        wl = self.getpatternWavelength()
        if wl == 'Laser 488nm':
            laserTag = 0
        elif wl == 'Laser 635nm':
            laserTag = 1
        else:
            laserTag = 0
            self._logger.error("The laser wavelenth is not implemented")    
        self.simPatternByID(patternID,laserTag)

    def getpatternWavelength(self):
        return self._widget.laser_dropdown.currentText()

    def displayMask(self, image):
        self._widget.updateSIMDisplay(image)

    def setIlluPatternByID(self, iRot, iPhi):
        self.detector.setIlluPatternByID(iRot, iPhi)

    def displayImage(self, im, name="SIM Reconstruction"):
        """ Displays the image in the view. """
        self._widget.setImage(im, name=name)

    def saveParams(self):
        pass

    def loadParams(self):
        pass
    
    def stopSIM(self):
        self.active = False
        self.simThread.join()
        self.lasers[0].setEnabled(False)
        self.lasers[1].setEnabled(False)
        self.detector.setParameter("trigger_source","Internal trigger")
        self.detector.setParameter("buffer_size",-1)
        self.detector.flushBuffers()


    def startSIM(self):
        #  need to be in trigger mode
        # therefore, we need to stop the camera first and then set the trigger mode
        self._commChannel.sigStopLiveAcquisition.emit(True)
        self.detector.setParameter("trigger_source","External start")
        self.detector.setParameter("buffer_size",9)
        self.detector.flushBuffers()
        #self._commChannel.sigStartLiveAcquistion.emit(True)
            
        # start the background thread
        self.active = True
        sim_parameters = self.getSIMParametersFromGUI()
        #sim_parameters["reconstructionMethod"] = self.getReconstructionMethod()
        #sim_parameters["useGPU"] = self.getIsUseGPU()
        self.simThread = threading.Thread(target=self.performSIMExperimentThread, args=(sim_parameters,), daemon=True)
        self.simThread.start()
    
    # for timelapse and zstack, check running is still needed also stop
    
    def startTimelapse(self):
        self._commChannel.sigStopLiveAcquisition.emit(True)
        self.detector.setParameter("trigger_source","External start")
        self.detector.setParameter("buffer_size",9)
        self.detector.flushBuffers()
        
        self.active = True
        sim_parameters = self.getSIMParametersFromGUI()
        
        timePeriod = int(self._widget.period_textedit.text())
        Nframes = int(self._widget.frames_textedit.text())
        self.oldTime = time.time()-timePeriod # to start the timelapse immediately
        iiter = 0
        # if it is nessary to put timelapse in background
        while iiter < Nframes:
            if time.time() - self.oldTime > timePeriod:
                self.oldTime = time.time()
                self.simThread = threading.Thread(target=self.performSIMTimelapseThread, args=(sim_parameters,), daemon=True)
                self.simThread.start()
                iiter += 1
        self._logger.debug("Timelapse finished")
        self.active = False
        self.lasers[0].setEnabled(False)
        self.lasers[1].setEnabled(False)
        self.detector.setParameter("trigger_source","Internal trigger")
        self.detector.setParameter("buffer_size",-1)
        self.detector.flushBuffers()

    def startZstack(self):
        self._commChannel.sigStopLiveAcquisition.emit(True)
        self.detector.setParameter("trigger_source","External start")
        self.detector.setParameter("buffer_size",9)
        self.detector.flushBuffers()
        
        self.active = True
        sim_parameters = self.getSIMParametersFromGUI()
        zMin = float(self._widget.zmin_textedit.text())
        zMax = float(self._widget.zmax_textedit.text())
        zStep = int(self._widget.nsteps_textedit.text())
        zDis = int((zMax - zMin) / zStep)
        self._master.detectorsManager
        #do Zstack in background
        self.simThread = threading.Thread(target=self.performSIMZstackThread, args=(sim_parameters,zDis,zStep), daemon=True)
        self.simThread.start()

    
    def toggle488Laser(self):
        self.is488 = not self.is488
        if self.is488:
            self._widget.is488LaserButton.setText("488 on")
        else:
            self._widget.is488LaserButton.setText("488 off")

    def toggle635Laser(self):
        self.is635 = not self.is635
        if self.is635:
            self._widget.is635LaserButton.setText("635 on")
        else:
            self._widget.is635LaserButton.setText("635 off")
        
    def updateDisplayImage(self, image):
        image = np.fliplr(image.transpose())
        self._widget.img.setImage(image, autoLevels=True, autoDownsample=False)
        self._widget.updateSIMDisplay(image)
        # self._logger.debug("Updated displayed image")

    @APIExport(runOnUIThread=True)
    def simPatternByID(self, patternID: int, wavelengthID: int):
        try:
            patternID = int(patternID)
            wavelengthID = int(wavelengthID)
            self.SIMClient.set_wavelength(wavelengthID)
            self.SIMClient.display_pattern(patternID)
            return wavelengthID
        except Exception as e:
            self._logger.error(e)

    @APIExport(runOnUIThread=True)
    def performSIMExperimentThread(self, sim_parameters):
        """ 
        Iterate over all SIM patterns, display them and acquire images 
        """     
        self.patternID = 0
        self.isReconstructing = False
        nColour = 2 #[488, 635]
        dic_wl = [488, 635]

        while self.active:
            
            for iColour in range(nColour):
                # toggle laser
                if not self.active:
                    break

                if iColour == 0 and self.is488 and self.lasers[iColour].power>0.0:
                    # enable laser 1
                    self.lasers[0].setEnabled(True)
                    self.lasers[1].setEnabled(False)
                    self._logger.debug("Switching to pattern"+self.lasers[0].name)
                    processor = self.SimProcessorLaser1
                    processor.setParameters(sim_parameters)
                    self.LaserWL = processor.wavelength
                    # set the pattern-path for laser wl 1
                elif iColour == 1 and self.is635 and self.lasers[iColour].power>0.0:
                    # enable laser 2
                    self.lasers[0].setEnabled(False)
                    self.lasers[1].setEnabled(True)
                    self._logger.debug("Switching to pattern"+self.lasers[1].name)
                    processor = self.SimProcessorLaser2
                    processor.setParameters(sim_parameters)                    
                    self.LaserWL = processor.wavelength
                    # set the pattern-path for laser wl 1
                else:
                    continue

                
                # select the pattern for the current colour
                self.SIMClient.set_wavelength(dic_wl[iColour])
                
                # display one round of SIM patterns for the right colour
                self.SIMClient.start_viewer_single_loop(1)
                
                # ensure lasers are off to avoid photo damage
                self.lasers[0].setEnabled(False)
                self.lasers[1].setEnabled(False)
                
                # download images from the camera    
                self.SIMStack = self.detector.getChunk(); self.detector.flushBuffers()
                if self.SIMStack is None:
                    self._logger.error("No image received")
                    continue
                self.sigImageReceived.emit(np.array(self.SIMStack),"SIMStack"+str(processor.wavelength))
                processor.setSIMStack(self.SIMStack)
                processor.getWF(self.SIMStack)

                # activate recording in processor 
                processor.setRecordingMode(self.isRecording)
                processor.setReconstructionMode(self.isRecordReconstruction)
                processor.setWavelength(self.LaserWL,sim_parameters)
                
                # store the raw SIM stack
                if self.isRecording and self.lasers[iColour].power>0.0:
                    date = datetime. now(). strftime("%Y_%m_%d-%I-%M-%S_%p")
                    processor.setDate(date)
                    mFilenameStack = f"{date}_SIM_Stack_{self.LaserWL}nm.tif"
                    threading.Thread(target=self.saveImageInBackground, args=(self.SIMStack, mFilenameStack,), daemon=True).start()
                # self.detector.stopAcquisition()
                # We will collect N*M images and process them with the SIM processor
                
                # process the frames and display
                processor.reconstructSIMStack()
                    
                # reset the per-colour stack to add new frames in the next imaging series
                processor.clearStack()
    

    def performSIMTimelapseThread(self, sim_parameters):
        """ 
        Do timelapse SIM 
        Q: should it have a separate thread?
        """     
        self.isReconstructing = False
        nColour = 2 #[488, 635]
        dic_wl = [488, 635]
        for iColour in range(nColour):
            # toggle laser
            if not self.active:
                break

            if iColour == 0 and self.is488 and self.lasers[iColour].power>0.0:
                # enable laser 1
                self.lasers[0].setEnabled(True)
                self.lasers[1].setEnabled(False)
                self._logger.debug("Switching to pattern"+self.lasers[0].name)
                processor = self.SimProcessorLaser1
                processor.setParameters(sim_parameters)
                self.LaserWL = processor.wavelength
                # set the pattern-path for laser wl 1
            elif iColour == 1 and self.is635 and self.lasers[iColour].power>0.0:
                # enable laser 2
                self.lasers[0].setEnabled(False)
                self.lasers[1].setEnabled(True)
                self._logger.debug("Switching to pattern"+self.lasers[1].name)
                processor = self.SimProcessorLaser2
                processor.setParameters(sim_parameters)                    
                self.LaserWL = processor.wavelength
                # set the pattern-path for laser wl 1
            else:
                continue

            
            # select the pattern for the current colour
            self.SIMClient.set_wavelength(dic_wl[iColour])
            
            # display one round of SIM patterns for the right colour
            self.SIMClient.start_viewer_single_loop(1)
            
            # ensure lasers are off to avoid photo damage
            self.lasers[0].setEnabled(False)
            self.lasers[1].setEnabled(False)
            
            # download images from the camera    
            self.SIMStack = self.detector.getChunk(); self.detector.flushBuffers()
            if self.SIMStack is None:
                self._logger.error("No image received")
                continue
            self.sigImageReceived.emit(np.array(self.SIMStack),"SIMStack"+str(processor.wavelength))
            processor.setSIMStack(self.SIMStack)
            

            # activate recording in processor 
            processor.setRecordingMode(self.isRecording)
            processor.setReconstructionMode(self.isRecordReconstruction)
            processor.setWavelength(self.LaserWL,sim_parameters)
            
            # store the raw SIM stack
            if self.isRecording and self.lasers[iColour].power>0.0:
                date = datetime. now(). strftime("%Y_%m_%d-%I-%M-%S_%p")
                processor.setDate(date)
                mFilenameStack = f"{date}_SIM_Stack_{self.LaserWL}nm.tif"
                threading.Thread(target=self.saveImageInBackground, args=(self.SIMStack, mFilenameStack,), daemon=True).start()
            # self.detector.stopAcquisition()
            # We will collect N*M images and process them with the SIM processor
            
            # process the frames and display
            #processor.reconstructSIMStack()
                
            # reset the per-colour stack to add new frames in the next imaging series
            processor.clearStack()
            
    def performSIMZstackThread(self,sim_parameters,zDis,zStep):
        mStep = 0
        acc = 0    #hardcoded acceleration
        mspeed = 1000   #hardcoded speed
        while mStep < zStep:
            self.positioner.move(zDis,acceleration = acc, speed=mspeed)
            mStep += 1
            self.performSIMTimelapseThread(sim_parameters)
            time.sleep(0.1)
        self.active = False
        self.lasers[0].setEnabled(False)
        self.lasers[1].setEnabled(False)
        self.detector.setParameter("trigger_source","Internal trigger")
        self.detector.setParameter("buffer_size",-1)
        self.detector.flushBuffers()
        self._logger.debug("Zstack finished")        
        
        
    @APIExport(runOnUIThread=True)
    def sim_getSnapAPI(self, mystack):
        mystack.append(self.detector.getLatestFrame())
        #print(np.shape(mystack))
        
    @APIExport(runOnUIThread=True)
    def saveImageInBackground(self, image, filename):
        filename = os.path.join('C:\\Users\\admin\\Desktop\\Timelapse\\',filename) #FIXME: Remove hardcoded path
        tif.imsave(filename, image)
        self._logger.debug("Saving file: "+filename)

    def getSIMParametersFromGUI(self):
        ''' retrieve parameters from the GUI '''
        sim_parameters = SIMParameters()
        
        
        # parse textedit fields 
        sim_parameters.pixelsize = np.float32(self._widget.pixelsize_textedit.text())
        sim_parameters.NA = np.float32(self._widget.NA_textedit.text())
        sim_parameters.n = np.float32(self._widget.n_textedit.text())
        sim_parameters.alpha = np.float32(self._widget.alpha_textedit.text())
        sim_parameters.beta = np.float32(self._widget.beta_textedit.text())
        sim_parameters.eta = np.float32(self._widget.eta_textedit.text())
        sim_parameters.wavelength_1 = np.float32(self._widget.wavelength1_textedit.text())
        sim_parameters.wavelength_2 = np.float32(self._widget.wavelength2_textedit.text())
        sim_parameters.magnification = np.float32(self._widget.magnification_textedit.text())
        return sim_parameters
        

    def getReconstructionMethod(self):
        return self._widget.SIMReconstructorList.currentText()

    def getIsUseGPU(self):
        return self._widget.useGPUCheckbox.isChecked()
    

class SIMParameters(object):
    wavelength_1 = 0.52
    wavelength_2 = 0.66
    NA = 1.4
    n = 1.0
    magnification = 90
    pixelsize = 6.5
    eta = 0.6
    alpha = 0.5
    beta = 0.98
    
'''#####################################
# SIM PROCESSOR
#####################################'''

class SIMProcessor(object):

    def __init__(self, parent, simParameters, wavelength=488):
        '''
        setup parameters
        '''
        #current parameters is setting for 60x objective 488nm illumination
        self.parent = parent
        self.mFile = "/Users/bene/Dropbox/Dokumente/Promotion/PROJECTS/MicronController/PYTHON/NAPARI-SIM-PROCESSOR/DATA/SIMdata_2019-11-05_15-21-42.tiff"
        self.phases_number = 3
        self.angles_number = 3
        self.NA = simParameters.NA
        self.n = simParameters.n
        self.wavelength = wavelength
        self.pixelsize = simParameters.pixelsize
        self.dz= 0.55
        self.alpha = 0.5
        self.beta = 0.98
        self.w = 0.2
        self.eta = simParameters.eta
        self.group = 30
        self.use_phases = True
        self.find_carrier = True
        self.isCalibrated = False
        self.use_gpu = isPytorch
        self.stack = []

        # processing parameters
        self.isRecording = False
        self.allPatterns = []
        self.isReconstructing = False
        
        # initialize logger
        self._logger = initLogger(self, tryInheritParent=False)

        # switch for the different reconstruction algorithms
        self.reconstructionMethod = "napari"

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

    def loadPattern(self, path=None, filetype="bmp"):
        # sort filenames numerically
        import glob
        import cv2

        if path is None:
            path = sim_parameters["patternPath"]
        allPatternPaths = sorted(glob.glob(os.path.join(path, "*."+filetype)))
        self.allPatterns = []
        for iPatternPath in allPatternPaths:
            mImage = cv2.imread(iPatternPath)
            mImage = cv2.cvtColor(mImage, cv2.COLOR_BGR2GRAY)
            self.allPatterns.append(mImage)
        return self.allPatterns

    def getPattern(self, iPattern):
        # return ith sim pattern
        return self.allPatterns[iPattern]

    def setParameters(self, sim_parameters):
        # uses parameters from GUI
        self.pixelsize= sim_parameters.pixelsize
        self.NA= sim_parameters.NA
        self.n= sim_parameters.n
        self.reconstructionMethod = "napari" # sim_parameters["reconstructionMethod"]
        #self.use_gpu = False #sim_parameters["useGPU"]
        self.eta =  sim_parameters.eta
        self.magnification = sim_parameters.magnification
        
    def setReconstructionMethod(self, method):
        self.reconstructionMethod = method

    def setReconstructor(self):
        '''
        Sets the attributes of the Processor
        Executed frequently, upon update of several settings
        '''

        self.h.usePhases = self.use_phases
        self.h.magnification = 90
        self.h.NA = self.NA
        self.h.n = self.n
        #self.h.wavelength = self.wavelength
        #self.h.wavelength = 0.52
        self.h.pixelsize = self.pixelsize
        self.h.alpha = self.alpha
        self.h.beta = self.beta
        self.h.w = self.w
        self.h.eta = self.eta
        if not self.find_carrier:
            self.h.kx = self.kx_input
            self.h.ky = self.ky_input

    def getWF(self, mStack):
        # display the BF image
        bfFrame = np.sum(np.array(mStack[-3:]), 0)
        self.parent.sigSIMProcessorImageComputed.emit(bfFrame, "Widefield SUM") 
       
    def setSIMStack(self, stack):
        self.stack = stack

    def getSIMStack(self):
        return np.array(self.stack)
        
    def clearStack(self):
        self.stack=[]
        
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
        #self._logger.debug("Starting to calibrate the stack")
        if self.reconstructionMethod == "napari":
            #imRaw = get_current_stack_for_calibration(mImages)
            if type(imRaw) is list:
                imRaw = np.array(imRaw)
            if self.use_gpu:
                self.h.calibrate_pytorch(imRaw, self.find_carrier)
            else:
                #self.h.calibrate(imRaw, self.find_carrier)
                self.h.calibrate(imRaw)
            self.isCalibrated = True
            if self.find_carrier: # store the value found
                self.kx_input = self.h.kx
                self.ky_input = self.h.ky
                self.p_input = self.h.p
                self.ampl_input = self.h.ampl
            self._logger.debug("Done calibrating the stack")
        elif self.reconstructionMethod == "mcsim":
            """
            test running SIM reconstruction at full speed on GPU
            """

            # ############################
            # for the first image, estimate the SIM parameters
            # this step is slow, can take ~1-2 minutes
            # ############################
            self._logger.debug("running initial reconstruction with full parameter estimation")
            
            # first we need to reshape the stack to become 3x3xNxxNy
            imRawMCSIM = np.stack((imRaw[0:3,],imRaw[3:6,],imRaw[6:,]),0)
            imgset = sim.SimImageSet({"pixel_size": self.pixelsize ,
                                    "na": self.NA,
                                    "wavelength": self.wavelength*1e-3},
                                    imRawMCSIM,
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
                                    use_gpu=self.use_gpu)
            
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


    def reconstructSIMStack(self):
        '''
        reconstruct the image stack asychronously
        '''
        # TODO: Perhaps we should work with quees? 
        # reconstruct and save the stack in background to not block the main thread
        if not self.isReconstructing:  # not
            self.isReconstructing=True
            mStackCopy = np.array(self.stack.copy())
            self.mReconstructionThread = threading.Thread(target=self.reconstructSIMStackBackground, args=(mStackCopy,), daemon=True)
            self.mReconstructionThread.start()

    def setRecordingMode(self, isRecording):
        self.isRecording = isRecording
        
    def setReconstructionMode(self, isRecordReconstruction):
        self.isRecordReconstruction = isRecordReconstruction
        
    def setDate(self, date):
        self.date = date
        
    def setWavelength(self, wavelength, sim_parameters):
        self.LaserWL = wavelength
        if self.LaserWL == 488:
            self.h.wavelength = sim_parameters.wavelength_1
        elif self.LaserWL == 635:
            self.h.wavelength = sim_parameters.wavelength_2
        
    def reconstructSIMStackBackground(self, mStack):
        '''
        reconstruct the image stack asychronously
        the stack is a list of 9 images (3 angles, 3 phases)
        '''
        # compute image
        # initialize the model
        
        self._logger.debug("Processing frames")
        if not self.getIsCalibrated():
            self.setReconstructor()
            self.calibrate(mStack)
        SIMReconstruction = self.reconstruct(mStack)

        # save images eventually
         
        if self.isRecordReconstruction:
            mFilenameRecon = f"{self.date}_SIM_Reconstruction_{self.LaserWL}nm.tif"                            
            threading.Thread(target=SIMController.saveImageInBackground, args=(SIMReconstruction, mFilenameRecon,), daemon=True).start()
            
        self.parent.sigSIMProcessorImageComputed.emit(np.array(SIMReconstruction), "SIM Reconstruction")
        self.isReconstructing = False

    def reconstruct(self, currentImage):
        '''
        reconstruction
        '''
        if self.reconstructionMethod == "napari":
            # we use the napari reconstruction method   
            self._logger.debug("reconstructing the stack with napari") 
            assert self.isCalibrated, 'SIM processor not calibrated, unable to perform SIM reconstruction'
            
            dshape= np.shape(currentImage)
            phases_angles = self.phases_number*self.angles_number
            rdata = currentImage[:phases_angles, :, :].reshape(phases_angles, dshape[-2],dshape[-1])
            if self.use_gpu:
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


class SIMClient:
    # Usage example
    # client = SIMClient(URL="169.254.165.4", PORT=8000)
    # client.start_viewer()
    # client.start_viewer_single_loop(5)
    # client.wait_for_viewer_completion()
    # client.set_pause(1.5)
    # client.stop_loop()
    # client.set_wavelength(1)    
    def __init__(self, URL, PORT):
        self.base_url = f"http://{URL}:{PORT}"
        self.commands = {
            "start": "/start_viewer/",
            "single_run": "/start_viewer_single_loop/",
            "pattern_compeleted": "/wait_for_viewer_completion/",
            "pause_time": "/set_wait_time/",
            "stop_loop": "/stop_viewer/",
            "pattern_wl": "/change_wavelength/",
            "display_pattern": "/display_pattern/",
        }
        self.iseq = 60
        self.itime = 120
        self.laser_power = (400, 250)

    def get_request(self, url, timeout=0.3):
        try: 
            response = requests.get(url, timeout=timeout)
            return response.json()
        except Exception as e:
            print(e)
            return -1
        
    def start_viewer(self):
        url = self.base_url + self.commands["start_viewer"]
        return self.get_request(url)

    def start_viewer_single_loop(self, number_of_runs, timeout=5):
        url = f"{self.base_url}{self.commands['single_run']}{number_of_runs}"
        return self.get_request(url, timeout=timeout)

    def wait_for_viewer_completion(self):
        url = self.base_url + self.commands["pattern_compeleted"]
        self.get_request(url)

    def set_pause(self, period):
        url = f"{self.base_url}{self.commands['pause_time']}{period}"
        self.get_request(url)

    def stop_loop(self):
        url = self.base_url + self.commands["stop_loop"]
        self.get_request(url)

    def set_wavelength(self, wavelength):
        url = f"{self.base_url}{self.commands['pattern_wl']}{wavelength}"
        self.get_request(url)
        
    def display_pattern(self, iPattern):
        url = f"{self.base_url}{self.commands['display_pattern']}{iPattern}"
        self.get_request(url)


      

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
