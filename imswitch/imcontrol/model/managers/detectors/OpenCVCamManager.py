import numpy as np

from imswitch.imcommon.model import initLogger
from .DetectorManager import DetectorManager, DetectorAction, DetectorNumberParameter, DetectorListParameter


class OpenCVCamManager(DetectorManager):
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

        
        try: # FIXME: get that form the real camera
            isRGB = detectorInfo.managerProperties['isRGB']  
        except:
            isRGB = False
            
        try:
            pixelSize = detectorInfo.managerProperties['cameraEffPixelsize'] # mum
        except:
            # returning back to default pixelsize
            pixelSize = 1

        self._camera = self._getOpenCVObj(detectorInfo.managerProperties['cameraListIndex'], isRGB)

        model = self._camera.model
        self._running = False
        
        for propertyName, propertyValue in detectorInfo.managerProperties['opencvcam'].items():
            self._camera.setPropertyValue(propertyName, propertyValue)

        fullShape = (self._camera.getPropertyValue('image_width'),
                     self._camera.getPropertyValue('image_height'))

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
            'pixel_format': DetectorListParameter(group='Misc', value='Mono12', options=['Mono8','Mono12'], editable=True), 
            'Camera pixel size': DetectorNumberParameter(group='Miscellaneous', value=pixelSize,
                                                valueUnits='µm', editable=True)
            }            

        # Prepare actions
        actions = {
            'More properties': DetectorAction(group='Misc',
                                              func=self._camera.openPropertiesGUI)
        }

        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1],
                         model=model, parameters=parameters, actions=actions, croppable=True)

    def getLatestFrame(self, is_save=False, returnFrameNumber=False):
        if returnFrameNumber:
            frame, frameNumber = self._camera.getLast(returnFrameNumber=returnFrameNumber)
            return frame, frameNumber
        else:
            frame = self._camera.getLast(returnFrameNumber=returnFrameNumber)
            return frame
        
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
    
    @property
    def pixelSizeUm(self):
        umxpx = self.parameters['Camera pixel size'].value
        return [1, umxpx, umxpx]

    def setPixelSizeUm(self, pixelSizeUm):
        self.parameters['Camera pixel size'].value = pixelSizeUm

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
        return np.expand_dims(self._camera.getLastChunk(),0)

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
        self.__logger.debug('stoplive for roi change')

    def finalize(self) -> None:
        super().finalize()
        self.__logger.debug('Safely disconnecting the camera...')
        self._camera.close()

    def crop(self, hpos, vpos, hsize, vsize):
        def cropAction():
            # self.__logger.debug(
            #     f'{self._camera.model}: crop frame to {hsize}x{vsize} at {hpos},{vpos}.'
            # )
            self._camera.setROI(hpos, vpos, hsize, vsize)

        self._performSafeCameraAction(cropAction)
        # TODO: unsure if frameStart is needed? Try without.
        # This should be the only place where self.frameStart is changed
        # self._frameStart = (hpos, vpos)
        # Only place self.shapes is changed 
        #vsize = self._camera.getPropertyValue('image_width')
        #hsize = self._camera.getPropertyValue('image_height')
        self._shape = self._camera.shape
    
    def _performSafeCameraAction(self, function):
        """ This method is used to change those camera properties that need
        the camera to be idle to be able to be adjusted.
        """
        
        wasrunning = self._running
        self.stopAcquisitionForROIChange()
        function()
        if wasrunning:
            self.startAcquisition()

    def openPropertiesDialog(self):
        self._camera.openPropertiesGUI()

    def _getOpenCVObj(self, cameraindex=0, isRGB=0):
        try:
            from imswitch.imcontrol.model.interfaces.opencvcam import CameraOpenCV
            self.__logger.debug(f'Trying to initialize OpenCV IMX219 camera')
            camera = CameraOpenCV(cameraindex, isRGB=isRGB)
        except Exception as e:
            self.__logger.error(e)
            self.__logger.warning(f'Failed to initialize OpenCV IMX219 camera, loading TIS mocker')
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
