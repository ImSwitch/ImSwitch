import glob
import os
from pathlib import Path
from dataclasses import dataclass
from dataclasses_json import dataclass_json

import constants


@dataclass_json
@dataclass(frozen=True)
class Options:
    setupFileName: str  # JSON file that contains setup info


_configFilesDir = os.path.join(constants.rootFolderPath, 'config_files')

_optionsFilePath = os.path.join(_configFilesDir, 'options.json')
if not os.path.isfile(_optionsFilePath):
    with open(_optionsFilePath, 'w') as optionsFile:
        # Options file doesn't exist, create it. TODO: The user should pick the default config
        _options = Options(
            setupFileName=Path(glob.glob(os.path.join(_configFilesDir, '*.json'))[0]).name
        )
        optionsFile.write(_options.to_json())
else:
    with open(_optionsFilePath) as optionsFile:
        _options = Options.from_json(optionsFile.read(), infer_missing=True)


def loadSetupInfo(setupInfoType):
    with open(os.path.join(_configFilesDir, _options.setupFileName)) as setupFile:
        return setupInfoType.from_json(setupFile.read(), infer_missing=True)


def saveSetupInfo(setupInfo):
    with open(os.path.join(_configFilesDir, _options.setupFileName), 'w') as setupFile:
        setupFile.write(setupInfo.to_json(indent=4))
