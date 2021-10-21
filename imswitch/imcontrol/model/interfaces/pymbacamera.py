#%%
try:
    from pymba import Vimba, VimbaException
except:
    print("No pymba installed..")
from typing import Optional
import cv2


import logging
import threading
import time

# todo add more colours
PIXEL_FORMATS_CONVERSIONS = {
    'BayerRG8': cv2.COLOR_BAYER_RG2RGB,
}

#%%

class AVCamera(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.FEATURE_NAME = 'ExposureTime'
        self.exposure_time = 10000

        self.is_running = False
        self.kill = False
        self.last_frame = None

        self.exposure_time = 10000
        self.gain = 0
        self.blacklevel = 0
        self.shape = (1000,1000)
        self.is_active = True

        self.is_changevalue = False

    def run(self):
        print("Starting Frame acquisitoin")
        
        with Vimba() as vimba:
            self.camera = vimba.camera(0)
            self.camera.open()
            self.is_running = True
            # read a feature value
            feature = self.camera.feature(self.FEATURE_NAME)
            
            # set the feature value (with the same value)
            feature.value = self.exposure_time

            self.camera.arm('SingleFrame')

            # capture a single frame, more than once if desired
            while(not self.kill):

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
                    self.last_frame = self.camera.acquire_frame().buffer_data_numpy()[0:1000,0:1000]
                except VimbaException as e:
                    # rearm camera upon frame timeout
                    if e.error_code == VimbaException.ERR_TIMEOUT:
                        print(e)
                        self.camera.disarm()
                        self.camera.arm('SingleFrame')
                    else:
                        raise

            self.camera.disarm()
            self.camera.close()
            self.is_running = False
            self.kill = False

    def stop(self):
        self.kill = True

    def setExposureTime(self, value):
        self.exposuretime = value
        self.is_changevalue = True
        self.feature_key = "ExposureTime"
        self.feature_value = value

    def setGain(self, value):
        self.gain = value
        self.is_changevalue = True
        self.feature_key = "Gain"
        self.feature_value = value   

    def setBlacklevel(self, value):
        self.gavaluein = value
        self.is_changevalue = True
        self.feature_key = "Blacklevel"
        self.feature_value = value        
        