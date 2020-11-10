from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import Dict, Union

import constants


# Laser control
@dataclass(frozen=True)
class LaserControlPresetLaser:
    value: str = '0'  # laser unit


@dataclass(frozen=True)
class LaserControlPreset:
    lasers: Dict[str, LaserControlPresetLaser] = field(default_factory=dict)  # map from device ID to LaserControlPresetLaser


# Positioner
@dataclass(frozen=True)
class PositionerPresetStagePiezzo:
    stepSize: str = '0.05'  # micrometres


@dataclass(frozen=True)
class PositionerPreset:
    stagePiezzos: Dict[str, PositionerPresetStagePiezzo] = field(default_factory=dict)  # map from device ID to PositionerPresetStagePiezzo


# Scan
@dataclass(frozen=True)
class ScanPresetStagePiezzo:
    size: str = '2'  # micrometres
    stepSize: str = '0.1'  # micrometres


@dataclass(frozen=True)
class ScanPresetTTL:
    start: str = '0'  # milliseconds
    end: str = '10'  # milliseconds


@dataclass(frozen=True)
class ScanPreset:
    stagePiezzos: Dict[str, ScanPresetStagePiezzo] = field(default_factory=dict)  # map from device ID to ScanPresetStagePiezzo
    pulses: Dict[str, ScanPresetTTL] = field(default_factory=dict)  # map from device ID to ScanPresetTTL
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
class MiscOptions:
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
