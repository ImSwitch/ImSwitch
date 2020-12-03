import os
from dataclasses import dataclass
from dataclasses_json import dataclass_json

import constants


@dataclass_json
@dataclass(frozen=True)
class Options:
    setupFileName: str  # JSON file that contains setup info


_configFilesDir = os.path.join(constants.rootFolderPath, 'config_files')

with open(os.path.join(_configFilesDir, 'options.json')) as optionsFile:
    _options = Options.from_json(optionsFile.read(), infer_missing=True)


def loadSetupInfo(setupInfoType):
    with open(os.path.join(_configFilesDir, _options.setupFileName)) as setupFile:
        return setupInfoType.from_json(setupFile.read(), infer_missing=True)


def saveSetupInfo(setupInfo):
    with open(os.path.join(_configFilesDir, _options.setupFileName), 'w') as setupFile:
        setupFile.write(setupInfo.to_json(indent=4))
