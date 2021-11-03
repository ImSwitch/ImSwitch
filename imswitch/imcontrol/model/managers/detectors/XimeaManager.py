import numpy as np
from ximea import xiapi
from imswitch.imcommon.model import initLogger
from collections import deque
from .DetectorManager import (
    DetectorManager, DetectorNumberParameter, DetectorListParameter
)

class XimeaManager(DetectorManager):
    """ DetectorManager that deals with the Ximea parameters and frame
    extraction for a Ximea camera.

    Manager properties:

    - ``cameraListIndex`` -- the camera's index in the Ximea camera list
      (list indexing starts at 0); set this to an invalid value, e.g. the
      string "mock" to load a mocker
    - ``ximea`` -- dictionary of DCAM API properties to pass to the driver
    """

    def __init__(self, detectorInfo, name, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)
        self._camera, self._img, settings = self._getCameraObj(detectorInfo.managerProperties['cameraListIndex'])

        # todo: local circular buffer used as a temporary workaround for getChunk
        # we should investigate if this is the proper way to store images
        # or another solution is feasible
        self._frame_buffer = deque([], maxlen=1000)

        # to set Ximea parameters, camera must be open first
        self._camera.open_device()

        for propertyName, propertyValue in detectorInfo.managerProperties['ximea'].items():
            self._camera.set_param(propertyName, propertyValue)

        fullShape = (self._camera.get_width_maximum(),
                     self._camera.get_height_maximum())

        model = self._camera.get_device_model_id()

        # Prepare parameters
        parameters = {
            'Exposure': DetectorNumberParameter(group='Timings', value=100,
                                                         valueUnits='µs', editable=True),

            'Trigger source': DetectorListParameter(group='Trigger settings',
                                                    value=settings.trigger_source[0],
                                                    options=settings.trigger_source,
                                                    editable=True),
            
            'Trigger selector': DetectorListParameter(group='Trigger settings',
                                                value=settings.trigger_selector[0],
                                                options=settings.trigger_selector,
                                                editable=True),

            'GPI mode': DetectorListParameter(group='Trigger settings',
                                            value=settings.gpi_mode[0],
                                            options=settings.gpi_mode,
                                            editable=True),

            'GPI selector': DetectorListParameter(group='Acquisition mode',
                                                    value=settings.gpi_selector[0],
                                                    options=settings.gpi_selector,
                                                    editable=True),
            
            'Camera pixel size': DetectorNumberParameter(group='Miscellaneous', value=13.7,
                                                         valueUnits='µm', editable=False),                                                        
        }

        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1],
                         model=model, parameters=parameters, croppable=True)
    
    @property
    def pixelSizeUm(self):
        umxpx = self.parameters['Camera pixel size'].value
        return [1, umxpx, umxpx]

    def getLatestFrame(self):
        self._camera.get_image(self._img)
        data = self._img.get_image_data_numpy()
        self._frame_buffer.append(data)
        return data

    def getChunk(self):
        return np.stack(self._frame_buffer)

    def flushBuffers(self):
        self._frame_buffer.clear()

    def crop(self, hpos, vpos, hsize, vsize):
        """Method to crop the frame read out by the camera. """

        def cropAction():
            self._camera.set_offsetX(0)
            self._camera.set_offsetY(0)
            self._camera.set_width(self.fullShape[1])
            self._camera.set_height(self.fullShape[0])

            if (hsize, vsize) != self.fullShape:
                self._camera.set_offsetX(vpos)
                self._camera.set_offsetY(hpos)
                self._camera.set_width(vsize)
                self._camera.set_height(hsize)

        self._performSafeCameraAction(cropAction)

        # This should be the only place where self.frameStart is changed
        self._frameStart = (hpos, vpos)
        # Only place self.shapes is changed
        self._shape = (hsize, vsize)

    def setBinning(self, binning):
        # todo: Ximea binning works in a different way
        # investigate how to properly update this value
        super().setBinning(binning)

    def setParameter(self, name : str, value):
        # Ximea parameters should follow the naming convention
        # described in https://www.ximea.com/support/wiki/apis/XiAPI_Manual

        # parameter names are lower case
        # for multiple words, join them with '_' character
        name = "_".join(name.lower().split(" "))

        # call set_param from Ximea camera
        self._camera.set_param(name, value)

        # then update local parameters
        super().setParameter(name, value)

        return self.parameters

    def startAcquisition(self):
        self._camera.start_acquisition()

    def stopAcquisition(self):
        self._camera.stop_acquisition()
    
    def finalize(self) -> None:
        self._camera.close_device()

    def _setExposure(self, time):
        self._camera.set_exposure(time)

    def _performSafeCameraAction(self, function):
        """ This method is used to change those camera properties that need
        the camera to be idle to be able to be adjusted.
        """
        try:
            function()
        except Exception:
            self.stopAcquisition()
            function()
            self.startAcquisition()

    def _getCameraObj(self, cameraId):
        
        from imswitch.imcontrol.model.interfaces import XimeaSettings
        camera_settings = XimeaSettings()

        try:
            from ximea.xiapi import Camera, Image
            self.__logger.debug(f'Trying to initialize Ximea camera {cameraId}')
            camera = Camera(cameraId)
            image = Image()
            camera_name = camera.get_device_info_string("device_name") + ": " + camera.get_device_info_string("device_type")
        except:
            self.__logger.warning(f'Failed to initialize Ximea camera {cameraId},'
                                  f' loading mocker')
            from imswitch.imcontrol.model.interfaces import MockXimea, MockImage
            camera = MockXimea()
            image = MockImage()
            camera_name = camera.get_device_info_string("device_name") + ": " + camera.get_device_info_string("device_type")

        self.__logger.info(f'Initialized camera, model: {camera_name}')
        return camera, image, camera_settings