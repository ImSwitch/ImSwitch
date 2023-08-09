import os
import threading
from datetime import datetime
import time
import cv2
import matplotlib.pyplot as plt
import numpy as np
import scipy
import scipy.ndimage as ndi
import scipy.signal as signal
import skimage.transform as transform
import tifffile as tif

from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex, Timer
from imswitch.imcommon.model import dirtools, initLogger, APIExport
from skimage.registration import phase_cross_correlation
from ..basecontrollers import ImConWidgetController

class LightsheetController(ImConWidgetController):
    """Linked to LightsheetWidget."""
    sigImageReceived = Signal()
    sigSliderIlluValueChanged = Signal(float)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self)

        self.lightsheetTask = None
        self.lightsheetStack = np.ones((1,1,1))
        self._widget.startButton.clicked.connect(self.startLightsheet)
        self._widget.stopButton.clicked.connect(self.stopLightsheet)
        
        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]
        
        # select lasers and add to gui
        allLaserNames = self._master.lasersManager.getAllDeviceNames()
        self._widget.setAvailableIlluSources(allLaserNames)
        
        # select stage
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]
        self._widget.setAvailableStageAxes(self.stages.axes)
        self.isLightsheetRunning = False
        
        self._widget.sigSliderIlluValueChanged.connect(self.valueIlluChanged)
        self.sigImageReceived.connect(self.displayImage)
        
    def displayImage(self):
        # a bit weird, but we cannot update outside the main thread
        name = "Lightsheet Stack"
        # subsample stack 
        self._widget.setImage(np.uint16(self.lightsheetStack ), colormap="gray", name=name, pixelsize=(100,1,1), translation=(0,0,0))

    def valueIlluChanged(self):
        illuSource = self._widget.getIlluminationSource()
        illuValue = self._widget.illuminationSlider.value()
        self._master.lasersManager
        if not self._master.lasersManager[illuSource].enabled:
            self._master.lasersManager[illuSource].setEnabled(1)
        
        illuValue = illuValue/100*self._master.lasersManager[illuSource].valueRangeMax
        self._master.lasersManager[illuSource].setValue(illuValue)

    def startLightsheet(self):
        minPos = self._widget.getMinPosition()
        maxPos = self._widget.getMaxPosition()
        speed = self._widget.getSpeed()
        illuSource = self._widget.getIlluminationSource()
        stageAxis = self._widget.getStageAxis()
        self._logger.debug("Starting lightsheet scanning with "+str(illuSource)+" on "+str(stageAxis)+" axis.")

        self._widget.startButton.setEnabled(False)
        self._widget.stopButton.setEnabled(True)
        self._widget.startButton.setText("Running")
        self._widget.stopButton.setText("Stop") 
        self._widget.stopButton.setStyleSheet("background-color: red")
        self._widget.startButton.setStyleSheet("background-color: green")

        self.performScanningRecording(minPos, maxPos, speed, stageAxis, illuSource, 0)

    def performScanningRecording(self, minPos, maxPos, speed, axis, illusource, illuvalue):
        if not self.isLightsheetRunning:
            self.isLightsheetRunning = True
            if self.lightsheetTask is not None:
                self.lightsheetTask.join()
                del self.lightsheetTask
            self.lightsheetTask = threading.Thread(target=self.lightsheetThread, args=(minPos, maxPos, speed, axis, illusource, illuvalue))
            self.lightsheetTask.start()
        
        
    def lightsheetThread(self, minPos, maxPos, speed, axis, illusource, illuvalue):
        self._logger.debug("Lightsheet thread started.")
        
        initialPosition = self.stages.getPosition()[axis]
        self.detector.startAcquisition()
        # move to minPos
        self.stages.move(value=minPos, axis=axis, is_absolute=False, is_blocking=True)
        
        # now start acquiring images and move the stage in Background
        controller = MovementController(self.stages)
        controller.move_to_position(maxPos+np.abs(minPos), axis, speed, is_absolute=False)

        iFrame = 0
        allFrames = []
        while self.isLightsheetRunning:
            allFrames.append(self.detector.getLatestFrame())
            if controller.is_target_reached():
                break
            iFrame += 1
            print(iFrame)
        # move back to initial position
        self.stages.move(value=-maxPos, axis=axis, is_absolute=False, is_blocking=True)
        
        # do something with the frames 
        self.lightsheetStack = np.array(allFrames[0::30])
        self.sigImageReceived.emit()
        
        self.stopLightsheet()
        
        
        
    def stopLightsheet(self):
        self.isLightsheetRunning = False
        self._widget.startButton.setEnabled(True)
        self._widget.stopButton.setEnabled(False)
        self._widget.startButton.setText("Start")
        self._widget.stopButton.setText("Stopped")
        self._widget.stopButton.setStyleSheet("background-color: green")
        self._widget.startButton.setStyleSheet("background-color: red")
        self._logger.debug("Lightsheet scanning stopped.")
        


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
