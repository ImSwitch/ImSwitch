from imcommon.model import DataItem
from imcontrol.model import (
    DetectorsManager, LasersManager, NidaqManager, PositionersManager, RecordingManager, ScanManager
)


class MasterController:
    """
    This class will handle the communication between software and hardware,
    using the managers for each hardware set.
    """

    def __init__(self, setupInfo, commChannel, moduleCommChannel):
        print('init master controller')
        self.__setupInfo = setupInfo
        self.__commChannel = commChannel
        self.__moduleCommChannel = moduleCommChannel

        # Init managers
        self.detectorsManager = DetectorsManager(self.__setupInfo.detectors, updatePeriod=100)
        self.recordingManager = RecordingManager(self.detectorsManager)
        self.nidaqManager = NidaqManager(self.__setupInfo)
        self.scanManager = ScanManager(self.__setupInfo)  # Make sure compatibility
        self.lasersManager = LasersManager(self.__setupInfo.lasers, nidaqManager=self.nidaqManager)
        self.positionersManager = PositionersManager(self.__setupInfo.positioners,
                                                     nidaqManager=self.nidaqManager)

        # Connect signals
        self.detectorsManager.acquisitionStarted.connect(self.__commChannel.acquisitionStarted)
        self.detectorsManager.acquisitionStopped.connect(self.__commChannel.acquisitionStopped)
        self.detectorsManager.detectorSwitched.connect(self.__commChannel.detectorSwitched)
        self.detectorsManager.imageUpdated.connect(self.__commChannel.updateImage)

        self.recordingManager.recordingEnded.connect(self.__commChannel.endRecording)
        self.recordingManager.recordingFrameNumUpdated.connect(self.__commChannel.updateRecFrameNum)
        self.recordingManager.recordingTimeUpdated.connect(self.__commChannel.updateRecTime)
        self.recordingManager.memoryRecordingAvailable.connect(self.memoryRecordingAvailable)

    def memoryRecordingAvailable(self, name, file, filePath, savedToDisk):
        self.__moduleCommChannel.memoryRecordings[name] = DataItem(
            data=file, filePath=filePath, savedToDisk=savedToDisk
        )

# Copyright (C) 2020, 2021 Staffan Al-Kadhimi, Xavier Casas, Andreas Boden
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
