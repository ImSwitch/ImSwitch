from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import List

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

@dataclass_json
@dataclass
class PycroManagerXYZScan:
    points : List[PycroManagerXYZPoint]