import os
import subprocess
import sys
import time

from imcommon.framework import Timer
from .basecontrollers import ImConWidgetController
from imcontrol.model.managers.RecordingManager import SaveMode, RecMode
from imcontrol.view import guitools as guitools


class RecorderController(ImConWidgetController):
    """ Linked to RecordingWidget. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.setDetectorList(self._master.detectorsManager.execOnAll(lambda c: c.model))

        self.lapseCurrent = 0
        self.lapseTotal = 0

        imreconstructRegistered = self._moduleCommChannel.isModuleRegistered('imreconstruct')
        self._widget.setSaveMode(SaveMode.Disk.value)
        self._widget.setSaveModeVisible(imreconstructRegistered)

        self.untilStop()

        # Connect CommunicationChannel signals
        self._commChannel.endRecording.connect(self.endRecording)
        self._commChannel.updateRecFrameNum.connect(self._widget.updateRecFrameNum)
        self._commChannel.updateRecTime.connect(self._widget.updateRecTime)
        self._commChannel.endScan.connect(self.scanDone)

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
            if sys.platform == 'darwin':
                subprocess.check_call(['open', self._widget.getRecFolder()])
            elif sys.platform == 'linux':
                subprocess.check_call(['xdg-open', self._widget.getRecFolder()])
            elif sys.platform == 'win32':
                os.startfile(self._widget.getRecFolder())
        except FileNotFoundError or subprocess.CalledProcessError:
            if sys.platform == 'darwin':
                subprocess.check_call(['open', self._widget.dataDir])
            elif sys.platform == 'linux':
                subprocess.check_call(['xdg-open', self._widget.dataDir])
            elif sys.platform == 'win32':
                os.startfile(self._widget.dataDir)

    def snap(self):
        """ Take a snap and save it to a .tiff file. """
        detectorNames = self.getDetectorNamesToCapture()
        folder = self._widget.getRecFolder()
        if not os.path.exists(folder):
            os.mkdir(folder)
        time.sleep(0.01)
        name = os.path.join(folder, self.getFileName()) + '_snap'
        savename = guitools.getUniqueName(name)
        attrs = self._commChannel.getCamAttrs()
        for attrDict in attrs.values():
            attrDict.update(self._commChannel.sharedAttrs.getHDF5Attributes())
        self._master.recordingManager.snap(detectorNames, savename, attrs)

    def toggleREC(self, checked):
        """ Start or end recording. """
        if checked:
            folder = self._widget.getRecFolder()
            if not os.path.exists(folder):
                os.mkdir(folder)
            time.sleep(0.01)
            name = os.path.join(folder, self.getFileName()) + '_rec'
            self.savename = guitools.getUniqueName(name)
            self.saveMode = SaveMode(self._widget.getSaveMode())

            self.detectorsBeingCaptured = self.getDetectorNamesToCapture()
            self.attrs = self._commChannel.getCamAttrs()
            for attrDict in self.attrs.values():
                attrDict.update(self._commChannel.sharedAttrs.getHDF5Attributes())
                attrDict.update(self._commChannel.getScanStageAttrs())
                attrDict.update(self._commChannel.getScanTTLAttrs())
                attrDict.update(self.getRecAttrs())

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
                self._commChannel.prepareScan.emit()
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
                    self._commChannel.moveZstage.emit(self._widget.getDimlapseStepSize())
                    self.timer = Timer(singleShot=True)
                    self.timer.timeout.connect(self.nextLapse)
                    self.timer.start(1000)
                else:
                    self._commChannel.moveZstage.emit(
                        -self.lapseTotal * self._widget.getDimlapseStepSize()
                    )
                    self._master.recordingManager.endRecording()

    def nextLapse(self):
        fileName = self.savename + "_" + str(self.lapseCurrent).zfill(len(str(self.lapseTotal)))
        self._master.recordingManager.startRecording(
            self.detectorsBeingCaptured, self.recMode, fileName, self.saveMode, self.attrs
        )
        time.sleep(0.3)
        self._commChannel.prepareScan.emit()

    def endRecording(self):
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
        detectorListData = self._widget.getDetectorsToCapture()
        if detectorListData == -2:  # All detectors
            # When recording all detectors, the SpecFrames mode isn't supported
            self._widget.setSpecifyFramesAllowed(False)
        else:
            self._widget.setSpecifyFramesAllowed(True)

    def getDetectorNamesToCapture(self):
        """ Returns a list of which detectors the user has selected to be captured. """
        detectorListData = self._widget.getDetectorsToCapture()
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