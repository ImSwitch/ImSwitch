import numpy as np

from imswitch.imcommon.model import APIExport
from imswitch.imcommon.model import initLogger
from .DetectorManager import DetectorManager, DetectorAction

class ESP32SerialCamManager(DetectorManager):
    """ DetectorManager that deals with TheImagingSource cameras and the
    parameters for frame extraction from them.

    Manager properties:

    - ``cameraListIndex`` -- the camera's index in the Allied Vision camera list (list
      indexing starts at 0); set this string to an invalid value, e.g. the
      string "mock" to load a mocker
    - ``picamera`` -- dictionary of Allied Vision camera properties
    """

    def __init__(self, detectorInfo, name, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        
        self._rs232manager = _lowLevelManagers['rs232sManager'][
            detectorInfo.managerProperties['esp32cam']["rs232device"]
        ]
        model = "ESP32SerialCamera"
        self._running = False
        self._adjustingParameters = False
        fullShape = (640,480) # TODO: get from camera

        # Prepare actions
        actions = {}

        # Prepare parameters
        parameters = {
            }            

        # init super-class
        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1],
            model=model, parameters=parameters, actions=actions, croppable=True)

        # assign camera object
        self._camera = self._rs232manager._esp32.camera


    def getLatestFrame(self, is_save=False):
        return self._camera.get_frame() 

    def setParameter(self, name, value):
        """Sets a parameter value and returns the value.
        If the parameter doesn't exist, i.e. the parameters field doesn't
        contain a key with the specified parameter name, an error will be
        raised."""

        super().setParameter(name, value)

        if name not in self._DetectorManager__parameters:
            raise AttributeError(f'Non-existent parameter "{name}" specified')

        value = self._camera.setPropertyValue(name, value)
        return value

    def getParameter(self, name):
        """Gets a parameter value and returns the value.
        If the parameter doesn't exist, i.e. the parameters field doesn't
        contain a key with the specified parameter name, an error will be
        raised."""

        if name not in self._parameters:
            raise AttributeError(f'Non-existent parameter "{name}" specified')

        value = self._camera.getPropertyValue(name)
        return value
    
    @APIExport(runOnUIThread=True)
    def setCameraLED(self, value):
        self._camera.set_led(value)

    def setBinning(self, binning):
        super().setBinning(binning) 
        
    def getChunk(self):
        pass

    def flushBuffers(self):
        pass

    def startAcquisition(self):
        pass

    def stopAcquisition(self):
        pass

    def stopAcquisitionForROIChange(self):
        pass

    def finalize(self) -> None:
        super().finalize()
        self.__logger.debug('Safely disconnecting the camera...')
        self._camera.close()

    @property
    def pixelSizeUm(self):
        return [1, 1, 1]

    def crop(self, hpos, vpos, hsize, vsize):
        pass

    def _performSafeCameraAction(self, function):
        pass

    def openPropertiesDialog(self):
        self._camera.openPropertiesGUI()

    def closeEvent(self):
        pass

# Copyright (C) ImSwitch developers 2021
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
