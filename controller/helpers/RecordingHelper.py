# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 15:17:52 2020

@author: Testa4
"""
import enum
import time

import h5py
import numpy as np
from pyqtgraph.Qt import QtCore


class RecordingHelper:
    def __init__(self, commChannel, cameraHelper):
        self.__commChannel = commChannel
        self.__cameraHelper = cameraHelper
        self.__record = False
        self.__recordingWorker = RecordingWorker(self)
        self.__thread = QtCore.QThread()
        self.__recordingWorker.moveToThread(self.__thread)
        self.__thread.started.connect(self.__recordingWorker.run)
        
    @property
    def record(self):
        return self.__record

    @property
    def cameraHelper(self):
        return self.__cameraHelper

    @property
    def commChannel(self):
        return self.__commChannel

    def startRecording(self, cameraNames, recMode, savename, attrs, frames=None, time=None):
        self.__record = True    
        self.__recordingWorker.cameraNames = cameraNames
        self.__recordingWorker.recMode = recMode
        self.__recordingWorker.savename = savename
        self.__recordingWorker.attrs = attrs
        self.__recordingWorker.frames = frames
        self.__recordingWorker.time = time
        self.__cameraHelper.execOnAll(lambda c: c.updateCameraIndices())
        self.__thread.start()

    def endRecording(self):
        self.__record = False
        self.__thread.quit()
        self.__thread.wait()
    
    def snap(self, cameraNames, savename, attrs):
        for cameraName in cameraNames:
            file = h5py.File(f'{savename}_{cameraName}.hdf5', 'w', track_order=True)

            shape = self.__cameraHelper.execOn(cameraName, lambda c: c.shape)

            dataset = file.create_dataset('data', (shape[0], shape[1]), dtype='i2')

            for key, value in attrs[cameraName].items():
                file.attrs[key] = value

            umxpx = attrs[cameraName]['Camera_pixel_size']
            dataset.attrs["element_size_um"] = [1, umxpx, umxpx]

            dataset[:, :] = self.__cameraHelper.execOn(cameraName, lambda c: c.image)

            file.close()


class RecordingWorker(QtCore.QObject):
    def __init__(self, recordingHelper, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__recordingHelper = recordingHelper

    def run(self):
        files = {cameraName: h5py.File(f'{self.savename}_{cameraName}.hdf5', 'w')
                 for cameraName in self.cameraNames}

        shapes = {cameraName: self.__recordingHelper.cameraHelper.execOn(cameraName,
                                                                         lambda c: c.shape)
                  for cameraName in self.cameraNames}

        currentFrame = {}
        datasets = {}
        for cameraName in self.cameraNames:
            currentFrame[cameraName] = 0

            datasets[cameraName] = files[cameraName].create_dataset(
                'data', (1, shapes[cameraName][0], shapes[cameraName][1]),
                maxshape=(None, shapes[cameraName][0], shapes[cameraName][1]),
                dtype='i2'
            )

            for key, value in self.attrs[cameraName].items():
                files[cameraName].attrs[key] = value

            umxpx = self.attrs[cameraName]['Camera_pixel_size']
            datasets[cameraName].attrs["element_size_um"] = [1, umxpx, umxpx]

        try:
            if self.recMode == RecMode.SpecFrames:
                if len(self.cameraNames) > 1:
                    self.__recordingHelper.commChannel.endRecording.emit()
                    self.__recordingHelper.endRecording()
                    raise ValueError('Only one camera can be recorded in SpecFrames mode')

                cameraName = self.cameraNames[0]
                frames = self.frames
                while self.__recordingHelper.record and currentFrame[cameraName] < frames:
                    newframes, _ = self.__recordingHelper.cameraHelper.execOn(
                        cameraName, lambda c: c.getChunk()
                    )
                    n = len(newframes)
                    if n > 0:
                        it = currentFrame[cameraName]
                        dataset = datasets[cameraName]
                        if (it + n) <= frames:
                            dataset.resize(n + it, axis=0)
                            dataset[it:it + n, :, :] = np.reshape(newframes, [n, shapes[cameraName][0], shapes[cameraName][1]])
                            currentFrame[cameraName] += n
                        else:
                            dataset.resize(frames, axis=0)
                            dataset[it:frames, :, :] = np.reshape(newframes[0:frames - it], [frames-it, shapes[cameraName][0], shapes[cameraName][1]])
                            currentFrame[cameraName] = frames
                        self.__recordingHelper.commChannel.updateRecFrameNumber.emit(it)
                self.__recordingHelper.commChannel.updateRecFrameNumber.emit(0)
                self.__recordingHelper.commChannel.endRecording.emit()
                self.__recordingHelper.endRecording()
            elif self.recMode == RecMode.SpecTime:
                start = time.time()
                currentRecTime = 0
                while self.__recordingHelper.record and currentRecTime < self.time:
                    for cameraName in self.cameraNames:
                        newframes, _ = self.__recordingHelper.cameraHelper.execOn(
                            cameraName, lambda c: c.getChunk()
                        )
                        n = len(newframes)
                        if n > 0:
                            it = currentFrame[cameraName]
                            dataset = datasets[cameraName]
                            dataset.resize(n + it, axis=0)
                            dataset[it:it + n, :, :] = np.reshape(newframes, [n, shapes[cameraName][0], shapes[cameraName][1]])
                            currentFrame[cameraName] += n
                            self.__recordingHelper.commChannel.updateRecTime.emit(
                                np.around(currentRecTime, decimals=2)
                            )
                            currentRecTime = time.time() - start
                self.__recordingHelper.commChannel.updateRecTime.emit(0)
                self.__recordingHelper.commChannel.endRecording.emit()
                self.__recordingHelper.endRecording()
            else:
                while self.__recordingHelper.record:
                    for cameraName in self.cameraNames:
                        newframes, _ = self.__recordingHelper.cameraHelper.execOn(
                            cameraName, lambda c: c.getChunk()
                        )
                        n = len(newframes)
                        if n > 0:
                            it = currentFrame[cameraName]
                            dataset = datasets[cameraName]
                            dataset.resize(n + it, axis=0)
                            dataset[it:it + n, :, :] = np.reshape(newframes, [n, shapes[cameraName][0], shapes[cameraName][1]])
                            currentFrame[cameraName] += n
        finally:
            [file.close() for file in files.values()]


class RecMode(enum.Enum):
    NotRecording = 0
    SpecFrames = 1
    SpecTime = 2
    ScanOnce = 3
    ScanLapse = 4
    DimLapse = 5
    UntilStop = 6
