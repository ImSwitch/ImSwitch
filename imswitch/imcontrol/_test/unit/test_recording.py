import pytest
from imswitch.imcontrol.model import DetectorsManager, RecordingManager, RecMode, SaveMode
from . import detectorInfosBasic, detectorInfosMulti, detectorInfosNonSquare


def record(qtbot, detectorInfos, *args, **kwargs):
    detectorsManager = DetectorsManager(detectorInfos, updatePeriod=100)
    recordingManager = RecordingManager(detectorsManager)

    filePerDetector, savedToDiskPerDetector = {}, {}

    def memoryRecordingAvailable(name, file, _, savedToDisk):
        nonlocal filePerDetector, savedToDiskPerDetector
        filePerDetector[name], savedToDiskPerDetector[name] = file, savedToDisk
        return True

    recordingManager.startRecording(*args, **kwargs)
    with qtbot.waitSignals(
        [recordingManager.sigMemoryRecordingAvailable for _ in detectorInfos],
        check_params_cbs=[memoryRecordingAvailable for _ in detectorInfos],
        timeout=30000
    ):
        pass

    return filePerDetector, savedToDiskPerDetector


@pytest.mark.parametrize('detectorInfos,numFrames',
                         [(detectorInfosBasic, 10), (detectorInfosNonSquare, 53)])
def test_recording_spec_frames(qtbot, detectorInfos, numFrames):
    filePerDetector, savedToDiskPerDetector = record(
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
        pixelSizeUm={detectorName: [1, 0.1, 0.1] for detectorName in detectorInfos.keys()},
        recFrames=numFrames
    )

    assert len(filePerDetector) == len(detectorInfos)
    assert len(savedToDiskPerDetector) == len(detectorInfos)

    for file in filePerDetector.values():
        dataset = file.get('data')
        assert dataset.shape[0] == numFrames
        file.close()  # Otherwise we can get segfaults
    for savedToDisk in savedToDiskPerDetector.values():
        assert savedToDisk is False


@pytest.mark.parametrize('detectorInfos',
                         [detectorInfosBasic, detectorInfosMulti, detectorInfosNonSquare])
def test_recording_spec_time(qtbot, detectorInfos):
    filePerDetector, savedToDiskPerDetector = record(
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
        pixelSizeUm={detectorName: [1, 0.1, 0.1] for detectorName in detectorInfos.keys()},
        recTime=5
    )

    assert len(filePerDetector) == len(detectorInfos)
    assert len(savedToDiskPerDetector) == len(detectorInfos)

    for file in filePerDetector.values():
        dataset = file.get('data')
        assert dataset.shape[0] > 0
        file.close()  # Otherwise we can get segfaults
    for savedToDisk in savedToDiskPerDetector.values():
        assert savedToDisk is False


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
