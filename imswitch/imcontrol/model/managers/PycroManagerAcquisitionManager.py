from pycromanager import Core, Acquisition, multi_d_acquisition_events, AcqNotification
from imswitch.imcommon.framework import Signal, SignalInterface, Worker, Thread, Timer
from imswitch.imcommon.model import initLogger, SaveMode
from tifffile.tifffile import TiffWriter
from typing import Dict
import os, json
import numpy as np

_PYCROMANAGER_LIVE_REFRESH_MS = 100 # live view refresh time

class PycroManagerAcquisitionManager(SignalInterface):

    sigLiveImageUpdated = Signal(np.ndarray) # image
    sigRecordingStarted = Signal()
    sigRecordingEnded = Signal()
    sigPycroManagerNotificationUpdated = Signal(str)  # (pycroManagerNotificationId)
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
        self.__liveTimer.setInterval(_PYCROMANAGER_LIVE_REFRESH_MS)

    def snap(self, folder: str, savename: str, saveMode: SaveMode, attrs: dict) -> None:
        """ Snaps an image calling an instance of the Pycro-Manager backend Core. 
        """
        # TODO: support multiple extension types?
        extension = ".ome.tiff"
        savename += extension
        fullPath = os.path.join(folder, savename)

        self.core.snap_image()
        tagged_image = self.core.get_tagged_image()
        pixels = np.reshape(tagged_image.pix, 
                            newshape=(
                                1, 
                                tagged_image.tags['Height'], 
                                tagged_image.tags['Width'])
                            )

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
    
    def startRecording(self, recordingArgs: Dict[str, dict]) -> None:
        self.__acquisitionWorker.recordingArgs = recordingArgs
        self.__acquisitionThread.started.connect(self.__acquisitionWorker.record)
        self.__acquisitionThread.finished.connect(self.__postInterruptionHandle)
        self.__acquisitionThread.start()

    def endRecording(self) -> None:
        self.__postInterruptionHandle()
    
    def startLiveView(self, recordingArgs: Dict[str, dict]) -> None:
        self.__acquisitionWorker.recordingArgs = recordingArgs
        self.__acquisitionThread.started.connect(self.__acquisitionWorker.liveView)
        self.__acquisitionThread.finished.connect(self.__postInterruptionHandle)
        self.__acquisitionThread.start()

        # enable live view timer if
        # no other image process function
        # is currently enabled
        if recordingArgs["Acquisition"]["image_process_fn"] is None:
            self.__liveTimer.start()

    def stopLiveView(self) -> None:
        if self.__liveTimer.isActive():
            self.__liveTimer.stop()
        self.__acquisitionWorker.live = False
    
    def __postInterruptionHandle(self) -> None:
        try:
            self.__acquisitionThread.quit()
            self.__acquisitionThread.started.disconnect()
            self.__acquisitionThread.finished.disconnect()
        except TypeError:
            # fallback in case signals were not connected
            pass

class PycroManagerAcqWorker(Worker):
    def __init__(self, manager: PycroManagerAcquisitionManager) -> None:
        super().__init__()
        self.recordingArgs : Dict[str, dict] = None
        self.__logger = initLogger(self)
        self.__manager = manager

        # TODO: what happens if user changes the settings during acquisition?
        width, height = self.__manager.core.get_image_width(), self.__manager.core.get_image_height()
        self.__localBuffer = np.zeros((height, width), dtype=np.uint16)
        self.live = False
    
    def __parse_record_notification(self, msg: AcqNotification) -> None:
        if msg.is_image_saved_notification():
            self.manager.sigPycroManagerNotificationUpdated.emit(json.dumps(msg.id))
    
    def __parse_live_notification(self, msg: AcqNotification) -> None:
        # TODO: apparently, msg.is_image_saved_notification()
        # should work as well, but it doesn't;
        # this is something which doesn't work probably on the
        # pycromanager side; for now we use the POST_EXPOSURE
        # phase to trigger notification
        if msg.phase == AcqNotification.Camera.POST_EXPOSURE:
            self.manager.sigPycroManagerNotificationUpdated.emit(json.dumps(msg.id))

    def __store_live_local(self, image: np.ndarray, _: dict) -> None:
        self.__localBuffer = image.astype(np.uint16)

    def record(self) -> None:
        events = multi_d_acquisition_events(**self.recordingArgs["multi_d_acquisition_events"])
        self.recordingArgs["Acquisition"]["notification_callback_fn"] = self.__parse_record_notification

        self.__logger.info("Starting acquisition")
        self.manager.sigRecordingStarted.emit()
        with Acquisition(**self.recordingArgs["Acquisition"]) as acq:
            acq.acquire(events)
        
        # dataset file handler causes a warning if not closed properly;
        acq.get_dataset().close()
        self.manager.sigRecordingEnded.emit()

        self.__logger.info("Acquisition ended")
        # TODO: is this necessary?
        del acq
    
    def liveView(self) -> None:
        self.__logger.info("Starting live view")
        self.live = True
        events = multi_d_acquisition_events(**self.recordingArgs["multi_d_acquisition_events"])
        self.recordingArgs["Acquisition"]["notification_callback_fn"] = self.__parse_live_notification

        # if no image processing function is provided, we store the image locally;
        # the latest saved image is emitted to the GUI every time the local timer
        # expires
        if self.recordingArgs["Acquisition"]["image_process_fn"] is None:
            self.recordingArgs["Acquisition"]["image_process_fn"] = self.__store_live_local

        # for live view we only redirect incoming images to the local buffer
        # deliting the directory and name keys from the dictionary
        # ensures that the images are not saved to disk
        self.recordingArgs["Acquisition"].pop("directory")
        self.recordingArgs["Acquisition"].pop("name")
        
        # get last time point for the future milestone
        # TODO: depending on the requested acquisition, multiple milestones
        # on different axis are required (i.e. XY, XYZ, different channels, etc.)
        milestone = self.recordingArgs["multi_d_acquisition_events"]["num_time_points"] - 1

        with Acquisition(**self.recordingArgs["Acquisition"]) as acq:
            while self.live:
                future = acq.acquire(events)
                future.await_execution({"time": milestone}, AcqNotification.Camera.POST_EXPOSURE)
            acq.abort()

        self.__logger.info("Live view stopped")

        # TODO: is this necessary?
        del acq
    
    @property
    def manager(self) -> PycroManagerAcquisitionManager:
        return self.__manager
    
    @property
    def localBuffer(self) -> np.ndarray:
        return self.__localBuffer