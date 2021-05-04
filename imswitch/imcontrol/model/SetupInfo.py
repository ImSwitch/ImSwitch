from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, Undefined, CatchAll
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class DeviceInfo:
    analogChannel: Optional[int]  # null if the device is digital or doesn't use Nidaq
    digitalLine: Optional[int]  # null if the device is analog or doesn't use Nidaq

    managerName: str  # manager class name
    managerProperties: Dict[str, Any]  # properties to be read by manager


@dataclass(frozen=True)
class DetectorInfo(DeviceInfo):
    forAcquisition: bool = False
    forFocusLock: bool = False


@dataclass(frozen=True)
class LaserInfo(DeviceInfo):
    wavelength: str  # hex code
    valueRangeMin: Optional[int]  # null if auto-detector or laser is binary
    valueRangeMax: Optional[int]  # null if auto-detector or laser is binary
    valueRangeStep: float = 1.0


@dataclass(frozen=True)
class PositionerInfo(DeviceInfo):
    axes: List[str]
    isPositiveDirection: bool = True
    forPositioning: bool = False
    forScanning: bool = False


@dataclass(frozen=True)
class RS232Info:
    managerName: str  # manager class name
    managerProperties: Dict[str, Any]  # properties to be read by manager


@dataclass(frozen=True)
class SLMInfo:
    monitorIdx: int
    width: int
    height: int
    wavelength: int
    pixelSize: float
    angleMount: float
    correctionPatternsDir: str


@dataclass(frozen=True)
class FocusLockInfo:
    camera: str  # detector name
    positioner: str  # positioner name
    updateFreq: int
    frameCropx: int
    frameCropy: int
    frameCropw: int
    frameCroph: int


@dataclass(frozen=True)
class ScanInfo:
    scanDesigner: str  # name of the scan designer class to use
    scanDesignerParams: Dict[str, Any]  # properties to be read by ScanDesigner
    TTLCycleDesigner: str  # name of the TTL cycle designer class to use
    TTLCycleDesignerParams: Dict[str, Any]  # properties to be read by TTLCycleDesigner
    sampleRate: int  # scan sample rate

@dataclass(frozen=True)
class NidaqInfo:
    counterChannel: int  # Output for Counter for timing purposes
    startTrigger: bool = False # Boolean for start triggering for sync


@dataclass_json(undefined=Undefined.INCLUDE)
@dataclass(frozen=True)
class SetupInfo:
    detectors: Dict[str, DetectorInfo] = field(default_factory=dict)  # map from device name to CameraInfo
    lasers: Dict[str, LaserInfo] = field(default_factory=dict)  # map from device name to LaserInfo
    positioners: Dict[str, PositionerInfo] = field(default_factory=dict)  # map from device name to PositionerInfo
    rs232devices: Dict[str, RS232Info] = field(default_factory=dict)  # map from device name to RS232Info

    slm: Optional[SLMInfo] = None
    focusLock: Optional[FocusLockInfo] = None

    scan: ScanInfo = field(default_factory=ScanInfo)

    nidaq: NidaqInfo = field(default_factory=dict)

    _catchAll: CatchAll = None

    def getDevice(self, deviceName):
        """ Returns the DeviceInfo for a specific device. """
        return self.getAllDevices()[deviceName]

    def getTTLDevices(self):
        """ Returns DeviceInfo from all devices that have a digitalLine. """
        devices = {}
        i = 0
        for deviceInfos in self.lasers, self.detectors:
            deviceInfosCopy = deviceInfos.copy()
            for item in list(deviceInfosCopy):
                if deviceInfosCopy[item].digitalLine is None:
                    del deviceInfosCopy[item]
            devices.update(deviceInfosCopy)
            i += 1

        return devices

    def getDetectors(self):
        devices = {}
        for deviceInfos in self.detectors:
            devices.update(deviceInfos)

        return devices

    def getAllDevices(self):
        devices = {}
        for deviceInfos in self.lasers, self.detectors, self.positioners:
            devices.update(deviceInfos)

        return devices
    

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
