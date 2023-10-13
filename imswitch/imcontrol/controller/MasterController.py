from imswitch.imcommon.model import VFileItem, initLogger
import traceback
from imswitch.imcontrol.model import (
    DetectorsManager, LasersManager, MultiManager, NidaqManager, PositionersManager, RecordingManager, RS232sManager, 
    ScanManagerPointScan, ScanManagerBase, ScanManagerMoNaLISA, SLMManager, StandManager, RotatorsManager, PyMMCoreManager, PycroManagerAcquisitionManager
)


class MasterController:
    """
    This class will handle the communication between software and hardware,
    using the managers for each hardware set.
    """

    def __init__(self, setupInfo, commChannel, moduleCommChannel):
        self.__logger = initLogger(self)
        self.__setupInfo = setupInfo
        self.__commChannel = commChannel
        self.__moduleCommChannel = moduleCommChannel

        # Init managers
        self.nidaqManager = NidaqManager(self.__setupInfo)
        #self.pulseStreamerManager = PulseStreamerManager(self.__setupInfo)
        self.rs232sManager = RS232sManager(self.__setupInfo.rs232devices)

        # Creating a pymmcoreManager is pointless if there are no devices defined
        # in the setupInfo. We check beforehand to reduce the startup time.
        mmcoreDeviceAvailable = any(device.managerName == "PyMMCoreCameraManager" 
                                    for device in list(self.__setupInfo.detectors.values())) or \
                                any(device.managerName == "PyMMCorePositionerManager" 
                                    for device in list(self.__setupInfo.positioners.values()))
        
        if mmcoreDeviceAvailable:
            self.pymmcoreManager = PyMMCoreManager(self.__setupInfo)
        else:
            self.pymmcoreManager = None

        lowLevelManagers = {
            'nidaqManager': self.nidaqManager,
            # TODO: this needs to be added as a signal generator somehow
            #'pulseStreamerManager' : self.pulseStreamerManager,
            'rs232sManager': self.rs232sManager,
            'pymmcManager': self.pymmcoreManager
        }

        self.detectorsManager = DetectorsManager(self.__setupInfo.detectors, updatePeriod=100,
                                                 **lowLevelManagers)
        self.lasersManager = LasersManager(self.__setupInfo.lasers,
                                           **lowLevelManagers)
        self.positionersManager = PositionersManager(self.__setupInfo.positioners,
                                                     **lowLevelManagers)
        self.rotatorsManager = RotatorsManager(self.__setupInfo.rotators,
                                               **lowLevelManagers)
        self.slmManager = SLMManager(self.__setupInfo.slm)

        if self.__setupInfo.microscopeStand:
            self.standManager = StandManager(self.__setupInfo.microscopeStand,
                                             **lowLevelManagers)

        # Generate scanManager type according to setupInfo
        if self.__setupInfo.scan:
            if self.__setupInfo.scan.scanWidgetType == "PointScan":
                self.scanManager = ScanManagerPointScan(self.__setupInfo)
            elif self.__setupInfo.scan.scanWidgetType == "Base":
                self.scanManager = ScanManagerBase(self.__setupInfo)
            elif self.__setupInfo.scan.scanWidgetType == "MoNaLISA":
                self.scanManager = ScanManagerMoNaLISA(self.__setupInfo)
            else:
                self.__logger.error(
                    'ScanWidgetType in SetupInfo["scan"] not recognized, choose one of the following:'
                    ' ["Base", "PointScan", "MoNaLISA"].'
                )
                return

        # Connect signals
        cc = self.__commChannel

        self.detectorsManager.sigAcquisitionStarted.connect(cc.sigAcquisitionStarted)
        self.detectorsManager.sigAcquisitionStopped.connect(cc.sigAcquisitionStopped)
        self.detectorsManager.sigDetectorSwitched.connect(cc.sigDetectorSwitched)
        self.detectorsManager.sigImageUpdated.connect(cc.sigUpdateImage)
        self.detectorsManager.sigNewFrame.connect(cc.sigNewFrame)

        self.recordingManager = None
        self.pycroManagerAcquisition = None

        # RecordingManager and PycroManager are mutually exclusive
        if "Recording" in self.__setupInfo.availableWidgets and "PycroManager" not in self.__setupInfo.availableWidgets:
            self.recordingManager = RecordingManager(self.detectorsManager)
            self.recordingManager.sigRecordingStarted.connect(cc.sigRecordingStarted)
            self.recordingManager.sigRecordingEnded.connect(cc.sigRecordingEnded)
            self.recordingManager.sigRecordingFrameNumUpdated.connect(cc.sigUpdateRecFrameNum)
            self.recordingManager.sigRecordingTimeUpdated.connect(cc.sigUpdateRecTime)
            self.recordingManager.sigMemorySnapAvailable.connect(cc.sigMemorySnapAvailable)
            self.recordingManager.sigMemoryRecordingAvailable.connect(self.memoryRecordingAvailable)
        elif "Recording" not in self.__setupInfo.availableWidgets and "PycroManager" in self.__setupInfo.availableWidgets:
            if mmcoreDeviceAvailable:
                self.pycroManagerAcquisition = PycroManagerAcquisitionManager(self.detectorsManager)
                self.pycroManagerAcquisition.sigRecordingStarted.connect(cc.sigRecordingStarted)
                self.pycroManagerAcquisition.sigRecordingEnded.connect(cc.sigRecordingEnded)
                self.pycroManagerAcquisition.sigPycroManagerNotificationUpdated.connect(cc.sigUpdatePycroManagerNotification)
                self.pycroManagerAcquisition.sigMemorySnapAvailable.connect(cc.sigMemorySnapAvailable)
                self.pycroManagerAcquisition.sigMemoryRecordingAvailable.connect(self.memoryRecordingAvailable)
            else:
                self.__logger.warning("No PyMMCore devices were found in the setupInfo. PycroManager will not be used.")
        else:
            self.__logger.warning("RecordingManager and PycroManager are mutually exclusive, only one can be used at a time.")
            self.__logger.warning("No recording backend will be used.")

        self.slmManager.sigSLMMaskUpdated.connect(cc.sigSLMMaskUpdated)

    def memoryRecordingAvailable(self, name, file, filePath, savedToDisk):
        self.__moduleCommChannel.memoryRecordings[name] = VFileItem(
            data=file, filePath=filePath, savedToDisk=savedToDisk
        )

    def closeEvent(self):
        # recordingManager and pycroManagerAcquisition are mutually exclusive objects;
        # only one can exists at a time in an ImSwitch instance
        try:
            if self.recordingManager is not None:
                self.recordingManager.endRecording(emitSignal=False, wait=True)
            else:
                self.pycroManagerAcquisition.endRecording()
        except Exception:
            self.__logger.error(f"Error while closing RecordingManager or PycroManagerAcquisitionManager: {traceback.format_exc()}")

        for attrName in dir(self):
            attr = getattr(self, attrName)
            if isinstance(attr, MultiManager):
                attr.finalize()


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
