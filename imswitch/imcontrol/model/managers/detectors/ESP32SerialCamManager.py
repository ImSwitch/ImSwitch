import numpy as np

from imswitch.imcommon.model import APIExport
from imswitch.imcommon.model import initLogger
from .DetectorManager import DetectorManager, DetectorAction, DetectorNumberParameter

class ESP32SerialCamManager(DetectorManager):
    """ DetectorManager that deals with the ESP32 Serial Cam 
    """

    def __init__(self, detectorInfo, name, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)


        model = "ESP32SerialCamera"
        self._running = False
        self._adjustingParameters = False
        fullShape = (320,240)

        # Prepare actions
        actions = {}

        # Prepare parameters
        parameters = {
            'exposure': DetectorNumberParameter(group='Misc', value=100, valueUnits='ms',
                                                editable=True),
            'gain': DetectorNumberParameter(group='Misc', value=1, valueUnits='arb.u.',
                                            editable=True)
            }          
        # initialize camera

        self._camera = self._getESP32CamObj()

        # init super-class
        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1],
            model=model, parameters=parameters, actions=actions, croppable=True)

        # assign camera object


    def getLatestFrame(self, is_save=False):
        return self._camera.getLast() 

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
    
        
    def getChunk(self):
        pass

    def flushBuffers(self):
        pass

    def startAcquisition(self):
        if self._camera.model == "mock":
            self.__logger.debug('We could attempt to reconnect the camera')
            pass
            
        if not self._running:
            self._camera.start_live()
            self._running = True
            self.__logger.debug('startlive')

    def stopAcquisition(self):
        if self._running:
            self._running = False
            self._camera.stop_live()
            self.__logger.debug('stoplive')

    def stopAcquisitionForROIChange(self):
        pass

    def finalize(self) -> None:
        super().finalize()
        self.__logger.debug('Safely disconnecting the camera...')
        #TODO: IMPLEMENT self._camera.close()

    @property
    def pixelSizeUm(self):
        return [1, 1, 1]

    def crop(self, hpos, vpos, hsize, vsize):
        pass

    def _performSafeCameraAction(self, function):
        pass

    def openPropertiesDialog(self):
        self._camera.openPropertiesGUI()


    def _getESP32CamObj(self):
        try:
            from imswitch.imcontrol.model.interfaces.CameraESP32CamSerial import CameraESP32CamSerial
            self.__logger.debug(f'Trying to initialize ESP32Camera')
            camera = CameraESP32CamSerial()
        except Exception as e:
            self.__logger.warning(f'Failed to initialize PiCamera {e}, loading TIS mocker')
            from imswitch.imcontrol.model.interfaces.tiscamera_mock import MockCameraTIS
            camera = MockCameraTIS()

        self.__logger.info(f'Initialized camera, model: {camera.model}')
        return camera

    def closeEvent(self):
        self._camera.close()

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
