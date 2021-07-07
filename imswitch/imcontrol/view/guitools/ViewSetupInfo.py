from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

from imswitch.imcontrol.model import SetupInfo


@dataclass(frozen=True)
class ROIInfo:
    x: int  # pixels
    y: int  # pixels
    w: int  # pixels
    h: int  # pixels


@dataclass(frozen=True)
class LaserPresetInfo:
    value: float


@dataclass(frozen=True)
class ScanDefaultsInfo:
    defaultScanFile: Optional[str] = None


@dataclass
class ViewSetupInfo(SetupInfo):
    # Additional ROIs available to select in detector settings
    rois: Dict[str, ROIInfo] = field(default_factory=dict)

    # Laser presets available to select (map preset name -> laser name -> laser preset info)
    laserPresets: Dict[str, Dict[str, LaserPresetInfo]] = field(default_factory=dict)

    # Default laser preset for scanning
    defaultLaserPresetForScan: Optional[str] = None

    # Which widgets are available (special values: True for all, False for none)
    availableWidgets: Union[List[str], bool] = field(default_factory=list)

    # Scan defaults
    scanDefaults: ScanDefaultsInfo = field(default_factory=ScanDefaultsInfo)

    def setROI(self, name, x, y, width, height):
        self.rois[name] = ROIInfo(x=x, y=y, w=width, h=height)

    def removeROI(self, name):
        try:
            del self.rois[name]
        except KeyError:
            pass

    def setLaserPreset(self, name, laserPresetInfos):
        self.laserPresets[name] = laserPresetInfos

    def removeLaserPreset(self, name):
        try:
            del self.laserPresets[name]
            if self.defaultLaserPresetForScan == name:
                self.setDefaultLaserPresetForScan(None)
        except KeyError:
            pass

    def setDefaultLaserPresetForScan(self, presetNameOrNone):
        self.defaultLaserPresetForScan = presetNameOrNone


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
