import json
import os

from imswitch.imcommon.model import initLogger, ostools
import numpy as np
import time
import tifffile
import threading
from datetime import datetime
import cv2
import tifffile as tif
import datetime 
from itertools import product
try:
    from ashlar import fileseries, thumbnail, reg
    IS_ASHLAR = True
except:
    print("Ashlar not installed")
    IS_ASHLAR = False
import numpy as np
from tifffile import imread, imwrite, TiffFile

from imswitch.imcommon.model import dirtools, initLogger, APIExport
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex, Timer
import time

from ..basecontrollers import LiveUpdatedController


# import NanoImagingPack as nip

class HistoScanController(LiveUpdatedController):
    """Linked to HistoScanWidget."""

    sigImageReceived = Signal()

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
        self._commChannel.sigUpdateMotorPosition.connect(self.updateAllPositionGUI)

        # select stage
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]

    
    def updateAllPositionGUI(self):
        allPositions = self.stages.position
        self._widget.updateBoxPosition(allPositions["X"], allPositions["Y"])

    def goToPosition(self, posX, posY):
        self.stages.move(value=(posX,posY), axis="XY", is_absolute=True, is_blocking=False)
        self._commChannel.sigUpdateMotorPosition.emit()
        
    def displayImage(self):
        # a bit weird, but we cannot update outside the main thread
        name = self.histoScanStackName
        # subsample stack 
        isRGB = self.histoscanStack.shape[-1]==3
        self._widget.setImageNapari(np.uint16(self.histoscanStack ), colormap="gray", isRGB=isRGB, name=name, pixelsize=(1,1), translation=(0,0))

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
        speed = 20000
        self._widget.startButton.setEnabled(False)
        self._widget.stopButton.setEnabled(True)
        self._widget.startButton.setText("Running")
        self._widget.stopButton.setText("Stop") 
        self._widget.stopButton.setStyleSheet("background-color: red")
        self._widget.startButton.setStyleSheet("background-color: green")

        self.performScanningRecording(minPosX, maxPosX, minPosY, maxPosY, speed, 0)

    def performScanningRecording(self, minPos, maxPos, minPosY, maxPosY, speed, axis):
        if not self.ishistoscanRunning:
            self.ishistoscanRunning = True
            if self.histoscanTask is not None:
                self.histoscanTask.join()
                del self.histoscanTask
            self.histoscanTask = threading.Thread(target=self.histoscanThread, args=(minPos, maxPos, minPosY, maxPosY, speed, axis))
            self.histoscanTask.start()
        
    def generate_snake_scan_coordinates(self, posXmin, posYmin, posXmax, posYmax, img_width, img_height):
        # Calculate the number of steps in x and y directions
        steps_x = int((posXmax - posXmin) / img_width)
        steps_y = int((posYmax - posYmin) / img_height)
        
        coordinates = []

        # Loop over the positions in a snake pattern
        for y in range(steps_y):
            if y % 2 == 0:  # Even rows: left to right
                for x in range(steps_x):
                    coordinates.append((posXmin + x * img_width, posYmin + y * img_height))
            else:  # Odd rows: right to left
                for x in range(steps_x - 1, -1, -1):  # Starting from the last position, moving backwards
                    coordinates.append((posXmin + x * img_width, posYmin + y * img_height))
        
        return coordinates

        
    def histoscanThread(self, minPosX, maxPosX, minPosY, maxPosY, speed, axis, overlap=0.75):
        self._logger.debug("histoscan thread started.")
        
        initialPosition = self.stages.getPosition()
        initPosX = initialPosition["X"]
        initPosY = initialPosition["Y"]
        if not self.detector._running: self.detector.startAcquisition()
        
        # now start acquiring images and move the stage in Background
        
        mFrame = self.detector.getLatestFrame()

        dimensionsFrame = mFrame.shape[1]*self.detector.pixelSizeUm[-1]
        NpixX, NpixY = mFrame.shape[0], mFrame.shape[1]
        
        # starting the snake scan
        # Calculate the size of the area each image covers
        img_width = NpixX * self.detector.pixelSizeUm[-1]
        img_height = NpixY * self.detector.pixelSizeUm[-1]

        # precompute the position list in advance 
        positionList = self.generate_snake_scan_coordinates(minPosX, minPosY, maxPosX, maxPosY, img_width, img_height)
        
        # reseve space for the large image we will draw
        file_name = "test"
        extension = ".ome.tif"
        folder = self._master.HistoScanManager.defaultConfigPath

        #min_coords, max_coords,  folder, file_name, extension, pixelsize_eff=1, subsample_factor=.25)
        stitcher = ImageStitcher(min_coords=(int(minPosX-img_width),int(minPosY-img_height)), max_coords=(int(maxPosX+img_width),int(maxPosY+img_height)), 
                                 folder=folder, file_name=file_name, extension=extension, 
                                 pixelsize_eff=self.detector.pixelSizeUm[-1])

        for iPos in positionList:
            try:
                if not self.ishistoscanRunning:
                    break
                t0 = time.time()
                self.stages.move(value=iPos, axis="XY", is_absolute=True, is_blocking=True)
                print("moving took "+str(time.time()-t0))
                mFrame = self.detector.getLatestFrame()  
                print("snapping took "+str(time.time()-t0))
                metadata = {'Pixels': {
                    'PhysicalSizeX': self.detector.pixelSizeUm[-1],
                    'PhysicalSizeXUnit': 'µm',
                    'PhysicalSizeY': self.detector.pixelSizeUm[-1],
                    'PhysicalSizeYUnit': 'µm'},

                    'Plane': {
                        'PositionX': iPos[0],
                        'PositionY': iPos[1]
                }, }

                def addImage(mFrame, iPos):
                    self._commChannel.sigUpdateMotorPosition.emit()
                    stitcher.add_image(mFrame, iPos, metadata)
                threading.Thread(target=addImage, args=(mFrame, iPos,)).start()

                print("adding took "+str(time.time()-t0))

            except Exception as e:
                self._logger.error(e)


        # get stitched result
        largeImage = stitcher.get_stitched_image()
        tif.imsave("stitchedImage.tif", largeImage, append=False) 
        # display result 
        self.histoScanStackName = "histoscanStitch"
        self.histoscanStack = largeImage
        self.sigImageReceived.emit()

        # return to initial position
        self.stages.move(value=(initPosX,initPosY), axis="XY", is_absolute=True, is_blocking=True)
        self._commChannel.sigUpdateMotorPosition.emit()

        # move back to initial position
        self.stophistoscan()
        
        
        
        
    def stophistoscan(self):
        self.ishistoscanRunning = False
        self._widget.startButton.setEnabled(True)
        self._widget.stopButton.setEnabled(False)
        self._widget.startButton.setText("Start")
        self._widget.stopButton.setText("Stopped")
        self._widget.stopButton.setStyleSheet("background-color: green")
        self._widget.startButton.setStyleSheet("background-color: red")
        self._logger.debug("histoscan scanning stopped.")
        


