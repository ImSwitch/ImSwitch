import json
import os

from imswitch.imcommon.model import initLogger, ostools
import numpy as np
import time
import tifffile
import threading
from datetime import datetime
import cv2
import numpy as np
from skimage.io import imsave
from scipy.ndimage import gaussian_filter
from collections import deque

import datetime 
from itertools import product
try:
    from ashlar import fileseries, thumbnail, reg
    IS_ASHLAR = True
except:
    print("Ashlar not installed")
    IS_ASHLAR = False
import numpy as np

from imswitch.imcommon.model import dirtools, initLogger, APIExport
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex, Timer
import time

from ..basecontrollers import LiveUpdatedController


# import NanoImagingPack as nip

class HistoScanController(LiveUpdatedController):
    """Linked to HistoScanWidget."""

    sigImageReceived = Signal()
    sigUpdatePartialImage = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self)
        # read default values from previously loaded config file
        offsetX = self._master.HistoScanManager.offsetX
        offsetY = self._master.HistoScanManager.offsetY
        self._widget.setOffset(offsetX, offsetY)
    
        
        self.histoscanTask = None
        self.histoscanStack = np.ones((1,1,1))
        self._widget.startButton.clicked.connect(self.starthistoscan)
        self._widget.stopButton.clicked.connect(self.stophistoscan)
        
        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]
        
        # select lasers and add to gui
        allLaserNames = self._master.lasersManager.getAllDeviceNames()
        self._widget.setAvailableIlluSources(allLaserNames)
        self.ishistoscanRunning = False
        
        self._widget.sigSliderIlluValueChanged.connect(self.valueIlluChanged)
        self._widget.sigGoToPosition.connect(self.goToPosition)
        self._widget.sigCurrentOffset.connect(self.calibrateOffset)
        self.sigImageReceived.connect(self.displayImage)
        self.sigUpdatePartialImage.connect(self.updatePartialImage)
        self._commChannel.sigUpdateMotorPosition.connect(self.updateAllPositionGUI)
        self._widget.sigSliderIlluValueChanged.connect(self.valueIlluChanged)
        
        self.partialImageCoordinates = (0,0,0,0)
        self.partialHistoscanStack = np.ones((1,1,3))
        self.acceleration = 600000
        
        self._widget.setDefaultSavePath(self._master.HistoScanManager.defaultConfigPath)
        
        # select stage
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]
        
        # get flatfield manager
        if hasattr(self._master, "FlatfieldManager"):
            self.flatfieldManager = self._master.FlatfieldManager
        else: 
            self.flatfieldManager = None

    def updateAllPositionGUI(self):
        allPositions = self.stages.position
        self._widget.updateBoxPosition(allPositions["X"], allPositions["Y"])

    def goToPosition(self, posX, posY):
