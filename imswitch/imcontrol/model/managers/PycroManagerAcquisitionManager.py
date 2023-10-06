from pycromanager import Core, Acquisition
from imswitch.imcommon.framework import Signal, SignalInterface, Thread, Worker
from imswitch.imcommon.model import initLogger, SaveMode
from tifffile.tifffile import TiffWriter
import os
import numpy as np

class AcquisitionWorker(Worker):
    
    def __init__(self):
        super().__init__()
    
    def run(self, **recordingArgs) -> None:
        pass
        
class PycroManagerAcquisitionManager(SignalInterface):
    
    sigRecordingStarted = Signal()
    sigRecordingEnded = Signal()
    sigRecordingFrameNumUpdated = Signal(int)  # (frameNumber)
    sigRecordingTimeUpdated = Signal(int)  # (recTime)
    sigMemorySnapAvailable = Signal(
        str, np.ndarray, object, bool
    )  # (name, image, filePath, savedToDisk)
    sigMemoryRecordingAvailable = Signal(
        str, object, object, bool
    )  # (name, file, filePath, savedToDisk)
    
    def __init__(self, detectorsManager):
        super().__init__()
        self.__logger = initLogger(self)
        self.__detectorsManager = detectorsManager
        self.__core = Core()
        self.__acquisitionThread = Thread()
        self.__acquisitionWorker = AcquisitionWorker()
        self.__acquisitionWorker.moveToThread(self.__acquisitionThread)
    
    def snap(self, folder: str, savename: str, saveMode: SaveMode, attrs: dict):
        """ Snaps an image calling an instance of the Pycro-Manager backend Core. 
        """
        # TODO: support multiple extension types?
        extension = ".ome.tiff"
        savename += extension
        fullPath = os.path.join(folder, savename)

        self.__core.snap_image()
        tagged_image = self.__core.get_tagged_image()
        pixels = np.reshape(tagged_image.pix, newshape=(1, tagged_image.tags['Height'], tagged_image.tags['Width']))
    	
        # TODO: add missing metadata fields
        metadata = {
                "axes" : "TYX",
                "PhysicalSizeX" : self.__core.get_pixel_size_um(),
                "PhysicalSizeXUnit" : "µm",
                "PhysicalSizeY" : self.__core.get_pixel_size_um(),
                "PhysicalSizeYUnit" : "µm",
                "PhysicalSizeZ" : 1,
                "PhysicalSizeZUnit" : "µm",
                "TimeIncrement": self.__core.get_exposure(),
                "TimeIncrementUnit": "ms",
        }

        if saveMode == SaveMode.Disk or saveMode == SaveMode.DiskAndRAM:
            self.__logger.info("Snapping to %s", fullPath)
            with TiffWriter(fullPath, ome=True) as tif:
                tif.write(pixels, metadata=metadata, software="ImSwitch")

        if saveMode == SaveMode.RAM or saveMode == SaveMode.DiskAndRAM:
            name = self.__core.get_camera_device()
            self.sigMemorySnapAvailable.emit(name, pixels, savename, saveMode == SaveMode.DiskAndRAM)
    
    @property
    def currentDetector(self) -> str:
        return self.__core.get_camera_device()
    
    def startRecording(self, **recordingArgs):
        self.__acquisitionThread.start()
        self.sigRecordingStarted.emit()
    
    def endRecording(self):
        self.sigRecordingEnded.emit()