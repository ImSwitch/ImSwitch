import numpy as np
import datetime
import tifffile as tif
try:
    import NanoImagingPack as nip
    isNIP = True
except:
    isNIP = False
import time
import os
from imswitch.imcommon.model import dirtools, APIExport
from imswitch.imcommon.framework import Signal, Worker, Mutex, Timer
from imswitch.imcontrol.view import guitools
from imswitch.imcommon.model import initLogger
from ..basecontrollers import LiveUpdatedController
import imswitch
from threading import Thread
from imswitch.imcontrol.model import RecMode, SaveMode, SaveFormat

class FlowStopController(LiveUpdatedController):
    """ Linked to FlowStopWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self, tryInheritParent=False)
        
        # load from config file in User/Documents/ImSwitchConfig
        self.wasRunning = self._master.FlowStopManager.defaultConfig["wasRunning"]
        self.defaultFlowRate = self._master.FlowStopManager.defaultConfig["defaultFlowRate"]
        self.defaultNumberOfFrames = self._master.FlowStopManager.defaultConfig["defaultNumberOfFrames"]
        self.defaultExperimentName = self._master.FlowStopManager.defaultConfig["defaultExperimentName"]
        self.defaultFrameRate = self._master.FlowStopManager.defaultConfig["defaultFrameRate"]
        self.defaultSavePath = self._master.FlowStopManager.defaultConfig["defaultSavePath"]
        self.pumpAxis = self._master.FlowStopManager.defaultConfig["defaultAxisFlow"]
        self.focusAxis = self._master.FlowStopManager.defaultConfig["defaultAxisFocus"]
        self.defaultDelayTimeAfterRestart = self._master.FlowStopManager.defaultConfig["defaultDelayTimeAfterRestart"]
        self.tSettle = 0.05
        
        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detectorFlowCam = self._master.detectorsManager[allDetectorNames[0]]
        
        self.is_measure = False
        
        # select light source and activate
        allIlluNames = self._master.lasersManager.getAllDeviceNames()
        self.ledSource = self._master.lasersManager[allIlluNames[0]]
        #self.ledSource.setValue(1023)
        self.ledSource.setEnabled(1)
        # connect camera and stage
        self.positionerName = self._master.positionersManager.getAllDeviceNames()[0]
        self.positioner = self._master.positionersManager[self.positionerName]

        # start live and adjust camera settings to auto exposure
        self.changeAutoExposureTime('auto')
        
        # Connect FlowStopWidget signals
        if not imswitch.IS_HEADLESS:
            # Connect CommunicationChannel signals
            self._commChannel.sigUpdateImage.connect(self.update)
            self._widget.sigSnapClicked.connect(self.snapImageFlowCam)
            self._widget.sigSliderFocusValueChanged.connect(self.changeFocus)
            self._widget.sigSliderPumpSpeedValueChanged.connect(self.changePumpSpeed)
            self._widget.sigExposureTimeChanged.connect(self.changeExposureTime)
            self._widget.sigGainChanged.connect(self.changeGain)
            self._widget.sigPumpDirectionToggled.connect(self.changePumpDirection)

            # Connect buttons
            self._widget.buttonStart.clicked.connect(self.startFlowStopExperimentByButton)
            self._widget.buttonStop.clicked.connect(self.stopFlowStopExperimentByButton)
            self._widget.pumpMovePosButton.clicked.connect(self.movePumpPos)
            self._widget.pumpMoveNegButton.clicked.connect(self.movePumpNeg)
            
        # start thread if it was funning 
        if self.wasRunning:
            timeStamp = datetime.datetime.now().strftime("%Y_%m_%d-%I-%M-%S_%p")
            experimentName = self.defaultExperimentName
            experimentDescription = ""
            uniqueId = np.random.randint(0, 2**16)
            numImages = self.defaultNumberOfFrames
            volumePerImage = self.defaultFlowRate
            timeToStabilize = self.tSettle
            delayToStart = self.defaultDelayTimeAfterRestart
            frameRate = self.defaultFrameRate
            filePath = self.defaultSavePath
            self.startFlowStopExperiment(timeStamp, experimentName, experimentDescription, 
                                         uniqueId, numImages, volumePerImage, timeToStabilize, delayToStart, 
                                         frameRate, filePath)
            
    def startFlowStopExperimentByButton(self):
        """ Start FlowStop experiment. """
        self.is_measure=True
        self.mExperimentParameters = self._widget.getAutomaticImagingParameters()

        # parse the parameters from dict to single variables
        '''
        'timeStamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'experimentName': self.textEditExperimentName.text(),
        'experimentDescription': self.textEditExperimentDescription.text(),
        'uniqueId': self.textEditUniqueId.text(),
        'numImages': self.textEditNumImages.text(),
        'volumePerImage': self.textEditVolumePerImage.text(),
        'timeToStabilize': self.textEditTimeToStabilize.text(),
        '''
        timeStamp = self.mExperimentParameters['timeStamp']
        experimentName = self.mExperimentParameters['experimentName']
        experimentDescription = self.mExperimentParameters['experimentDescription']
        uniqueId = self.mExperimentParameters['uniqueId']
        numImages = int(self.mExperimentParameters['numImages'])
        volumePerImage = float(self.mExperimentParameters['volumePerImage'])
        timeToStabilize = float(self.mExperimentParameters['timeToStabilize'])
        self._widget.buttonStart.setEnabled(False)
        self._widget.buttonStop.setEnabled(True)
        self._widget.buttonStop.setStyleSheet("background-color: red")
        self._widget.buttonStart.setStyleSheet("background-color: grey")
        self.startFlowStopExperiment(timeStamp, experimentName, experimentDescription, uniqueId, numImages, volumePerImage, timeToStabilize)

    @APIExport(runOnUIThread=True)
    def getStatus(self):
        return self.is_measure, self.imagesTaken

    @APIExport(runOnUIThread=True)
    def startFlowStopExperiment(self, timeStamp: str, experimentName: str, experimentDescription: str, 
                                uniqueId: str, numImages: int, volumePerImage: float, timeToStabilize: float, 
                                delayToStart: float=1, frameRate: float=1, filePath: str="./"):
        """ Start FlowStop experiment. """
        self.thread = Thread(target=self.flowExperimentThread, 
                             name="FlowStopExperiment", 
                             args=(timeStamp, experimentName, experimentDescription, 
                                   uniqueId, numImages, volumePerImage, timeToStabilize,
                                   delayToStart, frameRate, filePath))
        self.thread.start()

    def stopFlowStopExperimentByButton(self):
        """ Stop FlowStop experiment. """
        self._widget.buttonStart.setEnabled(True)
        self._widget.buttonStop.setEnabled(False)
        self._widget.buttonStop.setStyleSheet("background-color: grey")
        self._widget.buttonStart.setStyleSheet("background-color: green")
        self.stopFlowStopExperiment()

    @APIExport(runOnUIThread=True)
    def stopPump(self):
        self.positioner.stopAll()

    @APIExport(runOnUIThread=True)
    def movePump(self, value: float = 0.0, speed: float = 10000.0):
        self.positioner.move(value=value, speed=speed, axis=self.pumpAxis, is_absolute=False, is_blocking=False)
    
    @APIExport(runOnUIThread=True)
    def moveFocus(self, value: float = 0.0, speed: float = 10000.0):
        self.positioner.move(value=value, speed=speed, axis=self.focusAxis, is_absolute=False, is_blocking=False)
        
    @APIExport(runOnUIThread=True)
    def stopFocus(self):
        self.positioner.stopAll()
        
    @APIExport(runOnUIThread=True)
    def getCurrentFrameNumber(self):
        return self.imagesTaken
    
    @APIExport(runOnUIThread=True)
    def setIlluIntensity(self, value: float = 0.0):
        self.ledSource.setValue(value)

    @APIExport(runOnUIThread=True)
    def stopFlowStopExperiment(self):
        self.is_measure=False
        if not imswitch.IS_HEADLESS:
            self._widget.buttonStart.setEnabled(True)
            self._widget.buttonStop.setEnabled(False)
            self._widget.buttonStop.setStyleSheet("background-color: grey")
            self._widget.buttonStart.setStyleSheet("background-color: green")

    def flowExperimentThread(self, timeStamp: str, experimentName: str, 
                             experimentDescription: str, uniqueId: str, 
                             numImages: int, volumePerImage: float, 
                             timeToStabilize: float, delayToStart: float=0, 
                             frameRate: float=1, filePath:str="./"):
        ''' FlowStop experiment thread.
        The device captures images periodically by moving the pump at n-steps / ml, waits for a certain time
        and then moves on to the next step. The experiment is stopped when the user presses the stop button or
        it acquried N-images.

        User supplied parameters:

        '''
        self._logger.debug("Starting the FlowStop experiment thread in {delayToStart} seconds.")
        time.sleep(delayToStart)
        self._commChannel.sigStartLiveAcquistion.emit(True)
        self.is_measure = True
        if numImages < 0: numImages = np.inf
        self.imagesTaken = 0
        dirPath  = os.path.join(dirtools.UserFileDirs.Root, 'recordings', timeStamp)
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
        while True:
            currentTime = time.time()
            self.imagesTaken += 1
            if self.imagesTaken > numImages: break
            if self.is_measure:
                stepsToMove = volumePerImage
                self.positioner.move(value=stepsToMove, speed=1000, axis=self.pumpAxis, is_absolute=False, is_blocking=True)
                time.sleep(timeToStabilize)
                metaData = {
                    'timeStamp': timeStamp,
                    'experimentName': experimentName,
                    'experimentDescription': experimentDescription,
                    'uniqueId': uniqueId,
                    'numImages': numImages,
                    'volumePerImage': volumePerImage,
                    'timeToStabilize': timeToStabilize,
                }
                self.setSharedAttr('FlowStop', _metaDataAttr, metaData)
                

                # save image                    
                mFileName = f'{timeStamp}_{experimentName}_{uniqueId}_{self.imagesTaken}'
                mFilePath = os.path.join(dirPath, mFileName)
                self.snapImageFlowCam(mFilePath, metaData)
                
                # maintain framerate
                while (time.time()-currentTime)<(1/frameRate):
                    time.sleep(0.05)
                if not imswitch.IS_HEADLESS:
                    self._widget.labelStatusValue.setText(f'Running: {self.imagesTaken+1}/{numImages}')
            else:
                break

        self.stopFlowStopExperiment()

    def setSharedAttr(self, laserName, attr, value):
        self.settingAttr = True
        try:
            self._commChannel.sharedAttrs[(_attrCategory, laserName, attr)] = value
        finally:
            self.settingAttr = False

    @APIExport(runOnUIThread=True)
    def snapImageFlowCam(self, fileName=None, metaData={}):
        """ Snap image. """
        if fileName is None or not fileName:
            fileName = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

        if 1:
            mFrame = self.detectorFlowCam.getLatestFrame()  
            if mFrame is None:
                self._logger.warning("No frame received from the camera.")
                return
            tif.imsave(fileName, mFrame, append=False)
        else:
            pngFormat = SaveFormat.PNG
            saveMode = SaveMode.Disk
            self._master.recordingManager.snap([self.detectorFlowCam], saveMode=saveMode, saveFormat=pngFormat, savename=fileName, attrs=metaData)

    def movePumpPos(self):
        self.positioner.moveRelative((0,0,1*self.directionPump))

    def movePumpNeg(self):
        self.positioner.moveRelative((0,0,-1*self.directionPump))

    def changeFocus(self, value):
        """ Change focus. """
        self.positioner.move

    def changePumpSpeed(self, value):
        """ Change pump speed. """
        self.speedPump = value
        self.positioner.moveForever(speed=(self.speedPump,self.speedRotation,0),is_stop=False)

    @APIExport(runOnUIThread=True)
    def changeExposureTime(self, value):
        """ Change exposure time. """
        self.detector.setParameter(name="exposure", value=value)
    
    @APIExport(runOnUIThread=True)
    def changeAutoExposureTime(self, value):
        """ Change auto exposure time. """
        self.detectorFlowCam.setParameter(name="exposure_mode", value=value)
        
    def changeGain(self, value):
        """ Change gain. """
        self.detectorFlowCam.setGain(value)

    def changePumpDirection(self, value):
        """ Change pump direction. """
        self.directionPump = value
        self.positioner.moveForever(speed=(self.speedPump,self.speedRotation,0),is_stop=False)

    def __del__(self):
        self.is_measure=False
        if hasattr(super(), '__del__'):
            super().__del__()

    def displayImage(self, im):
        """ Displays the image in the view. """
        self._widget.setImage(im)

    def update(self, detectorName, im, init, isCurrentDetector):
        """ Update with new detector frame. """
        if not isCurrentDetector or not self.active:
            return

        if self.it == self.updateRate:
            self.it = 0
            self.imageComputationWorker.prepareForNewImage(im)
            self.sigImageReceived.emit()
        else:
            self.it += 1


_attrCategory = 'Laser'
_metaDataAttr = 'metaData'
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
