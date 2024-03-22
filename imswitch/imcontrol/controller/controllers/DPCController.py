    
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

pi    = np.pi
naxis = np.newaxis
F     = lambda x: np.fft.fft2(x)
IF    = lambda x: np.fft.ifft2(x)

class DPCController(ImConWidgetController):
    """Linked to DPCWidget."""

    sigImageReceived = Signal()
    sigDPCProcessorImageComputed = Signal(np.ndarray, str)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self)
        self.nSyncCameraSLM = 1  # 5 frames will be captured before a frame is retrieved from buffer for prcoessing 
        self.iSyncCameraSLM = 0 # counter for syncCameraSLM

        # switch to detect if a recording is in progress
        self.isRecording = False

        # load config file
        if self._setupInfo.dpc is None:
            self._widget.replaceWithError('DPC is not configured in your setup file.')
            return

        # define patterns
        self.nPattern = 4
        self.brightfieldPattern = {"0": [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]}
        self.allDPCPatternNames = ("left", "right", "top", "bottom")
        if False:
            self.allDPCPatterns = {self.allDPCPatternNames[0]: [0,1,2,7,8,9,10,11,12,21,22,23,24], 
                                    self.allDPCPatternNames[1]: [3,4,5,6,13,14,15,16,17,18,19,20,21,22], 
                                    self.allDPCPatternNames[2]: [0,5,6,7,8,18,19,20,21,22,23,24], 
                                    self.allDPCPatternNames[3]: [1,2,3,4,9,10,11,12,14,15,16]}
            self.nLEDs = 25
        else:        
            self.allDPCPatterns = {self.allDPCPatternNames[0]: [0,1,2,3,4,5,6,7], 
                        self.allDPCPatternNames[1]: [8,9,10,11,12,13,14,15], 
                        self.allDPCPatternNames[2]: [0,7,8,19,14,9,6,1], 
                        self.allDPCPatternNames[3]: [3,4,11,12,2,9,10,13]}
            self.nLEDs = 16
        #self._widget.applyChangesButton.clicked.connect(self.applyParams)
        self._widget.startDPCAcquisition.clicked.connect(self.startDPC)
        self._widget.isRecordingButton.clicked.connect(self.toggleRecording)
        
        # dpc parameters
        self.rotation  = self._master.dpcManager.rotations 
        self.wavelength = self._master.dpcManager.wavelength
        self.pixelsize = self._master.dpcManager.pixelsize
        self.NA = self._master.dpcManager.NA
        self.NAi =  self._master.dpcManager.NAi
        self.n =  self._master.dpcManager.n
        
        self.tWait = .1 # time to wait between turning on LED Matrix and frame acquisition

        # select LEDArray
        allLEDMatrixNames = self._master.LEDMatrixsManager.getAllDeviceNames()
        self.ledMatrix = self._master.LEDMatrixsManager[allLEDMatrixNames[0]]
        
        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]
        self.detector.startAcquisition()
        self.frameShape = self.detector.getLatestFrame().shape
        # initialize DPC processor
        ''' write parameters from file '''
        self.generalparams = [{'name': 'general', 'type': 'group', 'children': [
            {
                'name': 'pixelsize',
                'type': 'int',
                'value': self.pixelsize, 
                'limits': (0,50),
                'step': .01,
                'suffix': 'µm',
                },
            {
                'name': 'wavelength',
                'type': 'float',
                'value': self.wavelength, 
                'limits': (0,2),
                'step': .01,
                'suffix': 'µm',
                },
            {
                'name': 'NA',
                'type': 'float',
                'value': self.NA, 
                'limits': (0, 1.6),
                'step': 0.05,
                'suffix': 'A.U.',
                },
            {
                'name': 'NAi',
                'type': 'float',
                'value': self.NAi,
                'limits': (0, 1.6),
                'step': 0.05,
                'suffix': 'A.U.',
                },            
            {
                'name': 'n',
                'type': 'float',
                'value': self.n,
                'limits': (1.0, 1.6),
                'step': 0.1,
                'suffix': 'A.U.',
                },
            {
                'name': 'shape', 
                'value': self.frameShape,
            }
           ]}]
        #TODO: Set parameters
            
    
        #assign parameters from disk
        
        self.DPCProcessor = DPCProcessor(self, self.frameShape, self.generalparams)
        
        # connect the reconstructed image to the displayer
        self.sigDPCProcessorImageComputed.connect(self.displayImage)
        
    def __del__(self):
        pass

    def displayImage(self, im, name="DPC Reconstruction"):
        """ Displays the image in the view. """
        self._widget.setImage(im, name=name)

    def startDPC(self):
        if self._widget.startDPCAcquisition.text() == "Start":
            # start live processing => every frame is captured by the update() function. It also handles the pattern addressing
            self.iReconstructed = 0
            #  Start acquisition if not started already
            self._master.detectorsManager.startAcquisition(liveView=False)
            



            # start the background thread
            self.active = True
            dpc_info_dict = self.getInfoDict(generalParams=self._widget.DPCParameterTree.p)
            self.dpcThread = threading.Thread(target=self.performDPCExperimentThread, args=(dpc_info_dict,), daemon=True)
            self.dpcThread.start()
            self._widget.startDPCAcquisition.setText("Stop")
        else:
            # stop live processing 
            self.active = False
            self._master.detectorsManager.startAcquisition(liveView=True)
            self.dpcThread.join()
            self._widget.startDPCAcquisition.setText("Start")
            
    def toggleRecording(self):
        self.isRecording = not self.isRecording
        if self.isRecording:
            self._widget.isRecordingButton.setText("Stop Recording")
        else:
            self._widget.isRecordingButton.setText("Start Recording")
    

            
    def performDPCExperimentThread(self, dpc_info_dict):
        """ 
        Iterate over all DPC patterns, display them and acquire images 
        """     
        self.patternID = 0
        self.isReconstructing = False
        while self.active:
            
            if not self.active:
                break
            # initialize the processor 
            processor = self.DPCProcessor
            processor.setParameters(dpc_info_dict)
            
            # iterating over all illumination patterns
            for iPatternName in self.allDPCPatternNames:
                if not self.active:
                    break
                self.ledMatrix.mLEDmatrix.setAll(0)
                # 1. display the pattern
                ledIDs = self.allDPCPatterns[iPatternName]
                self._logger.debug("Showing pattern: "+iPatternName)
                ledPattern = []
                ledIntensity = (0,255,0)
                
                # no sparse update :( 
                for iLED in range(self.nLEDs): 
                    if iLED in ledIDs:
                        ledPattern.append(ledIntensity)
                    else:
                        ledPattern.append((0,0,0))
                self.ledMatrix.mLEDmatrix.send_LEDMatrix_array(np.array(ledPattern), getReturn = True)
                # wait a moment
                time.sleep(self.tWait)
                
                # 2 grab a frame 
                frame = self.detector.getLatestFrame()
                processor.addFrameToStack(frame)
                    
            # We will collect N*M images and process them with the DPC processor
            # process the frames and display
            if not self.isReconstructing:
                self.isReconstructing=True
                # reconstruct and save the stack in background to not block the main thread
                processor.reconstruct(self.isRecording)
                
                # reset the per-colour stack to add new frames in the next imaging series
                processor.clearStack()
        

    def getInfoDict(self, generalParams=None):
        state_general = None
        if generalParams is not None:
            # create dict for general params
            generalparamnames = []
            for i in generalParams.getValues()["general"][1]: generalparamnames.append(i)
            state_general = {generalparamname: float(
                generalParams.param("general").param(generalparamname).value()) for generalparamname
                             in generalparamnames}
            
        return state_general

