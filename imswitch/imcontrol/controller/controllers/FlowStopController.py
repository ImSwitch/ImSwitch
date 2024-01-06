import numpy as np
import datetime
try:
    import NanoImagingPack as nip
    isNIP = True
except:
    isNIP = False
import time
import threading
import collections
from imswitch.imcommon.model import dirtools, modulesconfigtools, ostools, APIExport
from imswitch.imcommon.framework import Signal, Worker, Mutex, Timer
from imswitch.imcontrol.view import guitools
from imswitch.imcommon.model import initLogger
from ..basecontrollers import LiveUpdatedController
import imswitch 
from threading import Thread


class FlowStopController(LiveUpdatedController):
    """ Linked to FlowStopWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self, tryInheritParent=False)

        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detectorFlowCam = allDetectorNames[0]
        # connect camera and stage
        self.positionerName = self._master.positionersManager.getAllDeviceNames()[0]
        self.positioner = self._master.positionersManager[self.positionerName]
        # self.imageComputationWorker.setPositioner(self.positioner)
        self.pumpAxis = 'Y'
        self.focusAxis = 'Z'
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
            # start measurment thread (pressure)

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
        return self.is_measure, self.imagesTaken, self.mExperimentParameters
    
    @APIExport(runOnUIThread=True)
    def startFlowStopExperiment(self, timeStamp: str, experimentName: str, experimentDescription: str, uniqueId: str, numImages: int, volumePerImage: float, timeToStabilize: float):
        """ Start FlowStop experiment. """
        self.thread = Thread(target=self.flowExperimentThread, name="FlowStopExperiment", args=(timeStamp, experimentName, experimentDescription, uniqueId, numImages, volumePerImage, timeToStabilize))
        self.thread.start()
        
    def stopFlowStopExperimentByButton(self):
        """ Stop FlowStop experiment. """
        self._widget.buttonStart.setEnabled(True)
        self._widget.buttonStop.setEnabled(False)
        self._widget.buttonStop.setStyleSheet("background-color: grey")
        self._widget.buttonStart.setStyleSheet("background-color: green")
        self.stopFlowStopExperiment()
        
    @APIExport(runOnUIThread=True)
    def stopFlowStopExperiment(self):
        self.is_measure=False
        if not imswitch.IS_HEADLESS:
            self._widget.buttonStart.setEnabled(True)
            self._widget.buttonStop.setEnabled(False)
            self._widget.buttonStop.setStyleSheet("background-color: grey")
            self._widget.buttonStart.setStyleSheet("background-color: green")
            

    def flowExperimentThread(self, timeStamp: str, experimentName: str, experimentDescription: str, uniqueId: str, numImages: int, volumePerImage: float, timeToStabilize: float):
        ''' FlowStop experiment thread. 
        The device captures images periodically by moving the pump at n-steps / ml, waits for a certain time
        and then moves on to the next step. The experiment is stopped when the user presses the stop button or
        it acquried N-images.
        
        User supplied parameters:
        
        '''
        
        for i in range(numImages):
            if self.is_measure:
                stepsToMove = volumePerImage 
                self.positioner.move(value=stepsToMove, axis=self.pumpAxis, is_absolute=False, is_blocking=True)
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
                mFileName = f'{timeStamp}_{experimentName}_{uniqueId}_{i}'
                self.snapImageFlowCam(mFileName, metaData)
                time.sleep(timeToStabilize)
                self.imagesTaken = i
                
                if not imswitch.IS_HEADLESS:
                    self._widget.labelStatusValue.setText(f'Running: {i+1}/{numImages}')
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
        self._master.recordingManager.snap([self.detectorFlowCam], savename=fileName, attrs=metaData)
        
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
    
    def changeExposureTime(self, value):
        """ Change exposure time. """
        self.detectorFlowCam.setExposureTime(value)
        
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
