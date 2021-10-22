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

        self.exposure_time = 10000
        self.gain = 0
        self.blacklevel = 0
        self.shape = (1000,1000)
        self.is_active = True
        self.SensorHeight = self.shape[0]
        self.SensorWidth = self.shape[1]
        
        self.last_frame = np.zeros(self.shape)
        self.is_changevalue = False # change parameters

        self.needs_reconnect = True # if we loose connection => reconnect

    def run(self):
        print("Starting Frame acquisitoin")
        
        with Vimba() as vimba:
            # capture a single frame, more than once if desired
            while(not self.kill):
                while(self.needs_reconnect): # will be done in the first run and when connection is lost
                    try:
                        self.camera = vimba.camera(0)
                        self.camera.open()
                        self.needs_reconnect = False
                        self.is_running = True
                        self.camera.arm('SingleFrame')
                        self.__logger.debug("camera connected")
                        self.SensorHeight = self.camera.feature("SensorHeight").value
                        self.SensorWidth = self.camera.feature("SensorWidth").value
                    
                    except Exception as e:
                        self.__logger.debug(e)
                        time.sleep(2)
                    self.__logger.debug("try to reconnect the camera (replug?)...")
                    
                # Need to change acquisition parameters?
                if self.is_changevalue:
                    # cannot access outside the with statement?
                    try:
                        feature = self.camera.feature(self.feature_key)
                        feature.value = self.feature_value
                    except:
                        print("Value not available?")
                    self.is_changevalue = False

                # acquire frame
                try:
                    self.last_frame = self.camera.acquire_frame().buffer_data_numpy()[self.SensorHeight//2-self.shape[0]//2:self.SensorHeight//2+self.shape[0]//2,
                                                                                        self.SensorWidth//2-self.shape[1]//2:self.SensorWidth//2+self.shape[1]//2]
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

    def stop(self):
        self.kill = True

    def setExposureTime(self, value):
        self.exposuretime = value
        self.feature_key = "ExposureTime"
        self.feature_value = value
        self.is_changevalue = True

    def setGain(self, value):
        self.gain = value
        self.feature_key = "Gain"
        self.feature_value = value   
        self.is_changevalue = True

    def setBlacklevel(self, value):
        self.gavaluein = value
        self.feature_key = "Blacklevel"
        self.feature_value = value      
        self.is_changevalue = True  
        