
import os
import threading
from datetime import datetime
import time
import cv2
import matplotlib.pyplot as plt
import numpy as np
import scipy.ndimage as ndi
import scipy.signal as signal
import skimage.transform as transform
import tifffile as tif

from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex, Timer
from imswitch.imcommon.model import dirtools, initLogger, APIExport
from skimage.registration import phase_cross_correlation
from ..basecontrollers import ImConWidgetController
import imswitch

import h5py
import numpy as np



class MCTController(ImConWidgetController):
    """Linked to MCTWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self)

        # mct parameters
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

        self.Illu1Value = 0
        self.Illu2Value = 0
        self.Illu3Value = 0
        self.MCTFilename = ""
        self.activeIlluminations = []
        self.availableIlliminations = []

        # time to let hardware settle
        try:
            self.tWait = self._master.mctManager.tWait 
        except:
            self.tWait = 0.1

        # connect XY positionercanning live update  https://github.com/napari/napari/issues/1110
        self.sigImageReceived.connect(self.displayImage)

        # autofocus related
        self.isAutofocusRunning = False
        self._commChannel.sigAutoFocusRunning.connect(self.setAutoFocusIsRunning)

        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]
        self.detectorWidth, self.detectorHeight = self.detector._camera.SensorWidth, self.detector._camera.SensorHeight
        self.isRGB = self.detector._camera.isRGB
        self.detectorPixelSize = self.detector.pixelSizeUm
        
        # select lasers
        allIlluNames = self._master.lasersManager.getAllDeviceNames()+ self._master.LEDMatrixsManager.getAllDeviceNames()
        for iDevice in allIlluNames:
            try:
                # laser maanger
                self.availableIlliminations.append(self._master.lasersManager[iDevice])
            except:
                # lexmatrix manager
                self.availableIlliminations.append(self._master.LEDMatrixsManager[iDevice])
              
        # select stage
        try:
            self.positioner = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]
        except:
            self.positioner = None

        self.isMCTrunning = False

        # Connect MCTWidget signals
        if not imswitch.IS_HEADLESS:
            self._widget.mctStartButton.clicked.connect(self.startMCT)
            self._widget.mctStopButton.clicked.connect(self.stopMCT)
            self._widget.mctShowLastButton.clicked.connect(self.showLast)

            self._widget.sigSliderIllu1ValueChanged.connect(self.valueIllu1Changed)
            self._widget.sigSliderIllu2ValueChanged.connect(self.valueIllu2Changed)
            self._widget.sigSliderIllu3ValueChanged.connect(self.valueIllu3Changed)
            self._widget.mctShowLastButton.setEnabled(False)

            # setup gui limits for sliders
            if len(self.availableIlliminations) == 1:
                self._widget.sliderIllu1.setMaximum(self.availableIlliminations[0].valueRangeMax)
                self._widget.sliderIllu1.setMinimum(self.availableIlliminations[0].valueRangeMin)           
            if len(self.availableIlliminations) > 1:
                self._widget.sliderIllu2.setMaximum(self.availableIlliminations[1].valueRangeMax)
                self._widget.sliderIllu2.setMinimum(self.availableIlliminations[1].valueRangeMin)
            if len(self.availableIlliminations) > 2:
                self._widget.sliderIllu3.setMaximum(self.availableIlliminations[2].valueRangeMax)
                self._widget.sliderIllu3.setMinimum(self.availableIlliminations[2].valueRangeMin)


    def startMCT(self):
        # initilaze setup
        # this is not a thread!
        # this is called from the GUI

        # get active illuminations 
        self.activeIlluminations = []
        if self.Illu1Value>0: self.activeIlluminations.append(self.availableIlliminations[0])
        if self.Illu2Value>0: self.activeIlluminations.append(self.availableIlliminations[1])
        if self.Illu3Value>0: self.activeIlluminations.append(self.availableIlliminations[2])
        
        # start the timelapse
        if not self.isMCTrunning and len(self.activeIlluminations)>0:
            self.nImagesTaken = 0
            self.switchOffIllumination()
            
            # GUI updates
            if not imswitch.IS_HEADLESS:
                self._widget.mctStartButton.setEnabled(False)
                self._widget.setMessageGUI("Starting timelapse...")
            

                # get parameters from GUI
                self.zStackMin, self.zStackMax, self.zStackStep, self.zStackEnabled = self._widget.getZStackValues()
                self.xScanMin, self.xScanMax, self.xScanStep, self.yScanMin, self.yScanMax, self.yScanStep, self.xyScanEnabled = self._widget.getXYScanValues()
                self.timePeriod, self.nImagesToCapture = self._widget.getTimelapseValues()
                self.MCTFilename = self._widget.getFilename()
                self.MCTDate = datetime.now().strftime("%Y_%m_%d-%I-%M-%S_%p")

                # reserve space for the stack
                self._widget.mctShowLastButton.setEnabled(False)

            # start the timelapse - otherwise we have to wait for the first run after timePeriod to take place..
            self.takeTimelapse(self.timePeriod, self.nImagesToCapture, 
                               self.MCTFilename, self.MCTDate,
                               self.zStackEnabled, self.zStackMin, self.zStackMax, self.zStackStep,
                               self.xyScanEnabled, self.xScanMin, self.xScanMax, self.xScanStep, self.yScanMin, self.yScanMax, self.yScanStep)

        else:
            self.isMCTrunning = False
            self._widget.mctStartButton.setEnabled(True)


    def stopMCT(self):
        self.isMCTrunning = False

        self._widget.setMessageGUI("Stopping timelapse...")

        self._widget.mctStartButton.setEnabled(True)

        # go back to initial position
        try:
            if self.xyScanEnabled and self.positioner is not None:
                self.positioner.move(value=(self.initialPosition[0], self.initialPosition[1]), axis="XY", is_absolute=True, is_blocking=True)
        except:
            pass

        # delete any existing timer
        try:
            del self.timer
        except:
            pass

        # delete any existing thread
        try:
            del self.MCTThread
        except:
            pass

        self._widget.setMessageGUI("Done wit timelapse...")

    def showLast(self, isCleanStack=False):
        #  isCleanStack=False => subtract backgroudn or not
        if hasattr(self, "LastStackIllu1ArrayLast"):
            try:
                #subtract background and normalize stack
                if isCleanStack: LastStackIllu1ArrayLast = self.cleanStack(self.LastStackIllu1ArrayLast)
                else: LastStackIllu1ArrayLast = self.LastStackIllu1ArrayLast
                self._widget.setImage(LastStackIllu1ArrayLast, colormap="green", name="GFP",pixelsize=self.detectorPixelSize)
            except  Exception as e:
                self._logger.error(e)

        if hasattr(self, "LastStackIllu2ArrayLast"):
            try:
                if isCleanStack: LastStackIllu2ArrayLast = self.cleanStack(self.LastStackIllu2ArrayLast)
                else: LastStackIllu2ArrayLast = self.LastStackIllu2ArrayLast
                self._widget.setImage(LastStackIllu2ArrayLast, colormap="red", name="SiR",pixelsize=self.detectorPixelSize)
            except Exception as e:
                self._logger.error(e)

        if hasattr(self, "LastStackLEDArrayLast"):
            try:
                if isCleanStack: LastStackLEDArrayLast = self.cleanStack(self.LastStackLEDArrayLast)
                else: LastStackLEDArrayLast = self.LastStackLEDArrayLast
                self._widget.setImage(LastStackLEDArrayLast, colormap="gray", name="Brightfield",pixelsize=self.detectorPixelSize)
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

    @APIExport(runOnUIThread=True)
    def takeTimelapse(self, tperiod, nImagesToCapture, 
                      MCTFilename, MCTDate, 
                      zStackEnabled, zStackMin, zStackMax, zStackStep, 
                      xyScanEnabled, xScanMin, xScanMax, xScanStep, yScanMin, yScanMax, yScanStep):
        # this is called periodically by the timer
        if not self.isMCTrunning:
            try:
                # make sure there is no exisiting thrad
                del self.MCTThread
            except:
                pass

            # this should decouple the hardware-related actions from the GUI
            self.isMCTrunning = True
            self.MCTThread = threading.Thread(target=self.takeTimelapseThread, args=(tperiod, nImagesToCapture, 
                                                                                     MCTFilename, MCTDate, 
                                                                                     zStackEnabled, zStackMin, zStackMax, zStackStep, 
                                                                                    xyScanEnabled, xScanMin, xScanMax, xScanStep, 
                                                                                    yScanMin, yScanMax, yScanStep), daemon=True)

            self.MCTThread.start()

    def doAutofocus(self, params, timeout=10):
        self._logger.info("Autofocusing...")
        self._widget.setMessageGUI("Autofocusing...")
        self._commChannel.sigAutoFocus.emit(int(params["valueRange"]), int(params["valueSteps"]))
        self.isAutofocusRunning = True

        while self.isAutofocusRunning:
            time.sleep(0.1)
            t0 = time.time()
            if not self.isAutofocusRunning or time.time()-t0>timeout:
                self._logger.info("Autofocusing done.")
                return


    def takeTimelapseThread(self, tperiod, nImagesToCapture, 
                                    MCTFilename, MCTDate, 
                                    zStackEnabled, zStackMin, zStackMax, zStackStep, 
                                    xyScanEnabled, xScanMin, xScanMax, xScanStep, 
                                    yScanMin, yScanMax, yScanStep):
        # this wil run in the background
        self.timeLast = 0
        if zStackEnabled:
            nZStack = int(np.ceil((zStackMax-zStackMin)/zStackStep))
        else:
            nZStack = 1
        # get current position
        if self.positioner is not None:
            currentPositions = self.positioner.getPosition()
            self.initialPosition = (currentPositions["X"], currentPositions["Y"])
            self.initialPositionZ = currentPositions["Z"]
        else:
            self.initialPosition = (0,0)
            self.initialPositionZ = 0
        
        # HDF5 file setup: prepare data storage 
        fileExtension = "h5"
        fileName = self.getSaveFilePath(date=MCTDate,
                                filename=MCTFilename,
                                extension=fileExtension)
        if self.isRGB:
            init_dims = (1, len(self.activeIlluminations), nZStack, self.detectorWidth, self.detectorHeight, 3) # time, channels, z, y, x, RGB
            max_dims = (None, 3, nZStack, None, None, 3)  # Allow unlimited time points and z slices
        else:
            init_dims = (1, len(self.activeIlluminations), nZStack, self.detectorWidth, self.detectorHeight) # time, channels, z, y, x
            max_dims = (None, 3, nZStack, None, None)  # Allow unlimited time points and z slices
        
        self.h5File = HDF5File(filename=fileName, init_dims=init_dims, max_dims=max_dims, isRGB=self.isRGB)

        # run as long as the MCT is active
        while(self.isMCTrunning):
            # stop measurement once done
            if self.nImagesTaken >= nImagesToCapture:
                self.isMCTrunning = False
                self._logger.debug("Done with timelapse")
                self._widget.mctStartButton.setEnabled(True)
                break

            # initialize a run
            if time.time() - self.timeLast >= (tperiod):

                # run an event
                self.timeLast = time.time() # makes sure that the period is measured from launch to launch
                
                # reserve and free space for displayed stacks
                self.LastStackIllu1 = []
                self.LastStackIllu2 = []
                self.LastStackLED = []

                try:
                    '''
                    AUTOFOCUS
                    '''
                    self.performAutofocus()

                    '''
                    ACQUIRE CHANNELS, Z-STACKS, XY-SCANS
                    '''
                    self.acquireCZXYScan()

                    '''
                    UPDATE GUI
                    '''
                    self.updateGUI()
                    
                    #increase iterator
                    self.nImagesTaken += 1

                except Exception as e:
                    self._logger.error("Thread closes with Error: "+str(e))
                    self.isMCTrunning = False
                    self._logger.debug("Done with timelapse")
                    self._widget.mctStartButton.setEnabled(True)
                    return 

            # pause to not overwhelm the CPU
            time.sleep(0.1)


    def updateGUI(self):
        # update the text in the GUI
        self._widget.setMessageGUI(self.nImagesTaken)

        # sneak images into arrays for displaying stack
        if self.zStackEnabled and not self.xyScanEnabled:
            self.LastStackIllu1ArrayLast = np.array(self.LastStackIllu1)
            self.LastStackIllu2ArrayLast = np.array(self.LastStackIllu2)
            self.LastStackLEDArrayLast = np.array(self.LastStackLED)
            self._widget.mctShowLastButton.setEnabled(True)

    def performAutofocus(self):
        autofocusParams = self._widget.getAutofocusValues()
        if self.positioner is not None and self._widget.isAutofocus() and np.mod(self.nImagesTaken, int(autofocusParams['valuePeriod'])) == 0:
            self._widget.setMessageGUI("Autofocusing...")
            # turn on illuimination
            self.activeIlluminations[0].setValue(autofocusParams["valueRange"])
            self.activeIlluminations[0].setEnabled(True)
            time.sleep(self.tWait)
            self.doAutofocus(autofocusParams)
            self.switchOffIllumination()
            
    def acquireCZXYScan(self):
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
        # TODO: This should go into some function outside the MCT!!!
        #if not ("IDENTIFIER_NAME" in self._master.UC2ConfigManager.ESP32.state.get_state() and self._master.UC2ConfigManager.ESP32.state.get_state()["IDENTIFIER_NAME"] == "uc2-esp"):
        #    mThread = threading.Thread(target=self._master.UC2ConfigManager.initSerial)
        #    mThread.start()
        #    mThread.join()

        # initialize xyz coordinates
        if self.xyScanEnabled and self.positioner is not None:
            self.positioner.move(value=(self.xScanMin+self.initialPosition[0],self.yScanMin+self.initialPosition[1]), axis="XY", is_absolute=True, is_blocking=True)

        # initialize iterator
        
        # iterate over all xy coordinates iteratively

        ''' 
        XY Scan
        '''
        for ipos, iXYPos in enumerate(xyScanStepsAbsolute):
            if not self.isMCTrunning:
                break
            # move to xy position is necessary
            if self.xyScanEnabled and self.positioner is not None:
                self.positioner.move(value=(iXYPos[0]+self.initialPosition[0],iXYPos[1]+self.initialPosition[1]), axis="XY", is_absolute=True, is_blocking=True)

            ''' 
            Z-stack 
            '''
            allZStackFrames = []
            for iZ in zStepsAbsolute:
                # move to each position
                if self.zStackEnabled and self.positioner is not None:
                    self.positioner.move(value=iZ, axis="Z", is_absolute=True, is_blocking=True)
                    time.sleep(self.tWait) # unshake

                '''
                Illumination
                '''
                # capture image for every illumination
                allChannelFrames = []
                allPositions = []
                for illuIndex, mIllumination in enumerate(self.activeIlluminations):
                    if mIllumination.name==self.availableIlliminations[0].name:
                        illuValue = self.Illu1Value
                    elif mIllumination.name==self.availableIlliminations[1].name:
                        illuValue = self.Illu2Value
                    elif mIllumination.name==self.availableIlliminations[2].name:
                        illuValue = self.Illu3Value
                    
                    mIllumination.setValue(illuValue)
                    mIllumination.setEnabled(True, getReturn=True)
                    time.sleep(self.tWait)
                    allChannelFrames.append(self.detector.getLatestFrame().copy())
                    
                    # store positions
                    mPositions = self.positioner.getPosition()
                    allPositions.append((mPositions["X"], mPositions["Y"], mPositions["Z"]))
                    '''
                    elif mIllumination=="LEDMatrix":
                        self.illu.setAll(1, (self.Illu3Value,self.Illu3Value,self.Illu3Value))
                        time.sleep(self.tWait)
                        lastFrame = self.detector.getLatestFrame()
                        self.LastStackLED.append(lastFrame.copy())
                    '''
                allZStackFrames.append(allChannelFrames)
            
            
            # ensure all illus are off
            self.switchOffIllumination()
            
            # save to HDF5
            if self.isRGB:
                framesToSave = np.transpose(np.array(allZStackFrames), (1,0,3,2,4)) # time, # todo check order!!
            else:
                framesToSave = np.transpose(np.array(allZStackFrames), (1,0,2,3)) # time, 
            self.h5File.append_data(self.nImagesTaken, framesToSave, np.array(allPositions))
            del framesToSave
                

            # reduce backlash => increase chance to endup at the same position
            if self.zStackEnabled and self.positioner is not None:
                self.positioner.move(value=(self.initialPositionZ), axis="Z", is_absolute=True, is_blocking=True)

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
        if self.xyScanEnabled and self.positioner is not None:
            self.positioner.move(value=(self.initialPosition[0], self.initialPosition[1]), axis="XY", is_absolute=True, is_blocking=True)
        if self.zStackEnabled and self.positioner is not None:
            self.positioner.move(value=(self.initialPositionZ), axis="Z", is_absolute=True, is_blocking=True)


        # disable motors to prevent overheating
        if self.positioner is not None:
            self.positioner.enalbeMotors(enable=self.positioner.is_enabled)

    def switchOffIllumination(self):
        # switch off all illu sources
        for mIllu in self.activeIlluminations:
            mIllu.setEnabled(False)
            mIllu.setValue(0)
            time.sleep(0.1)
            
    def changeValueIlluSlider(self, currIllu, value):
        allIllus = np.arange(len(self.availableIlliminations))
        # turn on current illumination
        if not self.availableIlliminations[currIllu].enabled: self.availableIlliminations[currIllu].setEnabled(1)
        self.availableIlliminations[currIllu].setValue(value)

        # switch off other illus
        for illuIndex in allIllus:
            if illuIndex != currIllu and self.availableIlliminations[illuIndex].power>0:
                self.availableIlliminations[illuIndex].setValue(0)
                self.availableIlliminations[illuIndex].setEnabled(0)
            
    def valueIllu1Changed(self, value):
        # turn on current illumination based on slider value
        currIllu = 0
        self.Illu1Value = value
        self._widget.mctLabelIllu1.setText('Intensity (Laser 1):'+str(value))
        self.changeValueIlluSlider(currIllu, value)        
        
    def valueIllu2Changed(self, value):
        currIllu = 1
        self.Illu2Value = value
        self._widget.mctLabelIllu2.setText('Intensity (Laser 2):'+str(value))
        self.changeValueIlluSlider(currIllu, value)

    def valueIllu3Changed(self, value):
        currIllu = 2
        self.Illu3Value = value
        self._widget.mctLabelIllu3.setText('Intensity (Laser 3):'+str(value))
        self.changeValueIlluSlider(currIllu, value)

    def __del__(self):
        pass

    def getSaveFilePath(self, date, filename, extension):
        mFilename =  f"{date}_{filename}.{extension}"
        dirPath  = os.path.join(dirtools.UserFileDirs.Root, 'recordings', date)

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


    # helper functions
    def downscale_image(self, image, factor):
        # Downscale the image
        downscaled_image = transform.downscale_local_mean(image, (factor, factor))
        return downscaled_image

    def crop_center(self, image, size):
        # Get the dimensions of the image
        height, width = image.shape[:2]

        # Calculate the coordinates for cropping
        start_x = max(0, int((width - size) / 2))
        start_y = max(0, int((height - size) / 2))
        end_x = min(width, start_x + size)
        end_y = min(height, start_y + size)

        # Crop the image
        cropped_image = image[start_y:end_y, start_x:end_x]

        return cropped_image


class HDF5File(object):
    def __init__(self, filename, init_dims, max_dims=None, isRGB=False):
        self.filename = filename
        self.init_dims = init_dims # time, channels, z, y, x
        self.max_dims = max_dims # time, channels, z, y, x
        self.isRGB=isRGB
        self.create_dataset()

    def create_dataset(self):
        with h5py.File(self.filename, 'w') as file:
            # Create a resizable dataset for the image data
            dset = file.create_dataset('ImageData', shape=self.init_dims, maxshape=self.max_dims, dtype='uint16', compression="gzip")
            
            # Initialize a group for storing metadata
            meta_group = file.create_group('Metadata')

    def append_data(self, timepoint, frame_data, xyz_coordinates):
        with h5py.File(self.filename, 'a') as file:
            dset = file['ImageData']
            meta_group = file['Metadata']
            
            # Resize the dataset to accommodate the new timepoint
            current_size = dset.shape[0]
            dset.resize(current_size + 1, axis=0)
            
            # Add the new frame data
            try:
                if self.isRGB:
                    dset[current_size, :, :, :, :, :] = np.uint16(frame_data)
                else:
                    dset[current_size, :, :, :, :] = np.uint16(frame_data)
            except:
                # in case X/Y are swapped 
                if self.isRGB:
                    dset[current_size, :, :, :, :, :] = np.transpose(np.uint16(frame_data), (0,1,2,4,3))
                else:
                    dset[current_size, :, :, :, :] = np.transpose(np.uint16(frame_data), (0,1,3,2))
                            
            # Add metadata for the new frame
            for channel, xyz in enumerate(xyz_coordinates):
                meta_group.create_dataset(f'Time_{timepoint}_Channel_{channel}', data=np.float32(xyz))



'''
Crosscolleration based drift correction
                    if False and not self.xyScanEnabled:
                        # treat images
                        imageStack = self.LastStackIllu2 # FIXME: Hardcoded
                        imageStack = self.LastStackLED # FIXME: Hardcoded

                        driftCorrectionDownScaleFactor = 5
                        driftCorrectionCropSize = 800
                        iShift = [0,0]
                        imageList = []

                        # convert to list if necessary
                        if type(imageStack)!=list or len(imageStack)<2:
                            imageStack = list(imageStack)

                        # image processing
                        for iImage in imageStack:
                            if len(iImage.shape)>2:
                                # if RGB => make mono
                                iImage = np.mean(iImage, -1)
                            image = self.crop_center(iImage, driftCorrectionCropSize)
                            image = self.downscale_image(image, driftCorrectionDownScaleFactor)
                            imageList.append(image)

                        # remove background
                        imageList = np.array(imageList)
                        if len(imageList.shape)<3:
                            imageList = np.expand_dims(imageList,0)
                        imageList = imageList/ndi.filters.gaussian_filter(np.mean(imageList,0), 10)

                        # Find max focus
                        bestFocus = 0
                        bestFocusIndex = 0
                        for index, image in enumerate(imageList):
                            # remove high frequencies
                            imagearraygf = ndi.filters.gaussian_filter(image, 3)

                            # compute focus metric
                            focusValue = np.mean(ndi.filters.laplace(imagearraygf))
                            if focusValue > bestFocus:
                                bestFocus = focusValue
                                bestFocusIndex = index

                        # Align the images
                        image2 = np.std(imageList, (0))

                        #image2 = scipy.ndimage.gaussian_filter(image2, sigma=10)
                        if self.nImagesTaken > 0:
                            shift, error, diffphase = phase_cross_correlation(image1, image2)
                            iShift += (shift)

                            # Shift image2 to align with image1
                            image = imageList[bestFocusIndex]
                            #aligned_image = np.roll(image, int(iShift[1]), axis=1)
                            #aligned_image = np.roll(aligned_image,int(iShift[0]), axis=0)
                            self.positioner.move(value=(self.initialPosition[0]+shift[1], self.initialPosition[1]+shift[0]), axis="XY", is_absolute=True, is_blocking=True)

                        image1 = image2.copy()

                    #save values
                    #make sure not to have too large travelrange after last (e.g. initial position + 2*shift))
'''
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
