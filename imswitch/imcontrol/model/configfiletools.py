import glob
import os
from pathlib import Path

from imswitch.imcommon.model import dirtools
from .Options import Options


def getSetupList():
    return [Path(file).name for file in glob.glob(os.path.join(_setupFilesDir, '*.json'))]


def loadSetupInfo(options, setupInfoType):
    with open(os.path.join(_setupFilesDir, options.setupFileName)) as setupFile:
        return setupInfoType.from_json(setupFile.read(), infer_missing=True)


def saveSetupInfo(options, setupInfo):
    with open(os.path.join(_setupFilesDir, options.setupFileName), 'w') as setupFile:
        setupFile.write(setupInfo.to_json(indent=4))


def loadOptions():
    global _options

    if _options is not None:
        return _options, False

    optionsDidNotExist = False
    if not os.path.isfile(_optionsFilePath):
        _options = Options(
            setupFileName=getSetupList()[0]
        )
        optionsDidNotExist = True
    else:
        with open(_optionsFilePath, 'r') as optionsFile:
            _options = Options.from_json(optionsFile.read(), infer_missing=True)

    return _options, optionsDidNotExist


def saveOptions(options):
    global _options

    _options = options
    with open(_optionsFilePath, 'w') as optionsFile:
        optionsFile.write(_options.to_json(indent=4))


dirtools.initUserFilesIfNeeded()
_setupFilesDir = os.path.join(dirtools.UserFileDirs.Root, 'imcontrol_setups')
os.makedirs(_setupFilesDir, exist_ok=True)
_optionsFilePath = os.path.join(dirtools.UserFileDirs.Config, 'imcontrol_options.json')
_debugLogDir = os.path.join(dirtools.UserFileDirs.Root, 'imcontrol_debug_logs')
os.makedirs(_debugLogDir, exist_ok=True)

_options = None


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
