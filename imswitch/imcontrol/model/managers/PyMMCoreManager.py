from imswitch.imcommon.framework import SignalInterface
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model.configfiletools import _mmcoreLogDir
from typing import Union, Tuple, Dict, List
from pymmcore_plus import CMMCorePlus, PropertyType
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
        self.__core = CMMCorePlus()
        
        self.__logger.info(f"Micro-Manager path: {self.__core._mm_path}")

        self.__logger.info(self.__core.getAPIVersionInfo())

        self.__getXYStagePosition = {
            "X" : self.__core.getXPosition,
            "Y" : self.__core.getYPosition
        }
        
        logpath = os.path.join(_mmcoreLogDir, dt.datetime.now().strftime("%d_%m_%Y") + ".log")
        self.__core.setPrimaryLogFile(logpath)
        self.__core.enableDebugLog(True)
    
    @property
    def core(self) -> CMMCorePlus:
        return self.__core
    
    def loadProperties(self, label: str, preInitValues: dict = None) -> dict:
        properties = {}

        for propName in self.__core.getDevicePropertyNames(label):

            propObj = self.__core.getPropertyObject(label, propName)
            propType = propObj.type()
            isReadOnly = propObj.isReadOnly()
            isPreInit = propObj.isPreInit()
            values = list(propObj.allowedValues())

            if propType in [PropertyType.Integer, PropertyType.Float]:
                if len(values) > 0:
                    values = [propType.to_python()(value) for value in values]
                else:
                    if isPreInit and preInitValues and propName in preInitValues and not isReadOnly:
                        propObj.setValue(preInitValues[propName])
                    values = propObj.value
            elif propType == PropertyType.String:
                # allowedValues() may not return nothing if the property is read-only
                # hence we make sure we get the proper value
                if isReadOnly:
                    values = propObj.value
            else:
                raise ValueError(f"Property {propName} is of unrecognized type!")
            
            
            properties[propName] = {
                "type": type(values),
                "values": values,
                "read_only": isReadOnly
            }
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
            self.__core.loadDevice(
                devInfo[0],
                devInfo[1],
                devInfo[2]
            )
            self.__core.initializeDevice(devInfo[0])
        except RuntimeError:
            raise ValueError(f"Error in loading device \"{devInfo[0]}\", check the values of \"module\" and \"device\" in the configuration file (current values: {devInfo[1]}, {devInfo[2]})")
        if isCamera:
            self.__core.setCameraDevice(devInfo[0])
            self.__core.initializeCircularBuffer()
    
    def unloadDevice(self, label: str) -> None:
        """ Tries to unload from the MMCore a previously loaded device (used for finalize() call)
        """
        try:
            self.__core.unloadDevice(label)
        except RuntimeError:
            raise ValueError(f"Error in unloading device \"{label}\"")
    
    def getProperty(self, label: str, property: str) -> str:
        """ Returns the property of a device.

        Args:
            label (``str``): name of the device
            property (``str``): label of the property to read            
        """
        try:
            return self.__core.getProperty(label, property)
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
            self.__core.setProperty(label, property, value)
        except RuntimeError as err:
            self.__logger.error(f"Failed to set \"{property}\" to {value}: {err.__str__()}")
    
    def getStagePosition(self, label: str, axis: str) -> float:
        """ Returns the current stage position (on a given axis for double-axis stages).
        
        Args:
            label (``str``): name of the positioner
            axis (``str``): axis to read
        """
        return (self.__getXYStagePosition[axis](label) if axis in self.__getXYStagePosition.keys() else self.__core.getPosition(label))
    
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
                self.__core.setPosition(label, positions[axis])
            else:
                self.__core.setRelativePosition(label, positions[axis])
            positions[axis] = self.getStagePosition(label, axis)
        else:
            # axis are forced by the manager constructor
            # to be "X-Y", so this call should be safe
            # just keep it under control...
            if isAbsolute:
                self.__core.setXYPosition(label, positions["X"], positions["Y"]) 
            else:
                self.__core.setRelativeXYPosition(label, positions["X"], positions["Y"])
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
            self.__core.setOrigin(label)
            positions[axes[0]] = self.__core.getPosition(label)
        else:
            self.__core.setOriginXY(label)
            positions = {ax : self.__getXYStagePosition[ax](label) for ax in axes}
        return positions
    
    def getROI(self, label: str) -> tuple:
        """Returns the current ROI for the selected camera device.

        Args:
            label (str): name of the camera.

        Returns:
            tuple: a rectangle describing the captured image. The tuple is described as: `[x, y, xSize, ySize]`.
        """
        return tuple(self.__core.getROI())
    
    def setROI(self, label: str, hpos: int, vpos: int, hsize: int, vsize: int) -> None:
        """Creates a new ROI for the camera device.

        Args:
            - `label (str)`: name of the camera.
            - `hpos (int)`: horizontal offset.
            - `vpos (int)`: vertical offset.
            - `hsize (int)`: horizontal size of the ROI (width).
            - `vsize (int)`: vertical size of the ROI (height).
        """
        self.__core.setROI(hpos, vpos, hsize, vsize)
    
    def setShutterStatus(self, label: str, status: bool) -> None:
        """Sets the shutter status of the selected device.

        Args:
            label (str): name of the device.
            status (bool): ``True`` if the shutter is open, ``False`` otherwise.
        """
        self.__core.setShutterOpen(label, status)
