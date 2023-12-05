from imswitch.imcommon.framework import SignalInterface
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model.configfiletools import _mmcoreLogDir
from typing import Union, Tuple, Dict, List
from pymmcore_plus import PropertyType
from pycromanager import Core, start_headless, stop_headless
from pycromanager.headless import _create_pymmcore_instance
import datetime as dt
import os

PropertyValue = Union[bool, float, int, str]

class PyMMCoreManager(SignalInterface):
    """ For interaction with Micro-Manager C++ core. 
        Using pymmcore-plus package (a Python-API wrapper).
    """

    def __init__(self, setupInfo) -> None:
        super().__init__()
        self.__logger = initLogger(self)
        self.__core = None
        self.__usingPycroManager = False

        if "PycroManager" in setupInfo.availableWidgets:
            self.__usingPycroManager = True
            self.__logger.info("Starting headless instance...")
            start_headless(
                mm_app_path=setupInfo.pycroManager.mmPath,
                max_memory_mb=setupInfo.pycroManager.maxMemoryMB,
                buffer_size_mb=setupInfo.pycroManager.bufferSizeMB,
                port=setupInfo.pycroManager.port 
            )
            self.__logger.info(f"Started on port {setupInfo.pycroManager.port}")
            self.__core = Core()
        else:
            self.__logger.info("Starting pymmcore instance...")
            self.__core = _create_pymmcore_instance()
            self.__core.set_device_adapter_search_paths([setupInfo.pycroManager.mmPath,])
            self.__core.set_circular_buffer_memory_footprint(setupInfo.pycroManager.bufferSizeMB)
            self.__logger.info("Using pymmcore backend")

        self.__logger.info(self.__core.get_api_version_info())

        self.__getXYStagePosition = {
            "X" : self.__core.get_x_position,
            "Y" : self.__core.get_y_position
        }
        
        logpath = os.path.join(_mmcoreLogDir, dt.datetime.now().strftime("%d_%m_%Y") + ".log")
        self.__core.set_primary_log_file(logpath)
        self.__core.enable_debug_log(True)
    
    def __del__(self):
        if self.__usingPycroManager:
            stop_headless()
    
    @property
    def usingPycroManager(self) -> bool:
        return self.__usingPycroManager

    @property
    def core(self) -> Core:
        return self.__core
    
    def loadProperties(self, label: str, preInitValues: dict = None) -> dict:
        properties = {}

        if self.__usingPycroManager:
            propNamesStrVec = self.__core.get_device_property_names(label)
            propNames = [propNamesStrVec.get(i) for i in range(propNamesStrVec.size())]
        else:
            propNames = self.__core.get_device_property_names(label)

        for propName in propNames:
            isReadOnly = self.__core.is_property_read_only(label, propName)
            isPreInit = self.__core.is_property_pre_init(label, propName)
            if self.__usingPycroManager:
                propType = PropertyType(self.__core.get_property_type(label, propName).swig_value())
                valuesStrVec = self.__core.get_allowed_property_values(label, propName)
                values = [valuesStrVec.get(i) for i in range(valuesStrVec.size())]
            else:
                propType = PropertyType(self.__core.get_property_type(label, propName))
                values = self.__core.get_allowed_property_values(label, propName)

            propDict = {
                "type" : propType,
                "values": None,
                "read_only": isReadOnly,
            }

            if propType in [PropertyType.Integer, PropertyType.Float]:
                if len(values) > 0:
                    values = [propType.to_python()(value) for value in values]
                else:
                    if isPreInit and preInitValues and propName in preInitValues and not isReadOnly:
                        self.__core.set_property(label, propName, preInitValues[propName])
                    values = self.__core.get_property(label, propName)
                pass
            elif propType == PropertyType.String:
                # get_allowed_property_values() may not return nothing 
                # if the property is read-only
                # hence we make sure we get the proper value
                if isReadOnly:
                    values = [self.__core.get_property(label, propName)]
            else:
                raise ValueError(f"Property {propName} is of unrecognized type!")
            
            propDict["values"] = values
            properties[propName] = propDict

        return properties
    
    def loadDevice(self, devInfo: Tuple[str, str, str], isCamera: bool = False) -> None:
        """ Tries to load a device into the MMCore. If the device is a camera, it also initializes the circular buffer.

        Args:
            devInfo (``tuple[str, str, str]``): a tuple describing the device information. It's arranged as:
            - devInfo[0]: label
            - devInfo[1]: moduleName
            - devInfo[2]: deviceName
            isCamera (``bool``): flag signaling wether the requested device is a camera.
        """
        try:
            self.__core.load_device(
                devInfo[0],
                devInfo[1],
                devInfo[2]
            )
            self.__core.initialize_device(devInfo[0])
        except RuntimeError:
            raise ValueError(f"Error in loading device \"{devInfo[0]}\", check the values of \"module\" and \"device\" in the configuration file (current values: {devInfo[1]}, {devInfo[2]})")
        if isCamera:
            self.__core.set_camera_device(devInfo[0])
    
    def unloadDevice(self, label: str) -> None:
        """ Tries to unload from the MMCore a previously loaded device (used for finalize() call)
        """
        try:
            self.__core.unload_device(label)
        except RuntimeError:
            raise ValueError(f"Error in unloading device \"{label}\"")
    
    def getProperty(self, label: str, property: str) -> str:
        """ Returns the property of a device.

        Args:
            label (``str``): name of the device
            property (``str``): label of the property to read            
        """
        try:
            return self.__core.get_property(label, property)
        except Exception as err:
            raise RuntimeError(f"Failed to load property \"{property}\": {err.__str__()}")
    
    def setProperty(self, label: str, property: str, value: PropertyValue) -> None:
        """ Sets the property of a device.
        
        Args:
            label (``str``): name of the device
            property (``str``): label of the property to read
            value (``PropertyValue``): value to set the property with
        """
        try:
            self.__core.set_property(label, property, value)
        except RuntimeError as err:
            self.__logger.error(f"Failed to set \"{property}\" to {value}: {err.__str__()}")
    
    def getStagePosition(self, label: str, axis: str) -> float:
        """ Returns the current stage position (on a given axis for double-axis stages).
        
        Args:
            label (``str``): name of the positioner
            axis (``str``): axis to read
        """
        return (self.__getXYStagePosition[axis](label) if axis in self.__getXYStagePosition.keys() else self.__core.get_position(label))
    
    def setStagePosition(self, label: str, stageType: str, axis: str, positions: Dict[str, float], isAbsolute: bool = True) -> Dict[str, float]:
        """ Sets the selected stage position. Stages can be of two types:
        - single: a single-axis stage;
        - double: an X-Y stage.

        Args:
            label (``str``): name of the positioner
            stageType (``str``): type of positioner (either "single" or "double")
            axis (``str``): axis to move (used only for "single" stage type)
            positions (``dict[str, float]``): dictionary with the positions to set.
            isAbsolute (``bool``): ``True`` if absolute movement is requested, otherwise false.  
        
        Returns:
            the dictionary with the new [axis, position] assignment.
        """
        if stageType == "single":
            if isAbsolute:
                self.__core.set_position(label, positions[axis])
            else:
                self.__core.set_relative_position(label, positions[axis])
            positions[axis] = self.getStagePosition(label, axis)
        else:
            # axis are forced by the manager constructor
            # to be "X-Y", so this call should be safe
            # just keep it under control...
            if isAbsolute:
                self.__core.set_xy_position(label, positions["X"], positions["Y"]) 
            else:
                self.__core.set_relative_xy_position(label, positions["X"], positions["Y"])
            positions = {axis : self.__getXYStagePosition[axis](label) for axis in ["X", "Y"]}
        return positions
    
    def setStageOrigin(self, label: str, stageType: str, axes: List[str]) -> Dict[str, float]:
        """Zeroes the stage at the current position.

        Args:
            label (``str``): name od the positioner
            stageType (``str``): type of positioner (either "single" or "double")
            axis (str): axis to move (used only for "single" stage type)

        Returns:
            Dict[str, float]: dictionary containing the new positioner's origin.
        """
        positions = {}
        if stageType == "single":
            self.__core.set_origin(label)
            positions[axes[0]] = self.__core.get_position(label)
        else:
            self.__core.set_origin_xy(label)
            positions = {ax : self.__getXYStagePosition[ax](label) for ax in axes}
        return positions
    
    def getROI(self, label: str) -> tuple:
        """Returns the current ROI for the selected camera device.

        Args:
            label (str): name of the camera.

        Returns:
            tuple: a rectangle describing the captured image. The tuple is described as: `[x, y, xSize, ySize]`.
        """
        if self.__usingPycroManager:
            roiObj = self.__core.get_roi()
            return (roiObj.x, roiObj.y, roiObj.width, roiObj.height)
        else:
            return tuple(self.__core.get_roi(label))
    
    def setROI(self, label: str, hpos: int, vpos: int, hsize: int, vsize: int) -> None:
        """Creates a new ROI for the camera device.

        Args:
            - `label (str)`: name of the camera.
            - `hpos (int)`: horizontal offset.
            - `vpos (int)`: vertical offset.
            - `hsize (int)`: horizontal size of the ROI (width).
            - `vsize (int)`: vertical size of the ROI (height).
        """
        self.__core.set_roi(hpos, vpos, hsize, vsize)
    
    def setShutterStatus(self, label: str, status: bool) -> None:
        """Sets the shutter status of the selected device.

        Args:
            label (str): name of the device.
            status (bool): ``True`` if the shutter is open, ``False`` otherwise.
        """
        self.__core.set_shutter_open(label, status)
