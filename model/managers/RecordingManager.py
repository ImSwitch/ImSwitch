# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 15:17:52 2020

@author: Testa4
"""
import enum
import time

import h5py
import numpy as np

from framework import Signal, SignalInterface, Thread, Worker


class RecordingManager(SignalInterface):
    recordingEnded = Signal()
    recordingFrameNumUpdated = Signal(int)  # (frameNumber)
    recordingTimeUpdated = Signal(int)  # (recTime)

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

    def startRecording(self, detectorNames, recMode, savename, attrs, frames=None, time=None):
        self.__record = True    
        self.__recordingWorker.detectorNames = detectorNames
        self.__recordingWorker.recMode = recMode
        self.__recordingWorker.savename = savename
        self.__recordingWorker.attrs = attrs
        self.__recordingWorker.frames = frames
        self.__recordingWorker.time = time
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
            dataset = file.create_dataset(f'data:{detectorName}', (shape[0], shape[1]), dtype='i2')

            for key, value in attrs[detectorName].items():
                #print(key)
                #print(value)
                file.attrs[key] = value
                dataset.attrs[key] = value

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
                frames = self.frames
                while self.__recordingManager.record and currentFrame[detectorName] < frames:
                    newframes, _ = self.__recordingManager.detectorsManager[detectorName].getChunk()
                    n = len(newframes)
                    if n > 0:
                        it = currentFrame[detectorName]
                        dataset = datasets[detectorName]
                        if (it + n) <= frames:
                            dataset.resize(n + it, axis=0)
                            dataset[it:it + n, :, :] = np.reshape(newframes, [n, shapes[detectorName][0], shapes[detectorName][1]])
                            currentFrame[detectorName] += n
                        else:
                            dataset.resize(frames, axis=0)
                            dataset[it:frames, :, :] = np.reshape(newframes[0:frames - it], [frames-it, shapes[detectorName][0], shapes[detectorName][1]])
                            currentFrame[detectorName] = frames
                        self.__recordingManager.recordingFrameNumUpdated.emit(it)
                self.__recordingManager.recordingFrameNumUpdated.emit(0)
                self.__recordingManager.endRecording()
            elif self.recMode == RecMode.SpecTime:
                start = time.time()
                currentRecTime = 0
                while self.__recordingManager.record and currentRecTime < self.time:
                    for detectorName in self.detectorNames:
                        newframes, _ = self.__recordingManager.detectorsManager[detectorName].getChunk()
                        n = len(newframes)
                        if n > 0:
                            it = currentFrame[detectorName]
                            dataset = datasets[detectorName]
                            dataset.resize(n + it, axis=0)
                            dataset[it:it + n, :, :] = np.reshape(newframes, [n, shapes[detectorName][0], shapes[detectorName][1]])
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
                        newframes, _ = self.__recordingManager.detectorsManager[detectorName].getChunk()
                        n = len(newframes)
                        if n > 0:
                            it = currentFrame[detectorName]
                            dataset = datasets[detectorName]
                            dataset.resize(n + it, axis=0)
                            dataset[it:it + n, :, :] = np.reshape(newframes, [n, shapes[detectorName][0], shapes[detectorName][1]])
                            currentFrame[detectorName] += n
        finally:
            [file.close() for file in files.values()]


class RecMode(enum.Enum):
    SpecFrames = 1
    SpecTime = 2
    ScanOnce = 3
    ScanLapse = 4
    DimLapse = 5
    UntilStop = 6
