import enum
import os
import time
from datetime import datetime
from math import ceil
from imswitch.imcontrol.model.configfiletools import _debugLogDir
from io import BytesIO
from typing import Dict, Optional, Type, List, Tuple, Union
from types import DynamicClassAttribute

import h5py
import zarr
import numpy as np
import tifffile as tiff

from imswitch.imcommon.framework import (
    Signal, 
    SignalInterface, 
    FunctionWorker,
    create_worker,
)
from imswitch.imcommon.model import initLogger
from ome_zarr.writer import write_multiscales_metadata
from ome_zarr.format import format_from_version
import abc
import logging

from imswitch.imcontrol.model.managers.detectors import DetectorManager
from imswitch.imcontrol.model.managers.DetectorsManager import DetectorsManager

logger = logging.getLogger(__name__)

class StreamingWorker(FunctionWorker):
    pass

class RecMode(enum.Enum):
    SpecFrames = 1
    SpecTime = 2
    ScanOnce = 3
    ScanLapse = 4
    UntilStop = 5

class SaveMode(enum.Enum):
    Disk = 1
    RAM = 2
    DiskAndRAM = 3
    Numpy = 4


class SaveFormat(enum.Enum):
    HDF5 = 1
    TIFF = 2
    ZARR = 3

    @DynamicClassAttribute
    def name(self):
        name = super(SaveFormat, self).name
        if name == "TIFF":
            name = "OME-TIFF"
        return name

class AsTemporayFile(object):
    """ A temporary file that when exiting the context manager is renamed to its original name. """
    def __init__(self, filepath, tmp_extension='.tmp'):
        if os.path.exists(filepath):
            raise FileExistsError(f'File {filepath} already exists.')
        self.path = filepath
        self.tmp_path = filepath + tmp_extension

    def __enter__(self):
        return self.tmp_path

    def __exit__(self, *args, **kwargs):
        os.rename(self.tmp_path, self.path)

class Storer(SignalInterface):
    frameNumberUpdate = Signal(str, int) # channel, frameNumber
    timeUpdate = Signal(str, float) # channel, timeCount
    sigMemRecAvailable = Signal(
        str, object, object, bool
    )  # (name, file, filePath, savedToDisk)

    def __init__(self, filepath: str, filedest: Union[h5py.File, np.memmap, zarr.storage.DirectoryStore], detectorsManager: DetectorsManager):
        """ Storer base class.

        Args:
            filepath (str): filepath to save the data to disk.
            filedest (Union[h5py.File, np.memmap, zarr.storage.DirectoryStore]): file-like object to save the data to RAM
            detectorsManager (DetectorsManager): detectors manager to read data from.
        """

        super().__init__()
        self.filepath = filepath
        self.filedest = filedest
        self.detectorsManager = detectorsManager
        self.frameCount : int = 0
        self.timeCount : float = 0.0
        self._record = False
    
    @property
    def record(self) -> bool:
        return self._record

    @record.setter
    def record(self, record: bool):
        self._record = record

    def snap(self, images: Dict[str, np.ndarray], attrs: Dict[str, str] = None):
        """ Stores images and attributes according to the spec of the storer """
        raise NotImplementedError

    def stream(self, channel: str, recMode: RecMode, saveMode: SaveMode, attrs: Dict[str, str], **kwargs) -> None:
        """ Stores data in a streaming fashion. """
        raise NotImplementedError
    
    def unpackChunk(self, detectorManager: DetectorManager) -> Tuple[np.ndarray, np.ndarray]:
        """ Checks if the value returned by getChunk is a tuple (packing the recorded chunk and the associated time points).
        If the return type is only the recorded stack, a zero array is generated with the same length of 
        the recorded chunk.

        Args:
            channel (str): detector's channel to read chunk from

        Returns:
            tuple: a 2-element tuple with the recorded chunk and the single data points associated with each frame.
        """
        chunk = detectorManager.getChunk()
        if type(chunk) == tuple:
            return chunk
        else: # type is np.ndarray
            chunk = (chunk, np.zeros(len(chunk)))
        return chunk

