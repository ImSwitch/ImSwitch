from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from dataclasses_json import dataclass_json, Undefined, CatchAll


@dataclass(frozen=True)
class DeviceInfo:
    analogChannel: Optional[Union[str, int]]
    """ Channel for analog communication. ``null`` if the device is digital or
    doesn't use NI-DAQ. If an integer is specified, it will be translated to
    "Dev1/ao{analogChannel}". """

    digitalLine: Optional[Union[str, int]]
    """ Line for digital communication. ``null`` if the device is analog or
    doesn't use NI-DAQ. If an integer is specified, it will be translated to
    "Dev1/port0/line{digitalLine}". """

    managerName: str
    """ Manager class name. """

    managerProperties: Dict[str, Any]
    """ Properties to be read by the manager. """

    def getAnalogChannel(self):
        """ :meta private: """
        if isinstance(self.analogChannel, int):
            return f'Dev1/ao{self.analogChannel}'  # for backwards compatibility
        else:
            return self.analogChannel

    def getDigitalLine(self):
        """ :meta private: """
        if isinstance(self.digitalLine, int):
            return f'Dev1/port0/line{self.digitalLine}'  # for backwards compatibility
        else:
            return self.digitalLine


@dataclass(frozen=True)
class DetectorInfo(DeviceInfo):
    forAcquisition: bool = False
    """ Whether the detector is used for acquisition. """

    forFocusLock: bool = False
    """ Whether the detector is used for focus lock. """


@dataclass(frozen=True)
class LaserInfo(DeviceInfo):
    valueRangeMin: Optional[Union[int, float]]
    """ Minimum value of the laser. ``null`` if laser doesn't setting a value.
    """

    valueRangeMax: Optional[Union[int, float]]
    """ maximum value of the laser. ``null`` if laser doesn't setting a value.
    """

    wavelength: Union[int, float]
    """ Laser wavelength in nanometres. """

    freqRangeMin: Optional[int] = 0
    """ Minimum value of frequency modulation. Don't fill if laser doesn't support it. """

    freqRangeMax: Optional[int] = 0
    """ Minimum value of frequency modulation. Don't fill if laser doesn't support it. """

    freqRangeInit: Optional[int] = 0
    """ Initial value of frequency modulation. Don't fill if laser doesn't support it. """

    valueRangeStep: float = 1.0
    """ The default step size of the value range that the laser can be set to.
    """


@dataclass(frozen=True)
class PositionerInfo(DeviceInfo):
    axes: List[str]
    """ A list of axes (names) that the positioner controls. """

    isPositiveDirection: bool = True
    """ Whether the direction of the positioner is positive. """

    forPositioning: bool = False
    """ Whether the positioner is used for manual positioning. """

    forScanning: bool = False
    """ Whether the positioner is used for scanning. """

    resetOnClose: bool = True
    """ Whether the positioner should be reset to 0-position upon closing ImSwitch. """


@dataclass(frozen=True)
class RS232Info:
    managerName: str
    """ RS232 manager class name. """

    managerProperties: Dict[str, Any]
    """ Properties to be read by the RS232 manager. """


@dataclass(frozen=True)
class SLMInfo:
    monitorIdx: int
    """ Index of the monitor in the system list of monitors (indexing starts at
    0). """

    width: int
    """ Width of SLM, in pixels. """

    height: int
    """ Height of SLM, in pixels. """

    wavelength: int
    """ Wavelength of the laser line used with the SLM. """

    pixelSize: float
    """ Pixel size or pixel pitch of the SLM, in millimetres. """

    correctionPatternsDir: str
    """ Directory of .bmp images provided by Hamamatsu for flatness correction
    at various wavelengths. A combination will be chosen based on the
    wavelength. """


@dataclass(frozen=True)
class FocusLockInfo:
    camera: str
    """ Detector name. """

    positioner: str
    """ Positioner name. """

    updateFreq: int
    """ Update frequency, in milliseconds. """

    frameCropx: int
    """ Starting X position of camera frame crop. """

    frameCropy: int
    """ Starting Y position of camera frame crop. """

    frameCropw: int
    """ Width of camera frame crop. """

    frameCroph: int
    """ Height of camera frame crop. """

    swapImageAxes: bool
    """ Swap camera image axes when grabbing camera frame. """

    piKp: float
    """ Default kp value of feedback loop. """

    piKi: float
    """ Default ki value of feedback loop. """

@dataclass(frozen=True)
class AutofocusInfo:
    camera: str
    """ Detector name. """

    positioner: str
    """ Positioner name. """

    updateFreq: int
    """ Update frequency, in milliseconds. """

    frameCropx: int
    """ Starting X position of frame crop. """

    frameCropy: int
    """ Starting Y position of frame crop. """

    frameCropw: int
    """ Width of frame crop. """

    frameCroph: int
    """ Height of frame crop. """


@dataclass(frozen=True)
class ScanInfo:
    scanWidgetType: str
    """ Type of scan widget to generate: PointScan/MoNaLISA/Base/etc."""

    scanDesigner: str
    """ Name of the scan designer class to use. """

    scanDesignerParams: Dict[str, Any]
    """ Params to be read by the scan designer. """

    TTLCycleDesigner: str
    """ Name of the TTL cycle designer class to use. """

    TTLCycleDesignerParams: Dict[str, Any]
    """ Params to be read by the TTL cycle designer. """

    sampleRate: int
    """ Scan sample rate. """

    lineClockLine: Optional[Union[str, int]]
    """ Line for line clock output. ``null`` if not wanted or NI-DAQ is not used.
    If integer, it will be translated to "Dev1/port0/line{lineClockLine}".
    """

    frameStartClockLine: Optional[Union[str, int]]
    """ Line for frame startclock output. ``null`` if not wanted or NI-DAQ is not used.
    If integer, it will be translated to "Dev1/port0/line{frameStartClockLine}".
    """

    frameEndClockLine: Optional[Union[str, int]]
    """ Line for frame end clock output. ``null`` if not wanted or NI-DAQ is not used.
    If integer, it will be translated to "Dev1/port0/line{frameEndClockLine}".
    """


