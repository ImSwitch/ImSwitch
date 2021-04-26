from dataclasses import dataclass, field
from typing import Dict, List, Optional

from imswitch.imcontrol.model import SetupInfo


@dataclass(frozen=True)
class ROIInfo:
    x: int  # pixels
    y: int  # pixels
    w: int  # pixels
    h: int  # pixels


@dataclass(frozen=True)
class ScanDefaultsInfo:
    defaultScanFile: Optional[str] = None


@dataclass(frozen=True)
class ViewSetupInfo(SetupInfo):
    # additional ROIs available to select in detector settings
    rois: Dict[str, ROIInfo] = field(default_factory=dict)

    # which widgets are available
    availableWidgets: List[str] = field(default_factory=list)

    # scan defaults
    scanDefaults: ScanDefaultsInfo = field(default_factory=ScanDefaultsInfo)


    def setROI(self, name, x, y, width, height):
        self.rois[name] = ROIInfo(x=x, y=y, w=width, h=height)

    def removeROI(self, name):
        try:
            del self.rois[name]
        except KeyError:
            pass


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
