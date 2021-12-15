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



        self.is_camera_open = False
        self.is_live = False
        self.is_stop = False # flag to terminate the thread

        self.exposure_time = 1000
        self.gain = 0
        self.blacklevel = 0
        
        self.PreviewWidthRatio = 4
        self.PreviewHeightRatio = 4
        #TODO: NO hardcoding here!
        self.SensorHeight = -1
        self.SensorWidth = -1
        
        self.last_frame = None
        self.last_frame_preview = None

        self.needs_reconnect = True # if we loose connection => reconnect
        
        self.frame_id = -1
        
        self.openCamera()
        


    def startVimba(self, is_restart = False):
        if is_restart:
            try:
                self.vimba.shutdown()
                del self.vimba
            except:
                pass
        self.vimba = Vimba()
        self.vimba.startup()
        

    def openCamera(self):
        try:
            self.startVimba(is_restart=True)
            self.camera = self.vimba.camera(0)
            self.camera.open()
            self.needs_reconnect = False
            self.is_camera_open = True
            self.camera.arm('SingleFrame')
            self.__logger.debug("camera connected")
            self.SensorHeight = self.camera.feature("SensorHeight").value
            self.SensorWidth = self.camera.feature("SensorWidth").value
            #self.shape = (np.min((self.SensorHeight,self.SensorWidth)),np.min((self.SensorHeight,self.SensorWidth)))
            #self.shape = (self.SensorHeight,self.SensorWidth)

        except Exception as e:
            self.__logger.debug(e)
            
    def closeCamera(self):
        self.__logger.debug(f"Closing Camera.")
        try:
            self.camera.disarm()
            self.camera.close()
        except:
            pass
        self.is_camera_open = False
        
    def run(self):
        print("Starting Frame acquisitoin")

        # capture a single frame, more than once if desired
        while(not self.is_stop):
            if(self.is_live): # produce frames only when necessary
                while(self.is_live and self.needs_reconnect): # will be done in the first run and when connection is lost
                    self.__logger.debug("try to reconnect the camera (replug?)...")
                    self.openCamera()
                    time.sleep(2)
                
                # acquire frame
                try:
                    frame = self.camera.acquire_frame()
                    self.frame_id = frame.data.frameID
                    self.__logger(self.frame_id)
                    self.last_frame = frame.buffer_data_numpy()
                    self.last_frame_preview = self.last_frame.copy()

                    # crop and resize?
                    #self.last_frame_preview = self.last_frame_preview [self.SensorHeight//2-self.sensorheight//2:self.SensorHeight//2+self.sensorheight//2,
                    #                                self.SensorWidth//2-self.sensorwidth//2:self.SensorWidth//2+self.sensorwidth//2]
                    self.last_frame_preview = cv2.resize(self.last_frame_preview , dsize=None, fx=1/self.PreviewWidthRatio, fy=1/self.PreviewHeightRatio, interpolation= cv2.INTER_LINEAR)
                
                except Exception as e:
                    # rearm camera upon frame timeout
                    self.__logger.error(e)
                    self.__logger.error("Please reconnect the camera")
                    # TODO: Try reconnecting the camera automaticaly
                    self.needs_reconnect = True
                    self.frame_id = -1
            else:
                time.sleep(.1) # don't bother the CPU, dirty! 

    def start_live(self):
        self.is_live = True

    def stop_live(self):
        self.is_live = False
        
    def close(self):
        self.is_live = False
        self.is_stop = True
        while(self.is_alive()):
            time.sleep(.1) # wait until thread is done
        self.join()
        self.closeCamera()
        self.vimba.shutdown()

    def set_value(self ,feature_key, feature_value):
        # Need to change acquisition parameters?
        if self.is_camera_open:
            try:
                feature = self.camera.feature(feature_key)
                feature.value = feature_value
            except Exception as e:
                self.__logger.error(e)
                self.__logger.error(feature_key)
                self.__logger.debug("Value not available?")
            
    def setExposureTime(self, value):
        self.set_value("ExposureTime", value)

    def setGain(self, value):
        self.set_value("Gain", value)

    def setBlacklevel(self, value):
        self.set_value("Blacklevel", value)

    def setROI(self, vpos, hpos, vsize, hsize):
        image_Height = self.camera.feature("Height")
        image_Width = self.camera.feature("Width")
        image_Height.value = hsize
        image_Width.value = vsize
        
# Copyright (C) ImSwitch developers 2021
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.