import numpy as np
import pytest

from imswitch.imcontrol.model import DetectorsManager
from . import detectorInfosBasic, detectorInfosMulti, detectorInfosNonSquare


def getImage(qtbot, detectorsManager):
    receivedImage = None
    numImagesReceived = 0

    def imageUpdated(_, img, __, isCurrentDetector):
        nonlocal receivedImage, numImagesReceived
        if isCurrentDetector:
            receivedImage = img
            numImagesReceived += 1

    detectorsManager.sigImageUpdated.connect(imageUpdated)

    handle = detectorsManager.startAcquisition(liveView=True)
    while numImagesReceived < 3:  # Make sure we get at least 3 images
        with qtbot.waitSignal(detectorsManager.sigImageUpdated, timeout=30000):
            pass

    detectorsManager.sigImageUpdated.disconnect(imageUpdated)
    detectorsManager.stopAcquisition(handle, liveView=True)

    return receivedImage


@pytest.mark.parametrize('detectorInfos', [detectorInfosBasic, detectorInfosNonSquare])
def test_acquisition_liveview_single(qtbot, detectorInfos):
    detectorsManager = DetectorsManager(detectorInfos, updatePeriod=100)
    receivedImage = getImage(qtbot, detectorsManager)

    assert receivedImage is not None
    assert receivedImage.shape == (
        detectorInfos['CAM'].managerProperties['hamamatsu']['image_height'],
        detectorInfos['CAM'].managerProperties['hamamatsu']['image_width']
    )
    assert not np.all(receivedImage == receivedImage[0, 0])  # Assert that not all pixels are same


@pytest.mark.parametrize('currentDetector', ['Camera 1', 'Camera 2'])
def test_acquisition_liveview_multi(qtbot, currentDetector):
    detectorsManager = DetectorsManager(detectorInfosMulti, updatePeriod=100)
    detectorsManager.setCurrentDetector(currentDetector)
    receivedImage = getImage(qtbot, detectorsManager)

    assert receivedImage is not None
    assert receivedImage.shape == (
        detectorInfosMulti[currentDetector].managerProperties['hamamatsu']['image_height'],
        detectorInfosMulti[currentDetector].managerProperties['hamamatsu']['image_width']
    )
    assert not np.all(receivedImage == receivedImage[0, 0])  # Assert that not all pixels are same


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
