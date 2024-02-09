from pycromanager import Core, Acquisition, multi_d_acquisition_events, AcqNotification
from imswitch.imcommon.framework import Signal, SignalInterface, Worker, Thread, Timer
from imswitch.imcommon.model import initLogger, SaveMode
from tifffile.tifffile import TiffWriter
from typing import Dict
import os, json
import numpy as np


class PycroManagerAcquisitionManager(SignalInterface):

    sigLiveImageUpdated = Signal(np.ndarray) # image
    sigRecordingStarted = Signal()
    sigRecordingEnded = Signal()
    sigPycroManagerNotificationUpdated = Signal(dict)  # (pycroManagerNotificationId)
    sigMemorySnapAvailable = Signal(
        str, np.ndarray, object, bool
    )  # (name, image, filePath, savedToDisk)
    sigMemoryRecordingAvailable = Signal(
        str, object, object, bool
    )  # (name, file, filePath, savedToDisk)

    # TODO: find another way to retrieve the current detector name
    def __init__(self):
        super().__init__()
        self.__logger = initLogger(self)
        self.__core = Core()
        self.__acquisitionWorker = PycroManagerAcqWorker(self)
        self.__acquisitionThread = Thread()
        self.__acquisitionWorker.moveToThread(self.__acquisitionThread)
        self.__liveTimer = Timer()
        self.__liveTimer.timeout.connect(lambda : self.sigLiveImageUpdated.emit(self.__acquisitionWorker.localBuffer))
        self.__liveTimer.setInterval(100)

    def snap(self, folder: str, savename: str, saveMode: SaveMode, attrs: dict):
        """ Snaps an image calling an instance of the Pycro-Manager backend Core. 
        """
        # TODO: support multiple extension types?
        extension = ".ome.tiff"
        savename += extension
        fullPath = os.path.join(folder, savename)

        self.core.snap_image()
        tagged_image = self.core.get_tagged_image()
        pixels = np.reshape(tagged_image.pix, newshape=(
            1, tagged_image.tags['Height'], tagged_image.tags['Width']))

        # TODO: add missing metadata fields
        metadata = {
            "axes": "TYX",
            "PhysicalSizeX": self.core.get_pixel_size_um(),
            "PhysicalSizeXUnit": "µm",
            "PhysicalSizeY": self.core.get_pixel_size_um(),
            "PhysicalSizeYUnit": "µm",
            "PhysicalSizeZ": 1,
            "PhysicalSizeZUnit": "µm",
            "TimeIncrement": self.core.get_exposure(),
            "TimeIncrementUnit": "ms",
        }

        if saveMode == SaveMode.Disk or saveMode == SaveMode.DiskAndRAM:
            self.__logger.info("Snapping to %s", fullPath)
            with TiffWriter(fullPath, ome=True) as tif:
                tif.write(pixels, metadata=metadata, software="ImSwitch")

        if saveMode == SaveMode.RAM or saveMode == SaveMode.DiskAndRAM:
            name = self.core.get_camera_device()
            self.sigMemorySnapAvailable.emit(
                name, pixels, savename, saveMode == SaveMode.DiskAndRAM)

    @property
    def core(self) -> Core:
        return self.__core
    
    def startRecording(self, recordingArgs: dict):
        self.__acquisitionWorker.recordingArgs = recordingArgs
        self.__acquisitionThread.started.connect(self.__acquisitionWorker.record)
        self.__acquisitionThread.finished.connect(self.__postInterruptionHandle)
        self.__acquisitionThread.start()

    def endRecording(self) -> None:
        self.__postInterruptionHandle()
    
    def startLiveView(self, recordingArgs: dict):
        self.__acquisitionWorker.recordingArgs = recordingArgs
        self.__acquisitionThread.started.connect(self.__acquisitionWorker.liveView)
        self.__acquisitionThread.finished.connect(self.__postInterruptionHandle)
        self.__acquisitionThread.start()
        self.__liveTimer.start()

    def stopLiveView(self):
        self.__liveTimer.stop()
        self.__acquisitionWorker.live = False
    
    def __postInterruptionHandle(self):
        try:
            self.__acquisitionThread.quit()
            self.__acquisitionThread.started.disconnect()
            self.__acquisitionThread.finished.disconnect()
        except TypeError:
            pass

class PycroManagerAcqWorker(Worker):
    def __init__(self, manager: PycroManagerAcquisitionManager) -> None:
        super().__init__()
        self.__logger = initLogger(self)
        self.__manager = manager
        width, height = self.__manager.core.get_image_width(), self.__manager.core.get_image_height()
        self.__localBuffer = np.zeros((height, width), dtype=np.uint16)

        # TODO: usage of a local variable would
        # enable to dynamicall abort recording
        # if requested by the UI... needs implementation
        self.__acquisition = None
        self.recordingArgs : Dict[str, dict] = None
        self.live = False
    
    def __parse_notification(self, msg: AcqNotification):
        # TODO: this notification works to send updates
        # to the recording progress bar for recording;
        # as live view bypasses saving data to disk,
        # this notification is never reached;
        # find another notification type to send updates
        # during live acquisition
        if msg.is_image_saved_notification():
            self.manager.sigPycroManagerNotificationUpdated.emit(msg.id)

    def __store_live_local(self, image: np.ndarray, _: dict):
        self.__localBuffer = image.astype(np.uint16)

    def record(self) -> None:
        events = multi_d_acquisition_events(**self.recordingArgs["multi_d_acquisition_events"])
        self.recordingArgs["Acquisition"]["notification_callback_fn"] = self.__parse_notification

        self.__logger.info("Starting acquisition")
        self.manager.sigRecordingStarted.emit()
        with Acquisition(**self.recordingArgs["Acquisition"]) as self.__acquisition:
            self.__acquisition.acquire(events)
        
        # dataset file handler causes a warning if not closed properly;
        self.__acquisition.get_dataset().close()
        self.manager.sigRecordingEnded.emit()
    
    def liveView(self):
        self.__logger.info("Starting live view")
        self.live = True
        events = multi_d_acquisition_events(**self.recordingArgs["multi_d_acquisition_events"])
        self.recordingArgs["Acquisition"]["notification_callback_fn"] = self.__parse_notification
        self.recordingArgs["Acquisition"]["image_process_fn"] = self.__store_live_local

        # for live view we only redirect incoming images to the local buffer
        self.recordingArgs["Acquisition"].pop("directory")
        self.recordingArgs["Acquisition"].pop("name")
        self.__acquisition = Acquisition(**self.recordingArgs["Acquisition"])

        while self.live:
            self.__acquisition.acquire(events)
        self.__acquisition.mark_finished()
        
        self.__logger.info("Live view stopped")
    
    @property
    def manager(self) -> PycroManagerAcquisitionManager:
        return self.__manager
    
    @property
    def localBuffer(self) -> np.ndarray:
        return self.__localBuffer