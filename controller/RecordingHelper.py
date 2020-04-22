# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 15:17:52 2020

@author: Testa4
"""
from pyqtgraph.Qt import QtCore
import numpy as np
import h5py
import time
import tifffile as tiff

class RecordingHelper():
    def __init__(self, comm_channel, cameraHelper):
        self.__comm_channel = comm_channel
        self.__cameraHelper = cameraHelper
        self.__recordingWorker = RecordingWorker(self)
        self.__thread = QtCore.QThread()
        self.__recordingWorker.moveToThread(self.__thread)
        self.__thread.started.connect(self.__recordingWorker.run)
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
            
    def startRecording(self, recMode, frames=None):
        self.recMode = recMode
        self.frames = frames
        self.__cameraHelper.updateCameraIndices()
        self.__record = True
        self.__thread.start()
        
    def endRecording(self):
        self.__record = False
        self.__thread.quit()
                   
    def snap(self, savename, dataname, attrs, ext):
        store_file = h5py.File(savename)
        for key in attrs.keys():
            store_file.attrs[key] = attrs[key]
        size = self.__cameraHelper.shapes
        d = store_file.create_dataset(dataname, (size[0], size[1]), dtype = 'i2')
        umxpx = attrs["pixel_size"]
        d.attrs["element_size_um"] = [1, umxpx, umxpx] 
        d[:, :] = self.__cameraHelper.image
        store_file.close()
        
class RecordingWorker(QtCore.QObject):
    def __init__(self, recordingHelper, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__recordingHelper = recordingHelper
        
        
    def run(self):
        print("Thread started")
        it = 0
       # f = h5py.File('C:\\Users\\Testa4\\Documents\\mvcTempesta\\test\\stack2.hdf5', 'w', libver="latest") 
        f = h5py.File('D:\\test\\stack2.hdf5', 'w', libver="latest") 
        size = self.__recordingHelper.cameraHelper.shapes
        d = f.create_dataset('dataset', (1, size[0], size[1]), maxshape=(None, size[0], size[1]), dtype='i2')
        print("File created")
        if self.__recordingHelper.recMode == 1:
            frames = self.__recordingHelper.frames
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
                self.__recordingHelper.comm_channel.updateFrameNumber(it)
            f.close()
            self.__recordingHelper.comm_channel.endRecording()
            self.__recordingHelper.endRecording()
        else:
            while self.__recordingHelper.record:
                newframes = self.__recordingHelper.cameraHelper.getChunk()
                n = len(newframes)
                d.resize(n + it, axis = 0)
                d[it:it+n, :,:] = np.array(newframes)
                it += n       
            f.close()
          
