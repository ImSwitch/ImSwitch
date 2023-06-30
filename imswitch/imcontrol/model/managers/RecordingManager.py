import enum
import os
from datetime import datetime
from io import BytesIO
from typing import Dict, Optional, Type, List, Tuple
from types import DynamicClassAttribute

import h5py
import zarr
import numpy as np
import tifffile as tiff

from imswitch.imcommon.framework import (
    Signal,
    SignalInterface,
    RunnablePool
)
from imswitch.imcommon.model import initLogger

from imswitch.imcontrol.model.managers.detectors.DetectorManager import DetectorManager
from imswitch.imcontrol.model.managers.DetectorsManager import DetectorsManager

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

from imswitch.imcontrol.model.managers.storers.StorerManager import (
    RecMode,
    SaveMode,
    StreamingInfo
)
from imswitch.imcontrol.model.managers.storers import (
    StorerManager,
    ZarrStorerManager,
    HDF5StorerManager,
    TIFFStorerManager,
)


DEFAULT_STORER_MAP: Dict[str, Type[StorerManager]] = {
    SaveFormat.ZARR: ZarrStorerManager,
    SaveFormat.HDF5: HDF5StorerManager,
    SaveFormat.TIFF: TIFFStorerManager
}

class RecordingManager(SignalInterface):
    """ RecordingManager handles single frame captures as well as continuous
    recordings of detector data. """

    sigRecordingStarted = Signal()
    sigRecordingEnded = Signal()
    sigRecordingFrameNumUpdated = Signal(int)  # (frameNumber)
    sigRecordingTimeUpdated = Signal(float)  # (recTime)
    sigMemorySnapAvailable = Signal(
        str, np.ndarray, object, bool
    )  # (name, image, filePath, savedToDisk)
    sigMemoryRecordingAvailable = Signal(
        str, object, object, bool
    )  # (name, file, filePath, savedToDisk)

    def __init__(self, detectorsManager, storerMap: Optional[Dict[str, Type[StorerManager]]] = None):
        super().__init__()
        self.__logger = initLogger(self)
        self.__storerMap: Dict[str, Type[StorerManager]] = storerMap or DEFAULT_STORER_MAP
        self._memRecordings: Dict[str, Type[BytesIO]] = {}  # { filePath: bytesIO }
        self.__detectorsManager : DetectorsManager = detectorsManager
        self.__runnablePool : RunnablePool = RunnablePool()
        self.__record = False
        self.__signalBuffer = dict()
        self.__threadCount = 0
        self.__totalThreads = 0
        self.__recordingHandle = None
        self.__storersList : List[StorerManager] = []
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
    
    def _updateFinishedThreadCount(self) -> None:
        self.__threadCount += 1
        if self.__threadCount == self.__totalThreads:
            self.sigRecordingFrameNumUpdated.emit(0)
            self.sigRecordingTimeUpdated.emit(0)
            self.endRecording()
    
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
        
        self.__totalThreads = len(detectorNames)
        self.__threadCount = 0
        virtualFiles, filePaths = self.getFiles(savename, detectorNames, recMode, saveMode, saveFormat)
        self.__storersList = []

        for path, virtual, (id, detectorName) in zip(list(filePaths.values()), list(virtualFiles.values()), enumerate(detectorNames, start=1)):
            streamInfo = StreamingInfo(
                filePath=path,
                virtualFile=virtual,
                detector=self.detectorsManager[detectorName],
                storeID=id,
                recMode=recMode,
                saveMode=saveMode,
                attrs=attrs[detectorName],
                totalFrames=recFrames,
                totalTime=recTime
            )

            storer = self.__storerMap[saveFormat](streamInfo)
            storer.signals.sigMemRecAvailable.connect(self.sigMemoryRecordingAvailable.emit)
            storer.signals.finished.connect(self._updateFinishedThreadCount)
            if recMode in [RecMode.SpecFrames, RecMode.ScanLapse]:
                storer.signals.frameNumberUpdate.connect(self._updateFramesCounter)
            elif recMode == RecMode.SpecTime:
                storer.signals.timeUpdate.connect(self._updateSecondsCounter)
            self.__storersList.append(storer)

        self.__record = True
        self.__wasLiveActive = len(self.detectorsManager._activeAcqLVHandles) == 1
        
        if self.__wasLiveActive:
            # we have to temporarely interrupt the live view, as for very fast acquisitions
            # the frames captured by the live thread will create gaps in the
            # video recording; having contigous recordings is necessary for applications
            # requiring specific timestamps
            self.__oldLiveHandle = self.detectorsManager._activeAcqLVHandles[0]
            self.detectorsManager.stopAcquisition(self.__oldLiveHandle, liveView=True)
        
        self.__recordingHandle = self.detectorsManager.startAcquisition()
        self.sigRecordingStarted.emit()
        
        self.__logger.info('Starting recording threads')
        for storer in self.__storersList:
            self.__runnablePool.start(storer)

    def endRecording(self, emitSignal=True, wait=True):
        """ Ends the current recording. Unless emitSignal is false, the
        sigRecordingEnded signal will be emitted. Unless wait is False, this
        method will wait until the recording is complete before returning. """

        if self.__recordingHandle != None:
            self.detectorsManager.stopAcquisition(self.__recordingHandle)
            self.__recordingHandle = None
            if self.__record:
                self.__logger.info('Stopping recording')
                self.__record = False
            self.detectorsManager.execOnAll(lambda c: c.flushBuffers(), condition=lambda c: c.forAcquisition)
        if emitSignal:
            self.sigRecordingEnded.emit()


    def snap(self, detectorNames, savename, saveMode, saveFormat, attrs):
        """ Saves an image with the specified detectors to a file
        with the specified name prefix, save mode, file format and attributes
        to save to the capture per detector. """

        images = {}
        detectors = {}
        acqHandle = self.__detectorsManager.startAcquisition()

        # Collect the images and the detectors reference. 
        # We'll use the latter to access metadata information.
        for detectorName in detectorNames:
            detectors[detectorName] : DetectorManager = self.__detectorsManager[detectorName]
            images[detectorName] = detectors[detectorName].getLatestFrame(is_save=True)
        self.__detectorsManager.stopAcquisition(acqHandle)

        if saveFormat:
            storer : StorerManager = self.__storerMap[saveFormat]
            if saveMode == SaveMode.Disk or saveMode == SaveMode.DiskAndRAM:
                # Save images to disk
                kwargs = dict(filepath=savename, 
                            detectors=detectors,
                            acquisitionDate=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                storer.saveSnap(images, attrs, savename, **kwargs)
            if saveMode == SaveMode.RAM or saveMode == SaveMode.DiskAndRAM:
                for channel, image in images.items():
                    name = os.path.basename(f'{savename}_{channel}')
                    self.sigMemorySnapAvailable.emit(name, image, savename, saveMode == SaveMode.DiskAndRAM)
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
