from pycromanager import Core
from imswitch.imcommon.framework import Signal, SignalInterface, Thread, Worker
from imswitch.imcommon.model import initLogger, SaveMode
from tifffile.tifffile import imwrite
import numpy as np

class AcquisitionWorker(Worker):
    def __init__(self):
        super().__init__()
        
class PycroManagerManager(SignalInterface):
    
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
    
    def snap(self, savename: str, saveMode: SaveMode):
        """ Snaps an image calling an instance of the Pycro-Manager backend Core. 
        """
        self.__core.snap_image()
        tagged_image = self.__core.get_tagged_image()
        pixels = np.reshape(tagged_image.pix,
                        newshape=(tagged_image.tags['Height'], tagged_image.tags['Width']))
    
        if saveMode == SaveMode.Disk or saveMode == SaveMode.DiskAndRAM:
            # TODO: question support other data formats?
            imwrite(file=savename, data=pixels, imagej=True)

        if saveMode == SaveMode.RAM or saveMode == SaveMode.DiskAndRAM:
            name = self.__core.get_camera_device()
            self.sigMemorySnapAvailable.emit(name, pixels, savename, saveMode == SaveMode.DiskAndRAM)
    
    def startRecording(self):
        pass
    
    def stopRecording(self):
        pass