'''#####################################
# DPC PROCESSOR
#####################################'''

class DPCProcessor(object):

    def __init__(self, parent, shape, infoDict):
        '''
        setup parameters
        '''
        # initialize logger
        self._logger = initLogger(self, tryInheritParent=False)
        self.parent = parent

        # Default values
        self.shape = shape
        self.pixelsize = .2
        self.NA= .3
        self.NAi = .3
        self.n= 1
        self.wavelength = .53
        self.rotation = [0, 180, 90, 270]    
        
        self.dpc_solver_obj = DPCSolver(shape=self.shape, wavelength=self.wavelength, na=self.NA, NAi=self.NAi, pixelsize=self.pixelsize, rotation=self.rotation)
        #parameters for Tikhonov regurlarization [absorption, phase] ((need to tune this based on SNR)
        self.dpc_solver_obj.setTikhonovRegularization(reg_u = 1e-1, reg_p = 5e-3)
        
        # stack to store the individual DPC images
        self.stack = []
        
    def setParameters(self, dpc_info_dict):
        # uses parameters from GUI
        self.pixelsize = dpc_info_dict["pixelsize"]
        self.NA= dpc_info_dict["NA"]
        self.NAi = dpc_info_dict["NAi"]
        self.n= dpc_info_dict["n"]
        self.wavelength = dpc_info_dict["wavelength"]
        self.rotation = [0, 180, 90, 270] 
        self.dpc_num = 4
        
    def addFrameToStack(self, frame):
        '''
        append stacks to to-be-processed stack
        '''
        self.stack.append(frame)
        # display the BF image
        if len(self.stack) % 4 == 0 and len(self.stack)>0:
            bfFrame = np.sum(np.array(self.stack[-3:]), 0)
            self.parent.sigDPCProcessorImageComputed.emit(bfFrame, "Widefield SUM")

    def getDPCStack(self):
        '''
        return the imagestack
        '''
        return np.array(self.stack)
        
    def clearStack(self):
        '''
        reset the stack 
        '''
        self.stack=[]
        
    def reconstruct(self, isRecording=False):
        '''
        reconstruction
        '''
        self.stackToReconstruct = np.array(self.stack)
        self.mReconstructionThread = threading.Thread(target=self.reconstructThread, args=(isRecording,), daemon=True)
        self.mReconstructionThread.start()

    def reconstructThread(self, isRecording):
        # compute image
        # initialize the model
        self._logger.debug("Processing frames")
        qdpc_result = self.dpc_solver_obj.solve(dpc_imgs=self.stackToReconstruct)

        # save images eventually
        if isRecording:
            date = datetime.now().strftime("%Y_%m_%d-%I-%M-%S_%p")
            mFilenameRecon = f"{date}_DPC_Reconstruction.tif"   
            tif.imsave(mFilenameRecon, qdpc_result)         
        
        # compute gradient images
        dpc_result_1 = (self.stackToReconstruct[0]-self.stackToReconstruct[1])/(self.stackToReconstruct[0]+self.stackToReconstruct[1])
        dpc_result_2 = (self.stackToReconstruct[2]-self.stackToReconstruct[3])/(self.stackToReconstruct[2]+self.stackToReconstruct[3])

        # display images
        self.parent.sigDPCProcessorImageComputed.emit(np.angle(np.array(qdpc_result)), "qDPC Reconstruction (Phase)")
        self.parent.sigDPCProcessorImageComputed.emit(np.abs(np.array(qdpc_result)), "qDPC Reconstruction (Magnitude)")
        self.parent.sigDPCProcessorImageComputed.emit(np.array(dpc_result_1), "DPC left/right")
        self.parent.sigDPCProcessorImageComputed.emit(np.array(dpc_result_2), "DPC top/bottom")
        self.parent.isReconstructing = False
        return dpc_result_1, dpc_result_2, qdpc_result



