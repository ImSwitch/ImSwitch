import os, time, json, numpy as np
from typing import Optional, Union, List, Dict
from imswitch.imcommon.framework import Signal
from imswitch.imcommon.framework.pycromanager import (
    PycroManagerAcquisitionMode,
    PycroManagerZStack,
    PycroManagerXYScan,
    PycroManagerXYZScan,
    PycroManagerXYPoint,
    PycroManagerXYZPoint
)

from imswitch.imcommon.model import (
    ostools,
    APIExport,
    SaveMode,
    initLogger
)
from ..basecontrollers import ImConWidgetController


class PycroManagerController(ImConWidgetController):
    """ Linked to RecordingWidget. """
    
    sigToggleLive = Signal(bool) # (enabled)
    sigErrorCondition = Signal(str, str, str) # (title, type, msg)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        
        # set default time and space modes;
        # at startup these are the pre-selected
        # modes in the widget
        self.timeRecMode = PycroManagerAcquisitionMode.Frames
        self.spaceRecMode = PycroManagerAcquisitionMode.Absent        
        self.settingAttr = False
        self.lapseTotal = 0

        self._widget.setSnapSaveMode(SaveMode.Disk.value)
        self._widget.setSnapSaveModeVisible(self._setupInfo.hasWidget('Image'))

        self._widget.setRecSaveMode(SaveMode.Disk.value)
        self._widget.setRecSaveModeVisible(
            self._moduleCommChannel.isModuleRegistered('imreconstruct')
        )
        
        # At startup no space mode is selected;
        # only the time mode is selected
        self._widget.setEnableTimeParams(True, False)
        self._widget.setEnableSpaceParams(self.spaceRecMode)

        # Connect signals from CommunicationChannel
        self._commChannel.sigRecordingStarted.connect(self.recordingStarted)
        self._commChannel.sigRecordingEnded.connect(self.recordingEnded)
        self._commChannel.sigUpdatePycroManagerNotification.connect(self.updateProgressBars)
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged)
        self._commChannel.sigSnapImg.connect(self.snap)
        self._commChannel.sigStartRecordingExternal.connect(self.startRecording)
        self._commChannel.sigLiveAcquisitionStarted.connect(self.startLiveAcquisition)
        self._commChannel.sigLiveAcquisitionStopped.connect(self.stopLiveAcquisition)

        # Connect signals to CommunicationChannel
        self.sigToggleLive.connect(self._commChannel.sigLiveViewUpdateRequested)
        self._master.pycroManagerAcquisition.sigLiveImageUpdated.connect(self.updateImage)

        # Connect PycroManagerWidget signals
        self._widget.sigOpenRecFolderClicked.connect(self.openFolder)
        self._widget.sigSpecFileToggled.connect(self._widget.setCustomFilenameEnabled)

        self._widget.sigSpecTimeChanged.connect(self.specTimeMode)
        self._widget.sigSpecSpaceChanged.connect(self.specSpaceMode)

        self._widget.sigSnapRequested.connect(self.snap)
        self._widget.sigRecToggled.connect(self.toggleRecording)
        
        self._widget.sigTableDataToController.connect(self.parseTableData)
        self._widget.sigTableLoaded.connect(self.readPointsJSONData)
        self.xyScan = None
        self.xyzScan = None
        
        # Feedback signal to the widget in case of failure to load JSON file
        self.sigErrorCondition.connect(self._widget.displayErrorMessage)

    def openFolder(self):
        """ Opens current folder in File Explorer. """
        folder = self._widget.getRecFolder()
        if not os.path.exists(folder):
            os.makedirs(folder)
        ostools.openFolderInOS(folder)

    def snapSaveModeChanged(self):
        saveMode = SaveMode(self._widget.getSnapSaveMode())
        self._widget.setsaveFormatEnabled(saveMode != SaveMode.RAM)

    def snap(self):
        self.updateRecAttrs(isSnapping=True)

        attrs = {
            self._master.pycroManagerAcquisition.core.get_camera_device(): self._commChannel.sharedAttrs.getHDF5Attributes()
        }

        folder = self._widget.getRecFolder()
        if not os.path.exists(folder):
            os.makedirs(folder)
        time.sleep(0.01)
        
        savename =  self.getFileName() + '_snap'
        self._master.pycroManagerAcquisition.snap(folder, savename, SaveMode(self._widget.getSnapSaveMode()), attrs)

    def toggleRecording(self, enabled: bool):
        """ Trigger an acquisition from the PycroManager backend. Performs sanity checks on the requested datapoints.
        Sends a warning to the UI if the requested datapoints are not valid.
        """
        if enabled:
            if not self.performSanityCheck():
                self.recordingCycleEnded()
                return

            self.updateRecAttrs(isSnapping=False)

            folder = self._widget.getRecFolder()
            if not os.path.exists(folder):
                os.makedirs(folder)
            time.sleep(0.01)
            savename = self.getFileName() + '_rec'

            self.setupProgressBars()
            recordingArgs = self.packRecordingArguments(folder, savename)

            # before launching the recording, we stop the live view if this is running
            self.sigToggleLive.emit(False)
            self._master.pycroManagerAcquisition.startRecording(recordingArgs)
        else:
            self._master.pycroManagerAcquisition.endRecording()

            # resume live view if previously running
            self.sigToggleLive.emit(True)
    
    def startLiveAcquisition(self):
        if not self.performSanityCheck():
            return
        self.updateRecAttrs(isSnapping=False)
        self.setupProgressBars()
        recordingArgs = self.packRecordingArguments()
        self._master.pycroManagerAcquisition.startLiveView(recordingArgs)

    def stopLiveAcquisition(self):
        self._master.pycroManagerAcquisition.stopLiveView()
        self._widget.updateProgressBars({key : 0 for key in self._widget.progressBarsKeys})
    
    def updateImage(self, image: np.ndarray):
        self._commChannel.sigUpdateImage.emit(
            self._master.detectorsManager.getCurrentDetectorName(), 
            image, 
            True, 
            self._master.detectorsManager.getCurrentDetector().scale, 
            True)

    def setupProgressBars(self) -> None:
        maxDict = {key : 0 for key in self._widget.progressBarsKeys}
        
        self.__logger.info(f"Recording mode: time = {self.timeRecMode.name}, space = {self.spaceRecMode.name}")

        # maximum value is the specified amount - 1, as
        # pycromanager IDs are indexed from 0 to N-1
        if self.timeRecMode & PycroManagerAcquisitionMode.Frames:
            max = self._widget.getNumExpositions()
            self.__logger.info(f"Recording {max} time points at {float(self._master.pycroManagerAcquisition.core.get_exposure())} ms")
            maxDict["time"] = max - 1
        elif self.timeRecMode & PycroManagerAcquisitionMode.Time:
            max = int(self._widget.getTimeToRec() * 1000 / self._master.pycroManagerAcquisition.core.get_exposure())
            self.__logger.info(f"Recording {max} time points at {float(self._master.pycroManagerAcquisition.core.get_exposure())} ms")
            maxDict["time"] = max - 1
        
        if self.spaceRecMode & PycroManagerAcquisitionMode.ZStack:
            start, stop, step = self._widget.getZStackValues()
            max = len(np.linspace(start, stop, int((stop - start) / step)))
            self.__logger.info(f"Recording {max} Z points (start: {start}, stop: {stop}, step: {step})")
            maxDict["z"] = max - 1
        elif self.spaceRecMode & PycroManagerAcquisitionMode.XYList:
            max = len(self.xyScan)
            self.__logger.info(f"Recording {max} X-Y points")
            maxDict["position"] = max - 1
        elif self.spaceRecMode & PycroManagerAcquisitionMode.XYZList:
            max = len(self.xyzScan)
            self.__logger.info(f"Recording {max} X-Y-Z points")
            maxDict["position"] = max - 1
            maxDict["z"] = max - 1

        self._widget.setProgressBarsMaximum(maxDict)
        self._widget.setProgressBarsVisibility({key: value != 0 for key, value in maxDict.items()})
    
    def packRecordingArguments(self, folder: str = "temp", savename: str = "live") -> Dict[str, dict]:
        # packing arguments
        # if folder and savename are None,
        # no file will be saved
        recordingArgs = {
            "Acquisition" : {
                "directory" : folder,
                "name" : savename,
                "image_process_fn": None,
                "event_generation_hook_fn": None,
                "pre_hardware_hook_fn":  None,
                "post_hardware_hook_fn":  None,
                "post_camera_hook_fn": None,
                "notification_callback_fn": None,
                "image_saved_fn":  None,
                "napari_viewer" : None,
                "show_display": False,
                "debug" : False,
            },
            "multi_d_acquisition_events" : {
                "num_time_points": self.__calculateNumTimePoints(),
                "time_interval_s": self.__calculateTimeIntervalS(),
                "z_start": self._widget.getZStackValues()[0] if self.spaceRecMode & PycroManagerAcquisitionMode.ZStack else None,
                "z_end": self._widget.getZStackValues()[1] if self.spaceRecMode & PycroManagerAcquisitionMode.ZStack else None,
                "z_step": self._widget.getZStackValues()[2] if self.spaceRecMode & PycroManagerAcquisitionMode.ZStack else None,
                "channel_group": None, # TODO: add customization option in UI
                "channels": None, # TODO: add customization option in UI
                "channel_exposures_ms": None, # TODO: add customization option in UI
                "xy_positions": np.array(self.xyScan) if self.spaceRecMode & PycroManagerAcquisitionMode.XYList else None,
                "xyz_positions": np.array(self.xyzScan) if self.spaceRecMode & PycroManagerAcquisitionMode.XYZList else None,
                "position_labels": self.__checkLabels(),
                "order": "tpcz" # todo: make this a parameter in the widget
            },
            "tags" : {
                # TODO: attributes should be reworked
                self._master.pycroManagerAcquisition.core.get_camera_device(): self._commChannel.sharedAttrs.getHDF5Attributes()
            }
        }
        return recordingArgs

    def __calculateNumTimePoints(self) -> list:
        if self.timeRecMode & PycroManagerAcquisitionMode.Frames:
            return self._widget.getNumExpositions()
        if self.timeRecMode & PycroManagerAcquisitionMode.Time:
            return self._widget.getTimeToRec() * 1000 // float(self._master.pycroManagerAcquisition.core.get_exposure())
        else:
            return None
    
    def __calculateTimeIntervalS(self) -> int:
        if self.timeRecMode & PycroManagerAcquisitionMode.Time:
            return (self._widget.getTimeToRec() * 1000 / float(self._master.pycroManagerAcquisition.core.get_exposure())) * 1e-3
        else:
            return 0
    
    def __checkLabels(self) -> Union[None, list]:
        if self.spaceRecMode & PycroManagerAcquisitionMode.XYList:
            return self.xyScan.labels()
        elif self.spaceRecMode & PycroManagerAcquisitionMode.XYZList:
            return self.xyzScan.labels()
        else:
            return None
    
    def performSanityCheck(self) -> bool:
        """ Checks the validity of the incoming recording request.
        If a condition occurs such as the recording would fail (no stages available, missing data points),
        a warning is sent to the UI and the recording is not triggered.
        """
        
        errTitle = "Recording aborted"
        retStatus = True

        def getMMCorePositioners() -> list:
            """ Returns a list of positioners part of the MMCore suite in the currently loaded configuration. """
            return [dev for dev in self._master.positionersManager._subManagers.values() if dev.__class__.__name__ == "PyMMCorePositionerManager"]
        
        if self.spaceRecMode != PycroManagerAcquisitionMode.Absent:
            mmcorePositionersList = getMMCorePositioners()
            if len(mmcorePositionersList) == 0:
                msg = "No MMCore positioners were found in the setupInfo. Recording aborted."
                self.__logger.warning(msg)
                self.sigErrorCondition.emit(errTitle, "warning", msg)
                retStatus = False
            else:
                if self.spaceRecMode & PycroManagerAcquisitionMode.XYList:
                    if self.xyScan is None:
                        msg = "No XY points were specified. Recording aborted."
                        self.__logger.warning(msg)
                        self.sigErrorCondition.emit(errTitle, "warning", msg)
                        retStatus = False
                    else:
                        # TODO: what happens if we have multiple XY stages?
                        xyStage = next((dev for dev in mmcorePositionersList if "".join(dev.axes) == "XY"), None)
                        if xyStage is not None:
                            self._master.pycroManagerAcquisition.core.set_xy_stage_device(xyStage.name)
                            self.__logger.info("XY stage selected: ", self._master.pycroManagerAcquisition.core.get_xy_stage_device())
                            retStatus = False
                        else:
                            msg = "No XY stages are currently configured. Recording aborted."
                            self.__logger.warning("msg")
                            self.sigErrorCondition.emit(errTitle, "warning", msg)
                            retStatus = False
                elif self.spaceRecMode & PycroManagerAcquisitionMode.XYZList:
                    if self.xyzScan is None:
                        msg = "No XYZ points were specified. Recording aborted."
                        self.__logger.warning(msg)
                        self.sigErrorCondition.emit(errTitle, "warning", msg)
                        retStatus = False
                    else:
                        xyStage = next((dev for dev in mmcorePositionersList if "".join(dev.axes) == "XY"), None)
                        zStage = next((dev for dev in mmcorePositionersList if "".join(dev.axes) == "Z"), None)
                        if xyStage is not None and zStage is not None:
                            self._master.pycroManagerAcquisition.core.set_xy_stage_device(xyStage.name)
                            self._master.pycroManagerAcquisition.core.set_focus_device(zStage.name)
                            self.__logger.info("XY stage selected: ", self._master.pycroManagerAcquisition.core.get_xy_stage_device())
                            self.__logger.info("Z stage selected: ", self._master.pycroManagerAcquisition.core.get_focus_device())
                        else:
                            ax = ""
                            if xyStage is None and zStage is None:
                                ax = "XY and Z"
                            elif xyStage is None:
                                ax = "XY"
                            else:
                                ax = "Z"
                            msg = f"No {ax} stages are currently configured. Recording aborted."
                            self.__logger.warning(msg)
                            self.sigErrorCondition.emit(errTitle, "warning", msg)
                            
                elif self.spaceRecMode & PycroManagerAcquisitionMode.ZStack:
                    # TODO: it may happen that the widgets do not hold any content;
                    # keep an eye on this.
                    zStage = next((dev for dev in mmcorePositionersList if "".join(dev.axes) == "Z"), None)
                    if zStage is not None:
                        self._master.pycroManagerAcquisition.core.set_focus_device(zStage.name)
                        self.__logger.info("Z stage selected: ", self._master.pycroManagerAcquisition.core.get_focus_device())
                    else:
                        msg = "No Z stages is currently configured. Recording aborted."
                        self.__logger.warning(msg)
                        self.sigErrorCondition.emit(errTitle, "warning", msg)
                        retStatus = False

        return retStatus

    def recordingStarted(self):
        self._widget.setFieldsEnabled(False)

    def recordingCycleEnded(self):
        self._widget.updateProgressBars({key : 0 for key in self._widget.progressBarsKeys})
        self._widget.setFieldsEnabled(True)
        self._widget.recButton.setChecked(False)
        self._widget.setProgressBarsVisibility({key : False for key in self._widget.progressBarsKeys})

    def recordingEnded(self):
        self.recordingCycleEnded()        
    
    def updateProgressBars(self, newProgressDict: Dict[str, int]) -> None:
        self._widget.updateProgressBars(newProgressDict)
    
    def specTimeMode(self, mode: PycroManagerAcquisitionMode):
        self._widget.setEnableTimeParams(
            mode == PycroManagerAcquisitionMode.Frames,
            mode == PycroManagerAcquisitionMode.Time,
        )
        self.timeRecMode = mode
    
    def specSpaceMode(self, mode: PycroManagerAcquisitionMode):
        self._widget.setEnableSpaceParams(mode)
        self.spaceRecMode = mode
    
    def parseTableData(self, coordinates: str, points: list):
        """ Parses the table data from the widget and creates a list of points.
        Required for sanity check of the data points.
        """
        if coordinates == 'XY':
            self.xyScan = PycroManagerXYScan(
                [
                    PycroManagerXYPoint(X=point[0], Y=point[1], Label=point[2]) for point in points
                ]
            )
        else:
            self.xyzScan = PycroManagerXYZScan(
                [
                    PycroManagerXYPoint(X=point[0], Y=point[1], Z=point[2], Label=point[3]) for point in points
                ]
            )
        
        
    def readPointsJSONData(self, coordinates: str, filePath: str):
        """ Reads the JSON file containing the points data and creates a list of points.
        Required for sanity check of the data points.
        """
        with open(filePath, "r") as file:
            try:
                if coordinates == 'XY':
                    self.xyScan = PycroManagerXYScan(
                        [
                            PycroManagerXYPoint(**data) for data in json.load(file)
                        ]
                    )
                else:
                    self.xyzScan = PycroManagerXYZScan(
                        [
                            PycroManagerXYZPoint(**data) for data in json.load(file)
                        ]
                    )
            except Exception as e:
                errorMsg = f"Error reading JSON file {filePath}: {e}"
                self.__logger.error(errorMsg)
                self.sigErrorCondition.emit("Failed to load JSON file", "error", errorMsg)
                self._widget._dataCache[coordinates] = None

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
            self.setSharedAttr(_recModeAttr, f"time:{self.timeRecMode.name};space:{self.spaceRecMode.name}")
            if self.timeRecMode & PycroManagerAcquisitionMode.Frames:
                self.setSharedAttr(_framesAttr, self._widget.getNumExpositions())
            elif self.timeRecMode & PycroManagerAcquisitionMode.Time:
                self.setSharedAttr(_timeAttr, self._widget.getTimeToRec())
            else:
                self.setSharedAttr(_framesAttr, None)
                self.setSharedAttr(_timeAttr, None)
            # TODO: add shared attributes for space modes

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
