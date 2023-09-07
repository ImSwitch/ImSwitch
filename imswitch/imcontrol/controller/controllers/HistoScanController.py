import json
import os

from imswitch.imcommon.model import initLogger, ostools
import numpy as np
import time
import tifffile
import threading
from datetime import datetime
import cv2
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
        
        # select stage
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]
        self._widget.setAvailableStageAxes(self.stages.axes)
        self.ishistoscanRunning = False
        
        self._widget.sigSliderIlluValueChanged.connect(self.valueIlluChanged)
        self.sigImageReceived.connect(self.displayImage)
        
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

    def starthistoscan(self):
        minPosX = self._widget.getMinPositionX()
        maxPosX = self._widget.getMaxPositionX()
        minPosY = self._widget.getMinPositionY()
        maxPosY = self._widget.getMaxPositionY()        
        speed = self._widget.getSpeed()
        illuSource = self._widget.getIlluminationSource()
        stageAxis = self._widget.getStageAxis()
        self._logger.debug("Starting histoscan scanning with "+str(illuSource)+" on "+str(stageAxis)+" axis.")

        self._widget.startButton.setEnabled(False)
        self._widget.stopButton.setEnabled(True)
        self._widget.startButton.setText("Running")
        self._widget.stopButton.setText("Stop") 
        self._widget.stopButton.setStyleSheet("background-color: red")
        self._widget.startButton.setStyleSheet("background-color: green")

        self.performScanningRecording(minPosX, maxPosX, minPosY, maxPosY, speed, stageAxis, illuSource, 0)

    def performScanningRecording(self, minPos, maxPos, minPosY, maxPosY, speed, axis, illusource, illuvalue):
        if not self.ishistoscanRunning:
            self.ishistoscanRunning = True
            if self.histoscanTask is not None:
                self.histoscanTask.join()
                del self.histoscanTask
            self.histoscanTask = threading.Thread(target=self.histoscanThread, args=(minPos, maxPos, minPosY, maxPosY, speed, axis, illusource, illuvalue))
            self.histoscanTask.start()
        
        
    def histoscanThread(self, minPosX, maxPosX, minPosY, maxPosY, speed, axis, illusource, illuvalue):
        self._logger.debug("histoscan thread started.")
        
        initialPosition = self.stages.getPosition()
        if not self.detector._running: self.detector.startAcquisition()
        # move to minPos
        self.stages.move(value=minPosX, axis="X", is_absolute=False, is_blocking=True)
        self.stages.move(value=minPosY, axis="Y", is_absolute=False, is_blocking=True)
        
        # now start acquiring images and move the stage in Background
        controller = MovementController(self.stages)
        
        
        # starting the snake scan
        direction = 1
        for yPos in np.arange(int(minPosY), int(maxPosY+1), int((maxPosY-minPosY)/4)):
            
            # move y axis
            self.stages.move(value=initialPosition["Y"]+yPos, axis="Y", is_absolute=True, is_blocking=True)
            
            # move and record for x axis
            controller.move_to_position(direction*(maxPosX+np.abs(minPosX)), "X", speed, is_absolute=False)
            # After each row, reverse the X direction to create the snake pattern
            direction *= -1
            iFrame = 0
            allFrames = []
            nThFrame = 1
            mFrameOverlap = 0.5
            self.detector
            # artificially reduce framerate
            while self.ishistoscanRunning:
                if iFrame%nThFrame == 0: # limit framerate?
                    allFrames.append(self.detector.getLatestFrame())
                if controller.is_target_reached():
                    break
                iFrame += 1
                print(iFrame)
                
            # assign positions based on number of frames and time (assume constant speed)
            posList = np.linspace(minPosX, maxPosX, len(allFrames))
            if not direction:
                posList = np.flip(posList)
            # now pick frames that match the overlap
            dimensionsFrame = allFrames[0].shape[1]*self.detector.pixelSizeUm[-1]
            # pick frames according to their position over the x-scan
            allSelectedFrames = []
            selectedPosList = []
            nSelectedFrames = int(((maxPosX+abs(minPosX))/dimensionsFrame)/mFrameOverlap)
            for iSelectedFrame in range(0, nSelectedFrames):
                iPosition = iSelectedFrame*dimensionsFrame*mFrameOverlap+minPosX
                # find closest position and add to the list
                closestPosition = np.argmin(np.abs(posList-iPosition))
                allSelectedFrames.append(allFrames[closestPosition])
                selectedPosList.append(posList[closestPosition])
                
            # subsample stack    
            self.histoscanStack = np.array(allSelectedFrames)
            nX, nY = self.histoscanStack.shape[1], self.histoscanStack.shape[2]
            if len(self.histoscanStack.shape) > 3:
                nC = self.histoscanStack.shape[3]
            else: 
                nC = 1
            nPixelCanvasX = int(nX*len(allSelectedFrames)*mFrameOverlap)
            xCanvas = np.zeros((nPixelCanvasX, nY, nC))
            for iFrame, frame in enumerate(self.histoscanStack):
                # add frames to canvas according to their positions and blend them
                try:
                    xCanvas[int(iFrame*nX*mFrameOverlap):int(iFrame*nX*mFrameOverlap+nX), :, :] += frame
                except Exception as e:
                    # probably out of bounds due to last frame not fitting in
                    print(e)
        
            # display result 
            self.histoScanStackName = "histoscan"+str(yPos)
            self.histoscanStack = xCanvas
            self.sigImageReceived.emit()
        
        self.stophistoscan()
        
        # move back to initial position
        self.stages.move(value=initialPosition["X"], axis="X", is_absolute=True, is_blocking=False)
        self.stages.move(value=initialPosition["Y"], axis="Y", is_absolute=True, is_blocking=False)
        
        
        
    def stophistoscan(self):
        self.ishistoscanRunning = False
        self._widget.startButton.setEnabled(True)
        self._widget.stopButton.setEnabled(False)
        self._widget.startButton.setText("Start")
        self._widget.stopButton.setText("Stopped")
        self._widget.stopButton.setStyleSheet("background-color: green")
        self._widget.startButton.setStyleSheet("background-color: red")
        self._logger.debug("histoscan scanning stopped.")
        


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
