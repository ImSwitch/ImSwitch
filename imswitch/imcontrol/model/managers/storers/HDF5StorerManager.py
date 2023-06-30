import numpy as np
import h5py
import time
import os
from math import ceil
from typing import Any, Dict
from numpy import ndarray
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model.configfiletools import _debugLogDir
from imswitch.imcontrol.model.managers.storers.StorerManager import RecMode, SaveMode
from .StorerManager import (
    StorerManager,
    RecMode,
    SaveMode
)

class HDF5StorerManager(StorerManager):
    """ An HDF5 implementation of a data streaming object. See `StorerManager` for details on the interface. """
    
    @classmethod
    def saveSnap(self, images: Dict[str, ndarray], attrs: Dict[str, str], **kwargs) -> None:
        logger = initLogger(self)

        for channel, image in images.items():
            filePath = kwargs["filePath"]
            detector = kwargs["detectors"][channel]
            with h5py.File(f"{filePath}_{channel}.h5", "w") as file:
                shape = image.shape
                dataset = file.create_dataset('data', tuple(reversed(shape)), dtype=detector.dtype)
                for key, value in attrs.items():
                    try:
                        dataset.attrs[key] = value
                    except:
                        logger.debug(f'Could not put key:value pair {key}:{value} in hdf5 metadata.')

                dataset.attrs['detector_name'] = channel

                # For ImageJ compatibility
                dataset.attrs['element_size_um'] = detector.pixelSizeUm

                if image.ndim == 3:
                    dataset[:, ...] = np.moveaxis(image, [0, 1, 2], [2, 1, 0])
                elif image.ndim == 4:
                    dataset[:, ...] = np.moveaxis(image, [0, 1, 2, 3], [3, 2, 1, 0])
                else:
                    dataset[:, ...] = np.moveaxis(image, 0, -1)
            logger.info(f"Saved image to hdf5 file {filePath}_{channel}.h5")

    def stream(self, recMode: RecMode, saveMode: SaveMode, attrs: Dict[str, str], **kwargs) -> None:

        self.logger.info("Storer {}. Detector name: {}".format(self.streamInfo.storeID, self.streamInfo.detector.name))
        self.record = True
        frameNumberWindow = []
        pixelSize = self.streamInfo.detector.pixelSizeUm
        channel = self.streamInfo.detector.name
        shape = self.streamInfo.detector.shape
        dtype = self.streamInfo.detector.dtype
        frameInterval = self.streamInfo.detector.frameInterval
        imageProcessing = self.streamInfo.detector.imageProcessing
        
        def create_dataset(file: h5py.File, name: str, shape: tuple, compression: str = None) -> h5py.Dataset:
            """ Create a frame dataset and a frame ID dataset to store recordings.

            Args:
                file (`h5py.File`): file handler
                name (`str`): name of the detector
                shape (`tuple`): size of the video to record

            Returns:
                h5py.Dataset: the created dataset
            """
            dataset = file.create_dataset(name,
                                        dtype=self.streamInfo.detector.dtype,
                                        shape=shape, 
                                        maxshape=(None, *shape[1:]), 
                                        compression=compression)
            for key, value in attrs.items():
                try:
                    dataset.attrs[key] = value
                except:
                    self.__logger.debug(f'Could not put key:value pair {key}:{value} in hdf5 metadata.')
            dataset.attrs["detector_name"] = name
            dataset.attrs["element_size_um"] = pixelSize
            return dataset
        
        if saveMode == SaveMode.RAM:
            file = h5py.File(self.streamInfo.virtualFile, mode="a")
        else:
            file = h5py.File(self.streamInfo.filePath, mode="a")

        if recMode in [RecMode.SpecFrames, RecMode.ScanLapse]:
            totalFrames = kwargs["totalFrames"]
            self.frameCount = 0
            dataset = create_dataset(file, channel, (totalFrames, *reversed(shape)))
            while self.frameCount < totalFrames and self.record:
                frames, frameIDs = self.unpackChunk()
                if self.frameCount + len(frames) > totalFrames:
                    # we only collect the remaining frames required,
                    # and discard the remaining
                    frames = frames[0: totalFrames - self.frameCount]
                    frameIDs = frameIDs[0: totalFrames - self.frameCount]
                dataset[self.frameCount : self.frameCount + len(frames)] = frames
                frameNumberWindow.extend(frameIDs)
                self.frameCount += len(frames)
                self.signals.frameNumberUpdate.emit(channel, self.frameCount)
        elif recMode == RecMode.SpecTime:
            totalTime = kwargs["totalTime"] # s
            totalFrames = int(ceil(totalTime * 1e6 / frameInterval))
            dataset = create_dataset(file, channel, (totalFrames, *reversed(shape)))
            currentRecTime = 0
            start = time.perf_counter()
            index = 0
            while index < totalFrames and self.record:
                try:
                    frames, frameIDs = self.unpackChunk()
                    nframes = len(frames)
                    dataset[index: index + nframes] = frames
                    frameNumberWindow.extend(frameIDs)
                    self.timeCount = np.around(currentRecTime, decimals=2)
                    self.signals.timeUpdate.emit(channel, min(self.timeCount, totalTime))
                    index += nframes
                    currentRecTime = time.perf_counter() - start
                except Exception as e:
                    self.logger.error("Error while recording: %s", e)
                    self.record = False
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
            totalTime = 1e6 # us
            totalFrames = int(ceil(totalTime / frameInterval))
            dataset = create_dataset(file, channel, (totalFrames, *reversed(shape)))
            index = 0
            while self.record:
                frames, frameIDs = self.unpackChunk()
                nframes = len(frames)
                if nframes > index:
                    dataset.resize(index + totalFrames, axis=0)
                dataset[index: nframes] = frames
                frameNumberWindow.extend(frameIDs)
                index += nframes
        else:
            self.logger.error("Unknown recording mode.")
        # we write the ids to a separate dataset;
        # after testing, for large recordings we go 
        # over the maximum attribute size of 64k,
        # so we just write the data separately
        file.create_dataset(f"data_id", data=frameNumberWindow)
        if dtype == np.int16:
            new_dset = create_dataset(file, file["data"].shape, "data1", dtype=np.float32)
            new_dset[:] = dataset[:]
            del file["data"]
        if len(imageProcessing) > 0:
            for key, value in imageProcessing.items():
                file.create_dataset(key, data=value["content"])
        
        # we check that all frame IDs are equidistant
        if np.all(frameNumberWindow == 0):
            self.logger.warning(f"No frame IDs were provided for detector \'{channel}\'.")
        elif not np.all(np.ediff1d(frameNumberWindow) == 1):
            dbgPath = os.path.join(_debugLogDir, f"frame_id_differences_{channel}.txt")
            self.logger.error(f"[{channel}] Frames lost. Frame interval: {frameInterval} μs")
            self.logger.error(f"[{channel}] You can find the frame ID list in {dbgPath}")
            np.savetxt(os.path.join(_debugLogDir, f"frame_id_differences_{channel}.txt"), np.ediff1d(frameNumberWindow), fmt="%d")

        if saveMode in [SaveMode.DiskAndRAM, SaveMode.RAM]:
            if saveMode == SaveMode.DiskAndRAM:
                file.flush()
                self.signals.sigMemRecAvailable.emit(channel, file, self.streamInfo.filePath, True)
            else:
                file.close()
                self.signals.sigMemRecAvailable.emit(channel, self.streamInfo.virtualFile, self.streamInfo.filePath, False)
        else:
            file.close()
        self.signals.finished.emit()