# (C) Wallerlab 2019
# https://github.com/Waller-Lab/DPC/blob/master/python_code/dpc_algorithm.py
import numpy as np
import matplotlib.pyplot as plt
from os import listdir
from skimage import io
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
from scipy.ndimage import uniform_filter

class DPCSolver:
    def __init__(self, shape, wavelength, na, NAi, pixelsize, rotation):
        self.shape = shape
        if self.shape[0] == 0:
            self.shape = (512, 512)
            
        self.wavelength = wavelength
        self.na         = na
        self.NAi      = NAi
        self.pixel_size = pixelsize
        self.dpc_num    = len(rotation)
        self.rotation   = rotation
        self.fxlin      = np.fft.ifftshift(self.genGrid(self.shape[-1], 1.0/self.shape[-1]/self.pixel_size))
        self.fylin      = np.fft.ifftshift(self.genGrid(self.shape[-2], 1.0/self.shape[-2]/self.pixel_size))
        self.pupil      = self.pupilGen(self.fxlin, self.fylin, self.wavelength, self.na)
        self.sourceGen()
        self.WOTFGen()
        
    def setTikhonovRegularization(self, reg_u = 1e-6, reg_p = 1e-6):
        self.reg_u      = reg_u
        self.reg_p      = reg_p
        
    def normalization(self):
        for img in self.dpc_imgs:
            img          /= uniform_filter(img, size=img.shape[0]//2)
            meanIntensity = img.mean()
            img          /= meanIntensity        # normalize intensity with DC term
            img          -= 1.0                  # subtract the DC term
        
    def sourceGen(self):
        self.source = []
        pupil = self.pupilGen(self.fxlin, self.fylin, self.wavelength, self.na, NAi=self.NAi)
        for rotIdx in range(self.dpc_num):
            self.source.append(np.zeros((self.shape)))
            rotdegree = self.rotation[rotIdx]
            if rotdegree < 180:
                self.source[-1][self.fylin[:, naxis]*np.cos(np.deg2rad(rotdegree))+1e-15>=
                                self.fxlin[naxis, :]*np.sin(np.deg2rad(rotdegree))] = 1.0
                self.source[-1] *= pupil
            else:
                self.source[-1][self.fylin[:, naxis]*np.cos(np.deg2rad(rotdegree))+1e-15<
                                self.fxlin[naxis, :]*np.sin(np.deg2rad(rotdegree))] = -1.0
                self.source[-1] *= pupil
                self.source[-1] += pupil
        self.source = np.asarray(self.source)
        
    def WOTFGen(self):
        self.Hu = []
        self.Hp = []
        for rotIdx in range(self.source.shape[0]):
            FSP_cFP  = F(self.source[rotIdx]*self.pupil)*F(self.pupil).conj()
            I0       = (self.source[rotIdx]*self.pupil*self.pupil.conj()).sum()
            self.Hu.append(2.0*IF(FSP_cFP.real)/I0)
            self.Hp.append(2.0j*IF(1j*FSP_cFP.imag)/I0)
        self.Hu = np.asarray(self.Hu)
        self.Hp = np.asarray(self.Hp)

    def solve(self, dpc_imgs, xini=None, plot_verbose=False, **kwargs):
        self.dpc_imgs   = dpc_imgs.astype('float64')
        self.normalization()

        dpc_result  = []
        AHA         = [(self.Hu.conj()*self.Hu).sum(axis=0)+self.reg_u,            (self.Hu.conj()*self.Hp).sum(axis=0),\
                       (self.Hp.conj()*self.Hu).sum(axis=0)           , (self.Hp.conj()*self.Hp).sum(axis=0)+self.reg_p]
        determinant = AHA[0]*AHA[3]-AHA[1]*AHA[2]
        for frame_index in range(self.dpc_imgs.shape[0]//self.dpc_num):
            fIntensity = np.asarray([F(self.dpc_imgs[frame_index*self.dpc_num+image_index]) for image_index in range(self.dpc_num)])
            AHy        = np.asarray([(self.Hu.conj()*fIntensity).sum(axis=0), (self.Hp.conj()*fIntensity).sum(axis=0)])
            absorption = IF((AHA[3]*AHy[0]-AHA[1]*AHy[1])/determinant).real
            phase      = IF((AHA[0]*AHy[1]-AHA[2]*AHy[0])/determinant).real
            dpc_result.append(absorption+1.0j*phase)
            
        return np.asarray(dpc_result)
    
    
    def pupilGen(self, fxlin, fylin, wavelength, na, NAi=0.0):
        pupil = np.array(fxlin[naxis, :]**2+fylin[:, naxis]**2 <= (na/wavelength)**2)
        if NAi != 0.0:
            pupil[fxlin[naxis, :]**2+fylin[:, naxis]**2 < (NAi/wavelength)**2] = 0.0
        return pupil

    def genGrid(self, size, dx):
        xlin = np.arange(size, dtype='complex128')
        return (xlin-size//2)*dx


    

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
