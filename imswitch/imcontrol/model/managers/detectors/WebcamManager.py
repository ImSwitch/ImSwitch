import cv2
from platform import system
from imswitch.imcommon.model import initLogger
from .DetectorManager import (
    DetectorManager,
    DetectorNumberParameter, 
    DetectorListParameter
)

class WebcamManager(DetectorManager):
    """ DetectorManager that deals with TheImagingSource cameras and the
    parameters for frame extraction from them.
    Manager properties:
    - ``cameraListIndex`` -- camera index
    """

    # dictionary with exposure times and their corresponding codes
    # this is used only when the application runs on Windows
    # https://www.kurokesu.com/main/2020/05/22/uvc-camera-exposure-timing-in-opencv/
    msExposure = {
        "1 s":  0,
        "500 ms": -1,
        "250 ms": -2,
        "125 ms": -3,
        "62.5 ms": -4,
        "31.3 ms": -5,
        "15.6 ms": -6, # default
        "7.8 ms": -7,
        "3.9 ms": -8,
        "2 ms": -9,
        "976.6 us": -10,
        "488.3 us": -11,
        "244.1 us": -12,
        "122.1 us": -13
    }

    def __init__(self, detectorInfo, name, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)
        self.detectorInfo = detectorInfo
        cameraId = detectorInfo.managerProperties['cameraListIndex']
        
        # initialize the camera
        self._camera = cv2.VideoCapture(cameraId)
        fullShape = (self._camera.get(cv2.CAP_PROP_FRAME_WIDTH),
                        self._camera.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self._running = False
        self._adjustingParameters = False

        parameters = {}

        if system() == 'Windows':
            # Exposure time
            parameters['Exposure'] = DetectorListParameter(
                group='Misc', 
                value='15.6 ms', 
                editable=True,
                options=list(self.msExposure.keys())
            )
            self._camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, self.msExposure['15.6 ms'])
        else:
            parameters['Exposure'] = DetectorNumberParameter(
                group='Misc', 
                value=15.6*1e-3, 
                valueUnits='s',
                editable=True
            )
            # warning: this depends on the used camera
            # some may not expose this property
            self._camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 15.6*1e-3)
        parameters['Camera pixel size'] = DetectorNumberParameter(
            group='Misc',
            value=10,
            valueUnits='um',
            editable=True
        )

        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1],
                         model="OpenCV", parameters=parameters, croppable=True)

    @property
    def pixelSizeUm(self):
        try:
            umxpx =  self.parameters['Camera pixel size'].value
        except:
            umxpx = 1   
        return [1, umxpx, umxpx]
        
    def getLatestFrame(self, is_save=False):
        frame = self._camera.read()[1][self._frameStart[1]:, self._frameStart[0]:]
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    def setParameter(self, name, value):
        if name == 'Exposure':
            if system() == 'Windows':
                self._camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, self.msExposure[value])
            else:
                self._camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, float(value))
        super().setParameter(name, value)
        
    def getChunk(self):
        try:
            return self.getLatestFrame()
        except:
            return None

    def flushBuffers(self):
        pass

    def startAcquisition(self, liveView=False):
        pass

    def stopAcquisition(self):
        pass

    def finalize(self) -> None:
        self._camera.release()

    def setPixelSizeUm(self, pixelSizeUm):
        self.parameters['Camera pixel size'].value = pixelSizeUm

    def crop(self, hpos, vpos, hsize, vsize):
        try:
            self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, hsize)
            self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, vsize)
            self._shape = (hsize, vsize)
            self._frameStart = (hpos, vpos)
        except:
            raise ValueError(f"Camera does not support {hsize}x{vsize} resolution")

# Copyright (C) ImSwitch developers 2023
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