#            {"task":"/motor_act",     "motor":     {         "steppers": [             { "stepperid": 1, "position": -1000, "speed": 30000, "isabs": 0, "isaccel":1, "isen":0, "accel":500000}     ]}}
        self.stages.move(value=(posX,posY), axis="XY", is_absolute=True, is_blocking=False, acceleration=(self.acceleration,self.acceleration))
        self._commChannel.sigUpdateMotorPosition.emit()
        
    def displayImage(self):
        # a bit weird, but we cannot update outside the main thread
        name = self.histoScanStackName
        # subsample stack 
        isRGB = self.histoscanStack.shape[-1]==3
        self._widget.setImageNapari(np.uint16(self.histoscanStack ), colormap="gray", isRGB=isRGB, name=name, pixelsize=(1,1), translation=(0,0))

    def updatePartialImage(self):
        # a bit weird, but we cannot update outside the main thread
        name = self.histoScanStackName
        # subsample stack 
        isRGB = self.histoscanStack.shape[-1]==3
        # coordinates: (x,y,w,h)
        self._widget.updatePartialImageNapari(im=np.uint16(self.partialHistoscanStack ), 
                                              coords=self.partialImageCoordinates,
                                              name=name)

    def valueIlluChanged(self):
        illuSource = self._widget.getIlluminationSource()
        illuValue = self._widget.illuminationSlider.value()
        self._master.lasersManager
        if not self._master.lasersManager[illuSource].enabled:
            self._master.lasersManager[illuSource].setEnabled(1)
        
        illuValue = illuValue/100*self._master.lasersManager[illuSource].valueRangeMax
        self._master.lasersManager[illuSource].setValue(illuValue)

    def calibrateOffset(self):
        # move to a known position and click in the 
        # 1. retreive the coordinates on the canvas
        clickedCoordinates = self._widget.ScanSelectViewWidget.clickedCoordinates
        # 2. measure the stage coordinates that relate to the clicked coordintes 
        self.stageinitialPosition = self.stages.getPosition()
        # true position:
        initX = self.stageinitialPosition["X"]
        initY = self.stageinitialPosition["Y"]
        initZ = self.stageinitialPosition["Z"]

        # compute the differences
        offsetX =  initX - clickedCoordinates[0]
        offsetY =  initY - clickedCoordinates[1]
        self._logger.debug("Offset coordinates in X/Y"+str(offsetX)+" / "+str(offsetY))

        # now we need to calculate the offset here
        self._master.HistoScanManager.writeConfig({"offsetX":offsetX, "offsetY":offsetY})
        self._widget.ScanSelectViewWidget.setOffset(offsetX,offsetY)
        
    def starthistoscan(self):
        minPosX = self._widget.getMinPositionX()
        maxPosX = self._widget.getMaxPositionX()
        minPosY = self._widget.getMinPositionY()
        maxPosY = self._widget.getMaxPositionY()   
        nTimes = self._widget.getNTimesScan()
        tPeriod = self._widget.getTPeriodScan()     
        self._widget.startButton.setEnabled(False)
        self._widget.stopButton.setEnabled(True)
        self._widget.startButton.setText("Running")
        self._widget.stopButton.setText("Stop") 
        self._widget.stopButton.setStyleSheet("background-color: red")
        self._widget.startButton.setStyleSheet("background-color: green")
        overlap = 0.75
        illuSource = self._widget.getIlluminationSource()

        self.performScanningRecording(minPosX, maxPosX, minPosY, maxPosY, overlap, nTimes, tPeriod, illuSource)

    def performScanningRecording(self, minPos, maxPos, minPosY, maxPosY, overlap, nTimes, tPeriod, illuSource):
        if not self.ishistoscanRunning:
            self.ishistoscanRunning = True
            if self.histoscanTask is not None:
                self.histoscanTask.join()
                del self.histoscanTask
            self.histoscanTask = threading.Thread(target=self.histoscanThread, args=(minPos, maxPos, minPosY, maxPosY, overlap, nTimes, tPeriod, illuSource))
            self.histoscanTask.start()
        
    def generate_snake_scan_coordinates(self, posXmin, posYmin, posXmax, posYmax, img_width, img_height, overlap):
        # Calculate the number of steps in x and y directions
        steps_x = int((posXmax - posXmin) / (img_width*overlap))
        steps_y = int((posYmax - posYmin) / (img_height*overlap))
        
        coordinates = []

        # Loop over the positions in a snake pattern
        for y in range(steps_y):
            if y % 2 == 0:  # Even rows: left to right
                for x in range(steps_x):
                    coordinates.append((posXmin + x * img_width *overlap, posYmin + y * img_height *overlap))
            else:  # Odd rows: right to left
                for x in range(steps_x - 1, -1, -1):  # Starting from the last position, moving backwards
                    coordinates.append((posXmin + x * img_width *overlap, posYmin + y * img_height *overlap))
        
        return coordinates

        
    def histoscanThread(self, minPosX, maxPosX, minPosY, maxPosY, overlap=0.75, nTimes=1, tPeriod=0, illuSource=None):
        self._logger.debug("histoscan thread started.")
        
        initialPosition = self.stages.getPosition()
        initPosX = initialPosition["X"]
        initPosY = initialPosition["Y"]
        if not self.detector._running: self.detector.startAcquisition()
        
        # now start acquiring images and move the stage in Background
        mFrame = self.detector.getLatestFrame()
        dimensionsFrame = mFrame.shape[1]*self.detector.pixelSizeUm[-1]
        NpixX, NpixY = mFrame.shape[1], mFrame.shape[0]
        
        # starting the snake scan
        # Calculate the size of the area each image covers
        img_width = NpixX * self.detector.pixelSizeUm[-1]
        img_height = NpixY * self.detector.pixelSizeUm[-1]

        # precompute the position list in advance 
        positionList = self.generate_snake_scan_coordinates(minPosX, minPosY, maxPosX, maxPosY, img_width, img_height, overlap)

        maxPosPixY = int((maxPosY-minPosY)/self.detector.pixelSizeUm[-1])
        maxPosPixX = int((maxPosX-minPosX)/self.detector.pixelSizeUm[-1])
        
        # are we RGB or monochrome?
        if len(mFrame.shape)==2:
            nChannels = 1
        else:
            nChannels = mFrame.shape[-1]
            
        # perform timelapse imaging
        for i in range(nTimes):
            tz = datetime.timezone.utc
            ft = "%Y-%m-%dT%H_%M_%S"
            t = datetime.datetime.now(tz=tz).strftime(ft)
            file_name = "test_"+t
            extension = ".ome.tif"
            folder = self._widget.getDefaulSavePath()

            t0 = time.time()
            
            # create a new image stitcher          
            if self.flatfieldManager is not None:
                flatfieldImage = self.flatfieldManager.getFlatfieldImage()
            else:
                flatfieldImage = None
            stitcher = ImageStitcher(self, min_coords=(0,0), max_coords=(maxPosPixX, maxPosPixY), folder=folder, nChannels=nChannels, file_name=file_name, extension=extension, flatfieldImage=flatfieldImage)
            
            # move to the first position
            self.stages.move(value=positionList[0], axis="XY", is_absolute=True, is_blocking=True, acceleration=(self.acceleration,self.acceleration))
            # move to all coordinates and take an image   
            if illuSource is not None: 
                self._master.lasersManager[illuSource].setEnabled(1)
                self._master.lasersManager[illuSource].setValue(255)
                time.sleep(.5)
            
            # we try an alternative way to move the stage and take images:
            # We move the stage in the background from min to max X and take
            # images in the foreground everytime the stage is in the region where there is a frame due
            if 0:
                self.stages.move(value=(minPosX, minPosY), axis="XY", is_absolute=True, is_blocking=True)
            
                # now we need to move to max X and take images in the foreground everytime the stage is in the region where there is a frame due
                self.stages.move(value=maxPosX, axis="X", is_absolute=True, is_blocking=False)
                stepSizeX = positionList[1][0]-positionList[0][0]
                lastStagePositionX = self.stages.getPosition()["X"]
                running=1
                while running:
                    currentPosX = self.stages.getPosition()["X"]
                    print(currentPosX)
                    if currentPosX-lastStagePositionX > stepSizeX:
                        print("Taking image")
                        mFrame = self.detector.getLatestFrame()  
                        import tifffile as tif
                        tif.imsave("test.tif", mFrame, append=True)
                        
                        lastStagePositionX = currentPosX
                        

            for iPos in positionList:
                try:
                    if not self.ishistoscanRunning:
                        break
                    self.stages.move(value=iPos, axis="XY", is_absolute=True, is_blocking=True, acceleration=(self.acceleration,self.acceleration))
                    mFrame = self.detector.getLatestFrame()  

                    def addImage(mFrame, positionList):
                        metadata = {'Pixels': {
                            'PhysicalSizeX': self.detector.pixelSizeUm[-1],
                            'PhysicalSizeXUnit': 'µm',
                            'PhysicalSizeY': self.detector.pixelSizeUm[-1],
                            'PhysicalSizeYUnit': 'µm'},

                            'Plane': {
                                'PositionX': positionList[0],
                                'PositionY': positionList[1]
                        }, }
                        self._commChannel.sigUpdateMotorPosition.emit()
                        posY_pix_value = (float(positionList[1])-minPosY)/self.detector.pixelSizeUm[-1]
                        posX_pix_value = (float(positionList[0])-minPosX)/self.detector.pixelSizeUm[-1]
                        iPosPix = (posX_pix_value, posY_pix_value)
                        #stitcher._place_on_canvas(np.copy(mFrame), np.copy(iPosPix))
                        stitcher.add_image(np.copy(mFrame), np.copy(iPosPix), metadata.copy())
                    threading.Thread(target=addImage, args=(mFrame,iPos)).start()

                except Exception as e:
                    self._logger.error(e)
            if illuSource is not None:
                self._master.lasersManager[illuSource].setEnabled(0)

            # wait until we go for the next timelapse
            while 1:
                if time.time()-t0 > tPeriod:
                    break
                if not self.ishistoscanRunning:
                    return
                time.sleep(1)
        # return to initial position
        self.stages.move(value=(initPosX,initPosY), axis="XY", is_absolute=True, is_blocking=True, acceleration=(self.acceleration,self.acceleration))
        self._commChannel.sigUpdateMotorPosition.emit()
        
        # move back to initial position
        self.stophistoscan()

        # get stitched result
        def getStitchedResult():
            largeImage = stitcher.get_stitched_image()
            tifffile.imsave("stitchedImage.tif", largeImage, append=False) 
            # display result 
            self.setImageForDisplay(largeImage, "histoscanStitch")
        threading.Thread(target=getStitchedResult).start()

    def valueIlluChanged(self):
        illuSource = self._widget.getIlluminationSource()
        illuValue = self._widget.illuminationSlider.value()
        self._master.lasersManager
        if not self._master.lasersManager[illuSource].enabled:
            self._master.lasersManager[illuSource].setEnabled(1)
        
        illuValue = illuValue/100*self._master.lasersManager[illuSource].valueRangeMax
        self._master.lasersManager[illuSource].setValue(illuValue)

    def setImageForDisplay(self, image, name):
        self.histoScanStackName = name
        self.histoscanStack = image
        self.sigImageReceived.emit()
        
    def setPartialImageForDisplay(self, image, coordinates, name):
        # coordinates: (x,y,w,h)
        self.partialImageCoordinates = coordinates
        self.partialHistoscanStack = image
        self.histoscanStack = image
        self.sigUpdatePartialImage.emit()

    def stophistoscan(self):
        self.ishistoscanRunning = False
        self._widget.startButton.setEnabled(True)
        self._widget.stopButton.setEnabled(False)
        self._widget.startButton.setText("Start")
        self._widget.stopButton.setText("Stopped")
        self._widget.stopButton.setStyleSheet("background-color: green")
        self._widget.startButton.setStyleSheet("background-color: red")
        self._logger.debug("histoscan scanning stopped.")
        




