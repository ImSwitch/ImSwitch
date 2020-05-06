# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 15:17:52 2020

@author: Testa4
"""
from pyqtgraph.Qt import QtCore
import numpy as np
import h5py
import time

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
        print('Start recording')
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
        self.__record = True
        self.__thread.start()
        
    def endRecording(self):
        self.__record = False
        self.__recordingWorker.f.close()
        self.__thread.terminate()
                   
    def snap(self, savename, attrs):
        store_file = h5py.File(savename, 'w', track_order=True)
        for key in attrs.keys():
            store_file.attrs[key] = attrs[key]
        size = self.__cameraHelper.shapes
        d = store_file.create_dataset('data', (size[0], size[1]),  dtype = 'i2')
        umxpx = attrs['Camera_pixel_size']
        d.attrs["element_size_um"] = [1, umxpx, umxpx] 
        d[:, :] = self.__cameraHelper.image
        store_file.close()
        
class RecordingWorker(QtCore.QObject):
    def __init__(self, recordingHelper, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__recordingHelper = recordingHelper

    def run(self):
        it = 0
        self.f = h5py.File(self.savename, 'w') 
        for key in self.attrs.keys():
            self.f.attrs[key] = self.attrs[key]
        size = self.__recordingHelper.cameraHelper.shapes
        print(size)
        d = self.f.create_dataset('data', (1, size[0], size[1]), maxshape=(None, size[0], size[1]), dtype='i2')
        umxpx = self.attrs['Camera_pixel_size']
        d.attrs["element_size_um"] = [1, umxpx, umxpx]
        if self.recMode == 1:
            frames = self.frames
            while it<frames:
                newframes = self.__recordingHelper.cameraHelper.getChunk()
                n = len(newframes)
                if (it+n)<=frames:
                    d.resize(n + it, axis = 0)
                    d[it:it+n, :,:] = np.array(newframes)
                    it += n 
                else:
                    d.resize(frames, axis = 0)     
                    d[it:frames, :, :] = np.array(newframes[0:frames-it])
                    it = frames
                self.__recordingHelper.comm_channel.updateRecFrameNumber(it)
            self.__recordingHelper.comm_channel.updateRecFrameNumber(0)
            self.__recordingHelper.comm_channel.endRecording()
            self.__recordingHelper.endRecording()
        elif self.recMode == 2:
            start = time.time()
            current = 0
            while current < self.time:
                newframes = self.__recordingHelper.cameraHelper.getChunk()
                n = len(newframes)
                d.resize(n + it, axis = 0)
                d[it:it+n, :,:] = np.array(newframes)
                it += n 
                self.__recordingHelper.comm_channel.updateRecTime(np.around(current, decimals=2))
                current = time.time() - start
            self.__recordingHelper.comm_channel.updateRecTime(0)
            self.__recordingHelper.comm_channel.endRecording()
            self.__recordingHelper.endRecording()
                
        else:
            while self.__recordingHelper.record:
                newframes = self.__recordingHelper.cameraHelper.getChunk()
                n = len(newframes)
                d.resize(n + it, axis = 0)
                d[it:it+n, :,:] = np.array(newframes)
                it += n       