@dataclass(frozen=True)
class EtSTEDInfo:
    detectorFast: str
    """ Name of the STED detector to use. """

    detectorSlow: str
    """ Name of the widefield detector to use. """

    laserFast: str
    """ Name of the widefield laser to use. """


@dataclass(frozen=True)
class MicroscopeStandInfo:
    managerName: str
    """ Name of the manager to use. """

    rs232device: str
    """ Name of the rs232 device to use. """


@dataclass(frozen=True)
class EtSTEDInfo:
    swapXY: bool = False
    """ Swap X and Y axes before transforming coordinates of a detected event. """

    invertX: bool = False
    """ Invert X value before transforming coordinates of a detected event. """
    
    invertY: bool = False
    """ Invert Y value before transforming coordinates of a detected event. """


@dataclass(frozen=True)
class NidaqInfo:
    timerCounterChannel: Optional[Union[str, int]] = None
    """ Output for Counter for timing purposes. If an integer is specified, it
    will be translated to "Dev1/ctr{timerCounterChannel}". """

    startTrigger: bool = False
    """ Boolean for start triggering for sync. """

    simulation: Optional[bool] = False
    """ Boolean for allowing to run nidaq-commands without access to a nidaq card. """

    def getTimerCounterChannel(self):
        """ :meta private: """
        if isinstance(self.timerCounterChannel, int):
            return f'Dev1/ctr{self.timerCounterChannel}'  # for backwards compatibility
        else:
            return self.timerCounterChannel


@dataclass(frozen=True)
class PulseStreamerInfo:
    ipAddress: Optional[str] = None
    """ IP address of Pulse Streamer hardware. """


@dataclass(frozen=True)
class PyroServerInfo:
    name: Optional[str] = 'ImSwitchServer'
    host: Optional[str] = '127.0.0.1'
    port: Optional[int] = 54333
    active: Optional[bool] = False


@dataclass_json(undefined=Undefined.INCLUDE)
@dataclass
class SetupInfo:
    # default_factory seems to be required for the field to show up in autodocs for deriving classes

    detectors: Dict[str, DetectorInfo] = field(default_factory=dict)
    """ Detectors in this setup. This is a map from unique detector names to
    DetectorInfo objects. """

    lasers: Dict[str, LaserInfo] = field(default_factory=dict)
    """ Lasers in this setup. This is a map from unique laser names to
    LaserInfo objects. """

    positioners: Dict[str, PositionerInfo] = field(default_factory=dict)
    """ Positioners in this setup. This is a map from unique positioner names
    to DetectorInfo objects. """

    rs232devices: Dict[str, RS232Info] = field(default_factory=dict)
    """ RS232 connections in this setup. This is a map from unique RS232
    connection names to RS232Info objects. Some detector/laser/positioner
    managers will require a corresponding RS232 connection to be referenced in
    their properties.
    """

    slm: Optional[SLMInfo] = field(default_factory=lambda: None)
    """ SLM settings. Required to be defined to use SLM functionality. """

    focusLock: Optional[FocusLockInfo] = field(default_factory=lambda: None)
    """ Focus lock settings. Required to be defined to use focus lock
    functionality. """
    
    autofocus: Optional[AutofocusInfo] = field(default_factory=lambda: None)
    """ Autofocus settings. Required to be defined to use autofocus 
    functionality. """

    scan: Optional[ScanInfo] = field(default_factory=lambda: None)
    """ Scan settings. Required to be defined to use scan functionality. """

    rotators: Optional[Dict[str, DeviceInfo]] = field(default_factory=lambda: None)
    """ Standa motorized rotator mounts settings. Required to be defined to use rotator functionality. """

    microscopeStand: Optional[MicroscopeStandInfo] = field(default_factory=lambda: None)
    """ Microscope stand settings. Required to be defined to use MotCorr widget. """

    etSTED: Optional[EtSTEDInfo] = field(default_factory=lambda: None)
    """ EtSTED stand settings. """

    nidaq: NidaqInfo = field(default_factory=NidaqInfo)
    """ NI-DAQ settings. """

    pulseStreamer: PulseStreamerInfo = field(default_factory=PulseStreamerInfo)
    """ Pulse Streamer settings. """

    pyroServerInfo: PyroServerInfo = field(default_factory=PyroServerInfo)

    _catchAll: CatchAll = None

    def getDevice(self, deviceName):
        """ Returns the DeviceInfo for a specific device.

        :meta private:
        """
        return self.getAllDevices()[deviceName]

    def getTTLDevices(self):
        """ Returns DeviceInfo from all devices that have a digitalLine.

        :meta private:
        """
        devices = {}
        i = 0
        for deviceInfos in self.lasers, self.detectors:
            deviceInfosCopy = deviceInfos.copy()
            for item in list(deviceInfosCopy):
                if deviceInfosCopy[item].getDigitalLine() is None:
                    del deviceInfosCopy[item]
            devices.update(deviceInfosCopy)
            i += 1

        return devices

    def getDetectors(self):
        """ :meta private: """
        devices = {}
        for deviceInfos in self.detectors:
            devices.update(deviceInfos)

        return devices

    def getAllDevices(self):
        """ :meta private: """
        devices = {}
        for deviceInfos in self.lasers, self.detectors, self.positioners:
            devices.update(deviceInfos)

        return devices


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
