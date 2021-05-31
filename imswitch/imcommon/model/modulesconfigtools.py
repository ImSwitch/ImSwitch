import os
import pkgutil
import dataclasses
from dataclasses import dataclass
from typing import List

from dataclasses_json import dataclass_json

import imswitch
from imswitch.imcommon import constants


@dataclass_json
@dataclass(frozen=True)
class _Modules:
    enabled: List[str]


def getEnabledModuleIds():
    return _modules.enabled.copy()


def setEnabledModuleIds(moduleIds):
    global _modules
    _modules = dataclasses.replace(_modules, enabled=moduleIds)
    with open(_modulesFilePath, 'w') as modulesFile:
        modulesFile.write(_modules.to_json(indent=4))


def getAvailableModules():
    moduleIdsAndNamesDict = {}
    for moduleInfo in pkgutil.iter_modules(imswitch.__path__):
        if moduleInfo.ispkg and moduleInfo.name != 'imcommon':  # Exception for imcommon
            moduleId = moduleInfo.name
            modulePkg = moduleInfo.module_finder.find_spec(moduleId).loader.load_module(moduleId)
            moduleName = modulePkg.__title__ if hasattr(modulePkg, '__title__') else moduleId
            moduleIdsAndNamesDict[moduleInfo.name] = moduleName

    return moduleIdsAndNamesDict


_configFilesDir = os.path.join(constants.rootFolderPath, 'config')
_modulesFilePath = os.path.join(_configFilesDir, 'modules.json')

if not os.path.isfile(_modulesFilePath):
    # Modules file doesn't exist, create it.
    _modules = _Modules(enabled=['imcontrol', 'imscripting'])
else:
    with open(_modulesFilePath, 'r') as modulesFile:
        _modules = _Modules.from_json(modulesFile.read(), infer_missing=True)

with open(_modulesFilePath, 'w') as modulesFile:
    modulesFile.write(_modules.to_json(indent=4))


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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
