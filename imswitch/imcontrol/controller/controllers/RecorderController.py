import os
import time

from imswitch.imcommon.framework import Timer
from imswitch.imcommon.model import osutils, APIExport
from imswitch.imcontrol.model import SaveMode, RecMode
from imswitch.imcontrol.view import guitools as guitools
from .basecontrollers import ImConWidgetController


class RecorderController(ImConWidgetController):
    """ Linked to RecordingWidget. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.setDetectorList(self._master.detectorsManager.execOnAll(lambda c: c.model))

        self.lapseCurrent = 0
        self.lapseTotal = 0
        self.recording = False

        imreconstructRegistered = self._moduleCommChannel.isModuleRegistered('imreconstruct')
        self._widget.setSaveMode(SaveMode.Disk.value)
        self._widget.setSaveModeVisible(imreconstructRegistered)

        self.untilStop()

        # Connect CommunicationChannel signals
        self._commChannel.sigRecordingEnded.connect(self.recordingEnded)
        self._commChannel.sigUpdateRecFrameNum.connect(self._widget.updateRecFrameNum)
        self._commChannel.sigUpdateRecTime.connect(self._widget.updateRecTime)
        self._commChannel.sigScanEnded.connect(self.scanDone)

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
        self._widget.sigDimLapsePicked.connect(self.dimLapse)
        self._widget.sigUntilStopPicked.connect(self.untilStop)

    def openFolder(self):
        """ Opens current folder in File Explorer. """
        try:
            osutils.openFolderInOS(self._widget.getRecFolder())
        except osutils.OSUtilsError:
            osutils.openFolderInOS(self._widget.dataDir)

    def snap(self):
        """ Take a snap and save it to a .tiff file. """
        detectorNames = self.getDetectorNamesToCapture()
        folder = self._widget.getRecFolder()
        if not os.path.exists(folder):
            os.mkdir(folder)
        time.sleep(0.01)
        name = os.path.join(folder, self.getFileName()) + '_snap'
        savename = guitools.getUniqueName(name)
        attrs, pixelSizeUm = self._commChannel.getCamAttrs()
        for attrDict in attrs.values():
            attrDict.update(self._commChannel.sharedAttrs.getHDF5Attributes())
        self._master.recordingManager.snap(detectorNames, savename, attrs, pixelSizeUm)

    def toggleREC(self, checked):
        """ Start or end recording. """
        if checked and not self.recording:
            folder = self._widget.getRecFolder()
            if not os.path.exists(folder):
                os.mkdir(folder)
            time.sleep(0.01)
            name = os.path.join(folder, self.getFileName()) + '_rec'
            self.savename = guitools.getUniqueName(name)
            self.saveMode = SaveMode(self._widget.getSaveMode())

            self.detectorsBeingCaptured = self.getDetectorNamesToCapture()
            self.attrs, self.pixelSizeUm = self._commChannel.getCamAttrs()
            for attrDict in self.attrs.values():
                attrDict.update(self._commChannel.sharedAttrs.getHDF5Attributes())
                attrDict.update(self._commChannel.getScanStageAttrs())
                attrDict.update(self._commChannel.getScanTTLAttrs())
                attrDict.update(self.getRecAttrs())

            recordingArgs = (self.detectorsBeingCaptured, self.recMode, self.savename,
                             self.saveMode, self.attrs, self.pixelSizeUm)

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
            elif self.recMode == RecMode.DimLapse:
                self.lapseTotal = self._widget.getDimlapseSlices()
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
            elif self.recMode == RecMode.DimLapse:
                self.lapseCurrent += 1
                if self.lapseCurrent < self.lapseTotal:
                    self._widget.updateRecSliceNum(self.lapseCurrent)
                    self._master.recordingManager.endRecording(emitSignal=False)
                    time.sleep(0.3)
                    self._commChannel.sigMoveZStage.emit(self._widget.getDimlapseStepSize())
                    self.timer = Timer(singleShot=True)
                    self.timer.timeout.connect(self.nextLapse)
                    self.timer.start(1000)
                else:
                    self._commChannel.sigMoveZStage.emit(
                        (self.lapseTotal - 1) * -self._widget.getDimlapseStepSize()
                    )
                    self._master.recordingManager.endRecording()

    def nextLapse(self):
        fileName = self.savename + "_" + str(self.lapseCurrent).zfill(len(str(self.lapseTotal)))
        self._master.recordingManager.startRecording(
            self.detectorsBeingCaptured, self.recMode, fileName, self.saveMode, self.attrs,
            self.pixelSizeUm
        )
        time.sleep(0.3)
        self._commChannel.sigPrepareScan.emit()

    def recordingEnded(self):
        self.recording = False
        self.lapseCurrent = 0
        self._widget.updateRecFrameNum(0)
        self._widget.updateRecTime(0)
        self._widget.updateRecLapseNum(0)
        self._widget.updateRecSliceNum(0)
        self._widget.setRecButtonChecked(False)

    def specFrames(self):
        self._widget.setEnabledParams(numExpositions=True)
        self.recMode = RecMode.SpecFrames

    def specTime(self):
        self._widget.setEnabledParams(timeToRec=True)
        self.recMode = RecMode.SpecTime

    def recScanOnce(self):
        self._widget.setEnabledParams()
        self.recMode = RecMode.ScanOnce

    def recScanLapse(self):
        self._widget.setEnabledParams(timelapseTime=True, timelapseFreq=True)
        self.recMode = RecMode.ScanLapse

    def dimLapse(self):
        self._widget.setEnabledParams(dimlapseSlices=True, dimlapseStepSize=True)
        self.recMode = RecMode.DimLapse

    def untilStop(self):
        self._widget.setEnabledParams()
        self.recMode = RecMode.UntilStop

    def detectorChanged(self):
        detectorListData = self._widget.getDetectorToCapture()
        if detectorListData == -2:  # All detectors
            # When recording all detectors, the SpecFrames mode isn't supported
            self._widget.setSpecifyFramesAllowed(False)
        else:
            self._widget.setSpecifyFramesAllowed(True)

    def getDetectorNamesToCapture(self):
        """ Returns a list of which detectors the user has selected to be captured. """
        detectorListData = self._widget.getDetectorToCapture()
        if detectorListData == -1:  # Current detector at start
            return [self._master.detectorsManager.getCurrentDetectorName()]
        elif detectorListData == -2:  # All detectors
            return list(self._setupInfo.detectors.keys())
        else:  # A specific detector
            return [detectorListData]

    def getFileName(self):
        """ Gets the filename of the data to save. """
        filename = self._widget.getCustomFilename()
        if filename is None:
            filename = time.strftime('%Hh%Mm%Ss')
        return filename

    def getRecAttrs(self):
        attrs = {'Rec:Mode': self.recMode.name}
        if self.recMode == RecMode.SpecTime:
            attrs.update({'Rec:Time': self._widget.getTimeToRec()})
        elif self.recMode == RecMode.ScanLapse:
            attrs.update({'Rec:Time': self._widget.getTimelapseTime(),
                          'Rec:Freq': self._widget.getTimelapseFreq()})
        elif self.recMode == RecMode.SpecTime:
            attrs.update({'Rec:Slices': self._widget.getDimlapseSlices(),
                          'Rec:StepSize': self._widget.getDimlapseStepSize()})
        return attrs

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
    def setRecModeScanDimlapse(self, numSlices, stepSizeUm):
        """ Sets the recording mode to record a 3D-lapse of scans. """
        self.dimLapse()
        self._widget.setDimlapseSlices(numSlices)
        self._widget.setDimlapseStepSize(stepSizeUm)

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
