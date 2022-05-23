from imswitch.imcommon.framework import SignalInterface
from imswitch.imcommon.model import initLogger
import pymmcore

class PyMMCoreManager(SignalInterface):
    """ For interaction with Micro-Manager C++ core. 
        Using pymmcore package (a Python-API wrapper).

        Setup fields:
        - ``MMPath``: MM absolute path in the system
        - ``MMDevSearchPath`` (optional): list of MM device search paths. If not set, ``MMPath`` is taken as reference.
    """

    def __init__(self, setupInfo) -> None:
        super().__init__()
        self.__logger = initLogger(self)
        mmPath = setupInfo.pymmcore.MMPath

        if mmPath is None:
            raise ValueError("No Micro-Manager path defined.")

        self.__core = pymmcore.CMMCore()
        devSearchPath = (setupInfo.pymmcore.MMDevSearchPath 
                        if setupInfo.pymmcore.MMDevSearchPath is not None 
                        else mmPath)

        if not isinstance(devSearchPath, list):
            devSearchPath = [devSearchPath]
        
        self.__logger.info(f"Micro-Manager path: {mmPath}")
        self.__logger.info(f"Device search paths: {devSearchPath}")

        self.__core.setDeviceAdapterSearchPaths(devSearchPath)
        self.__logger.info(self.__core.getAPIVersionInfo())

        self.__getXYStagePosition = {
            "X" : self.__core.getXPosition,
            "Y" : self.__core.getYPosition
        }
    
    def loadPositioner(self, devInfo: tuple[str, str, str]) -> None:
        """ Tries to load a positioner device into the MMCore.

        Args:
            devInfo (``tuple[str, str, str]``): a tuple describing the device information. It's arranged as:
            - devInfo[0]: label
            - devInfo[1]: moduleName
            - devInfo[2]: deviceName
        """
        try:
            self.__core.loadDevice(
                devInfo[0],
                devInfo[1],
                devInfo[2]
            )
        except RuntimeError:
            raise ValueError(f"Error in loading device \"{devInfo[0]}\", check the values of \"module\" and \"device\" in the configuration file (current values: {devInfo[1]}, {devInfo[2]})")
    
    def unloadPositioner(self, label: str) -> None:
        """ Tries to unload from the MMCore a previously loaded device (used for finalize() call)
        """
        try:
            self.__core.unloadDevice(label)
        except RuntimeError:
            raise ValueError(f"Error in unloading device \"{label}\"")
    
    def getStagePosition(self, label: str, type: str, axis: str = None) -> float:
        """ Returns the current stage position (on a given axis for double-axis stages).
        
        Args:
            label (``str``): name of the positioner
            type (``str``): positioner type (either "single" or "double")
            axis (``str``): axis to read
        """
        if type == "single":
            return self.__core.getPosition(label)
        else:
            return self.__getXYStagePosition[axis](label)
        
    
    def setStagePosition(self, label: str, stageType: str, axis: str, positions: dict[str, float]) -> float:
        """ Sets the selected stage position.

        Args:
            label (``str``): name of the positioner
            stageType (``str``): type of positioner (either "single" or "double")
            axis (``str``): axis to move (used only for "single" stage type)
            newPos (``dict[str, float]``): dictionary with the positions to set.
        
        Returns:
            the dictionary with the new [axis, position] assignment.
        """
        if stageType == "single":
            self.__core.setPosition(label, positions[axis])
            positions[axis] = self.__core.getPosition()
        else:
            # axis are forced by the manager constructor
            # to be "X-Y", so this call should be safe
            # just keep it under control...
            self.__core.setXYPosition(label, positions["X"], positions["Y"])
            positions = {axis : self.__getXYStagePosition[axis] for axis in ["X", "Y"]}
        return positions

