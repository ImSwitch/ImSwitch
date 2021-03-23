import glob
import os
from dataclasses import dataclass
from pathlib import Path

from dataclasses_json import dataclass_json

import constants


@dataclass_json
@dataclass(frozen=True)
class Options:
    setupFileName: str  # JSON file that contains setup info


def loadSetupInfo(setupInfoType):
    with open(os.path.join(_setupFilesDir, _options.setupFileName)) as setupFile:
        return setupInfoType.from_json(setupFile.read(), infer_missing=True)


def saveSetupInfo(setupInfo):
    with open(os.path.join(_setupFilesDir, _options.setupFileName), 'w') as setupFile:
        setupFile.write(setupInfo.to_json(indent=4))


_configFilesDir = os.path.join(constants.rootFolderPath, 'config')
_setupFilesDir = os.path.join(_configFilesDir, 'imcontrol_setups')
_optionsFilePath = os.path.join(_configFilesDir, 'imcontrol_options.json')

if not os.path.isfile(_optionsFilePath):
    with open(_optionsFilePath, 'w') as optionsFile:
        # Options file doesn't exist, create it. TODO: The user should pick the default config
        _options = Options(
            setupFileName=Path(glob.glob(os.path.join(_setupFilesDir, '*.json'))[0]).name
        )
        optionsFile.write(_options.to_json())
else:
    with open(_optionsFilePath) as optionsFile:
        _options = Options.from_json(optionsFile.read(), infer_missing=True)


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
