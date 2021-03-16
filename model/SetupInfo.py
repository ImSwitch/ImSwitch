from dataclasses import dataclass
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
    pass


@dataclass(frozen=True)
class LaserInfo(DeviceInfo):
    wavelength: str  # hex code
    valueRangeMin: Optional[int]  # null if auto-detector or laser is binary
    valueRangeMax: Optional[int]  # null if auto-detector or laser is binary
    valueRangeStep: Optional[float]


@dataclass(frozen=True)
class PositionerInfo(DeviceInfo):
    pass


@dataclass(frozen=True)
class RS232Info:
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
class SLMInfo:
    monitorIdx: int
    width: int
    height: int
    wavelength: int
    pixelsize: float
    angle_mount: float
    correctionPatternsDir: str


@dataclass(frozen=True)
class FocusLockInfo:
    camera: str
    positioner: str
    updateFreq: int
    frameCrop_left: int
    frameCrop_right: int
    frameCrop_top: int
    frameCrop_bottom: int


@dataclass(frozen=True)
class DesignersInfo:
    scanDesigner: str  # name of the scan designer class to use
    TTLCycleDesigner: str  # name of the TTL cycle designer class to use


@dataclass_json(undefined=Undefined.INCLUDE)
@dataclass(frozen=True)
class SetupInfo:
    detectors: Dict[str, DetectorInfo]  # map from device name to CameraInfo

    lasers: Dict[str, LaserInfo]  # map from device name to LaserInfo
    positioners: Dict[str, PositionerInfo]  # map from device name to PositionerInfo
    rs232devices: Dict[str, RS232Info]  # map from device name to RS232Info
    scan: ScanInfo
    slm: SLMInfo
    focusLock: FocusLockInfo

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
