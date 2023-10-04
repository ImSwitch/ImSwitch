from ..PyMMCoreManager import PyMMCoreManager # only for type hinting
from imswitch.imcommon.model import initLogger
from contextlib import contextmanager
from .DetectorManager import (
    DetectorManager, DetectorNumberParameter, DetectorListParameter
)

class PyMMCoreCameraManager(DetectorManager):
    """ Manager class for camera controlled via the Micro-Manager core.

    Manager properties:
    
    - ``module`` -- name of the MM module referenced
    - ``device`` -- name of the MM device described in the module 
    - ``exposureName (str)`` --  name of the property related to the exposure time;
    - ``preInitProperties (dict) (optional)`` -- a dictionary containing properties that need to be pre-initialized by the user, in the form
    ``{name (str): value (Any)}``
    """

    def __init__(self, detectorInfo, name, **lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)
        self.__coreManager: PyMMCoreManager = lowLevelManagers["pymmcManager"]

        module = detectorInfo.managerProperties["module"]
        device = detectorInfo.managerProperties["device"]
        try:
            self.exposureProperty = detectorInfo.managerProperties["exposureName"]
        except:
            raise ValueError("No property name for exposure time has been defined!")

        devInfo = (name, module, device)

        self.__coreManager.loadDevice(devInfo, True)
        
        try:
            preInit = detectorInfo.managerProperties["preInitProperties"]
            properties = self.__coreManager.loadProperties(name, preInit)
        except KeyError:
            properties = self.__coreManager.loadProperties(name)

        # unfortunately handling of the device properties is currently a non-standardized mess;
        # sometimes the exposure time is also a property and we want to filter it out as the properties
        # at the moment don't have a reference unit measure which we can use to generate the parameters,
        # so for now we'll manage by filter out the exposure from the read properties
        if self.exposureProperty in properties:
            del properties[self.exposureProperty]

        # we initialize the parameters dictionary with the exposure property
        parameters = {
            self.exposureProperty : DetectorNumberParameter(group='Timings', value=10,
                                                valueUnits='ms', editable=True),
        }

        # we then iterate over the read properties;
        # these are arranged in a dictionary with the following keys:
        # "type": the type of the property,
        # "values": the actual values of the type, to discern between a number or a list,
        # "read_only": if it's a read-only parameter (hence editable or not)
        for propName, propVals in properties.items():
            if propVals["type"] == list:
                # apparently a property could exist and have no values set,
                # and we have to nest this check internally to avoid falling in the
                # other branch of the if-else...
                if len(propVals["values"]) > 0:
                    parameters[propName] = DetectorListParameter(group="Camera properties", value=propVals["values"][0], options=propVals["values"], editable=True)
            else:
                if propVals["type"] == str:
                    parameters[propName] = DetectorListParameter(group="Camera properties", value=propVals["values"], options=[propVals["values"]], editable=False)
                else:
                    parameters[propName] = DetectorNumberParameter(group="Camera properties", value=float(propVals["values"]), valueUnits="", editable=not propVals["read_only"])

        parameters["Camera pixel size"] = DetectorNumberParameter(group='Miscellaneous', value=10,  valueUnits='µm', editable=True)

        _, _, hsize, vsize = self.__coreManager.getROI(name)

        super().__init__(detectorInfo, name, fullShape=(hsize, vsize), supportedBinnings=[1], 
                        model=device, parameters=parameters, croppable=True)
        self.setParameter("Exposure", self.parameters["Exposure"].value)
        self.__frame = None
    
    @property
    def pixelSizeUm(self):
        umxpx = self.parameters['Camera pixel size'].value
        return [1, umxpx, umxpx]
    
    def setBinning(self, binning):
        # todo: Ximea binning works in a different way
        # investigate how to properly update this value
        # if possible
        super().setBinning(binning)
    
    def getLatestFrame(self, is_save=False):
        if self.__coreManager.core.get_remaining_image_count() > 0:
            self.__frame = self.__coreManager.core.pop_next_image()
        return self.__frame
    
    def getChunk(self):
        return [self.getLatestFrame()]
    
    def flushBuffers(self):
        self.__coreManager.core.clear_circular_buffer()
    
    @contextmanager
    def _camera_disabled(self):
        if self.__coreManager.core.is_sequence_running(self.name):
            try:
                self.stopAcquisition()
                yield
            finally:
                self.startAcquisition()
        else:
            yield
    
    def startAcquisition(self):
        self.__coreManager.core.start_continous_sequence_acquisition(self.parameters["Exposure"].value)

    def stopAcquisition(self):
        self.__coreManager.core.stop_sequence_acquisition(self.name)
    
    def setParameter(self, name, value):
        # this may not work properly, keep an eye on it
        with self._camera_disabled():
            if name == "Exposure":
                self.__coreManager.core.set_exposure(value)
            else:
                self.__coreManager.setProperty(self.name, name, value) 
        # there will be still images left in the circular buffer
        # captured using the previous property value, so we flush the buffer
            self.flushBuffers()
        super().setParameter(name, value)

    def crop(self, hpos: int, vpos: int, hsize: int, vsize: int):
        self.__coreManager.setROI(self.name, hpos, vpos, hsize, vsize)
        
        # This should be the only place where self.frameStart is changed
        self._frameStart = (hpos, vpos)
        # Only place self.shapes is changed
        self._shape = (hsize, vsize)