class ZarrStorer(Storer):
    """ A storer that stores the images in a zarr file store """
    def snap(self, images: Dict[str, np.ndarray], attrs: Dict[str, str] = None):
        with AsTemporayFile(f'{self.filepath}.zarr') as path:
            datasets: List[dict] = []
            store = zarr.storage.DirectoryStore(path)
            root = zarr.group(store=store)

            for channel, image in images.items():
                shape = self.detectorManager[channel].shape
                root.create_dataset(channel, data=image, shape=tuple(reversed(shape)),
                                        chunks=(512, 512), dtype='i2') #TODO: why not dynamic chunking?

                datasets.append({"path": channel, "transformation": None})
            write_multiscales_metadata(root, datasets, format_from_version("0.2"), shape, **attrs)
            logger.info(f"Saved image to zarr file {path}")


class HDF5Storer(Storer):
    """ A storer that stores the images in a series of hd5 files """
    def snap(self, images: Dict[str, np.ndarray], attrs: Dict[str, str] = None):
        for channel, image in images.items():
            with AsTemporayFile(f'{self.filepath}_{channel}.h5') as path:
                file = h5py.File(path, 'w')
                shape = self.detectorManager[channel].shape
                dataset = file.create_dataset('data', tuple(reversed(shape)), dtype='i2')
                for key, value in attrs[channel].items():
                    try:
                        dataset.attrs[key] = value
                    except:
                        logger.debug(f'Could not put key:value pair {key}:{value} in hdf5 metadata.')

                dataset.attrs['detector_name'] = channel

                # For ImageJ compatibility
                dataset.attrs['element_size_um'] = \
                    self.detectorManager[channel].pixelSizeUm

                if image.ndim == 3:
                    dataset[:, ...] = np.moveaxis(image, [0, 1, 2], [2, 1, 0])
                elif image.ndim == 4:
                    dataset[:, ...] = np.moveaxis(image, [0, 1, 2, 3], [3, 2, 1, 0])
                else:
                    dataset[:, ...] = np.moveaxis(image, 0, -1)
            
                file.close()
                logger.info(f"Saved image to hdf5 file {path}")

    def stream(self, channel: str, recMode: RecMode, saveMode: SaveMode, attrs: Dict[str, str], **kwargs) -> None:
        """ Stores data in a streaming fashion. """

        detector : DetectorManager = self.detectorsManager[channel]
        pixelSize = detector.pixelSizeUm
        self.record = True
        frameNumberWindow = []
        
        def create_dataset(file: h5py.File, shape: tuple, name: str = "data", dtype = detector.dtype, compression: str = None) -> Tuple[h5py.Dataset, h5py.Dataset]:
            """ Create a frame dataset and a frame ID dataset to store recordings.

            Args:
                file (h5py.File): file handler
                shape (tuple): size of the video to record

            Returns:
                h5py.Dataset: the created dataset
            """
            dataset = file.create_dataset(name, shape=shape, maxshape=(None, *shape[1:]), dtype=dtype, compression=compression)
            for key, value in attrs.items():
                try:
                    dataset.attrs[key] = value
                except:
                    logger.debug(f'Could not put key:value pair {key}:{value} in hdf5 metadata.')
            dataset.attrs["detector_name"] = channel
            dataset.attrs["element_size_um"] = pixelSize
            return dataset
        
        if saveMode == SaveMode.RAM:
            file = h5py.File(self.filedest, mode="a")
        else:
            file = h5py.File(self.filepath, mode="a")
        
        if recMode in [RecMode.SpecFrames, RecMode.ScanLapse]:
            totalFrames = kwargs["totalFrames"]
            self.frameCount = 0
            dataset = create_dataset(file, (totalFrames, *reversed(detector.shape)))
            while self.frameCount < totalFrames and self.record:
                frames, frameIDs = self.unpackChunk(detector)
                if self.frameCount + len(frames) > totalFrames:
                    # we only collect the remaining frames required,
                    # and discard the remaining
                    frames = frames[0: totalFrames - self.frameCount]
                    frameIDs = frameIDs[0: totalFrames - self.frameCount]
                dataset[self.frameCount : self.frameCount + len(frames)] = frames
                frameNumberWindow.extend(frameIDs)
                self.frameCount += len(frames)
                self.frameNumberUpdate.emit(channel, self.frameCount)
        elif recMode == RecMode.SpecTime:
            timeUnit = detector.frameInterval # us
            totalTime = kwargs["totalTime"] # s
            totalFrames = int(ceil(totalTime * 1e6 / timeUnit))
            dataset = create_dataset(file, (totalFrames, *reversed(detector.shape)))
            currentRecTime = 0
            start = time.time()
            index = 0
            while index < totalFrames and self.record:
                frames, frameIDs = self.unpackChunk(detector)
                nframes = len(frames)
                dataset[index: index + nframes] = frames
                frameNumberWindow.extend(frameIDs)
                self.timeCount = np.around(currentRecTime, decimals=2)
                self.timeUpdate.emit(channel, min(self.timeCount, totalTime))
                index += nframes
                currentRecTime = time.time() - start
            # we may have not used up the entirety of the HDF5 size,
            # so we resize the dataset to the value of "index"
            # in case this is lower than totalFrames
            if index < totalFrames:
                dataset.resize(index, axis=0)
        elif recMode == RecMode.UntilStop:
            # with HDF5 it's hard to make an estimation of an infinite recording
            # and set the correct data size... the best thing we can do is to 
            # create the dataset big enough to store 1 second worth of data recording
            # and keep extending it whenever we're going out of boundaries
            # but a better solution should be found
            timeUnit = detector.frameInterval # us
            totalTime = 1e6 # us
            totalFrames = int(ceil(totalTime / timeUnit))
            dataset = create_dataset(file, (totalFrames, *reversed(detector.shape)))
            index = 0
            while self.record:
                frames, frameIDs = self.unpackChunk(detector)
                nframes = len(frames)
                if nframes > index:
                    dataset.resize(index + totalFrames, axis=0)
                dataset[index: nframes] = frames
                frameNumberWindow.extend(frameIDs)
                index += nframes
        # we write the ids to a separate dataset;
        # after testing, for large recordings we go 
        # over the maximum attribute size of 64k,
        # so we just write the data separately
        file.create_dataset("data_id", data=frameNumberWindow)
        if detector.dtype == np.int16:
            new_dset = create_dataset(file, file["data"].shape, "data1", dtype=np.float32)
            new_dset[:] = dataset[:]
            del file["data"]
        if len(detector.imageProcessing) > 0:
            for key, value in detector.imageProcessing.items():
                file.create_dataset(key, data=value["content"])
        
        # we check that all frame IDs are equidistant
        if np.all(frameNumberWindow == 0):
            logger.warning(f"[REC:{detector.name}] No frame IDs were provided for {detector.name}.")
        elif not np.all(np.ediff1d(frameNumberWindow) == 1):
            dbgPath = os.path.join(_debugLogDir, f"frame_id_differences_{detector.name}.txt")
            logger.error(f"[REC:{detector.name}] Frames lost. Frame interval: {detector.frameInterval} μs")
            logger.error(f"[REC:{detector.name}] You can find the frame ID list in {dbgPath}")
            np.savetxt(os.path.join(_debugLogDir, f"frame_id_differences_{detector.name}.txt"), np.ediff1d(frameNumberWindow), fmt="%d")
        
        if saveMode in [SaveMode.DiskAndRAM, SaveMode.RAM]:
            if saveMode == SaveMode.DiskAndRAM:
                file.flush()
                self.sigMemRecAvailable.emit(channel, file, self.filepath, True)
            else:
                file.close()
                self.sigMemRecAvailable.emit(channel, self.filedest, self.filepath, False)
        else:
            file.close()        

