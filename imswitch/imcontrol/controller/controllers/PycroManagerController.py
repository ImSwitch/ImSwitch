import os
import time
from typing import Optional, Union, List
import numpy as np

from imswitch.imcommon.model import ostools, APIExport
from imswitch.imcontrol.model import RecMode, SaveMode, SaveFormat
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import initLogger


class PycroManagerController(ImConWidgetController):
    """ Linked to RecordingWidget. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        self.settingAttr = False
        self.recording = False
        self.doneScan = False
        self.endedRecording = False
        self.lapseTotal = 0

        self._widget.setSnapSaveMode(SaveMode.Disk.value)
        self._widget.setSnapSaveModeVisible(self._setupInfo.hasWidget('Image'))

        self._widget.setRecSaveMode(SaveMode.Disk.value)
        self._widget.setRecSaveModeVisible(
            self._moduleCommChannel.isModuleRegistered('imreconstruct')
        )

        self.specFrames()

        # Connect CommunicationChannel signals
        self._commChannel.sigRecordingStarted.connect(self.recordingStarted)
        self._commChannel.sigRecordingEnded.connect(self.recordingEnded)
        self._commChannel.sigUpdateRecFrameNum.connect(self.updateRecFrameNum)
        self._commChannel.sigUpdateRecTime.connect(self.updateRecTime)
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged)
        self._commChannel.sigSnapImg.connect(self.snap)
        self._commChannel.sigStartRecordingExternal.connect(self.startRecording)
        self._commChannel.sigRequestScanFreq.connect(self.sendScanFreq)

        # Connect PycroManagerWidget signals
        self._widget.sigOpenRecFolderClicked.connect(self.openFolder)
        self._widget.sigSpecFileToggled.connect(self._widget.setCustomFilenameEnabled)

        self._widget.sigSnapSaveModeChanged.connect(self.snapSaveModeChanged)

        self._widget.sigSpecFramesPicked.connect(self.specFrames)
        self._widget.sigSpecTimePicked.connect(self.specTime)

        self._widget.sigSnapRequested.connect(self.snap)
        self._widget.sigRecToggled.connect(self.toggleREC)

    def openFolder(self):
        """ Opens current folder in File Explorer. """
        folder = self._widget.getRecFolder()
        if not os.path.exists(folder):
            os.makedirs(folder)
        ostools.openFolderInOS(folder)

    def snapSaveModeChanged(self):
        saveMode = SaveMode(self._widget.getSnapSaveMode())
        self._widget.setsaveFormatEnabled(saveMode != SaveMode.RAM)
        if saveMode == SaveMode.RAM:
            self._widget.setsaveFormat(SaveFormat.TIFF.value)

    def snap(self):
        self.updateRecAttrs(isSnapping=True)

        folder = self._widget.getRecFolder()
        if not os.path.exists(folder):
            os.makedirs(folder)
        time.sleep(0.01)
        
        savename = os.path.join(folder, self.getFileName()) + '_snap'
        self._master.pycroManager.snap(savename, SaveMode(self._widget.getSnapSaveMode()))

    def toggleREC(self, checked):
        """ Start or end recording. """
        if checked and not self.recording:
            self.updateRecAttrs(isSnapping=False)

            folder = self._widget.getRecFolder()
            if not os.path.exists(folder):
                os.makedirs(folder)
            time.sleep(0.01)
            self.savename = os.path.join(folder, self.getFileName()) + '_rec'

            self.recordingArgs = {
                # TODO: add arguments for PycroManager acquisition
            }

            if self.recMode == RecMode.SpecFrames:
                self.recordingArgs['recFrames'] = self._widget.getNumExpositions()
                self._master.pycroManagerManager.startRecording(**self.recordingArgs)
            elif self.recMode == RecMode.SpecTime:
                self.recordingArgs['recTime'] = self._widget.getTimeToRec()
                self._master.pycroManagerManager.startRecording(**self.recordingArgs)
            else:
                self._master.pycroManagerManager.startRecording(**self.recordingArgs)

            self.recording = True
            self.endedRecording = False
        else:
            self._master.pycroManagerManager.endRecording()

    def recordingStarted(self):
        self._widget.setFieldsEnabled(False)

    def recordingCycleEnded(self):
        self.recording = False
        self._widget.updateRecFrameNum(0)
        self._widget.updateRecTime(0)
        self._widget.setRecButtonChecked(False)
        self._widget.setFieldsEnabled(True)

    def recordingEnded(self):
        self.endedRecording = True
        self.recordingCycleEnded()

    def updateRecFrameNum(self, recFrameNum):
        if self.recMode == RecMode.SpecFrames:
            self._widget.updateRecFrameNum(recFrameNum)

    def updateRecTime(self, recTime):
        if self.recMode == RecMode.SpecTime:
            self._widget.updateRecTime(recTime)

    def specFrames(self):
        self._widget.checkSpecFrames()
        self._widget.setEnabledParams(specFrames=True)
        self.recMode = RecMode.SpecFrames

    def specTime(self):
        self._widget.checkSpecTime()
        self._widget.setEnabledParams(specTime=True)
        self.recMode = RecMode.SpecTime

    def setRecMode(self, recMode):
        if recMode == RecMode.SpecFrames:
            self.specFrames()
        elif recMode == RecMode.SpecTime:
            self.specTime()
        else:
            raise ValueError(f'Invalid RecMode {recMode} specified')

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

    def setSharedAttr(self, attr, value):
        self.settingAttr = True
        try:
            self._commChannel.sharedAttrs[(_attrCategory, attr)] = value
        finally:
            self.settingAttr = False

    def updateRecAttrs(self, *, isSnapping):
        self.setSharedAttr(_framesAttr, 'null')
        self.setSharedAttr(_timeAttr, 'null')

        if isSnapping:
            self.setSharedAttr(_recModeAttr, 'Snap')
        else:
            self.setSharedAttr(_recModeAttr, self.recMode.name)
            if self.recMode == RecMode.SpecFrames:
                self.setSharedAttr(_framesAttr, self._widget.getNumExpositions())
            elif self.recMode == RecMode.SpecTime:
                self.setSharedAttr(_timeAttr, self._widget.getTimeToRec())

    @APIExport(runOnUIThread=True)
    def snapImage(self, output: bool = False) -> Optional[np.ndarray]:
        """ Take a snap and save it to a .tiff file at the set file path. """
        if output:
            return self.snapNumpy()
        else:
            self.snap()

    @APIExport(runOnUIThread=True)
    def startRecording(self) -> None:
        """ Starts recording with the set settings to the set file path. """
        self._widget.setRecButtonChecked(True)

    @APIExport(runOnUIThread=True)
    def stopRecording(self) -> None:
        """ Stops recording. """
        self._widget.setRecButtonChecked(False)

    @APIExport(runOnUIThread=True)
    def setRecModeSpecFrames(self, numFrames: int) -> None:
        """ Sets the recording mode to record a specific number of frames. """
        self.specFrames()
        self._widget.setNumExpositions(numFrames)

    @APIExport(runOnUIThread=True)
    def setRecModeSpecTime(self, secondsToRec: Union[int, float]) -> None:
        """ Sets the recording mode to record for a specific amount of time.
        """
        self.specTime()
        self._widget.setTimeToRec(secondsToRec)

    @APIExport(runOnUIThread=True)
    def setRecModeScanOnce(self) -> None:
        """ Sets the recording mode to record a single scan. """
        self.recScanOnce()

    @APIExport(runOnUIThread=True)
    def setRecModeScanTimelapse(self, lapsesToRec: int, freqSeconds: float,
                                timelapseSingleFile: bool = False) -> None:
        """ Sets the recording mode to record a timelapse of scans. """
        self.recScanLapse()
        self._widget.setTimelapseTime(lapsesToRec)
        self._widget.setTimelapseFreq(freqSeconds)
        self._widget.setTimelapseSingleFile(timelapseSingleFile)

    @APIExport(runOnUIThread=True)
    def setDetectorToRecord(self, detectorName: Union[List[str], str, int],
                            multiDetectorSingleFile: bool = False) -> None:
        """ Sets which detectors to record. One can also pass -1 as the
        argument to record the current detector, or -2 to record all detectors.
        """
        if isinstance(detectorName, int):
            self._widget.setDetectorMode(detectorName)
        else:
            if isinstance(detectorName, str):
                detectorName = [detectorName]
            self._widget.setDetectorMode(-3)
            self._widget.setSelectedSpecificDetectors(detectorName)
            self._widget.setMultiDetectorSingleFile(multiDetectorSingleFile)

    @APIExport(runOnUIThread=True)
    def setRecFilename(self, filename: Optional[str]) -> None:
        """ Sets the name of the file to record to. This only sets the name of
        the file, not the full path. One can also pass None as the argument to
        use a default time-based filename. """
        if filename is not None:
            self._widget.setCustomFilename(filename)
        else:
            self._widget.setCustomFilenameEnabled(False)

    @APIExport(runOnUIThread=True)
    def setRecFolder(self, folderPath: str) -> None:
        """ Sets the folder to save recordings into. """
        self._widget.setRecFolder(folderPath)


_attrCategory = 'Rec'
_recModeAttr = 'Mode'
_framesAttr = 'Frames'
_timeAttr = 'Time'


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
