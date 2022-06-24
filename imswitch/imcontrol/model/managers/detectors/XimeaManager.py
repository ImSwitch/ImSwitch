import numpy as np
import Pyro5.api
from ximea.xiapi import Xi_error
from imswitch.imcontrol.model.interfaces import XimeaSettings
from imswitch.imcommon.model import initLogger
from contextlib import contextmanager

from .DetectorManager import (
    DetectorManager, DetectorNumberParameter, DetectorListParameter, DetectorAction
)

class XimeaManager(DetectorManager):
    """ DetectorManager that deals with the Ximea parameters and frame
    extraction for a Ximea camera.

    Manager properties:

    - ``cameraListIndex`` -- the camera's index in the Ximea camera list
      (list indexing starts at 0); set this to an invalid value, e.g. the
      string "mock" to load a mocker
    - ``parameters`` -- dictionary of XiAPI properties to pass to the driver
    - ``medianFilter`` -- dictionary of parameters required for median filter acquisition
    - ``server`` -- URI of local ImSwitchServer in the format of host-port (i.e. \"127.0.0.1:54333\") 
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

        for propertyName, propertyValue in detectorInfo.managerProperties['parameters'].items():
            self._camera.set_param(propertyName, propertyValue)
        
        server = detectorInfo.managerProperties["server"]

        try:
            if server is None:
                self.__proxy = None
            elif server == "default":
                uri = Pyro5.api.URI("PYRO:ImSwitchServer@127.0.0.1:54333")
                self.__proxy = Pyro5.api.Proxy(uri)
            else:
                uri_str = "PYRO:ImSwitchServer@" + server
                uri = Pyro5.api.URI(uri_str)
                self.__proxy = Pyro5.api.Proxy(uri)
        except:
            self.__logger.warning("Failed to connect to ImSwitchServer")
            self.__proxy = None

        # gather parameters for median filter control
        try:
            self.__mfPositioners = detectorInfo.managerProperties["medianFilter"]["positioners"]
            self.__mfStep = detectorInfo.managerProperties["medianFilter"]["step"]
            self.__mfMaxFrames = detectorInfo.managerProperties["medianFilter"]["maxFrames"]
        except:
            self.__logger.warning("No information available for median filter control.")
            self.__mfPositioners = None
            self.__mfStep = None
            self.__mfMaxFrames = None

        # prepare parameters
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
                                                         valueUnits='µm', editable=True),                                                        
        }

        actions = {}
        if (self.__proxy is not None
                and self.__mfPositioners is not None
                and self.__mfStep is not None
                and self.__mfMaxFrames is not None):
            
            parameters["Step size"] = DetectorNumberParameter(group="Median Filter", value=self.__mfStep, valueUnits="µm", editable=True)
            parameters["Number of frames"] = DetectorNumberParameter(group="Median Filter", value=self.__mfMaxFrames, valueUnits="", editable=True)

            actions["Generate median filter"] = DetectorAction(group="Median Filter", func=self._generateMedianFilter)
            actions["Clear median filter"] = DetectorAction(group="Median Filter", func=self._clearMedianFilter)

        super().__init__(detectorInfo, name, fullShape=fullShape, supportedBinnings=[1],
                         model=model, parameters=parameters, croppable=True, actions=actions)
        
        # apparently the XiAPI for detecting if camera is in acquisition does not work
        # we need to use a flag
        self._isAcquiring = False
    
    @property
    def pixelSizeUm(self):
        umxpx = self.parameters['Camera pixel size'].value
        return [1, umxpx, umxpx]

    def getLatestFrame(self, is_save=False):
        self._camera.get_image(self._img)
        data = self._img.get_image_data_numpy()
        if self._median is not None:
            data = np.subtract(data, self._median, dtype=np.float32)
        return data

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
    
    @contextmanager
    def _camera_enabled(self):
        if not self._isAcquiring:
            try:
                self.startAcquisition()
                yield
            finally:
                self.stopAcquisition()
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

        if name == "Step size" or name == "Number of frames":
            if name == "Step size":
                self.__mfStep = value
            elif name == "Number of frames":
                self.__mfMaxFrames = value
            super().setParameter(name, value)
            return self.parameters

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

    def _generateMedianFilter(self):
        self.__logger.warning("Generating median filter...")
        with self._camera_enabled():
            buffer = []
            # we generate a square movement on the X-Y axis
            # we need to make sure that the maximum number of frames
            # is coherent (must be divisible by 4)
            residual = self.__mfMaxFrames % 4
            if residual != 0:
                self.__logger.warning(f"Adjusting maximum number of frames to {residual + self.__mfMaxFrames}")
                self.__mfMaxFrames += residual
                super().setParameter("Number of frames", self.__mfMaxFrames)
            movementList = ["X", "Y", "-X", "-Y"]
            movements = int(self.__mfMaxFrames / 4)
            for ax in movementList:
                if not "-" in ax:
                    for _ in range(movements):
                        self.__proxy.stepUp(self.__mfPositioners[ax], ax,  self.__mfStep)
                        buffer.append(self.getLatestFrame())
                else:
                    ax = ax.replace("-", "")
                    for _ in range(movements):
                        self.__proxy.stepDown(self.__mfPositioners[ax], ax,  self.__mfStep)
                        buffer.append(self.getLatestFrame())
        
        self._median = np.median(np.stack(buffer), axis=0)
        self.__logger.warning("... done!")
    
    def _clearMedianFilter(self):
        self.__logger.warning("Clearing median filter")
        self._median = None
