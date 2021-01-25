# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 15:17:52 2020

@author: Testa4
"""
import enum
import os
import time

import h5py
import numpy as np

from imcommon.framework import Signal, SignalInterface, Thread, Worker


class RecordingManager(SignalInterface):
    recordingEnded = Signal()
    recordingFrameNumUpdated = Signal(int)  # (frameNumber)
    recordingTimeUpdated = Signal(int)  # (recTime)
    memoryRecordingAvailable = Signal(str, object, np.ndarray)  # (name, path, data)

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

    def startRecording(self, detectorNames, recMode, savename, keepInMemory, attrs,
                       recFrames=None, recTime=None):
        self.__record = True    
        self.__recordingWorker.detectorNames = detectorNames
        self.__recordingWorker.recMode = recMode
        self.__recordingWorker.savename = savename
        self.__recordingWorker.attrs = attrs
        self.__recordingWorker.recFrames = recFrames
        self.__recordingWorker.recTime = recTime
        self.__recordingWorker.keepInMemory = keepInMemory
        self.__detectorsManager.execOnAll(lambda c: c.flushBuffers())
        self.__thread.start()

    def endRecording(self, emitSignal=True):
        self.__record = False
        self.__thread.quit()
        if emitSignal:
            self.recordingEnded.emit()
        self.__thread.wait()
    
    def snap(self, detectorNames, savename, attrs):
        for detectorName in detectorNames:
            file = h5py.File(f'{savename}_{detectorName}.hdf5', 'w', track_order=True)

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
        files = {detectorName: h5py.File(f'{self.savename}_{detectorName}.hdf5', 'w')
                 for detectorName in self.detectorNames}

        shapes = {detectorName: self.__recordingManager.detectorsManager[detectorName].shape
                  for detectorName in self.detectorNames}

        currentFrame = {}
        datasets = {}
        for detectorName in self.detectorNames:
            currentFrame[detectorName] = 0

            datasets[detectorName] = files[detectorName].create_dataset(
                'data', (1, shapes[detectorName][0], shapes[detectorName][1]),
                maxshape=(None, shapes[detectorName][0], shapes[detectorName][1]),
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
                        self.__recordingManager.recordingFrameNumUpdated.emit(it)
                self.__recordingManager.recordingFrameNumUpdated.emit(0)
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
                            self.__recordingManager.recordingTimeUpdated.emit(
                                np.around(currentRecTime, decimals=2)
                            )
                            currentRecTime = time.time() - start
                self.__recordingManager.recordingTimeUpdated.emit(0)
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
            if self.keepInMemory:
                for detectorName in self.detectorNames:
                    path = files[detectorName].filename
                    name = os.path.basename(path)
                    data = np.array(list(datasets.values())[0][:])
                    self.__recordingManager.memoryRecordingAvailable.emit(name, path, data)

            [file.close() for file in files.values()]


class RecMode(enum.Enum):
    SpecFrames = 1
    SpecTime = 2
    ScanOnce = 3
    ScanLapse = 4
    DimLapse = 5
    UntilStop = 6
