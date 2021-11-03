import numpy as np
from ximea import xiapi
from imswitch.imcommon.model import initLogger
from collections import deque

from imswitch.imcontrol.model.interfaces import ximea
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

        # open Ximea camera for allowing parameters settings
        self._camera.open_device()

        # todo: local circular buffer used as a temporary workaround for getChunk
        # we should investigate if this is the proper way to store images
        # or another solution is feasible
        self._frame_buffer = deque([], maxlen=1000)

        for propertyName, propertyValue in detectorInfo.managerProperties['ximea'].items():
            self._camera.set_param(propertyName, propertyValue)

        fullShape = (self._camera.get_width_maximum(),
                     self._camera.get_height_maximum())

        model = self._camera.get_device_info_string("device_name").decode("utf-8")

        # Prepare parameters
        parameters = {
            'Exposure': DetectorNumberParameter(group='Timings', value=100e-6,
                                                         valueUnits='s', editable=True),

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

        def set_ximea_param():
            # parameter names are lower case
            # for multiple words, join them with '_' character
            ximea_param_name = "_".join(name.lower().split(" "))

            # append ":direct_update" to perform update
            # without stopping acquisition (if it is running)
            # only valid for gain and exposure parameters
            if ximea_param_name == "exposure" or ximea_param_name == "gain":
                ximea_param_name += ":direct_update"
                ximea_param_val = int(value) * 10e6

            # call set_param from Ximea camera
            self.__logger.info(f"Setting {ximea_param_name} to {ximea_param_val}")
            self._camera.set_param(ximea_param_name, value)

        self._performSafeCameraAction(set_ximea_param)

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
            camera = Camera()
            image = Image()
            
            camera_name = camera.get_device_info_string("device_name").decode("utf-8")
        except:
            self.__logger.warning(f'Failed to initialize Ximea camera {cameraId},'
                                  f' loading mocker')
            from imswitch.imcontrol.model.interfaces import MockXimea, MockImage
            camera = MockXimea()
            image = MockImage()
            camera_name = camera.get_device_info_string("device_name")

        self.__logger.info(f'Initialized camera, model: {camera_name}')
        return camera, image, camera_settings