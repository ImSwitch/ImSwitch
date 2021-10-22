import numpy as np

from imswitch.imcommon.model import initLogger
from .DetectorManager import DetectorManager, DetectorAction, DetectorNumberParameter


class AVManager(DetectorManager):
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

        self._camera = self._getAVObj(detectorInfo.managerProperties['cameraListIndex'])

        model = self._camera.model
        self._running = False
        self._adjustingParameters = False

        for propertyName, propertyValue in detectorInfo.managerProperties['avcam'].items():
            self._camera.setPropertyValue(propertyName, propertyValue)

        fullShape = (self._camera.getPropertyValue('image_width'),
                     self._camera.getPropertyValue('image_height'))

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
            }            

        # Prepare actions
        actions = {
            'More properties': DetectorAction(group='Misc',
                                              func=self._camera.openPropertiesGUI)
        }

        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1],
                         model=model, parameters=parameters, actions=actions, croppable=True)

    def getLatestFrame(self):
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
        return self._camera.getLast()

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

    @property
    def pixelSizeUm(self):
        return [1, 1, 1]

    def crop(self, hpos, vpos, hsize, vsize):
        if(0):
            def cropAction():
                # self.__logger.debug(
                #     f'{self._camera.model}: crop frame to {hsize}x{vsize} at {hpos},{vpos}.'
                # )
                self._camera.setROI(hpos, vpos, hsize, vsize)

            self._performSafeCameraAction(cropAction)
            # TODO: unsure if frameStart is needed? Try without.
            # This should be the only place where self.frameStart is changed
            self._frameStart = (hpos, vpos)
            # Only place self.shapes is changed
            self._shape = (hsize, vsize)
        # TODO: Reimplement

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

    def _getAVObj(self, cameraId):
        try:
            from imswitch.imcontrol.model.interfaces.avcamera import CameraAV
            self.__logger.debug(f'Trying to initialize Allied Vision camera {cameraId}')
            camera = CameraAV(cameraId)
        except Exception as e:
            print(e)
            self.__logger.warning(f'Failed to initialize AV camera {cameraId}, loading TIS mocker')
            from imswitch.imcontrol.model.interfaces.tiscamera_mock import MockCameraTIS
            camera = MockCameraTIS()

        self.__logger.info(f'Initialized camera, model: {camera.model}')
        return camera

