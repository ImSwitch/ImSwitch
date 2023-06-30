from typing import Any, Dict, Tuple
from numpy import ndarray, zeros
from imswitch.imcommon.model import initLogger
from dataclasses import dataclass
from imswitch.imcontrol.model.managers.detectors.DetectorManager import DetectorManager
from imswitch.imcommon.framework import Signal, SignalInterface, Runnable
from enum import Enum
from logging import LoggerAdapter

class RecMode(Enum):
    SpecFrames = 1
    SpecTime = 2
    ScanOnce = 3
    ScanLapse = 4
    UntilStop = 5

class SaveMode(Enum):
    Disk = 1
    RAM = 2
    DiskAndRAM = 3
    Numpy = 4

@dataclass(frozen=True)
class StreamingInfo:
    filePath: str # filepath to save the data to disk.
    virtualFile: Any # file-like object to save the data to RAM
    detector: DetectorManager # reference to detector from which to stream data.
    storeID: int # unique identifier for the storer.
    recMode: RecMode # recording mode to use.
    saveMode: SaveMode # saving mode to use (disk, RAM or both).
    attrs: Dict[str, str] # dictionary of shared attributes to store.
    totalFrames: int # total number of frames to record (only for `RecMode.SpecFrames`).
    totalTime: float # total time to record (only for `RecMode.SpecTime`).

class StorerSignals(SignalInterface):
    finished = Signal()
    frameNumberUpdate = Signal(str, int) # channel, frameNumber
    timeUpdate = Signal(str, float) # channel, seconds
    sigMemRecAvailable = Signal(
        str, object, object, bool
    )  # (name, virtualFile, filePath, savedToDisk)


class StorerManager(Runnable):
    """ StorerManager is an abstract `Runnable` type class for implementing a data streaming manager.
    It provides the following signals:
    
    - `frameNumberUpdate(channel: `str`, frameNumber: `int`)`: emitted when `frameNumber` coming from `channel` detector have been written to memory;
    - `timeUpdate(channel: `str`, timeCount: `float`)`: emitted when new frames coming from `channel` detector have been written to memory after `timeCount` seconds;
    - `sigMemRecAvailable`: emitted when a memory recording has been saved to RAM; the content of the signals are the following (in order):
        - `name`: name of the detector;
        - `virtualFile`: file-like object containing the data;
        - `filePath`: filepath to the data (in case it has been saved to disk as well);
        - `savedToDisk`: `True` if the data has been saved to disk, `False` otherwise.

    Args:
        stramingInfo (`StreamingInfo`): streaming information dataclass.
    """
    def __init__(self, stramingInfo: StreamingInfo) -> None:
        self.signals = StorerSignals()
        self.streamInfo = stramingInfo
        self.frameCount = 0
        self.timeCount = 0.0
        self.record = False
        self.__logger = initLogger(self)
        super(StorerManager, self).__init__()
    
    @property
    def logger(self) -> LoggerAdapter:
        """ Returns the local logger instance.
        """
        return self.__logger

    @classmethod
    def saveSnap(self, images: Dict[str, ndarray], attrs: Dict[str, str], **kwargs) -> None:
        """ Collects input image snapshots and stores them according to the spec of the storer.

        Args:
            - images (`Dict[str, ndarray]`): dictionary of collected images to store (key: channel name, value: image);
            - attrs (`Dict[str, str]`): dictionary of shared attributes to store.
            - kwargs (`dict`): additional arguments:
                - filePath (`str`): filepath to save the data to disk;
                - detectors (`dict[str, DetectorManager]`): dictionary with references to the channel's detector;
                - acquisitionDate (`str`): timestamp of the acquisition.
        """
        raise NotImplementedError
    
    def stream(self, recMode: RecMode, saveMode: SaveMode, attrs: Dict[str, str], **kwargs) -> None:
        """ Starts streaming data from detector and storing it according to the spec of the storer. 

        Args:
            - recMode (`RecMode`): recording mode to use.
            - saveMode (`SaveMode`): saving mode to use (disk, RAM or both).
            - attrs (`Dict[str, str]`): dictionary of shared attributes to store.
            - kwargs (`dict`): additional arguments:
                - totalFrames (`int`): total number of frames to record (only for `RecMode.SpecFrames`);
                - totalTime (`float`): total number of seconds to record (only for `RecMode.SpecTime`);
        """
        raise NotImplementedError

    def unpackChunk(self) -> Tuple[ndarray, ndarray]:
        """ Checks if the value returned by getChunk is a tuple (packing the recorded chunk and the associated time points).
        If the return type is only the recorded stack, a zero array is generated with the same length of 
        the recorded chunk.

        Returns:
            tuple: a 2-element tuple with the recorded chunk and the single data points associated with each frame.
        """
        chunk = self.streamInfo.detector.getChunk()
        if type(chunk) == tuple:
            return chunk
        else: # type is np.ndarray
            chunk = (chunk, zeros(len(chunk)))
        return chunk
    
    def run(self) -> None:
        kwargs = dict(totalFrames=self.streamInfo.totalFrames, totalTime=self.streamInfo.totalTime)
        self.stream(self.streamInfo.recMode, self.streamInfo.saveMode, self.streamInfo.attrs, **kwargs)