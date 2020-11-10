from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ROIInfo:
    x: int  # pixels
    y: int  # pixels
    w: int  # pixels
    h: int  # pixels


@dataclass(frozen=True)
class DeviceInfo:
    analogChannel: Optional[int]  # null if the device is digital
    digitalLine: Optional[int]  # null if the device is analog


@dataclass(frozen=True)
class LaserInfo(DeviceInfo):
    digitalDriver: Optional[str]  # null if the laser is analog
    digitalPorts: Optional[List[str]]  # null if the laser is analog
    color: str  # hex code

    valueRangeMin: int  # mW if digital, V if analog
    valueRangeMax: int  # mW if digital, V if analog
    valueRangeStep: int  # mW if digital, V if analog


@dataclass(frozen=True)
class StagePiezzoInfo(DeviceInfo):
    conversionFactor: float
    minVolt: int  # piezzoconcept
    maxVolt: int  # piezzoconcept


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
class AvailableWidgetsInfo:
    AlignWidgetXY: bool = True
    AlignWidgetAverage: bool = True
    AlignmentLineWidget: bool = True
    BeadRecWidget: bool = True
    FFTWidget: bool = True
    ULensesWidget: bool = True


@dataclass(frozen=True)
class DesignersInfo:
    stageScanDesigner: str  # name of the stage scan designer class to use
    TTLCycleDesigner: str  # name of the TTL cycle designer class to use


@dataclass_json
@dataclass(frozen=True)
class SetupInfo:
    cameras: Dict[str, DeviceInfo]  # map from device ID to DeviceInfo
                                    # NOTE: Only 1 camera is currently supported!
    lasers: Dict[str, LaserInfo]  # map from device ID to LaserInfo
    stagePiezzos: Dict[str, StagePiezzoInfo]  # map from device ID to StagePiezzoInfo
    scan: ScanInfo

    rois: Dict[str, ROIInfo]  # additional ROIs available to select in camera settings

    availableWidgets: AvailableWidgetsInfo  # which widgets are available
    designers: DesignersInfo

    def getDevice(self, deviceId):
        """ Returns the DeviceInfo for a specific device. """
        return self.getAllDevices()[deviceId]

    def getTTLDevices(self):
        devices = {}
        for deviceInfos in self.lasers, self.cameras:
            devices.update(deviceInfos)

        return devices

    def getAllDevices(self):
        devices = {}
        for deviceInfos in self.lasers, self.cameras, self.stagePiezzos:
            devices.update(deviceInfos)

        return devices


