from numpy import ndarray, array
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import Union, List
from enum import Enum

class PycroManagerAcquisitionEngine(Enum):
    Acquistion = 1
    # TODO: implement XY tiled acquisition
    # XYTiledAcquisition = 2 

class PycroManagerAcquisitionMode(Enum):
    Frames = 1
    Time = 2
    ZStack = 3
    XYList = 4
    XYZList = 5

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