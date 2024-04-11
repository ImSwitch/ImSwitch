import numpy as np

from imswitch.imcommon.model import initLogger
from .DetectorManager import DetectorManager, DetectorAction, DetectorNumberParameter, DetectorListParameter


class ThorcamManager(DetectorManager):
    """ DetectorManager that deals with TheImagingSource cameras and the
    parameters for frame extraction from them.

    Manager properties:

    - ``cameraListIndex`` -- the camera's index in the Allied Vision camera list (list
      indexing starts at 0); set this string to an invalid value, e.g. the
      string "mock" to load a mocker
    - ``av`` -- dictionary of Allied Vision camera properties
    """

    def __init__(self, detectorInfo, name, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        cameraId = detectorInfo.managerProperties['cameraListIndex']
        self._camera = self._getGXObj(cameraId ) 
        
        for propertyName, propertyValue in detectorInfo.managerProperties['gxipycam'].items():
            self._camera.setPropertyValue(propertyName, propertyValue)

        fullShape = (self._camera.SensorWidth, 
                     self._camera.SensorHeight)
        
        model = self._camera.model
        self._running = False
        self._adjustingParameters = False

        # Prepare parameters
        parameters = {
            'exposure': DetectorNumberParameter(group='Misc', value=100, valueUnits='ms',
                                                editable=True),
            'image_width': DetectorNumberParameter(group='Misc', value=fullShape[0], valueUnits='arb.u.',
                        editable=False),
            'image_height': DetectorNumberParameter(group='Misc', value=fullShape[1], valueUnits='arb.u.',
                        editable=False)
            }            

        # Prepare actions
        actions = {
            'More properties': DetectorAction(group='Misc',
                                              func=self._camera.openPropertiesGUI)
        }

        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1],
                         model=model, parameters=parameters, actions=actions, croppable=False)
    
    def getExposure(self) -> int:
        return self._camera.getPropertyValue('exposure')        

    def getLatestFrame(self, is_save=False):
        if is_save:
            return self._camera.getLastChunk()
        else:
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
        try:
            return self._camera.getLastChunk()
        except:
            return None

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
        """ This method is used to change those camera properties that need
        the camera to be idle to be able to be adjusted.
        """
        self._adjustingParameters = True
        wasrunning = self._running
        self.stopAcquisitionForROIChange()
        function()
        if wasrunning:
            self.startAcquisition()
        self._adjustingParameters = False

    def openPropertiesDialog(self):
        self._camera.openPropertiesGUI()

    def _getGXObj(self, cameraId, binning=1):
        try:
            from imswitch.imcontrol.model.interfaces.thorcamera import ThorCamera
            self.__logger.debug(f'Trying to initialize Throcamera {cameraId}')
            camera = ThorCamera(cameraNo=cameraId, binning=binning)
        except Exception as e:
            self.__logger.debug(e)
            self.__logger.warning(f'Failed to initialize ThorCamera {cameraId}, loading TIS mocker')
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
