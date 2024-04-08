import enum
import os
import time
from io import BytesIO
from typing import Dict, Optional, Type, List

import debugpy

import h5py
try:
    import zarr
except:
    pass
import numpy as np
import tifffile as tiff
import cv2

from imswitch.imcommon.framework import Signal, SignalInterface, Thread, Worker
from imswitch.imcommon.model import initLogger
from ome_zarr.writer import write_multiscales_metadata
from ome_zarr.format import format_from_version
import abc
import logging

from imswitch.imcontrol.model.managers.DetectorsManager import DetectorsManager

logger = logging.getLogger(__name__)


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


class Storer(abc.ABC):
    """ Base class for storing data"""
    def __init__(self, filepath, detectorManager):
        self.filepath = filepath
        self.detectorManager: DetectorsManager = detectorManager

    def snap(self, images: Dict[str, np.ndarray], attrs: Dict[str, str] = None):
        """ Stores images and attributes according to the spec of the storer """
        raise NotImplementedError

    def stream(self, data = None, **kwargs):
        """ Stores data in a streaming fashion. """
        raise NotImplementedError


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


class TiffStorer(Storer):
    """ A storer that stores the images in a series of tiff files """
    def snap(self, images: Dict[str, np.ndarray], attrs: Dict[str, str] = None):
        for channel, image in images.items():
            with AsTemporayFile(f'{self.filepath}_{channel}.tiff') as path:
                tiff.imwrite(path, image,) # TODO: Parse metadata to tiff meta data
                logger.info(f"Saved image to tiff file {path}")

class PNGStorer(Storer):
    """ A storer that stores the images in a series of png files """
    def snap(self, images: Dict[str, np.ndarray], attrs: Dict[str, str] = None):
        for channel, image in images.items():
            #with AsTemporayFile(f'{self.filepath}_{channel}.png') as path:
            path = f'{self.filepath}_{channel}.png'
            # if image is BW only, we have to convert it to RGB
            if image.dtype == np.float32 or image.dtype == np.float64:
                image = cv2.convertScaleAbs(image)
            if image.ndim == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            cv2.imwrite(path, image)
            del image
            logger.info(f"Saved image to png file {path}")

class JPGStorer(Storer):
    """ A storer that stores the images in a series of jpg files """
    def snap(self, images: Dict[str, np.ndarray], attrs: Dict[str, str] = None):
        for channel, image in images.items():
            #with AsTemporayFile(f'{self.filepath}_{channel}.jpg') as path:
            path = f'{self.filepath}_{channel}.jpg'
            # if image is BW only, we have to convert it to RGB
            if image.ndim == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            cv2.imwrite(path, image)
            logger.info(f"Saved image to jpg file {path}")
class MP4Storer(Storer):
    """ A storer that writes the frames to an MP4 file """

    def snap(self, images: Dict[str, np.ndarray], attrs: Dict[str, str] = None):
        # not yet implemented
        pass


class SaveMode(enum.Enum):
    Disk = 1
    RAM = 2
    DiskAndRAM = 3
    Numpy = 4


class SaveFormat(enum.Enum):
    TIFF = 1
    HDF5 = 2
    ZARR = 3
    MP4 = 4
    PNG = 5
    JPG = 6


