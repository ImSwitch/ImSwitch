# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 15:17:52 2020

@author: Testa4
"""
import time

import h5py
import numpy as np
from pyqtgraph.Qt import QtCore

from controller.enums import RecMode


class RecordingHelper():
    def __init__(self, comm_channel, cameraHelper):
        self.__comm_channel = comm_channel
        self.__cameraHelper = cameraHelper
        self.__record = False

    @property
    def record(self):
        return self.__record

    @property
    def cameraHelper(self):
        return self.__cameraHelper

    @property
    def comm_channel(self):
        return self.__comm_channel

    def startRecording(self, recMode, savename, attrs, frames=None, time=None):
        self.__record = True
        self.__recordingWorker = RecordingWorker(self)
        self.__thread = QtCore.QThread()
        self.__recordingWorker.moveToThread(self.__thread)
        self.__thread.started.connect(self.__recordingWorker.run)
        self.__recordingWorker.recMode = recMode
        self.__recordingWorker.savename = savename
        self.__recordingWorker.attrs = attrs
        self.__recordingWorker.frames = frames
        self.__recordingWorker.time = time
        self.__cameraHelper.updateCameraIndices()
        self.__thread.start(QtCore.QThread.HighestPriority)

    def endRecording(self):
        self.__record = False
        self.__thread.quit()
        self.__thread.wait()

    def snap(self, savename, attrs):
        store_file = h5py.File(savename + '.hdf5', 'w', track_order=True)
        for key in attrs.keys():
            store_file.attrs[key] = attrs[key]
        size = self.__cameraHelper.shapes
        d = store_file.create_dataset('data', (size[0], size[1]), dtype='i2')
        umxpx = attrs['Camera_pixel_size']
        d.attrs["element_size_um"] = [1, umxpx, umxpx]
        d[:, :] = self.__cameraHelper.image
        store_file.close()


class RecordingWorker(QtCore.QObject):
    def __init__(self, recordingHelper, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__recordingHelper = recordingHelper

    def run(self):
        self.running = True
        it = 0
        size = self.__recordingHelper.cameraHelper.shapes

        self.f = h5py.File(self.savename + '.hdf5', 'w')
        d = self.f.create_dataset('data', (1, size[0], size[1]), maxshape=(None, size[0], size[1]),
                                  dtype='i2')
        for key in self.attrs.keys():
            self.f.attrs[key] = self.attrs[key]
        umxpx = self.attrs['Camera_pixel_size']
        d.attrs["element_size_um"] = [1, umxpx, umxpx]

        if self.recMode == RecMode.SpecFrames:
            frames = self.frames
            while it < frames:
                newframes, _ = self.__recordingHelper.cameraHelper.getChunk()
                n = len(newframes)
                if n > 0:
                    if (it + n) <= frames:
                        d.resize(n + it, axis=0)
                        d[it:it + n, :, :] = np.array(newframes)
                        it += n
                    else:
                        d.resize(frames, axis=0)
                        d[it:frames, :, :] = np.array(newframes[0:frames - it])
                        it = frames
                    self.__recordingHelper.comm_channel.updateRecFrameNumber.emit(it)
            self.__recordingHelper.comm_channel.updateRecFrameNumber.emit(0)
            self.__recordingHelper.comm_channel.endRecording.emit()
            self.__recordingHelper.endRecording()
        elif self.recMode == RecMode.SpecTime:
            start = time.time()
            current = 0
            while current < self.time:
                newframes, _ = self.__recordingHelper.cameraHelper.getChunk()
                n = len(newframes)
                if n > 0:
                    d.resize(n + it, axis=0)
                    d[it:it + n, :, :] = np.array(newframes)
                    it += n
                    self.__recordingHelper.comm_channel.updateRecTime.emit(
                        np.around(current, decimals=2)
                    )
                    current = time.time() - start
            self.__recordingHelper.comm_channel.updateRecTime.emit(0)
            self.__recordingHelper.comm_channel.endRecording.emit()
            self.__recordingHelper.endRecording()

        else:
            while self.__recordingHelper.record:
                newframes, _ = self.__recordingHelper.cameraHelper.getChunk()
                n = len(newframes)
                if n > 0:
                    d.resize(n + it, axis=0)
                    d[it:it + n, :, :] = np.array(newframes)
                    it += n
            self.f.close()
