import numpy as np
from ximea.xiapi import Xi_error
from imswitch.imcontrol.model.interfaces import XimeaSettings
from imswitch.imcommon.model import initLogger
from contextlib import contextmanager

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
        self._camera, self._img = self._getCameraObj(detectorInfo.managerProperties['cameraListIndex'])
        self._median : np.ndarray = None

        self._settings = XimeaSettings(self._camera)

        # open Ximea camera for allowing parameters settings
        self._camera.open_device()

        fullShape = (self._camera.get_width_maximum(),
                     self._camera.get_height_maximum())

        model = self._camera.get_device_info_string("device_name").decode("utf-8")

        for propertyName, propertyValue in detectorInfo.managerProperties['ximea'].items():
            self._camera.set_param(propertyName, propertyValue)

        # Prepare parameters
        parameters = {
            'Exposure': DetectorNumberParameter(group='Timings', value=1e-3,
                                                         valueUnits='s', editable=True),

            'Trigger source': DetectorListParameter(group='Trigger settings',
                                                    value=list(self._settings.settings[0].keys())[0],
                                                    options=list(self._settings.settings[0].keys()),
                                                    editable=True),
            
            'Trigger type': DetectorListParameter(group='Trigger settings',
                                                value=list(self._settings.settings[1].keys())[0],
                                                options=list(self._settings.settings[1].keys()),
                                                editable=True),
            
            'GPI': DetectorListParameter(group='Trigger settings',
                                        value=list(self._settings.settings[2].keys())[0],
                                        options=list(self._settings.settings[2].keys()),
                                        editable=True),

            'GPI mode': DetectorListParameter(group='Trigger settings',
                                            value=list(self._settings.settings[3].keys())[0],
                                            options=list(self._settings.settings[3].keys()),
                                            editable=True),
            
            'Bit depth' : DetectorListParameter(group='Miscellaneous',
                                                value=list(self._settings.settings[4].keys())[0],
                                                options=list(self._settings.settings[4].keys()),
                                                editable=True),

            'Camera pixel size': DetectorNumberParameter(group='Miscellaneous', value=13.7,
                                                         valueUnits='µm', editable=False),                                                        
        }

        self._isAcquiring = False

        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1],
                         model=model, parameters=parameters, croppable=True)
    
    @property
    def pixelSizeUm(self):
        umxpx = self.parameters['Camera pixel size'].value
        return [1, umxpx, umxpx]

    def getLatestFrame(self, is_save=False):
        if self._isAcquiring:
            self._camera.get_image(self._img)
            data = self._img.get_image_data_numpy()
            if self._median is not None:
                data /= self._median
        return data.astype(np.float32)

    def getChunk(self):
        return np.stack([self.getLatestFrame()])

    def flushBuffers(self):
        pass
    
    @contextmanager
    def _camera_disabled(self):
        if self._isAcquiring:
            try:
                self.stopAcquisition()
                yield
            finally:
                self.startAcquisition()
        else:
            yield

    def crop(self, hpos, vpos, hsize, vsize):
        """Method to crop the frame read out by the camera. """

        # Ximea ROI (at least for xiB-64) works only if the increment is performed
        # using a multiple of the minimum allowed increment of the sensor.
        with self._camera_disabled():
            if (hsize, vsize) != self.fullShape:
                try:
                    self.__logger.debug(f"Crop requested: X0 = {hpos}, Y0 = {vpos}, width = {hsize}, height = {vsize}")
                    hsize_incr = self._camera.get_width_increment()
                    vsize_incr = self._camera.get_height_increment()
                    hsize = (round(hsize / hsize_incr)*hsize_incr if (hsize % hsize_incr) != 0 else hsize)
                    vsize = (round(vsize / vsize_incr)*vsize_incr if (vsize % vsize_incr) != 0 else vsize)
                    self._camera.set_width(hsize)
                    self._camera.set_height(vsize)

                    hpos_incr  = self._camera.get_offsetX_increment()
                    vpos_incr  = self._camera.get_offsetY_increment()
                    hpos = (round(hpos / hpos_incr)*hpos_incr if (hpos % hpos_incr) != 0 else hpos)
                    vpos = (round(vpos / vpos_incr)*vpos_incr if (vpos % vpos_incr) != 0 else vpos)
                    self._camera.set_offsetX(hpos)
                    self._camera.set_offsetY(vpos)                
                    
                    self.__logger.debug(f"Increment info: X0_incr = {hpos_incr}, Y0_incr = {vpos_incr}, width_incr = {hsize_incr}, height_inc = {vsize_incr}")
                    self.__logger.debug(f"Actual crop: X0 = {hpos}, Y0 = {vpos}, width = {hsize}, height = {vsize}")
                except Xi_error as error:
                    self.__logger.error(f"Error in setting ROI (X0 = {hpos}, Y0 = {vpos}, width = {hsize}, height = {vsize})")
                    self.__logger.error(error)
            else:
                self._camera.set_offsetX(0)
                self._camera.set_offsetY(0)
                self._camera.set_width(self.fullShape[0])
                self._camera.set_height(self.fullShape[1])
                
        # This should be the only place where self.frameStart is changed
        self._frameStart = (hpos, vpos)
        # Only place self.shapes is changed
        self._shape = (hsize, vsize)

    def setBinning(self, binning):
        # todo: Ximea binning works in a different way
        # investigate how to properly update this value
        # if possible
        super().setBinning(binning)

    def setParameter(self, name : str, value):
        # Ximea parameters should follow the naming convention
        # described in https://www.ximea.com/support/wiki/apis/XiAPI_Manual
        ximea_value = None

        if name == "Exposure":
            # value must be translated into microseconds
            ximea_value = int(value*1e6)
        else:
            for setting in self._settings.settings:
                if value in setting.keys():
                    ximea_value = setting[value]
                    break
        try:
            self.__logger.info(f"Setting {name} to {ximea_value}")
            if name == "Bit depth":
                with self._camera_disabled():    
                    self._settings.set_parameter[name](ximea_value)
            else:
                self._settings.set_parameter[name](ximea_value)
            # update local parameters
            super().setParameter(name, value)
        except:
            self.__logger.error(f"Cannot set {name} to {ximea_value}")

        return self.parameters

    def startAcquisition(self):
        self._isAcquiring = True
        self._camera.start_acquisition()

    def stopAcquisition(self):
        self._isAcquiring = False
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
        return camera, image