import numpy as np
from skimage.io import imsave
from scipy.ndimage import gaussian_filter
from collections import deque

class ImageStitcher:

    def __init__(self, min_coords, max_coords,  folder, file_name, extension, pixelsize_eff=1, subsample_factor=.25):
        # Initial min and max coordinates 
        self.pixelsize_eff = pixelsize_eff
        self.subsample_factor = subsample_factor
        self.min_coords = np.int32(np.array(min_coords)/pixelsize_eff*self.subsample_factor)
        self.max_coords = np.int32(np.array(max_coords)/pixelsize_eff*self.subsample_factor)
        
        # reserve space for the image writer
        file_path = os.sep.join([folder, file_name + extension])
        self.tifwriter = tifffile.TiffWriter(file_path, bigtiff=True)

        # Create a blank canvas for the final image and a canvas to track blending weights
        self.stitched_image = np.zeros((self.max_coords[1] - self.min_coords[1], self.max_coords[0] - self.min_coords[0], 3), dtype=np.float32)
        self.weight_image = np.zeros(self.stitched_image.shape, dtype=np.float32)

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
        while self.isRunning:
            with self.lock:
                if not self.queue:
                    time.sleep(.1) # unload CPU
                    continue
                img, coords, metadata = self.queue.popleft()
                self._place_on_canvas(img, coords)

                # write image to disk
                self.tifwriter.write(data=img, metadata=metadata)
            

    def _place_on_canvas(self, img, coords):
        offset_x = int(coords[0]/self.pixelsize_eff*self.subsample_factor - self.min_coords[0])
        offset_y = int(coords[1]/self.pixelsize_eff*self.subsample_factor - self.min_coords[1])

        # Calculate a feathering mask based on image intensity
        img = cv2.resize(img, None, fx=self.subsample_factor, fy=self.subsample_factor, interpolation=cv2.INTER_NEAREST) > 1

        alpha = np.mean(img, axis=-1)
        alpha = gaussian_filter(alpha, sigma=10)
        alpha /= np.max(alpha)

        try:
            self.stitched_image[offset_y:offset_y+img.shape[0], offset_x:offset_x+img.shape[1]] += img * alpha[:, :, np.newaxis]
            self.weight_image[offset_y:offset_y+img.shape[0], offset_x:offset_x+img.shape[1]] += alpha[:, :, np.newaxis]
        except Exception as e:
            print(e)

    def get_stitched_image(self):
        with self.lock:
            # Normalize by the weight image to get the final result
            stitched = self.stitched_image / np.maximum(self.weight_image, 1e-5)
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



