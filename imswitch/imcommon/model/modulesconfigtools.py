import dataclasses
import importlib
import os
import pkgutil
from dataclasses import dataclass
from typing import List

from dataclasses_json import dataclass_json

import imswitch
from imswitch.imcommon.model import dirtools


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
    """ Returns the available modules as an { id: name } dict. """

    def iter_namespace(ns_pkg):
        # PyInstaller-compatible alternative to pkgutil.iter_modules
        # Source: https://github.com/pyinstaller/pyinstaller/issues/1905#issuecomment-525221546

        prefix = ns_pkg.__name__ + '.'
        for p in pkgutil.iter_modules(ns_pkg.__path__, prefix):
            yield p[1]

        # special handling when the package is bundled with PyInstaller 3.5
        # See https://github.com/pyinstaller/pyinstaller/issues/1905#issuecomment-445787510
        toc = set()
        for importer in pkgutil.iter_importers(ns_pkg.__name__.partition('.')[0]):
            if hasattr(importer, 'toc'):
                toc |= importer.toc
        for name in toc:
            if name.startswith(prefix):
                yield name

    moduleIdsAndNamesDict = {}
    for modulePkgPath in sorted(iter_namespace(imswitch)):
        if not modulePkgPath.startswith('imswitch.') or modulePkgPath.count('.') != 1:
            continue

        # E.g. "imswitch.imcontrol" -> "imcontrol"
        moduleId = modulePkgPath[modulePkgPath.rindex('.') + 1:]

        modulePkg = importlib.import_module(modulePkgPath)

        if (not hasattr(modulePkg, '__imswitch_module__') or
                modulePkg.__imswitch_module__ is not True):
            # ImSwitch modules must have __imswitch_module__ == True
            continue

        moduleName = modulePkg.__title__ if hasattr(modulePkg, '__title__') else moduleId
        moduleIdsAndNamesDict[moduleId] = moduleName

    return moduleIdsAndNamesDict


dirtools.initUserFilesIfNeeded()
_modulesFilePath = os.path.join(dirtools.UserFileDirs.Config, 'modules.json')

if not os.path.isfile(_modulesFilePath):
    # Modules file doesn't exist, create it.
    _modules = _Modules(enabled=['imcontrol', 'imscripting', 'imnotebook'])
else:
    with open(_modulesFilePath, 'r') as modulesFile:
        _modules = _Modules.from_json(modulesFile.read(), infer_missing=True)

with open(_modulesFilePath, 'w') as modulesFile:
    modulesFile.write(_modules.to_json(indent=4))


# Copyright (C) 2020-2023 ImSwitch developers
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
