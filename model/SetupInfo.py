from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined, CatchAll
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class DeviceInfo:
    analogChannel: Optional[int]  # null if the device is digital
    digitalLine: Optional[int]  # null if the device is analog


@dataclass(frozen=True)
class DetectorInfo(DeviceInfo):
    managerName: str  # manager class name
    managerProperties: Dict[str, Any]  # properties to be read by manager


@dataclass(frozen=True)
class LaserInfo(DeviceInfo):
    digitalDriver: Optional[str]  # null if the laser is analog
    digitalPorts: Optional[List[str]]  # null if the laser is analog
    wavelength: str  # hex code

    valueRangeMin: Optional[int]  # mW if digital, V if analog, null if binary
    valueRangeMax: Optional[int]  # mW if digital, V if analog, null if binary
    valueRangeStep: Optional[int]  # mW if digital, V if analog, null if binary

    def getUnit(self):
        return 'mW' if self.digitalDriver is not None else 'V'

    def isFullDigital(self):
        return (self.digitalDriver is not None and self.digitalPorts is not None
                and len(self.digitalPorts) > 0)

    def isAotf(self):
        return not self.isFullDigital() and self.analogChannel is not None

    def isBinary(self):
        return not self.isFullDigital() and not self.isAotf()


@dataclass(frozen=True)
class PositionerInfo(DeviceInfo):
    managerName: str  # manager class name
    managerProperties: Dict[str, Any]  # properties to be read by manager


@dataclass(frozen=True)
class ScanInfoStage:
    sampleRate: int
    returnTime: float


@dataclass(frozen=True)
class ScanInfoTTL:
    sampleRate: int


@dataclass(frozen=True)
class ScanInfo:
    stage: ScanInfoStage
    ttl: ScanInfoTTL


@dataclass(frozen=True)
class DesignersInfo:
    stageScanDesigner: str  # name of the stage scan designer class to use
    TTLCycleDesigner: str  # name of the TTL cycle designer class to use


@dataclass_json(undefined=Undefined.INCLUDE)
@dataclass(frozen=True)
class SetupInfo:
    detectors: Dict[str, DetectorInfo]  # map from device ID to CameraInfo

    lasers: Dict[str, LaserInfo]  # map from device ID to LaserInfo
    positioners: Dict[str, PositionerInfo]  # map from device ID to PositionerInfo
    scan: ScanInfo

    designers: DesignersInfo

    _catchAll: CatchAll = None

    def getDevice(self, deviceName):
        """ Returns the DeviceInfo for a specific device. """
        return self.getAllDevices()[deviceName]

    def getTTLDevices(self):
        devices = {}
        for deviceInfos in self.lasers, self.detectors:
            devices.update(deviceInfos)

        return devices

    def getAllDevices(self):
        devices = {}
        for deviceInfos in self.lasers, self.detectors, self.positioners:
            devices.update(deviceInfos)

        return devices
