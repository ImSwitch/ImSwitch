from pycromanager import Core, Acquisition, multi_d_acquisition_events, AcqNotification
from imswitch.imcommon.framework import Signal, SignalInterface, Worker, Thread
from imswitch.imcommon.model import initLogger, SaveMode
from tifffile.tifffile import TiffWriter
import os
import numpy as np


class PycroManagerAcquisitionManager(SignalInterface):

    sigLiveAcquisitionStarted = Signal()
    sigLiveAcquisitionStopped = Signal()
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
        self.__acquisitionThread.start()
        self.sigRecordingStarted.emit()

    def endRecording(self) -> None:
        self.__acquisitionThread.quit()
        self.__acquisitionThread.started.disconnect()
    
    def startLiveView(self, recordingArgs: dict):
        self.__acquisitionWorker.recordingArgs = recordingArgs
        self.__acquisitionThread.started.connect(self.__acquisitionWorker.liveView)
        self.__acquisitionThread.finished.connect(self.__postInterruptionHandle)
        self.__acquisitionThread.start()
        self.sigLiveAcquisitionStarted.emit()

    def stopLiveView(self):
        self.__acquisitionThread.requestInterruption()
    
    def __postInterruptionHandle(self):
        self.__acquisitionThread.quit()
        self.__acquisitionThread.started.disconnect()
        self.__acquisitionThread.finished.disconnect()
        self.sigLiveAcquisitionStopped.emit()

class PycroManagerAcqWorker(Worker):
    def __init__(self, manager: PycroManagerAcquisitionManager) -> None:
        super().__init__()
        self.__logger = initLogger(self)
        self.__manager = manager
        self.recordingArgs = None
        self.live = False
    
    def __parse_record_notification(self, msg: AcqNotification):
        if msg.is_image_saved_notification():
            self.__manager.sigPycroManagerNotificationUpdated.emit(msg.id)
        elif msg.is_acquisition_finished_notification():
            # For some reason the Dataset reference is not closed properly;
            # this is a workaround to avoid the error and close the reference
            self.__logger.info("Acquisition finished")
            self.__manager.sigRecordingEnded.emit()
    
    def __parse_live_notification(self, msg: AcqNotification):
        if msg.is_image_saved_notification():
            self.__manager.sigPycroManagerNotificationUpdated.emit(msg.id)

    def __notify_new_image(self, image: np.ndarray, _: dict):
        self.__manager.sigLiveImageUpdated.emit(image)

    def record(self) -> None:
        events = multi_d_acquisition_events(**self.recordingArgs["multi_d_acquisition_events"])
        self.recordingArgs["Acquisition"]["notification_callback_fn"] = self.__parse_record_notification

        self.__logger.info("Starting acquisition")
        with Acquisition(**self.recordingArgs["Acquisition"]) as acq:
            acq.acquire(events)
        acq.get_dataset().close()
    
    def liveView(self):
        events = multi_d_acquisition_events(**self.recordingArgs["multi_d_acquisition_events"])
        self.recordingArgs["Acquisition"]["notification_callback_fn"] = self.__parse_live_notification
        self.recordingArgs["Acquisition"]["img_process_fn"] = self.__notify_new_image
        with Acquisition(**self.recordingArgs["Acquisition"]) as acq:
            while self.thread().isInterruptionRequested():
                acq.acquire(events)
                acq.await_completion()