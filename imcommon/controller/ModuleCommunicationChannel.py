import numpy as np
from imcommon.framework import Signal, SignalInterface


class ModuleCommunicationChannel(SignalInterface):
    """
    ModuleCommunicationChannel is a class that handles the communication
    between modules.
    """

    sigMemoryRecordingAvailable = Signal(str, object, np.ndarray, dict)  # (name, Optional[path], data, attrs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__registeredModules = set()

    def register(self, modulePackage):
        self.__registeredModules.add(modulePackage.__name__)

    def unregister(self, modulePackage):
        self.__registeredModules.remove(modulePackage.__name__)

    def isModuleRegistered(self, moduleName):
        return moduleName in self.__registeredModules
