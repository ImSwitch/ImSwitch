import pytest
from imswitch.imcontrol.model import DetectorsManager, RecordingManager, RecMode, SaveMode
from . import detectorInfosBasic, detectorInfosMulti, detectorInfosNonSquare


def record(qtbot, detectorInfos, *args, **kwargs):  # TODO: Should check all and not just one recording available
    detectorsManager = DetectorsManager(detectorInfos, 1000)
    recordingManager = RecordingManager(detectorsManager)

    memRecName, memRecFile, memRecSavedToDisk = None, None, None

    def memoryRecordingAvailable(name, file, _, savedToDisk):
        nonlocal memRecName, memRecFile, memRecSavedToDisk
        memRecName, memRecFile, memRecSavedToDisk = name, file, savedToDisk

    recordingManager.sigMemoryRecordingAvailable.connect(memoryRecordingAvailable)

    with qtbot.waitSignal(recordingManager.sigMemoryRecordingAvailable, timeout=30000):
        recordingManager.startRecording(*args, **kwargs)

    recordingManager.sigMemoryRecordingAvailable.disconnect(memoryRecordingAvailable)

    return memRecName, memRecFile, memRecSavedToDisk


@pytest.mark.parametrize('detectorInfos,numFrames',
                         [(detectorInfosBasic, 10), (detectorInfosNonSquare, 53)])
def test_recording_spec_frames(qtbot, detectorInfos, numFrames):
    memRecName, memRecFile, memRecSavedToDisk = record(
        qtbot,
        detectorInfos,
        detectorNames=list(detectorInfos.keys()),
        recMode=RecMode.SpecFrames,
        savename='test',
        saveMode=SaveMode.RAM,
        attrs={detectorName: {
            'testAttr1': 2,
            'testAttr2': 'value'
        } for detectorName in detectorInfos.keys()},
        recFrames=numFrames
    )
    dataset = memRecFile.get('data')

    assert memRecSavedToDisk is False
    assert dataset.shape[0] == numFrames


@pytest.mark.parametrize('detectorInfos',
                         [detectorInfosBasic, detectorInfosMulti, detectorInfosNonSquare])
def test_recording_spec_time(qtbot, detectorInfos):
    memRecName, memRecFile, memRecSavedToDisk = record(
        qtbot,
        detectorInfos,
        detectorNames=list(detectorInfos.keys()),
        recMode=RecMode.SpecTime,
        savename='test',
        saveMode=SaveMode.RAM,
        attrs={detectorName: {
            'testAttr1': 2,
            'testAttr2': 'value'
        } for detectorName in detectorInfos.keys()},
        recTime=5
    )
    dataset = memRecFile.get('data')

    assert memRecSavedToDisk is False
    assert dataset.shape[0] > 0


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
