import os
import time

from imswitch.imcommon.framework import Timer
from imswitch.imcommon.model import filetools, ostools, APIExport
from imswitch.imcontrol.model import SaveMode, RecMode
from .basecontrollers import ImConWidgetController


class RecordingController(ImConWidgetController):
    """ Linked to RecordingWidget. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.setDetectorList(
            self._master.detectorsManager.execOnAll(lambda c: c.model,
                                                    condition=lambda c: c.forAcquisition)
        )

        self.settingAttr = False
        self.recording = False
        self.lapseCurrent = 0
        self.lapseTotal = 0

        imreconstructRegistered = self._moduleCommChannel.isModuleRegistered('imreconstruct')
        self._widget.setSaveMode(SaveMode.Disk.value)
        self._widget.setSaveModeVisible(imreconstructRegistered)

        self.untilStop()

        # Connect CommunicationChannel signals
        self._commChannel.sigRecordingEnded.connect(self.recordingEnded)
        self._commChannel.sigUpdateRecFrameNum.connect(self._widget.updateRecFrameNum)
        self._commChannel.sigUpdateRecTime.connect(self._widget.updateRecTime)
        self._commChannel.sigScanEnded.connect(self.scanDone)
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged)

        # Connect RecordingWidget signals
        self._widget.sigDetectorChanged.connect(self.detectorChanged)
        self._widget.sigOpenRecFolderClicked.connect(self.openFolder)
        self._widget.sigSpecFileToggled.connect(self._widget.setCustomFilenameEnabled)
        self._widget.sigSnapRequested.connect(self.snap)
        self._widget.sigRecToggled.connect(self.toggleREC)
        self._widget.sigSpecFramesPicked.connect(self.specFrames)
        self._widget.sigSpecTimePicked.connect(self.specTime)
        self._widget.sigScanOncePicked.connect(self.recScanOnce)
        self._widget.sigScanLapsePicked.connect(self.recScanLapse)
        self._widget.sigUntilStopPicked.connect(self.untilStop)

    def openFolder(self):
        """ Opens current folder in File Explorer. """
        try:
            ostools.openFolderInOS(self._widget.getRecFolder())
        except ostools.OSUtilsError:
            ostools.openFolderInOS(self._widget.dataDir)

    def snap(self):
        """ Take a snap and save it to a .tiff file. """
        self.updateRecAttrs(isSnapping=True)

        folder = self._widget.getRecFolder()
        if not os.path.exists(folder):
            os.mkdir(folder)
        time.sleep(0.01)

        detectorNames = self.getDetectorNamesToCapture()
        name = os.path.join(folder, self.getFileName()) + '_snap'
        savename = filetools.getUniqueName(name)
        attrs = {detectorName: self._commChannel.sharedAttrs.getHDF5Attributes()
                 for detectorName in detectorNames}

        self._master.recordingManager.snap(detectorNames, savename, attrs)

    def toggleREC(self, checked):
        """ Start or end recording. """
        if checked and not self.recording:
            self.updateRecAttrs(isSnapping=False)

            folder = self._widget.getRecFolder()
            if not os.path.exists(folder):
                os.mkdir(folder)
            time.sleep(0.01)
            name = os.path.join(folder, self.getFileName()) + '_rec'
            self.savename = filetools.getUniqueName(name)
            self.saveMode = SaveMode(self._widget.getSaveMode())

            self.detectorsBeingCaptured = self.getDetectorNamesToCapture()
            self.attrs = {detectorName: self._commChannel.sharedAttrs.getHDF5Attributes()
                          for detectorName in self.detectorsBeingCaptured}

            recordingArgs = (self.detectorsBeingCaptured, self.recMode, self.savename,
                             self.saveMode, self.attrs)

            if self.recMode == RecMode.SpecFrames:
                self._master.recordingManager.startRecording(
                    *recordingArgs, recFrames=self._widget.getNumExpositions()
                )
            elif self.recMode == RecMode.SpecTime:
                self._master.recordingManager.startRecording(
                    *recordingArgs, recTime=self._widget.getTimeToRec()
                )
            elif self.recMode == RecMode.ScanOnce:
                self._master.recordingManager.startRecording(*recordingArgs)
                time.sleep(0.1)
                self._commChannel.sigPrepareScan.emit()
            elif self.recMode == RecMode.ScanLapse:
                self.lapseTotal = self._widget.getTimelapseTime()
                self.lapseCurrent = 0
                self.nextLapse()
            else:
                self._master.recordingManager.startRecording(*recordingArgs)

            self.recording = True
        else:
            self._master.recordingManager.endRecording()

    def scanDone(self):
        if self._widget.recButton.isChecked():
            if self.recMode == RecMode.ScanOnce:
                self._master.recordingManager.endRecording()
            elif self.recMode == RecMode.ScanLapse:
                self.lapseCurrent += 1
                if self.lapseCurrent < self.lapseTotal:
                    self._master.recordingManager.endRecording(emitSignal=False)
                    self._widget.updateRecLapseNum(self.lapseCurrent)
                    self.timer = Timer(singleShot=True)
                    self.timer.timeout.connect(self.nextLapse)
                    self.timer.start(int(self._widget.getTimelapseFreq() * 1000))
                else:
                    self._master.recordingManager.endRecording()

    def nextLapse(self):
        fileName = self.savename + "_" + str(self.lapseCurrent).zfill(len(str(self.lapseTotal)))
        self._master.recordingManager.startRecording(
            self.detectorsBeingCaptured, self.recMode, fileName, self.saveMode, self.attrs
        )
        time.sleep(0.3)
        self._commChannel.sigPrepareScan.emit()

    def recordingEnded(self):
        self.recording = False
        self.lapseCurrent = 0
        self._widget.updateRecFrameNum(0)
        self._widget.updateRecTime(0)
        self._widget.updateRecLapseNum(0)
        self._widget.setRecButtonChecked(False)

    def specFrames(self):
        self._widget.checkSpecFrames()
        self._widget.setEnabledParams(numExpositions=True)
        self.recMode = RecMode.SpecFrames

    def specTime(self):
        self._widget.checkSpecTime()
        self._widget.setEnabledParams(timeToRec=True)
        self.recMode = RecMode.SpecTime

    def recScanOnce(self):
        self._widget.checkScanOnce()
        self._widget.setEnabledParams()
        self.recMode = RecMode.ScanOnce

    def recScanLapse(self):
        self._widget.checkScanLapse()
        self._widget.setEnabledParams(timelapseTime=True, timelapseFreq=True)
        self.recMode = RecMode.ScanLapse

    def untilStop(self):
        self._widget.checkUntilStop()
        self._widget.setEnabledParams()
        self.recMode = RecMode.UntilStop

    def setRecMode(self, recMode):
        if recMode == RecMode.SpecFrames:
            self.specFrames()
        elif recMode == RecMode.SpecTime:
            self.specTime()
        elif recMode == RecMode.ScanOnce:
            self.recScanOnce()
        elif recMode == RecMode.ScanLapse:
            self.recScanLapse()
        elif recMode == RecMode.UntilStop:
            self.untilStop()
        else:
            raise ValueError(f'Invalid RecMode {recMode} specified')

    def detectorChanged(self):
        detectorListData = self._widget.getDetectorToCapture()
        if detectorListData == -2:  # §
            # When recording all detectors, the SpecFrames mode isn't supported
            self._widget.setSpecifyFramesAllowed(False)
        else:
            self._widget.setSpecifyFramesAllowed(True)

    def getDetectorNamesToCapture(self):
        """ Returns a list of which detectors the user has selected to be captured. """
        detectorListData = self._widget.getDetectorToCapture()
        if detectorListData == -1:  # Current detector at start
            return [self._master.detectorsManager.getCurrentDetectorName()]
        elif detectorListData == -2:  # All acquisition detectors
            return list(
                self._master.detectorsManager.execOnAll(
                    lambda c: c.name,
                    condition=lambda c: c.forAcquisition
                ).values()
            )
        else:  # A specific detector
            return [detectorListData]

    def getFileName(self):
        """ Gets the filename of the data to save. """
        filename = self._widget.getCustomFilename()
        if filename is None:
            filename = time.strftime('%Hh%Mm%Ss')
        return filename

    def attrChanged(self, key, value):
        if self.settingAttr or len(key) != 2 or key[0] != _attrCategory or value == 'null':
            return

        if key[1] == _recModeAttr:
            if value == 'Snap':
                return
            self.setRecMode(RecMode[value])
        elif key[1] == _framesAttr:
            self._widget.setNumExpositions(value)
        elif key[1] == _timeAttr:
            self._widget.setTimeToRec(value)
        elif key[1] == _lapseTimeAttr:
            self._widget.setTimelapseTime(value)
        elif key[1] == _freqAttr:
            self._widget.setTimelapseFreq(value)

    def setSharedAttr(self, attr, value):
        self.settingAttr = True
        try:
            self._commChannel.sharedAttrs[(_attrCategory, attr)] = value
        finally:
            self.settingAttr = False

    def updateRecAttrs(self, *, isSnapping):
        self.setSharedAttr(_framesAttr, 'null')
        self.setSharedAttr(_timeAttr, 'null')
        self.setSharedAttr(_lapseTimeAttr, 'null')
        self.setSharedAttr(_freqAttr, 'null')
        self.setSharedAttr(_slicesAttr, 'null')
        self.setSharedAttr(_stepSizeAttr, 'null')

        if isSnapping:
            self.setSharedAttr(_recModeAttr, 'Snap')
        else:
            self.setSharedAttr(_recModeAttr, self.recMode.name)
            if self.recMode == RecMode.SpecFrames:
                self.setSharedAttr(_framesAttr, self._widget.getNumExpositions())
            elif self.recMode == RecMode.SpecTime:
                self.setSharedAttr(_timeAttr, self._widget.getTimeToRec())
            elif self.recMode == RecMode.ScanLapse:
                self.setSharedAttr(_lapseTimeAttr, self._widget.getTimelapseTime())
                self.setSharedAttr(_freqAttr, self._widget.getTimelapseFreq())

    @APIExport
    def snapImage(self):
        """ Take a snap and save it to a .tiff file at the set file path. """
        self.snap()

    @APIExport
    def startRecording(self):
        """ Starts recording with the set settings to the set file path. """
        self._widget.setRecButtonChecked(True)

    @APIExport
    def stopRecording(self):
        """ Stops recording. """
        self._widget.setRecButtonChecked(False)

    @APIExport
    def setRecModeSpecFrames(self, numFrames):
        """ Sets the recording mode to record a specific number of frames. """
        self.specFrames()
        self._widget.setNumExpositions(numFrames)

    @APIExport
    def setRecModeSpecTime(self, secondsToRec):
        """ Sets the recording mode to record for a specific amount of time.
        """
        self.specTime()
        self._widget.setTimeToRec(secondsToRec)

    @APIExport
    def setRecModeScanOnce(self):
        """ Sets the recording mode to record a single scan. """
        self.recScanOnce()

    @APIExport
    def setRecModeScanTimelapse(self, secondsToRec, freqSeconds):
        """ Sets the recording mode to record a timelapse of scans. """
        self.recScanLapse()
        self._widget.setTimelapseTime(secondsToRec)
        self._widget.setTimelapseFreq(freqSeconds)

    @APIExport
    def setRecModeUntilStop(self):
        """ Sets the recording mode to record until recording is manually
        stopped. """
        self.untilStop()

    @APIExport
    def setDetectorToRecord(self, detectorName):
        """ Sets which detectors to record. One can also pass -1 as the
        argument to record the current detector, or -2 to record all detectors.
        """
        self._widget.setDetectorToCapture(detectorName)

    @APIExport
    def setRecFilename(self, filename):
        """ Sets the name of the file to record to. This only sets the name of
        the file, not the full path. One can also pass None as the argument to
        use a default time-based filename. """
        if filename is not None:
            self._widget.setCustomFilename(filename)
        else:
            self._widget.setCustomFilenameEnabled(False)

    @APIExport
    def setRecFolder(self, folderPath):
        """ Sets the folder to save recordings into. """
        self._widget.setRecFolder(folderPath)


_attrCategory = 'Rec'
_recModeAttr = 'Mode'
_framesAttr = 'Frames'
_timeAttr = 'Time'
_lapseTimeAttr = 'LapseTime'
_freqAttr = 'LapseFreq'
_slicesAttr = 'DimSlices'
_stepSizeAttr = 'DimStepSize'


# Copyright (C) 2020, 2021 TestaLab
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
