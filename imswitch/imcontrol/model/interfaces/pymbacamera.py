#%%
try:
    from pymba import Vimba, VimbaException
except:
    print("No pymba installed..")
from typing import Optional
import cv2
import numpy as np
import threading
import time

from imswitch.imcommon.model import initLogger

# todo add more colours
PIXEL_FORMATS_CONVERSIONS = {
    'BayerRG8': cv2.COLOR_BAYER_RG2RGB,
}

#%%

class AVCamera(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.__logger = initLogger(self, tryInheritParent=True)
        self.__logger.debug(f"Opening Camrea")

        self.FEATURE_NAME = 'ExposureTime'
        self.exposure_time = 10000

        self.is_running = False
        self.kill = False

        self.exposure_time = 1000
        self.gain = 0
        self.blacklevel = 0
        self.shape = (1000,1000)
        self.is_active = True
        self.SensorHeight = self.shape[0]
        self.SensorWidth = self.shape[1]
        
        self.last_frame = np.zeros(self.shape)
        self.last_frame_preview = np.zeros(self.shape)
        self.is_changevalue = False # change parameters

        self.needs_reconnect = True # if we loose connection => reconnect

        self.vimba = Vimba()
        self.vimba.startup()

    def run(self):
        print("Starting Frame acquisitoin")
        self.kill = False
        # capture a single frame, more than once if desired
        while(not self.kill):
            while(self.needs_reconnect): # will be done in the first run and when connection is lost
                try:
                    self.camera = self.vimba.camera(0)
                    self.camera.open()
                    self.needs_reconnect = False
                    self.is_running = True
                    self.camera.arm('SingleFrame')
                    self.__logger.debug("camera connected")
                    self.SensorHeight = self.camera.feature("SensorHeight").value
                    self.SensorWidth = self.camera.feature("SensorWidth").value
                    self.shape = (np.min((self.SensorHeight,self.SensorWidth)),np.min((self.SensorHeight,self.SensorWidth)))
                except Exception as e:
                    self.__logger.debug(e)
                    time.sleep(2)
                self.__logger.debug("try to reconnect the camera (replug?)...")

            # acquire frame
            try:
                self.last_frame = self.camera.acquire_frame().buffer_data_numpy()[self.SensorHeight//2-self.shape[0]//2:self.SensorHeight//2+self.shape[0]//2,
                                                                                    self.SensorWidth//2-self.shape[1]//2:self.SensorWidth//2+self.shape[1]//2]
                preview_width = 300
                preview_height = 300

                self.last_frame_preview = cv2.resize(self.last_frame , (preview_width,preview_height), interpolation= cv2.INTER_LINEAR)
            
            except Exception as e:
                # rearm camera upon frame timeout
                self.__logger.error(e)
                self.__logger.error("Please reconnect the camra")
                # TODO: Try reconnecting the camera automaticaly
                self.needs_reconnect = True

        self.camera.disarm()
        self.camera.close()
        self.is_running = False
        self.kill = False
        del self.camera 

    def stop(self):
        self.kill = True

    def set_value(self ,feature_key, feature_value):
        # Need to change acquisition parameters?
        if self.is_running:
            try:
                feature = self.camera.feature(feature_key)
                feature.value = feature_value
            except Exception as e:
                self.__logger.error(e)
                self.__logger.debug("Value not available?")
            
    def setExposureTime(self, value):
        self.set_value("ExposureTime", value)

    def setGain(self, value):
        self.set_value("Gain", value)

    def setBlacklevel(self, value):
        self.set_value("Blacklevel", value)

        