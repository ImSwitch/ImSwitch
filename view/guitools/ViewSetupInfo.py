from dataclasses import dataclass, field
from typing import Dict

from model.SetupInfo import SetupInfo


@dataclass(frozen=True)
class ROIInfo:
    x: int  # pixels
    y: int  # pixels
    w: int  # pixels
    h: int  # pixels


@dataclass(frozen=True)
class AvailableWidgetsInfo:
    AlignWidgetXY: bool = True
    AlignWidgetAverage: bool = True
    AlignmentLineWidget: bool = True
    BeadRecWidget: bool = True
    FFTWidget: bool = True
    ULensesWidget: bool = True


@dataclass(frozen=True)
class ViewSetupInfo(SetupInfo):
    # additional ROIs available to select in camera settings
    rois: Dict[str, ROIInfo] = field(default_factory=list)

    # which widgets are available
    availableWidgets: AvailableWidgetsInfo = field(default_factory=AvailableWidgetsInfo)

    def setROI(self, name, x, y, width, height):
        self.rois[name] = ROIInfo(x=x, y=y, w=width, h=height)

    def removeROI(self, name):
        try:
            del self.rois[name]
        except KeyError:
            pass
