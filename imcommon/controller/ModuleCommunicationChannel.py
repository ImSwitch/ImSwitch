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

# Copyright (C) 2020, 2021 TestaLab
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License