class TiffStorer(Storer):
    """ A storer that stores the images in a series of tiff files """
    def snap(self, images: Dict[str, np.ndarray], attrs: Dict[str, str] = None):
        for channel, image in images.items():
            with AsTemporayFile(f'{self.filepath}_{channel}.tiff') as path:
                tiff.imwrite(path, image,) # TODO: Parse metadata to tiff meta data
                logger.info(f"Saved image to tiff file {path}")
    
    def stream(self, channel: str, recMode: RecMode, saveMode: SaveMode, attrs: Dict[str, str], **kwargs) -> None:
        # TODO: Parse metadata to tiff meta data
        detector: DetectorManager = self.detectorsManager[channel]
        _, physicalYSize, physicalXSize = self.detectorsManager[channel].pixelSizeUm
        frameNumberWindow = []
        
        self.record = True
        date = datetime.now()
        
        imageMetadata = dict(
            Name = detector.name,
            AcquisitionDate = date.strftime("%d-%m-%Y %H:%M:%S"),
            TimeIncrement = detector.frameInterval,
            TimeIncrementUnit = 'µs',
            PhysicalSizeX = physicalXSize,
            PhysicalSizeXUnit = 'µm',
            PhysicalSizeY = physicalYSize,
            PhysicalSizeYUnit = 'µm'
        )
        metadata = dict(
            Image = imageMetadata
        )
        
        with tiff.TiffWriter(self.filepath, ome=False, bigtiff=True) as file:
            if recMode == RecMode.SpecFrames:
                totalFrames = kwargs["totalFrames"]
                while self.frameCount < totalFrames and self.record:
                    frames, frameIDs = self.unpackChunk(detector)
                    if self.frameCount + len(frames) >= totalFrames:
                        # we only collect the remaining frames required,
                        # and discard the remaining
                        frames = frames[0: totalFrames - self.frameCount]
                        frameIDs = frameIDs[0: totalFrames - self.frameCount]
                    file.write(frames,  photometric="minisblack", description="", metadata=None)
                    frameNumberWindow.extend(frameIDs)
                    self.frameCount += len(frames)
                    self.frameNumberUpdate.emit(channel, self.frameCount)
            elif recMode == RecMode.SpecTime:
                timeUnit = detector.frameInterval # us
                totalTime = kwargs["totalTime"] # s
                totalFrames = int(ceil(totalTime * 1e6 / timeUnit))
                logger.info(f"Recording time: {totalTime} s @{timeUnit} μs -> {totalFrames} frames")
                currentRecTime = 0
                start = time.time()
                index = 0
                while index < totalFrames and self.record:
                    frames, frameIDs = self.unpackChunk(detector)
                    file.write(frames, description='', metadata=None)
                    frameNumberWindow.extend(frameIDs)
                    self.timeCount = np.around(currentRecTime, decimals=2)
                    self.timeUpdate.emit(channel, min(self.timeCount, totalTime))
                    currentRecTime = time.time() - start
                    index += len(frames)
                self.frameCount = totalFrames
            elif recMode == RecMode.UntilStop:
                while self.record:
                    frames, frameIDs = self.unpackChunk(detector)
                    file.write(frames, description='', metadata=None)
                    frameNumberWindow.extend(frameIDs)
                    self.frameCount += len(frames)
        
            # we check that all frame IDs are equidistant
            if np.all(frameNumberWindow == 0):
                logger.error(f"[REC:{detector.name}] No frame IDs were provided for {detector.name}.")
            elif not np.all(np.ediff1d(frameNumberWindow) == 1):
                logger.error(f"[REC:{detector.name}] Frames lost. Frame interval: {detector.frameInterval} μs")
            omexml = tiff.OmeXml(
                Creator = "ImSwitch"
            )
            omexml.addimage(
                dtype=detector.dtype,
                shape=(self.frameCount, *reversed(detector.shape)),
                storedshape=(self.frameCount, 1, 1, *reversed(detector.shape), 1),
                axes='TYX',
                metadata=metadata
            )
            description = omexml.tostring(declaration=True)
            file.overwrite_description(description.encode())

