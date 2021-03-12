import os
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import Dict

import constants


# Laser control
@dataclass(frozen=True)
class LaserControlPresetLaser:
    value: str = '0'  # laser unit


@dataclass(frozen=True)
class LaserControlPreset:
    lasers: Dict[str, LaserControlPresetLaser] = field(default_factory=dict)  # map from device name to LaserControlPresetLaser


# Positioner
@dataclass(frozen=True)
class PositionerPresetPositioner:
    stepSize: str = '0.05'  # micrometres


@dataclass(frozen=True)
class PositionerPreset:
    positioners: Dict[str, PositionerPresetPositioner] = field(default_factory=dict)  # map from device name to PositionerPresetPositioner


# Scan
@dataclass(frozen=True)
class ScanPresetPositioner:
    size: str = '2'  # micrometres
    stepSize: str = '0.1'  # micrometres


@dataclass(frozen=True)
class ScanPresetTTL:
    start: str = '0'  # milliseconds
    end: str = '0'  # milliseconds


@dataclass(frozen=True)
class ScanPreset:
    positioners: Dict[str, ScanPresetPositioner] = field(default_factory=dict)  # map from device name to ScanPresetPositioner
    pulses: Dict[str, ScanPresetTTL] = field(default_factory=dict)  # map from device name to ScanPresetTTL
    dwellTime: str = '10'  # milliseconds


# uLenses
@dataclass(frozen=True)
class ULensesPreset:
    pixelSize: str = '150'
    periodicity: str = '1000'
    xOffset: str = '0'
    yOffset: str = '0'


# Alignment
@dataclass(frozen=True)
class AlignmentLinePreset:
    lineAngle: str = '30'


# Camera
@dataclass(frozen=True)
class CameraPreset:
    pixelSize: float = 0.119  # micrometres
    binning: int = 1
    mode: str = 'Full chip'
    setExposureTime: float = 0.01  # seconds
    acquisitionMode: str = 'Internal trigger'


# Recording
@dataclass(frozen=True)
class RecordingPreset:
    outputFolder: str = constants.rootFolderPath
    includeDateInOutputFolder: bool = False


# Misc options
@dataclass(frozen=True)
class MiscOptions:  # TODO: Change to e.g. "StartOptions"; only for _default.json
    lasersAndAlignmentTogether: bool = False


# Main
@dataclass_json
@dataclass(frozen=True)
class Preset:
    laserControl: LaserControlPreset = field(default_factory=LaserControlPreset)
    positioner: PositionerPreset = field(default_factory=PositionerPreset)
    scan: ScanPreset = field(default_factory=ScanPreset)

    uLenses: ULensesPreset = field(default_factory=ULensesPreset)
    alignmentLine: AlignmentLinePreset = field(default_factory=AlignmentLinePreset)

    camera: CameraPreset = field(default_factory=CameraPreset)
    recording: RecordingPreset = field(default_factory=RecordingPreset)

    miscOptions: MiscOptions = field(default_factory=MiscOptions)

    @classmethod
    def fromFile(cls, presetDir, presetFileName):
        with open(os.path.join(presetDir, presetFileName)) as presetFile:
            return cls.from_json(presetFile.read())

    @classmethod
    def getDefault(cls, presetDir):
        return cls.fromFile(presetDir, '_default.json')

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