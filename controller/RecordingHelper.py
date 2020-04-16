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
    def __init__(self, cameraHelper):
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
            
    def startRecording(self):
        self.__cameraHelper.updateCameraIndices()
        self.__record = True
        self.__thread.start()
        
    def endRecording(self):
        self.__record = False
        self.__thread.quit()
                   

class RecordingWorker(QtCore.QObject):
    def __init__(self, recordingHelper, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__recordingHelper = recordingHelper
        
    def run(self, frames = None):
        print("Thread started")
        it = 0
        f = h5py.File('C:\\Users\\Testa4\\Documents\\mvcTempesta\\test\\stack2.hdf5', 'w', libver="latest") 
       # f = h5py.File('D:\\test\\stack2.hdf5', 'w', libver="latest") 
        size = self.__recordingHelper.cameraHelper.shapes
        d = f.create_dataset('dataset', (1, size[0], size[1]), maxshape=(None, size[0], size[1]), dtype='i2')
        print("File created")
#        if not frames is None:
        t0 = time.time()
        while self.__recordingHelper.record:
            newframes = self.__recordingHelper.cameraHelper.getChunk()
            n = len(newframes)
            d.resize(n + it, axis = 0)
            d[it:it+n, :,:] = np.array(newframes)
            it += n
#        else:
#            while it<=frames:
#                newframes = self.recordingHelper.cameraHelper.getFrames()
#                n = np.size(newframes, 3)
#                d.resize(n + it, axis = 0)
#                # Do it properly
#                if (it+n)<=frames:
#                    d[it:it+n, :,:] = newframes
#                else:
#                    d[it:frames, :, :] = newframes[0:frames-it, :, :]
#                it += n
        t1 = time.time()        
        print(t1-t0)        
        f.close()
          
