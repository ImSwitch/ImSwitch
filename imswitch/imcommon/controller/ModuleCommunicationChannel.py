from imswitch.imcommon.framework import SignalInterface
from imswitch.imcommon.model import VFileCollection


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
        self.__memoryRecordings = VFileCollection()
        self.__registeredModules = set()

    def register(self, modulePackage):
        self.__registeredModules.add(self.getModuleId(modulePackage))

    def unregister(self, modulePackage):
        self.__registeredModules.remove(self.getModuleId(modulePackage))

    def getModuleId(self, modulePackage):
        moduleId = modulePackage.__name__
        moduleId = moduleId[moduleId.rindex('.') + 1:]  # E.g. "imswitch.imcontrol" -> "imcontrol"
        return moduleId

    def isModuleRegistered(self, moduleId):
        return moduleId in self.__registeredModules


# Copyright (C) 2020-2021 ImSwitch developers
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
