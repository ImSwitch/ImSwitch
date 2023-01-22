import numpy as np

from imswitch.imcommon.model import initLogger
from .DetectorManager import DetectorManager, DetectorAction, DetectorNumberParameter


class BaslerManager(DetectorManager):
    """ DetectorManager that deals with TheImagingSource cameras and the
    parameters for frame extraction from them.

    Manager properties:

    - ``cameraListIndex`` -- the camera's index in the Basler camera list (list
      indexing starts at 0); set this string to an invalid value, e.g. the
      string "mock" to load a mocker
    - ``basler`` -- dictionary of Basler camera properties
    """

    def __init__(self, detectorInfo, name, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        self._camera = self._getBaslerObj(detectorInfo.managerProperties['cameraListIndex'])
        try:        
            pixelSize = detectorInfo.managerProperties['cameraEffPixelsize'] # mum
        except Exception as e:
            self.__logger.error("No value is given for the effective pixelsize in the config json!")
            pixelSize = 1

        model = self._camera.model
        self._running = False
        self._adjustingParameters = False

        for propertyName, propertyValue in detectorInfo.managerProperties['basler'].items():
            self._camera.setPropertyValue(propertyName, propertyValue)

        try: # FIXME: get that form the real camera
            isRGB = detectorInfo.managerProperties['basler']['isRGB']  
        except:
            isRGB = False

        fullShape = (self._camera.SensorHeight, 
                     self._camera.SensorWidth)

        # TODO: Not implemented yet 
        self.crop(hpos=0, vpos=0, hsize=fullShape[0], vsize=fullShape[1])

        # Prepare parameters
        parameters = {
            'exposure': DetectorNumberParameter(group='Misc', value=100, valueUnits='ms',
                                                editable=True),
            'gain': DetectorNumberParameter(group='Misc', value=1, valueUnits='arb.u.',
                                            editable=True),
            'blacklevel': DetectorNumberParameter(group='Misc', value=100, valueUnits='arb.u.',
                                            editable=True),
            'image_width': DetectorNumberParameter(group='Misc', value=fullShape[0], valueUnits='arb.u.',
                        editable=False),
            'image_height': DetectorNumberParameter(group='Misc', value=fullShape[1], valueUnits='arb.u.',
                        editable=False), 
            'isRGB': DetectorNumberParameter(group='Misc', value=isRGB, valueUnits='arb.u.',
                        editable=False),
            'Camera pixel size': DetectorNumberParameter(group='Misc', value=pixelSize,
                                    valueUnits='µm', editable=True)
            }            

        # Prepare actions
        actions = {
            'More properties': DetectorAction(group='Misc',
                                              func=self._camera.openPropertiesGUI)
        }

        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1],
                         model=model, parameters=parameters, actions=actions, croppable=True)

    def setPixelSizeUm(self, pixelSizeUm):
        self.parameters['Camera pixel size'].value = pixelSizeUm

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

    def setBinning(self, binning):
        super().setBinning(binning) 
        

    def getChunk(self):
        try:
            return np.expand_dims(self._camera.getLastChunk(),0)
        except:
            return None

    def flushBuffers(self):
        pass

    def startAcquisition(self):
        if not self._running:
            self._camera.start_live()
            self._running = True
            self.__logger.debug('startlive')

    def stopAcquisition(self):
        if self._running:
            self._running = False
            self._camera.suspend_live()
            self.__logger.debug('suspendlive')

    def stopAcquisitionForROIChange(self):
        self._running = False
        self._camera.stop_live()
        self.__logger.debug('stoplive')

    def finalize(self) -> None:
        super().finalize()
        self.__logger.debug('Safely disconnecting the camera...')
        self._camera.close()

    @property
    def pixelSizeUm(self):
        umxpx = self.parameters['Camera pixel size'].value
        return [1, umxpx, umxpx]

    def crop(self, hpos, vpos, hsize, vsize):
        def cropAction():
            # self.__logger.debug(
            #     f'{self._camera.model}: crop frame to {hsize}x{vsize} at {hpos},{vpos}.'
            # )
            pass
            #self._camera.setROI(hpos, vpos, hsize, vsize)

        self._performSafeCameraAction(cropAction)
        # TODO: unsure if frameStart is needed? Try without.
        # This should be the only place where self.frameStart is changed
        self._frameStart = (hpos, vpos)
        # Only place self.shapes is changed
        self._shape = (hsize, vsize)

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

    def _getBaslerObj(self, cameraId):
        try:
            from imswitch.imcontrol.model.interfaces.baslercamera import CameraBasler
            self.__logger.debug(f'Trying to initialize Basler Imaging camera {cameraId}')
            camera = CameraBasler(cameraId)
        except Exception as e:
            print(e)
            self.__logger.warning(f'Failed to initialize basler camera {cameraId}, loading TIS mocker')
            from imswitch.imcontrol.model.interfaces.tiscamera_mock import MockCameraTIS
            camera = MockCameraTIS()

        self.__logger.info(f'Initialized camera, model: {camera.model}')
        return camera

    def closeEvent(self):
        self._camera.close()

    def getFrameNumber(self):
        return self._camera.getFrameNumber()

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