DEFAULT_STORER_MAP: Dict[str, Type[Storer]] = {
    SaveFormat.ZARR: ZarrStorer,
    SaveFormat.HDF5: HDF5Storer,
    SaveFormat.TIFF: TiffStorer,
    SaveFormat.MP4: MP4Storer,
    SaveFormat.PNG: PNGStorer,
    SaveFormat.JPG: JPGStorer
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
        self.__storerMap = storerMap or DEFAULT_STORER_MAP
        self._memRecordings = {}  # { filePath: bytesIO }
        self.__detectorsManager = detectorsManager
        self.__record = False
        self.__recordingWorker = RecordingWorker(self)
        self.__thread = Thread()
        self.__recordingWorker.moveToThread(self.__thread)
        self.__thread.started.connect(self.__recordingWorker.run)

    def __del__(self):
        self.endRecording(emitSignal=False, wait=True)
        if hasattr(super(), '__del__'):
            super().__del__()

    @property
    def record(self):
        """ Whether a recording is currently being recorded. """
        return self.__record

    @property
    def detectorsManager(self):
        return self.__detectorsManager

    def startRecording(self, detectorNames, recMode, savename, saveMode, attrs,
                       saveFormat=SaveFormat.HDF5, singleMultiDetectorFile=False, singleLapseFile=False,
                       recFrames=None, recTime=None):
        """ Starts a recording with the specified detectors, recording mode,
        file name prefix and attributes to save to the recording per detector.
        In SpecFrames mode, recFrames (the number of frames) must be specified,
        and in SpecTime mode, recTime (the recording time in seconds) must be
        specified. """

        self.__logger.info('Starting recording')
        self.__record = True
        self.__recordingWorker.detectorNames = detectorNames
        self.__recordingWorker.recMode = recMode
        self.__recordingWorker.savename = savename
        self.__recordingWorker.saveMode = saveMode
        self.__recordingWorker.saveFormat = saveFormat
        self.__recordingWorker.attrs = attrs
        self.__recordingWorker.recFrames = recFrames
        self.__recordingWorker.recTime = recTime
        self.__recordingWorker.singleMultiDetectorFile = singleMultiDetectorFile
        self.__recordingWorker.singleLapseFile = singleLapseFile
        self.__detectorsManager.execOnAll(lambda c: c.flushBuffers(),
                                          condition=lambda c: c.forAcquisition)
        self.__thread.start()

    def endRecording(self, emitSignal=True, wait=True):
        """ Ends the current recording. Unless emitSignal is false, the
        sigRecordingEnded signal will be emitted. Unless wait is False, this
        method will wait until the recording is complete before returning. """

        self.__detectorsManager.execOnAll(lambda c: c.flushBuffers(),
                                          condition=lambda c: c.forAcquisition)

        if self.__record:
            self.__logger.info('Stopping recording')
        self.__record = False
        self.__thread.quit()
        if emitSignal:
            self.sigRecordingEnded.emit()
        if wait:
            self.__thread.wait()

    def snap(self, detectorNames=None, savename="", saveMode=SaveMode.Disk, saveFormat=SaveFormat.TIFF, attrs=None):
        """ Saves an image with the specified detectors to a file
        with the specified name prefix, save mode, file format and attributes
        to save to the capture per detector. """
        acqHandle = self.__detectorsManager.startAcquisition()

        if detectorNames is None:
            detectorNames = self.__detectorsManager.detectorNames

        try:
            images = {}

            # Acquire data
            for detectorName in detectorNames:
                images[detectorName] = self.__detectorsManager[detectorName].getLatestFrame(is_save=True)
                image = images[detectorName]

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

        except Exception as e:
            self.__logger.error(f'Failed to snap image: {e}')

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
        elif saveFormat == SaveFormat.PNG:
            cv2.imwrite(filePath, image)
        elif saveFormat == SaveFormat.JPG:
            cv2.imwrite(filePath, image)
        elif saveFormat == SaveFormat.ZARR:
            path = self.getSaveFilePath(f'{savename}.{fileExtension}')
            store = zarr.storage.DirectoryStore(path)
            root = zarr.group(store=store)
            shape = self.__detectorsManager[detectorName].shape
            d = root.create_dataset(detectorName, data=image, shape=tuple(reversed(shape)), chunks=(512, 512),
                                    dtype='i2')
            datasets = {"path": detectorName, "transformation": None}
            write_multiscales_metadata(root, datasets, format_from_version("0.2"), shape, **attrs)
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


class RecordingWorker(Worker):
    def __init__(self, recordingManager):
        super().__init__()
        self.__logger = initLogger(self)
        self.__recordingManager = recordingManager
        self.__logger = initLogger(self)

    def run(self):
        acqHandle = self.__recordingManager.detectorsManager.startAcquisition()
        try:
            self._record()

        finally:
            self.__recordingManager.detectorsManager.stopAcquisition(acqHandle)

    def _record(self):
        if self.saveFormat == SaveFormat.HDF5 or self.saveFormat == SaveFormat.ZARR:
            files, fileDests, filePaths = self._getFiles()

        shapes = {detectorName: self.__recordingManager.detectorsManager[detectorName].shape
                  for detectorName in self.detectorNames}

        currentFrame = {}
        datasets = {}
        filenames = {}

        for detectorName in self.detectorNames:
            currentFrame[detectorName] = 0

            datasetName = detectorName
            if self.recMode == RecMode.ScanLapse and self.singleLapseFile:
                # Add scan number to dataset name
                scanNum = 0
                datasetNameWithScan = f'{datasetName}_scan{scanNum}'
                while datasetNameWithScan in files[detectorName]:
                    scanNum += 1
                    datasetNameWithScan = f'{datasetName}_scan{scanNum}'
                datasetName = datasetNameWithScan

            # Initial number of frames must not be 0; otherwise, too much disk space may get
            # allocated. We remove this default frame later on if no frames are captured.
            shape = shapes[detectorName]
            if len(shape) > 2:
                shape = shape[-2:]

            if self.saveFormat == SaveFormat.HDF5:
                # Initial number of frames must not be 0; otherwise, too much disk space may get
                # allocated. We remove this default frame later on if no frames are captured.
                datasets[detectorName] = files[detectorName].create_dataset(
                    datasetName, (1, *reversed(shape)),
                    maxshape=(None, *reversed(shape)),
                    dtype='i2'
                )

                for key, value in self.attrs[detectorName].items():
                    self.__logger.debug(key)
                    self.__logger.debug(value)
                    try:
                        datasets[detectorName].attrs[key] = value
                    except:
                        pass

                datasets[detectorName].attrs['detector_name'] = detectorName

                # For ImageJ compatibility
                datasets[detectorName].attrs['element_size_um'] \
                    = self.__recordingManager.detectorsManager[detectorName].pixelSizeUm
                datasets[detectorName].attrs['writing'] = True

                for key, value in self.attrs[detectorName].items():
                    try:
                        datasets[detectorName].attrs[key] = value
                    except:
                        pass

            elif self.saveFormat == SaveFormat.MP4:
                # Need to initiliaze videowriter for each detector
                self.__logger.debug("Initialize MP4 recorder")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                fileExtension = str(self.saveFormat.name).lower()
                filePath = self.__recordingManager.getSaveFilePath(f'{self.savename}_{detectorName}.{fileExtension}')
                filenames[detectorName] = filePath
                datasets[detectorName] = cv2.VideoWriter(filePath, fourcc, 20.0, shapes[detectorName])
                #datasets[detectorName] = cv2.VideoWriter(filePath, cv2.VideoWriter_fourcc(*'MJPG'), 10, shapes[detectorName])


            elif self.saveFormat == SaveFormat.TIFF:
                fileExtension = str(self.saveFormat.name).lower()
                filenames[detectorName] = self.__recordingManager.getSaveFilePath(
                    f'{self.savename}_{detectorName}.{fileExtension}', False, False)

            elif self.saveFormat == SaveFormat.PNG:
                fileExtension = str(self.saveFormat.name).lower()
                filenames[detectorName] = self.__recordingManager.getSaveFilePath(
                    f'{self.savename}_{detectorName}.{fileExtension}', False, False)

            elif self.saveFormat == SaveFormat.JPG:
                fileExtension = str(self.saveFormat.name).lower()
                filenames[detectorName] = self.__recordingManager.getSaveFilePath(
                    f'{self.savename}_{detectorName}.{fileExtension}', False, False)

            elif self.saveFormat == SaveFormat.ZARR:
                datasets[detectorName] = files[detectorName].create_dataset(datasetName, shape=(1, *reversed(shape)),
                                                                            dtype='i2', chunks=(1, 512, 512)
                                                                            )
                datasets[detectorName].attrs['detector_name'] = detectorName
                # For ImageJ compatibility
                datasets[detectorName].attrs['element_size_um'] \
                    = self.__recordingManager.detectorsManager[detectorName].pixelSizeUm
                datasets[detectorName].attrs['writing'] = True
                info: List[dict] = [{"path": datasetName, "transformation": None}]
                write_multiscales_metadata(files[detectorName], info, format_from_version("0.2"), shape, **self.attrs[detectorName])


        self.__recordingManager.sigRecordingStarted.emit()
        try:
            if len(self.detectorNames) < 1:
                raise ValueError('No detectors to record specified')

            if self.recMode in [RecMode.SpecFrames, RecMode.ScanOnce, RecMode.ScanLapse]:
                recFrames = self.recFrames
                if recFrames is None:
                    raise ValueError('recFrames must be specified in SpecFrames, ScanOnce or'
                                     ' ScanLapse mode')

                while (self.__recordingManager.record and
                       any([currentFrame[detectorName] < recFrames
                            for detectorName in self.detectorNames])):
                    for detectorName in self.detectorNames:
                        if currentFrame[detectorName] >= recFrames:
                            continue  # Reached requested number of frames with this detector, skip

                        newFrames = self._getNewFrames(detectorName)
                        n = len(newFrames)

                        if n > 0:
                            it = currentFrame[detectorName]
                            if self.saveFormat == SaveFormat.TIFF:
                                try:
                                    filePath = filenames[detectorName]
                                    tiff.imwrite(filePath, newFrames, append=True)
                                except ValueError:
                                    self.__logger.error("TIFF File exceeded 4GB.")
                                    if self.saveFormat == SaveFormat.TIFF:
                                        filePath = self.__recordingManager.getSaveFilePath(
                                            f'{self.savename}_{detectorName}.{fileExtension}', False, False)
                                        continue
                            elif self.saveFormat == SaveFormat.HDF5:
                                dataset = datasets[detectorName]
                                if (it + n) <= recFrames:
                                    dataset.resize(n + it, axis=0)
                                    dataset[it:it + n, :, :] = newFrames
                                    currentFrame[detectorName] += n
                                else:
                                    dataset.resize(recFrames, axis=0)
                                    dataset[it:recFrames, :, :] = newFrames[0:recFrames - it]
                                    currentFrame[detectorName] = recFrames
                            elif self.saveFormat == SaveFormat.ZARR:
                                dataset = datasets[detectorName]
                                if it == 0:
                                    dataset[0, :, :] = newFrames[0, :, :]
                                    if n > 0:
                                        dataset.append(newFrames[1:n, :, :])
                                else:
                                    dataset.append(newFrames)
                                currentFrame[detectorName] += n
                            elif self.saveFormat == SaveFormat.MP4:
                                for iframe in range(n):
                                    frame = newFrames[iframe,:,:]
                                    #https://stackoverflow.com/questions/30509573/writing-an-mp4-video-using-python-opencv
                                    frame = cv2.cvtColor(cv2.convertScaleAbs(frame), cv2.COLOR_GRAY2BGR)
                                    self.__logger.debug(type(frame))

                                    datasets[detectorName].write(frame)


                            # Things get a bit weird if we have multiple detectors when we report
                            # the current frame number, since the detectors may not be synchronized.
                            # For now, we will report the lowest number.
                            self.__recordingManager.sigRecordingFrameNumUpdated.emit(
                                min(list(currentFrame.values()))
                            )
                    time.sleep(0.0001)  # Prevents freezing for some reason

                self.__recordingManager.sigRecordingFrameNumUpdated.emit(0)
            elif self.recMode == RecMode.SpecTime:
                recTime = self.recTime
                if recTime is None:
                    raise ValueError('recTime must be specified in SpecTime mode')

                start = time.time()
                currentRecTime = 0
                shouldStop = False
                while True:
                    for detectorName in self.detectorNames:
                        newFrames = self._getNewFrames(detectorName)
                        n = len(newFrames)
                        if n > 0:
                            if self.saveFormat == SaveFormat.TIFF:
                                try:
                                    filePath = filenames[detectorName]
                                    tiff.imwrite(filePath, newFrames, append=True)
                                except ValueError:
                                    self.__logger.error("TIFF File exceeded 4GB.")
                                    if self.saveFormat == SaveFormat.TIFF:
                                        filePath = self.__recordingManager.getSaveFilePath(
                                            f'{self.savename}_{detectorName}.{fileExtension}', False, False)
                                        continue
                            elif self.saveFormat == SaveFormat.HDF5 or self.saveFormat == SaveFormat.ZARR:
                                it = currentFrame[detectorName]
                                dataset = datasets[detectorName]
                                dataset.resize(n + it, axis=0)
                                dataset[it:it + n, :, :] = newFrames
                            elif self.saveFormat == SaveFormat.MP4:
                                for iframe in range(n):
                                    frame = newFrames[iframe,:,:]
                                    #https://stackoverflow.com/questions/30509573/writing-an-mp4-video-using-python-opencv
                                    frame = cv2.cvtColor(cv2.convertScaleAbs(frame), cv2.COLOR_GRAY2BGR)
                                    self.__logger.debug(type(frame))

                                    datasets[detectorName].write(frame)

                            currentFrame[detectorName] += n
                            self.__recordingManager.sigRecordingTimeUpdated.emit(
                                np.around(currentRecTime, decimals=2)
                            )
                            currentRecTime = time.time() - start

                    if shouldStop:
                        break  # Enter loop one final time, then stop

                    if not self.__recordingManager.record or currentRecTime >= recTime:
                        shouldStop = True

                    time.sleep(0.0001)  # Prevents freezing for some reason

                self.__recordingManager.sigRecordingTimeUpdated.emit(0)
            elif self.recMode == RecMode.UntilStop:
                shouldStop = False
                while True:
                    for detectorName in self.detectorNames:
                        newFrames = self._getNewFrames(detectorName)
                        n = len(newFrames)
                        if n > 0:
                            if self.saveFormat == SaveFormat.TIFF:
                                try:
                                    filePath = filenames[detectorName]
                                    tiff.imwrite(filePath, newFrames, append=True)
                                except ValueError:
                                    self.__logger.error("TIFF File exceeded 4GB.")
                                    if self.saveFormat == SaveFormat.TIFF:
                                        filePath = self.__recordingManager.getSaveFilePath(
                                            f'{self.savename}_{detectorName}.{fileExtension}', False, False)
                                        continue

                            elif self.saveFormat == SaveFormat.HDF5:
                                it = currentFrame[detectorName]
                                dataset = datasets[detectorName]
                                dataset.resize(n + it, axis=0)
                                dataset[it:it + n, :, :] = newFrames

                            elif self.saveFormat == SaveFormat.ZARR:
                                it = currentFrame[detectorName]
                                dataset = datasets[detectorName]
                                if it == 0:
                                    dataset[0, :, :] = newFrames[0, :, :]
                                    if n > 0:
                                        dataset.append(newFrames[1:n, :, :])
                                else:
                                    dataset.append(newFrames)
                            elif self.saveFormat == SaveFormat.MP4:
                                for iframe in range(n):
                                    frame = newFrames[iframe,:,:]
                                    #https://stackoverflow.com/questions/30509573/writing-an-mp4-video-using-python-opencv
                                    frame = cv2.cvtColor(cv2.convertScaleAbs(frame), cv2.COLOR_GRAY2BGR)

                                    datasets[detectorName].write(frame)


                            currentFrame[detectorName] += n

                    if shouldStop:
                        break

                    if not self.__recordingManager.record:
                        shouldStop = True  # Enter loop one final time, then stop

                    time.sleep(0.0001)  # Prevents freezing for some reason
            else:
                raise ValueError('Unsupported recording mode specified')
        finally:

            if self.saveFormat == SaveFormat.HDF5 or self.saveFormat == SaveFormat.ZARR:
                for detectorName, file in files.items():
                    # Remove default frame if no frames have been captured
                    if currentFrame[detectorName] < 1:
                        if self.saveFormat == SaveFormat.HDF5:
                            datasets[detectorName].resize(0, axis=0)

                    # Handle memory recordings
                    if self.saveMode == SaveMode.RAM or self.saveMode == SaveMode.DiskAndRAM:
                        filePath = filePaths[detectorName]
                        name = os.path.basename(filePath)
                        if self.saveMode == SaveMode.RAM:
                            file.close()
                            self.__recordingManager.sigMemoryRecordingAvailable.emit(
                                name, fileDests[detectorName], filePath, False
                            )
                        else:
                            file.flush()
                            self.__recordingManager.sigMemoryRecordingAvailable.emit(
                                name, file, filePath, True
                            )
                    else:
                        datasets[detectorName].attrs['writing'] = False
                        if self.saveFormat == SaveFormat.HDF5:
                            file.close()
                        elif self.saveFormat == SaveFormat.MP4:
                            for detectorName, file in files.items():
                                datasets[detectorName].release()
                        else:
                            self.store.close()
            emitSignal = True
            if self.recMode in [RecMode.SpecFrames, RecMode.ScanOnce, RecMode.ScanLapse]:
                emitSignal = False
            self.__recordingManager.endRecording(emitSignal=emitSignal, wait=False)

    def _getFiles(self):
        singleMultiDetectorFile = self.singleMultiDetectorFile
        singleLapseFile = self.recMode == RecMode.ScanLapse and self.singleLapseFile

        files = {}
        fileDests = {}
        filePaths = {}
        extension = 'hdf5' if self.saveFormat == SaveFormat.HDF5 else 'zarr'

        for detectorName in self.detectorNames:
            if singleMultiDetectorFile:
                baseFilePath = f'{self.savename}.{extension}'
            else:
                baseFilePath = f'{self.savename}_{detectorName}.{extension}'

            filePaths[detectorName] = self.__recordingManager.getSaveFilePath(
                baseFilePath,
                allowOverwriteDisk=singleLapseFile and self.saveMode != SaveMode.RAM,
                allowOverwriteMem=singleLapseFile and self.saveMode == SaveMode.RAM
            )

        for detectorName in self.detectorNames:
            if self.saveMode == SaveMode.RAM:
                memRecordings = self.__recordingManager._memRecordings
                if (filePaths[detectorName] not in memRecordings or
                        memRecordings[filePaths[detectorName]].closed):
                    memRecordings[filePaths[detectorName]] = BytesIO()
                fileDests[detectorName] = memRecordings[filePaths[detectorName]]
            else:
                fileDests[detectorName] = filePaths[detectorName]

            if singleMultiDetectorFile and len(files) > 0:
                files[detectorName] = list(files.values())[0]
            else:
                if self.saveFormat == SaveFormat.HDF5:
                    files[detectorName] = h5py.File(fileDests[detectorName],
                                                    'a' if singleLapseFile else 'w-')
                elif self.saveFormat == SaveFormat.ZARR:
                    self.store = zarr.storage.DirectoryStore(fileDests[detectorName])
                    files[detectorName] = zarr.group(store=self.store, overwrite=True)

        return files, fileDests, filePaths

    def _getNewFrames(self, detectorName):
        newFrames = self.__recordingManager.detectorsManager[detectorName].getChunk()
        newFrames = np.array(newFrames)
        return newFrames


class RecMode(enum.Enum):
    SpecFrames = 1
    SpecTime = 2
    ScanOnce = 3
    ScanLapse = 4
    UntilStop = 5


# Copyright (C) 2020-2023 ImSwitch developers
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
