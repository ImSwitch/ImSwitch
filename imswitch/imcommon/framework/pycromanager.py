from numpy import ndarray, array
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import Union, List
from enum import Enum, IntFlag, auto

class PycroManagerAcquisitionEngine(Enum):
    Acquistion = 1
    # TODO: implement XY tiled acquisition
    # XYTiledAcquisition = 2 

class PycroManagerAcquisitionMode(IntFlag):
    Absent = 0
    Frames = auto()
    Time = auto()
    ZStack = auto()
    XYList = auto()
    XYZList = auto()

@dataclass(frozen=True)
class PycroManagerZStack:
    start: float
    end: float
    step: float

@dataclass(frozen=True)
class PycroManagerXYPoint:
    X: float
    Y: float
    Label: str = field(default_factory=str)
    
@dataclass(frozen=True)
class PycroManagerXYZPoint:
    X: float
    Y: float
    Z: float
    Label: str = field(default_factory=str)

@dataclass_json
@dataclass
class PycroManagerXYScan:
    points : List[PycroManagerXYPoint]
    
    def __array__(self) -> ndarray:
        return array([(point.X, point.Y) for point in self.points])
    
    def labels(self) -> Union[None, List[str]]:
        """ Returns the scan labels as list of strings, or None if all labels are empty.
        """
        labelList = [point.Label for point in self.points]
        listEmpty = all([label == "" for label in labelList])
        return labelList if not listEmpty else None

@dataclass_json
@dataclass
class PycroManagerXYZScan:
    points : List[PycroManagerXYZPoint]
    
    def __array__(self) -> ndarray:
        return array([(point.X, point.Y, point.Z) for point in self.points])
    
    def labels(self) -> Union[None, List[str]]:
        """ Returns the scan labels as list of strings, or None if all labels are empty.
        """
        labelList = [point.Label for point in self.points]
        listEmpty = all([label == "" for label in labelList])
        return labelList if not listEmpty else None