from dataclasses import dataclass, field
from typing import Dict, Optional

from imcontrol.model import SetupInfo


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
class WidgetAvailabilityInfo:
    AlignWidgetXY: bool = True
    AlignWidgetAverage: bool = True
    AlignmentLineWidget: bool = True
    BeadRecWidget: bool = True
    FFTWidget: bool = True
    ULensesWidget: bool = True


@dataclass(frozen=True)
class WidgetLayoutInfo:
    lasersAndAlignmentInSingleDock: bool = False


@dataclass(frozen=True)
class ViewSetupInfo(SetupInfo):
    # additional ROIs available to select in detector settings
    rois: Dict[str, ROIInfo] = field(default_factory=list)

    # which widgets are available
    availableWidgets: WidgetAvailabilityInfo = field(default_factory=WidgetAvailabilityInfo)

    # widget layout
    widgetLayout: WidgetLayoutInfo = field(default_factory=WidgetLayoutInfo)

    # scan defaults
    scanDefaults: ScanDefaultsInfo = field(default_factory=ScanDefaultsInfo)

    def setROI(self, name, x, y, width, height):
        self.rois[name] = ROIInfo(x=x, y=y, w=width, h=height)

    def removeROI(self, name):
        try:
            del self.rois[name]
        except KeyError:
            pass
