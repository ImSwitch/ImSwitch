# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 15:17:52 2020

@author: Testa4
"""
import enum
import os
import time
from io import BytesIO

import h5py
import numpy as np

from imcommon.framework import Signal, SignalInterface, Thread, Worker


class RecordingManager(SignalInterface):
    sigRecordingEnded = Signal()
    sigRecordingFrameNumUpdated = Signal(int)  # (frameNumber)
    sigRecordingTimeUpdated = Signal(int)  # (recTime)
    sigMemoryRecordingAvailable = Signal(str, object, object, bool)  # (name, file, filePath, savedToDisk)

    def __init__(self, detectorsManager):
        super().__init__()
        self.__detectorsManager = detectorsManager
        self.__record = False
        self.__recordingWorker = RecordingWorker(self)
        self.__thread = Thread()
        self.__recordingWorker.moveToThread(self.__thread)
        self.__thread.started.connect(self.__recordingWorker.run)
        
    @property
    def record(self):
        return self.__record

    @property
    def detectorsManager(self):
        return self.__detectorsManager

    def startRecording(self, detectorNames, recMode, savename, saveMode, attrs,
                       recFrames=None, recTime=None):
        self.__record = True    
        self.__recordingWorker.detectorNames = detectorNames
        self.__recordingWorker.recMode = recMode
        self.__recordingWorker.savename = savename
        self.__recordingWorker.attrs = attrs
        self.__recordingWorker.recFrames = recFrames
        self.__recordingWorker.recTime = recTime
        self.__recordingWorker.saveMode = saveMode
        self.__detectorsManager.execOnAll(lambda c: c.flushBuffers())
        self.__thread.start()

    def endRecording(self, emitSignal=True):
        self.__record = False
        self.__thread.quit()
        if emitSignal:
            self.sigRecordingEnded.emit()
        self.__thread.wait()
    
    def snap(self, detectorNames, savename, attrs):
        for detectorName in detectorNames:
            file = h5py.File(f'{savename}_{detectorName}.hdf5', 'w')

            shape = self.__detectorsManager[detectorName].shape
            dataset = file.create_dataset('data', (shape[0], shape[1]), dtype='i2')

            for key, value in attrs[detectorName].items():
                file.attrs[key] = value

            dataset[:, :] = self.__detectorsManager[detectorName].image
            file.close()


class RecordingWorker(Worker):
    def __init__(self, recordingManager):
        super().__init__()
        self.__recordingManager = recordingManager

    def run(self):
        files = {}
        fileHandles = {}
        filePaths = {}
        for detectorName in self.detectorNames:
            filePaths[detectorName] = f'{self.savename}_{detectorName}.hdf5'
            fileHandles[detectorName] = BytesIO() if self.saveMode == SaveMode.RAM else filePaths[detectorName]
            files[detectorName] = h5py.File(fileHandles[detectorName], 'w')

        shapes = {detectorName: self.__recordingManager.detectorsManager[detectorName].shape
                  for detectorName in self.detectorNames}

        currentFrame = {}
        datasets = {}
        for detectorName in self.detectorNames:
            currentFrame[detectorName] = 0

            datasets[detectorName] = files[detectorName].create_dataset(
                'data', (1, *shapes[detectorName]),
                maxshape=(None, *shapes[detectorName]),
                dtype='i2'
            )

            for key, value in self.attrs[detectorName].items():
                files[detectorName].attrs[key] = value

        try:
            if self.recMode == RecMode.SpecFrames:
                if len(self.detectorNames) > 1:
                    self.__recordingManager.endRecording()
                    raise ValueError('Only one detector can be recorded in SpecFrames mode')

                detectorName = self.detectorNames[0]
                frames = self.recFrames
                while self.__recordingManager.record and currentFrame[detectorName] < frames:
                    newFrames, _ = self.__recordingManager.detectorsManager[detectorName].getChunk()
                    n = len(newFrames)
                    if n > 0:
                        it = currentFrame[detectorName]
                        dataset = datasets[detectorName]
                        if (it + n) <= frames:
                            dataset.resize(n + it, axis=0)
                            dataset[it:it + n, :, :] = newFrames
                            currentFrame[detectorName] += n
                        else:
                            dataset.resize(frames, axis=0)
                            dataset[it:frames, :, :] = newFrames[0:frames - it]
                            currentFrame[detectorName] = frames
                        self.__recordingManager.sigRecordingFrameNumUpdated.emit(it)
                self.__recordingManager.sigRecordingFrameNumUpdated.emit(0)
                self.__recordingManager.endRecording()
            elif self.recMode == RecMode.SpecTime:
                start = time.time()
                currentRecTime = 0
                while self.__recordingManager.record and currentRecTime < self.recTime:
                    for detectorName in self.detectorNames:
                        newFrames, _ = self.__recordingManager.detectorsManager[detectorName].getChunk()
                        n = len(newFrames)
                        if n > 0:
                            it = currentFrame[detectorName]
                            dataset = datasets[detectorName]
                            dataset.resize(n + it, axis=0)
                            dataset[it:it + n, :, :] = newFrames
                            currentFrame[detectorName] += n
                            self.__recordingManager.sigRecordingTimeUpdated.emit(
                                np.around(currentRecTime, decimals=2)
                            )
                            currentRecTime = time.time() - start
                self.__recordingManager.sigRecordingTimeUpdated.emit(0)
                self.__recordingManager.endRecording()
            else:
                while self.__recordingManager.record:
                    for detectorName in self.detectorNames:
                        newFrames, _ = self.__recordingManager.detectorsManager[detectorName].getChunk()
                        n = len(newFrames)
                        if n > 0:
                            it = currentFrame[detectorName]
                            dataset = datasets[detectorName]
                            dataset.resize(n + it, axis=0)
                            dataset[it:it + n, :, :] = newFrames
                            currentFrame[detectorName] += n
        finally:
            for detectorName, file in files.items():
                if self.saveMode == SaveMode.RAM or self.saveMode == SaveMode.DiskAndRAM:
                    filePath = filePaths[detectorName]
                    name = os.path.basename(filePath)
                    if self.saveMode == SaveMode.RAM:
                        file.close()
                        self.__recordingManager.sigMemoryRecordingAvailable.emit(
                            name, fileHandles[detectorName], filePath, False
                        )
                    else:
                        self.__recordingManager.sigMemoryRecordingAvailable.emit(name, file, filePath, True)
                else:
                    file.close()


class RecMode(enum.Enum):
    SpecFrames = 1
    SpecTime = 2
    ScanOnce = 3
    ScanLapse = 4
    DimLapse = 5
    UntilStop = 6


class SaveMode(enum.Enum):
    Disk = 1
    RAM = 2
    DiskAndRAM = 3