class ImageStitcher:

    def __init__(self, parent, min_coords, max_coords,  folder, file_name, extension, subsample_factor=.25, nChannels = 3, flatfieldImage=None):
        # Initial min and max coordinates 
        self._parent = parent
        self.subsample_factor = subsample_factor
        self.min_coords = np.int32(np.array(min_coords)*self.subsample_factor)
        self.max_coords = np.int32(np.array(max_coords)*self.subsample_factor)
        
        # determine write location
        self.file_name = file_name
        self.file_path = os.sep.join([folder, file_name + extension])
        
        # Create a blank canvas for the final image and a canvas to track blending weights
        self.nY = self.max_coords[1] - self.min_coords[1]
        self.nX = self.max_coords[0] - self.min_coords[0]
        self.stitched_image = np.zeros((self.nY, self.nX, nChannels), dtype=np.float32)
        self.stitched_image_shape= self.stitched_image.shape
        self._parent.setImageForDisplay(self.stitched_image, "Stitched Image"+self.file_name)
        
        # get the background image
        if flatfieldImage is not None:
            self.flatfieldImage = cv2.resize(np.copy(flatfieldImage), None, fx=self.subsample_factor, fy=self.subsample_factor, interpolation=cv2.INTER_NEAREST)  
        else:
            self.flatfieldImage = np.ones((self.nY, self.nX, nChannels), dtype=np.float32)
        
        # Queue to hold incoming images
        self.queue = deque()

        # Thread lock for thread safety
        self.lock = threading.Lock()

        # Start a background thread for processing the queue
        self.processing_thread = threading.Thread(target=self._process_queue)
        self.isRunning = True
        self.processing_thread.start()

    def add_image(self, img, coords, metadata):
        with self.lock:
            self.queue.append((img, coords, metadata))

    def _process_queue(self):
        with tifffile.TiffWriter(self.file_path, bigtiff=True, append=True) as tif:
            while self.isRunning:
                with self.lock:
                    if not self.queue:
                        time.sleep(.1) # unload CPU
                        continue
                    img, coords, metadata = self.queue.popleft()
                    img = img/self.flatfieldImage
                    self._place_on_canvas(img, coords)

                    # write image to disk
                    tif.write(data=img, metadata=metadata)
            

    def _place_on_canvas(self, img, coords):
        # these are pixelcoordinates (e.g. center of the imageslice)
        offset_x = int(coords[0]*self.subsample_factor - self.min_coords[0])
        offset_y = int(self.max_coords[1]-coords[1]*self.subsample_factor)
        #self._parent._logger.debug("Coordinates: "+str((offset_x,offset_y)))

        # Calculate a feathering mask based on image intensity
        img = cv2.resize(np.copy(img), None, fx=self.subsample_factor, fy=self.subsample_factor, interpolation=cv2.INTER_NEAREST) 
        img = np.flip(np.flip(img,1),0)
        try: 
            stitchDim = self.stitched_image[offset_y-img.shape[0]:offset_y, offset_x:offset_x+img.shape[1]].shape
            stitchImage = img[0:stitchDim[0], 0:stitchDim[1]]
            if len(stitchImage.shape)==2:
                stitchImage = np.expand_dims(stitchImage, axis=-1)
            self.stitched_image[offset_y-img.shape[0]:offset_y, offset_x:offset_x+img.shape[1]] = stitchImage
        
            # try to display in napari if ready
            #self._parent.setPartialImageForDisplay(stitchImage, (offset_x, offset_y, img.shape[1], img.shape[0]), "Stitched Image")
        except Exception as e:
            self.__logger.error(e)

    def get_stitched_image(self):
        with self.lock:
            # Normalize by the weight image to get the final result
            stitched = self.stitched_image.copy()
            self.isRunning = False
            return stitched 

    def save_stitched_image(self, filename):
        stitched = self.get_stitched_image()
        imsave(filename, stitched)
    
    

class MovementController:
    def __init__(self, stages):
        self.stages = stages
        self.target_reached = False
        self.target_position = None
        self.axis = None


    def move_to_position(self, minPos, axis, speed, is_absolute):
        self.target_position = minPos
        self.speed = speed
        self.is_absolute = is_absolute
        self.axis = axis
        thread = threading.Thread(target=self._move)
        thread.start()

    def _move(self):
        self.target_reached = False
        self.stages.move(value=self.target_position, axis=self.axis, speed=self.speed, is_absolute=self.is_absolute, is_blocking=True)
        self.target_reached = True

    def is_target_reached(self):
        return self.target_reached



