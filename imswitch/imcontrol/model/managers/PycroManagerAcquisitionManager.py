from traceback import format_exc
from pycromanager import Core, Acquisition, multi_d_acquisition_events, AcqNotification
from imswitch.imcommon.framework import Signal, SignalInterface, Thread, Worker
from imswitch.imcommon.framework.pycromanager import PycroManagerAcquisitionMode
from imswitch.imcommon.model import initLogger, SaveMode
from tifffile.tifffile import TiffWriter
import os
import numpy as np


class PycroManagerAcquisitionManager(SignalInterface):

    sigRecordingStarted = Signal()
    sigRecordingEnded = Signal()
    sigPycroManagerNotificationUpdated = Signal(dict)  # (pycroManagerNotificationId)
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
        self.__acquisition = None

    def snap(self, folder: str, savename: str, saveMode: SaveMode, attrs: dict):
        """ Snaps an image calling an instance of the Pycro-Manager backend Core. 
        """
        # TODO: support multiple extension types?
        extension = ".ome.tiff"
        savename += extension
        fullPath = os.path.join(folder, savename)

        self.__core.snap_image()
        tagged_image = self.__core.get_tagged_image()
        pixels = np.reshape(tagged_image.pix, newshape=(
            1, tagged_image.tags['Height'], tagged_image.tags['Width']))

        # TODO: add missing metadata fields
        metadata = {
            "axes": "TYX",
            "PhysicalSizeX": self.__core.get_pixel_size_um(),
            "PhysicalSizeXUnit": "µm",
            "PhysicalSizeY": self.__core.get_pixel_size_um(),
            "PhysicalSizeYUnit": "µm",
            "PhysicalSizeZ": 1,
            "PhysicalSizeZUnit": "µm",
            "TimeIncrement": self.__core.get_exposure(),
            "TimeIncrementUnit": "ms",
        }

        if saveMode == SaveMode.Disk or saveMode == SaveMode.DiskAndRAM:
            self.__logger.info("Snapping to %s", fullPath)
            with TiffWriter(fullPath, ome=True) as tif:
                tif.write(pixels, metadata=metadata, software="ImSwitch")

        if saveMode == SaveMode.RAM or saveMode == SaveMode.DiskAndRAM:
            name = self.__core.get_camera_device()
            self.sigMemorySnapAvailable.emit(
                name, pixels, savename, saveMode == SaveMode.DiskAndRAM)

    @property
    def core(self) -> Core:
        return self.__core

    def __parse_notification(self, msg: AcqNotification):
        if msg.is_image_saved_notification():
            self.sigPycroManagerNotificationUpdated.emit(msg.id)
        elif msg.is_acquisition_finished_notification():
            # For some reason the Dataset reference is not closed properly;
            # this is a workaround to avoid the error and close the reference
            d = self.__acquisition.get_dataset()
            d.close()
            self.__logger.info("Acquisition finished")
            self.sigRecordingEnded.emit()

    def startRecording(self, recordingArgs: dict):
        events = multi_d_acquisition_events(**recordingArgs["multi_d_acquisition_events"])
        recordingArgs["Acquisition"]["notification_callback_fn"] = self.__parse_notification

        self.__logger.info("Starting acquisition")
        self.__acquisition = Acquisition(**recordingArgs["Acquisition"])
        self.__acquisition.acquire(events)
        self.__acquisition.mark_finished()
        self.sigRecordingStarted.emit()

    def endRecording(self) -> None:
        if self.__acquisition is not None:
            self.__acquisition.abort()
            self.sigRecordingEnded.emit()
        self.__acquisition = None
