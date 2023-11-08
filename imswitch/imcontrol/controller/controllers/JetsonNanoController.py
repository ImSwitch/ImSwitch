import json
import os

import numpy as np
import time
import tifffile as tif
import threading
from datetime import datetime
import cv2



from imswitch.imcommon.model import dirtools, initLogger, APIExport
from imswitch.imcontrol.model import RecMode, SaveMode, SaveFormat
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex, Timer
import time

from ..basecontrollers import ImConWidgetController

#import NanoImagingPack as nip

class JetsonNanoController(ImConWidgetController):
    """Linked to JetsonNanoWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self)

        '''
        initliaze hardware
        '''
        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]
        self._master.detectorsManager.startAcquisition(liveView=True)

        
        # TODO: misleading we have LEDs and LED Matrices here...
        self.intensity = 100
        allLEDNames = self._master.LEDMatrixsManager.getAllDeviceNames()
        self.leds = []
        for iDevice in allLEDNames:
            if iDevice.find("LED")>=0:
                self.leds.append(self._master.LEDMatrixsManager[iDevice])
        # turn on a little bit
        self.leds[0].setAll(self.intensity)
        
        # default stepsize for steppers
        self.zDistance = 1000
        
        # connect XY Stagescanning live update  https://github.com/napari/napari/issues/1110
        self.sigImageReceived.connect(self.displayImage)

        # select stage
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]
        self.isJetsonNanorunning = False

        
        # wire up the gui        
        self._widget.pushButtonFocusDown.clicked.connect(self.focusDown)
        self._widget.pushButtonFocusUp.clicked.connect(self.focusUp)
        self._widget.pushButtonAutofocus.clicked.connect(self.autofocus)
        self._widget.pushButtonIlluOn.clicked.connect(self.illuOn)
        self._widget.pushButtonIlluOff.clicked.connect(self.illuOff)
        self._widget.pushButtonSnap.clicked.connect(self.snap)
        self._widget.pushButtonRec.clicked.connect(self.toggleRec)
        self._widget.spinBoxExposure.valueChanged.connect(self.setExposureTime)
        self._widget.spinBoxGain.valueChanged.connect(self.setGain)
        self._widget.spinBoxBlacklevel.valueChanged.connect(self.setBlacklevel)
        
        # autofocus related
        self.isAutofocusRunning = False
        #self._commChannel.sigAutoFocusRunning.connect(self.setAutoFocusIsRunning)

    def setExposureTime(self, value=None):
        if value is None:
            value = self._widget.spinBoxExposure.value()
        #self.detector.setProperty("exposure", value)
        self.detector._camera.set_exposure_time(value*1e-3)
        
    def setGain(self, value=None):
        if value is None:
            value = self._widget.spinBoxGain.value()
        #self.detector.setProperty("gain", value)
        self.detector._camera.set_gain(value)
        
    def setBlacklevel(self, value=None):
        if value is None:
            value = self._widget.spinBoxBlacklevel.value()
        #self.detector.setProperty("blacklevel", value)
        self.detector._camera.set_blacklevel(value)
               
    def moveFocusStage(self, zDistance=100):
        self.illuOff()
        self.stages.move(value=zDistance, axis="Z", is_absolute=False, is_blocking=True)
        self.illuOn()
    
    def focusDown(self, buttonValue):
        self.moveFocusStage(zDistance=-100)
        
    def focusUp(self, buttonValue=False, zDistance=-100):
        self.moveFocusStage(zDistance=100)
        
    def autofocus(self):
        #autofocusParams = self._widget.getAutofocusValues()
        autofocusParams = {}
        autofocusParams["valueRange"] = 400
        autofocusParams["valueSteps"] = 30
        
        # turn on illumination
        self.illuOn(value=255)
        time.sleep(.05)

        self.doAutofocus(autofocusParams)
    
    def setIllu(self, value=100):
        self.leds[0].setAll(value)
        
    def illuOn(self, buttonValue=False):
        self.setIllu(self.intensity)
        
    def illuOff(self, buttonValue=False):
        self.setIllu(0)
    
    def snap(self):
        '''snap a single image and save it to disk'''
        self.JetsonNanoFilename = "UC2_JetsonNano_Snap"
        JetsonNanoDate = datetime.now().strftime("%Y_%m_%d-%I-%M-%S_%p")
        fileExtension = "tif"
        filePath = self.getSaveFilePath(date=JetsonNanoDate,
                    timestamp=1,
                    filename=f'{self.JetsonNanoFilename}',
                    extension=fileExtension)
        self.leds[0].setAll(100)
        time.sleep(0.1)
        
        lastFrame = self.detector.getLatestFrame()
        # wait for frame after next frame to appear. Avoid motion blurring
        #while self.detector.getFrameNumber()<(frameNumber+nFrameSyncWait):time.sleep(0.05)
        #TODO: USE self._master.recordingManager.snap()
        tif.imwrite(filePath, lastFrame, append=True)
        self.displayImage(lastFrame, name="UC2 Snap")

    def toggleRec(self):
        """ Start or end recording. """
        if self.isJetsonNanorunning  and not self.recording:
        
            self.updateRecAttrs(isSnapping=False)

            folder = self._widget.getRecFolder()
            if not os.path.exists(folder):
                os.makedirs(folder)
            time.sleep(0.01)
            self.savename = os.path.join(folder, self.getFileName()) + '_rec'

            if self.recMode == RecMode.ScanOnce:
                self._commChannel.sigScanStarting.emit()  # To get correct values from sharedAttrs

            detectorsBeingCaptured = self.getDetectorNamesToCapture()

            self.recordingArgs = {
                'detectorNames': detectorsBeingCaptured,
                'recMode': self.recMode,
                'savename': self.savename,
                'saveMode': SaveMode(self._widget.getRecSaveMode()),
                'saveFormat': SaveFormat(self._widget.getsaveFormat()),
                'attrs': {detectorName: self._commChannel.sharedAttrs.getHDF5Attributes()
                          for detectorName in detectorsBeingCaptured},
                'singleMultiDetectorFile': (len(detectorsBeingCaptured) > 1 and
                                            self._widget.getMultiDetectorSingleFile())
            }

            if self.recMode == RecMode.SpecFrames:
                self.recordingArgs['recFrames'] = self._widget.getNumExpositions()
                self._master.recordingManager.startRecording(**self.recordingArgs)
            elif self.recMode == RecMode.SpecTime:
                self.recordingArgs['recTime'] = self._widget.getTimeToRec()
                self._master.recordingManager.startRecording(**self.recordingArgs)
            elif self.recMode == RecMode.ScanOnce:
                self.recordingArgs['recFrames'] = self._commChannel.getNumScanPositions()
                self._master.recordingManager.startRecording(**self.recordingArgs)
                time.sleep(0.3)
                self._commChannel.sigRunScan.emit(True, False)
            elif self.recMode == RecMode.ScanLapse:
                self.recordingArgs['singleLapseFile'] = self._widget.getTimelapseSingleFile()
                self.lapseTotal = self._widget.getTimelapseTime()
                self.lapseCurrent = 0
                self.nextLapse()
            else:
                self._master.recordingManager.startRecording(**self.recordingArgs)

            self.recording = True
        else:
            if self.recMode == RecMode.ScanLapse and self.lapseCurrent != -1:
                self._commChannel.sigAbortScan.emit()
            self._master.recordingManager.endRecording()        
        
    def displayImage(self, image, name="UC2 Snap"):
        # a bit weird, but we cannot update outside the main thread
        name = "tilescanning"
        self._widget.setImage(np.uint16(image), colormap="gray", name=name, pixelsize=(1,1), translation=(0,0))


    def getSaveFilePath(self, date, timestamp, filename, extension):
        mFilename =  f"{date}_{filename}.{extension}"
        dirPath  = os.path.join(dirtools.UserFileDirs.Root, 'recordings', date, "t"+str(timestamp))

        newPath = os.path.join(dirPath,mFilename)

        if not os.path.exists(dirPath):
            os.makedirs(dirPath)

        return newPath


    
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