DEFAULT_STORER_MAP: Dict[str, Type[Storer]] = {
    SaveFormat.ZARR: ZarrStorer,
    SaveFormat.HDF5: HDF5Storer,
    SaveFormat.TIFF: TiffStorer
}

class RecordingManager(SignalInterface):
    """ RecordingManager handles single frame captures as well as continuous
    recordings of detector data. """

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

    def __init__(self, detectorsManager, storerMap: Optional[Dict[str, Type[Storer]]] = None):
        super().__init__()
        self.__logger = initLogger(self)
        self.__storerMap: Dict[str, Type[Storer]] = storerMap or DEFAULT_STORER_MAP
        self._memRecordings: Dict[str, Type[BytesIO]] = {}  # { filePath: bytesIO }
        self.__detectorsManager : DetectorsManager = detectorsManager
        self.__record = False
        self.__signalBuffer = dict()
        self.__threadCount = 0
        self.__totalThreads = 0
        self.__recordingHandle = None
        self.__storersList : List[Storer] = []
        self.__storerThreads : List[StreamingWorker] = []
        self.__wasLiveActive = False
        self.__oldLiveHandle = None
        self.sigRecordingEnded.connect(self._resumeLiveView)

    def __del__(self):
        self.endRecording(emitSignal=False, wait=True)
        if hasattr(super(), '__del__'):
            super().__del__()

    @property
    def record(self):
        """ Whether a recording is currently started. """
        return self.__record

    @property
    def detectorsManager(self):
        return self.__detectorsManager
    
    def getFiles(self,
                savename: str,
                detectorNames: List[str],
                recMode: RecMode,
                saveMode: SaveMode,
                saveFormat: SaveFormat,
                singleLapseFile: bool = False) -> Tuple[dict, dict]:
        singleLapseFile = recMode == RecMode.ScanLapse and singleLapseFile

        fileDests = dict()
        filePaths = dict()
        extension = saveFormat.name.replace("-", ".").lower()

        for detectorName in detectorNames:
            baseFilePath = f'{savename}_{detectorName}.{extension}'

            filePaths[detectorName] = self.getSaveFilePath(
                baseFilePath,
                allowOverwriteDisk=singleLapseFile and saveMode != SaveMode.RAM,
                allowOverwriteMem=singleLapseFile and saveMode == SaveMode.RAM
            )

        for detectorName in detectorNames:
            if saveMode == SaveMode.RAM:
                memRecordings = self._memRecordings
                if (filePaths[detectorName] not in memRecordings or memRecordings[filePaths[detectorName]].closed):
                    memRecordings[filePaths[detectorName]] = BytesIO()
                fileDests[detectorName] = memRecordings[filePaths[detectorName]]
            else:
                fileDests[detectorName] = filePaths[detectorName]
        
        return fileDests, filePaths

    def _updateFramesCounter(self, channel: str, frameNumber: int) -> None:
        self.__signalBuffer[channel] = frameNumber
        self.sigRecordingFrameNumUpdated.emit(min(list(self.__signalBuffer.values())))
    
    def _updateSecondsCounter(self, channel: str, seconds: float) -> None:
        self.__signalBuffer[channel] = seconds
        self.sigRecordingTimeUpdated.emit(min(list(self.__signalBuffer.values())))
    
    def _closeThread(self, storer: Storer, thread: StreamingWorker) -> None:
        storer.record = False
        thread.quit()
        self.__threadCount += 1
        if self.__threadCount == self.__totalThreads:
            self.sigRecordingEnded.emit()
            self.sigRecordingFrameNumUpdated.emit(0)
            self.sigRecordingTimeUpdated.emit(0)
    
    def _resumeLiveView(self) -> None:
        if self.__wasLiveActive:
            self.__detectorsManager.startAcquisition(liveView=True)
            self.__wasLiveActive = False
            # we're now doing an hack...
            # the ViewController still believes
            # that the live view was active, and
            # in case the user wants to stop the
            # live view from the UI, the detectors
            # manager expects to find the same 
            # handle value; but the handle value
            # is randomly generated! hence we write back
            # the original hande value,
            # in order to override the handle randomly
            # generated by the startAcquisition call;
            # this is a bad hack, and is something
            # that should be reviewed with the architecture
            self.__detectorsManager._activeAcqLVHandles[0] = self.__oldLiveHandle
            
            

    def startRecording(self, 
                       detectorNames: List[str], 
                       recMode: RecMode, 
                       savename: str, 
                       saveMode: SaveMode, 
                       attrs: Dict[str, str],
                       saveFormat: SaveFormat = SaveFormat.HDF5, 
                       singleMultiDetectorFile: bool = False, 
                       singleLapseFile: bool = False,
                       recFrames: int = None, 
                       recTime: float = None):
        """ Starts a recording with the specified detectors, recording mode,
        file name prefix and attributes to save to the recording per detector.
        In SpecFrames mode, recFrames (the number of frames) must be specified,
        and in SpecTime mode, recTime (the recording time in seconds) must be
        specified. """

        self.__logger.info(f'Starting recording. Mode: {recMode.name}, save mode: {saveMode.name}, save format: {saveFormat.name}')
        
        self.__totalThreads = len(detectorNames)
        self.__threadCount = 0

        fileDests, filePaths = self.getFiles(savename, detectorNames, recMode, saveMode, saveFormat)
        recOptions = dict(totalFrames=recFrames, totalTime=recTime)
        self.__storersList = [self.__storerMap[saveFormat](path, dest, self.detectorsManager) for path, dest in zip(list(filePaths.values()), list(fileDests.values()))]
        self.__storerThreads = [create_worker(storer.stream,
                                    channel,
                                    recMode,
                                    saveMode,
                                    attrs[channel], 
                                    **recOptions,
                                    _worker_class=StreamingWorker,
                                    _start_thread=False) for (channel, storer) in zip(detectorNames, self.__storersList)]

        for storer in self.__storersList:
            storer.sigMemRecAvailable.connect(self.sigMemoryRecordingAvailable.emit)
        
        if recMode in [RecMode.SpecFrames, RecMode.ScanLapse]:
            for storer in self.__storersList:
                storer.frameNumberUpdate.connect(self._updateFramesCounter)
        elif recMode == RecMode.SpecTime:
            for storer in self.__storersList:
                storer.timeUpdate.connect(self._updateSecondsCounter)
        
        for storer, thread in zip(self.__storersList, self.__storerThreads):
            thread.finished.connect(
                lambda: self._closeThread(storer, thread)
            )

        self.__record = True
        self.__wasLiveActive = len(self.__detectorsManager._activeAcqLVHandles) == 1
        
        if self.__wasLiveActive:
            # we have to temporarely interrupt the live view, as for very fast acquisitions
            # the frames captured by the live thread will create gaps in the
            # video recording; having contigous recordings is necessary for applications
            # requiring specific timestamps
            self.__oldLiveHandle = self.__detectorsManager._activeAcqLVHandles[0]
            self.__detectorsManager.stopAcquisition(self.__oldLiveHandle, liveView=True)
        
        self.__recordingHandle = self.__detectorsManager.startAcquisition()
        self.sigRecordingStarted.emit()
        
        for thread in self.__storerThreads:
            thread.start()

    def endRecording(self, emitSignal=True, wait=True):
        """ Ends the current recording. Unless emitSignal is false, the
        sigRecordingEnded signal will be emitted. Unless wait is False, this
        method will wait until the recording is complete before returning. """

        if self.__recordingHandle != None:
            self.__detectorsManager.stopAcquisition(self.__recordingHandle)
            self.__recordingHandle = None
            if self.__record:
                self.__logger.info('Stopping recording')
                self.__record = False
            self.__detectorsManager.execOnAll(lambda c: c.flushBuffers(), condition=lambda c: c.forAcquisition)


    def snap(self, detectorNames, savename, saveMode, saveFormat, attrs):
        """ Saves an image with the specified detectors to a file
        with the specified name prefix, save mode, file format and attributes
        to save to the capture per detector. """
        acqHandle = self.__detectorsManager.startAcquisition()

        try:
            images = {}

            # Acquire data
            for detectorName in detectorNames:
                images[detectorName] = self.__detectorsManager[detectorName].getLatestFrame(is_save=True)

            if saveFormat:
                storer = self.__storerMap[saveFormat]

                if saveMode == SaveMode.Disk or saveMode == SaveMode.DiskAndRAM:
                    # Save images to disk
                    store = storer(savename, self.__detectorsManager)
                    store.snap(images, attrs)

                if saveMode == SaveMode.RAM or saveMode == SaveMode.DiskAndRAM:
                    for channel, image in images.items():
                        name = os.path.basename(f'{savename}_{channel}')
                        self.sigMemorySnapAvailable.emit(name, image, savename, saveMode == SaveMode.DiskAndRAM)

        finally:
            self.__detectorsManager.stopAcquisition(acqHandle)
            if saveMode == SaveMode.Numpy:
                return images

    def snapImagePrev(self, detectorName, savename, saveFormat, image, attrs):
        """ Saves a previously taken image to a file with the specified name prefix,
        file format and attributes to save to the capture per detector. """
        fileExtension = str(saveFormat.name).lower()
        filePath = self.getSaveFilePath(f'{savename}_{detectorName}.{fileExtension}')

        # Write file
        if saveFormat == SaveFormat.HDF5:
            file = h5py.File(filePath, 'w')

            shape = image.shape
            dataset = file.create_dataset('data', tuple(reversed(shape)), dtype='i2')

            for key, value in attrs[detectorName].items():
                try:
                    dataset.attrs[key] = value
                except:
                    self.__logger.debug(f'Could not put key:value pair {key}:{value} in hdf5 metadata.')

            dataset.attrs['detector_name'] = detectorName

            # For ImageJ compatibility
            dataset.attrs['element_size_um'] = \
                self.__detectorsManager[detectorName].pixelSizeUm

            dataset[:, ...] = np.moveaxis(image, 0, -1)
            file.close()
        elif saveFormat == SaveFormat.TIFF:
            tiff.imwrite(filePath, image)
        if saveFormat == SaveFormat.ZARR:
            path = self.getSaveFilePath(f'{savename}.{fileExtension}')
            store = zarr.storage.DirectoryStore(path)
            root = zarr.group(store=store)
            shape = self.__detectorsManager[detectorName].shape
            d = root.create_dataset(detectorName, data=image, shape=tuple(reversed(shape)), chunks=(512, 512),
                                    dtype='i2')
            d.attrs["ImSwitchData"] = attrs[detectorName]
            store.close()
        else:
            raise ValueError(f'Unsupported save format "{saveFormat}"')

    def getSaveFilePath(self, path, allowOverwriteDisk=False, allowOverwriteMem=False):
        newPath = path
        numExisting = 0

        def existsFunc(pathToCheck):
            if not allowOverwriteDisk and os.path.exists(pathToCheck):
                return True
            if not allowOverwriteMem and pathToCheck in self._memRecordings:
                return True
            return False

        while existsFunc(newPath):
            numExisting += 1
            pathWithoutExt, pathExt = os.path.splitext(path)
            newPath = f'{pathWithoutExt}_{numExisting}{pathExt}'
        return newPath

# Copyright (C) 2020-2021 ImSwitch developers
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
