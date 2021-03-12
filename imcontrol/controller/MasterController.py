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
        self.detectorsManager.sigAcquisitionStarted.connect(self.__commChannel.sigAcquisitionStarted)
        self.detectorsManager.sigAcquisitionStopped.connect(self.__commChannel.sigAcquisitionStopped)
        self.detectorsManager.sigDetectorSwitched.connect(self.__commChannel.sigDetectorSwitched)
        self.detectorsManager.sigImageUpdated.connect(self.__commChannel.sigUpdateImage)

        self.recordingManager.sigRecordingEnded.connect(self.__commChannel.sigRecordingEnded)
        self.recordingManager.sigRecordingFrameNumUpdated.connect(self.__commChannel.sigUpdateRecFrameNum)
        self.recordingManager.sigRecordingTimeUpdated.connect(self.__commChannel.sigUpdateRecTime)
        self.recordingManager.sigMemoryRecordingAvailable.connect(self.memoryRecordingAvailable)

    def memoryRecordingAvailable(self, name, file, filePath, savedToDisk):
        self.__moduleCommChannel.memoryRecordings[name] = DataItem(
            data=file, filePath=filePath, savedToDisk=savedToDisk
        )

    def closeEvent(self):
        for multiManager in (self.detectorsManager, self.lasersManager, self.positionersManager):
            multiManager.finalize()


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
