import tifffile as tiff
import time
import numpy as np
from datetime import datetime
from math import ceil
from typing import Dict
from numpy import ndarray
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model.managers.detectors.DetectorManager import DetectorManager
from imswitch.imcontrol.model.managers.storers.StorerManager import RecMode, SaveMode
from .StorerManager import (
    StorerManager,
    RecMode,
    SaveMode
)

class TIFFStorerManager(StorerManager):
    """ An OME-TIFF data streaming manager. See `StorerManager` for details on the interface.
    """
    
    @classmethod
    def saveSnap(self, images: Dict[str, ndarray], attrs: Dict[str, str], **kwargs) -> None:
        logger = initLogger(self)
        for channel, image in images.items():
            detector = kwargs["detectors"][channel]
            acquisitionDate = kwargs["acquisitionDate"]
            filePath = kwargs["filePath"]

            _, physicalYSize, physicalXSize = detector.pixelSizeUm
            imageMetadata = dict(
                Name = detector.name,
                AcquisitionDate = acquisitionDate,
                TimeIncrement = detector.frameInterval,
                TimeIncrementUnit = 'µs',
                PhysicalSizeX = physicalXSize,
                PhysicalSizeXUnit = 'µm',
                PhysicalSizeY = physicalYSize,
                PhysicalSizeYUnit = 'µm'
            )
            metadata = dict(Image = imageMetadata)
            fullPath = f"{filePath}_{channel}.tiff"
            with tiff.TiffWriter(fullPath, ome=False) as file:
                file.write(image, photometric="minisblack", description="", metadata=None)
                omexml = tiff.OmeXml(Creator = "ImSwitch")
                omexml.addimage(
                    dtype=detector.dtype,
                    shape=(1, *reversed(detector.shape)),
                    storedshape=(1, 1, 1, *reversed(detector.shape), 1),
                    axes='TYX',
                    metadata=metadata
                )
                description = omexml.tostring(declaration=True)
                file.overwrite_description(description.encode())
            logger.info(f"Saved image to tiff file {fullPath}")
    
    def stream(self, recMode: RecMode, saveMode: SaveMode, attrs: Dict[str, str], **kwargs) -> None:
        # TODO: parse attrs to tiff metadata
        frameNumberWindow = []
        channel = self.streamInfo.detector.name
        frameInterval = self.streamInfo.detector.frameInterval
        acquisitionDate = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        
        with tiff.TiffWriter(self.streamInfo.filePath, ome=False, bigtiff=True) as file:
            if recMode == RecMode.SpecFrames:
                totalFrames = kwargs["totalFrames"]
                while self.frameCount < totalFrames and self.record:
                    frames, frameIDs = self.unpackChunk()
                    if self.frameCount + len(frames) >= totalFrames:
                        # we only collect the remaining frames required,
                        # and discard the remaining
                        frames = frames[0: totalFrames - self.frameCount]
                        frameIDs = frameIDs[0: totalFrames - self.frameCount]
                    file.write(frames,  photometric="minisblack", description="", metadata=None)
                    frameNumberWindow.extend(frameIDs)
                    self.frameCount += len(frames)
                    self.signals.frameNumberUpdate.emit(channel, self.frameCount)
            elif recMode == RecMode.SpecTime:
                totalTime = kwargs["totalTime"] # s
                totalFrames = int(ceil(totalTime * 1e6 / frameInterval))
                self.logger.info(f"Recording time: {totalTime} s @{frameInterval} μs -> {totalFrames} frames")
                currentRecTime = 0
                start = time.time()
                index = 0
                while index < totalFrames and self.record:
                    frames, frameIDs = self.unpackChunk()
                    file.write(frames, description='', metadata=None)
                    frameNumberWindow.extend(frameIDs)
                    self.timeCount = np.around(currentRecTime, decimals=2)
                    self.signals.timeUpdate.emit(channel, min(self.timeCount, totalTime))
                    currentRecTime = time.time() - start
                    index += len(frames)
                self.frameCount = totalFrames
            elif recMode == RecMode.UntilStop:
                while self.record:
                    frames, frameIDs = self.unpackChunk()
                    file.write(frames, description='', metadata=None)
                    frameNumberWindow.extend(frameIDs)
                    self.frameCount += len(frames)
            _, physicalYSize, physicalXSize = self.streamInfo.detector.pixelSizeUm
            imageMetadata = dict(
                Name = self.streamInfo.detector.name,
                AcquisitionDate = acquisitionDate,
                TimeIncrement = self.streamInfo.detector.frameInterval,
                TimeIncrementUnit = 'µs',
                PhysicalSizeX = physicalXSize,
                PhysicalSizeXUnit = 'µm',
                PhysicalSizeY = physicalYSize,
                PhysicalSizeYUnit = 'µm'
            )
            metadata = dict(Image = imageMetadata)
            omexml = tiff.OmeXml(Creator = "ImSwitch")
            omexml.addimage(
                dtype=self.streamInfo.detector.dtype,
                shape=(self.frameCount, *reversed(self.streamInfo.detector.shape)),
                storedshape=(self.frameCount, 1, 1, *reversed(self.streamInfo.detector.shape), 1),
                axes='TYX',
                metadata=metadata
            )
            description = omexml.tostring(declaration=True)
            file.overwrite_description(description.encode())
        
            # we check that all frame IDs are equidistant
            if np.all(frameNumberWindow == 0):
                self.logger.error(f"[{channel}] No frame IDs were provided for {channel}.")
            elif not np.all(np.ediff1d(frameNumberWindow) == 1):
                self.logger.error(f"[{channel}] Frames lost. Frame interval: {frameInterval} μs")