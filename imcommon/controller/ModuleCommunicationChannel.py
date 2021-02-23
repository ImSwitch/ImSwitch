import numpy as np
from imcommon.framework import Signal, SignalInterface
from imcommon.model import DataCollection


class ModuleCommunicationChannel(SignalInterface):
    """
    ModuleCommunicationChannel is a class that handles the communication
    between modules.
    """

    @property
    def memoryRecordings(self):
        return self.__memoryRecordings

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__memoryRecordings = DataCollection()
        self.__registeredModules = set()

    def register(self, modulePackage):
        self.__registeredModules.add(modulePackage.__name__)

    def unregister(self, modulePackage):
        self.__registeredModules.remove(modulePackage.__name__)

    def isModuleRegistered(self, moduleName):
        return moduleName in self.__registeredModules
