from numpy import ndarray, array
from dataclasses import dataclass, field, asdict
from dataclasses_json import dataclass_json
from typing import Union, List
from enum import Enum, IntFlag, auto
from typing import Callable

ACQUISITION_ORDER_DEFAULT = "tcpz"

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

    def __len__(self) -> int:
        return len(self.points)
    
    def __post_init__(self) -> None:
        # Pycro-Manager notification ID includes the label (when provided);
        # we keep track of the index for UI updates (progress bar)
        self.__labelsIdx = {point.Label : i for point, i in zip(self.points, range(len(self.points)))}  
    
    def labels(self) -> Union[None, List[str]]:
        """ Returns the scan labels as list of strings, or None if all labels are empty.
        """
        labelList = [point.Label for point in self.points]
        listEmpty = all([label == "" for label in labelList])
        return labelList if not listEmpty else None
    
    def getIndex(self, idx: Union[str, int]) -> int:
        return idx if type(idx) == int else self.__labelsIdx[idx]

@dataclass_json
@dataclass
class PycroManagerXYZScan:
    points : List[PycroManagerXYZPoint]
    
    def __array__(self) -> ndarray:
        return array([(point.X, point.Y, point.Z) for point in self.points])
    
    def __len__(self) -> int:
        return len(self.points)

    def __post_init__(self) -> None:
        # Pycro-Manager notification ID includes the label (when provided);
        # we keep track of the index for UI updates (progress bar)
        self.__labelsIdx = {point.Label : i for point, i in zip(self.points, range(len(self.points)))}  
    
    def labels(self) -> Union[None, List[str]]:
        """ Returns the scan labels as list of strings, or None if all labels are empty.
        """
        labelList = [point.Label for point in self.points]
        listEmpty = all([label == "" for label in labelList])
        return labelList if not listEmpty else None
    
    def getIndex(self, idx: Union[str, int]) -> int:
        return idx if type(idx) == int else self.__labelsIdx[idx]

@dataclass
class PycroManagerHookContainer:
    image_process_fn : Callable = field(default_factory=lambda: None)
    event_generation_hook_fn : Callable = field(default_factory=lambda: None)
    pre_hardware_hook_fn : Callable = field(default_factory=lambda: None)
    post_hardware_hook_fn : Callable = field(default_factory=lambda: None)
    post_camera_hook_fn : Callable = field(default_factory=lambda: None)
    notification_callback_fn : Callable = field(default_factory=lambda: None)
    image_saved_fn : Callable = field(default_factory=lambda: None)

_hookContainer = PycroManagerHookContainer()

def set_as_hook(hook_type: str) -> Callable:
    """ Decorator to register an hook function
    to the PycroManager acquisition engine.
    See [here](https://pycro-manager.readthedocs.io/en/latest/acq_hooks.html)
    for supported hook types.

    Args:
        hook_type (`str`): type of hook to register.
    """
    def wrapper(f: Callable) -> Callable:
        if hasattr(_hookContainer, hook_type):
            setattr(_hookContainer, hook_type, f)
    return wrapper

def getHooksDictionary() -> dict:
    return asdict(_hookContainer)