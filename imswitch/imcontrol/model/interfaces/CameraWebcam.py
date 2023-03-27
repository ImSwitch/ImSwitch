from logging import raiseExceptions
import numpy as np
import time
import cv2
from imswitch.imcommon.model import initLogger
import collections

class TriggerMode:
    SOFTWARE = 'Software Trigger'
    HARDWARE = 'Hardware Trigger'
    CONTINUOUS = 'Continuous Acqusition'

class CameraWebcam:
    def __init__(self,cameraNo=None):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

        # many to be purged
        self.model = "Webcam"
        self.shape = (0, 0)
        
        self.is_connected = False
        self.is_streaming = False

        #%% starting the camera thread
        self.camera = None

        if cameraNo is not None:
            self._init_cam(cameraNo = cameraNo)
        else:
            raise Exception("No camera connected")
        
    def _init_cam(self, cameraNo=1):
        # start camera
        self.is_connected = True

        
        # Initialize the webcam
        self.camera = cv2.VideoCapture(cameraNo)

        # get the shape of the frame
        shape = self.camera.read()[1].shape
    
        # get framesize 
        self.SensorHeight = shape[1]
        self.SensorWidth = shape[0]
        
    def start_live(self):
        pass
        
    def stop_live(self):
        pass
    
    def suspend_live(self):
        pass
        
    def prepare_live(self):
        pass

    def close(self):
        self.camera.release()
        
    def set_exposure_time(self,exposure_time):
        self.exposure_time = exposure_time
        return
        self.camera.ExposureTime.set(self.exposure_time*1000)

    def set_gain(self,gain):
        self.gain = gain
        return
        self.camera.Gain.set(self.gain)

    def set_frame_rate(self, frame_rate):
        pass 
    
    def set_blacklevel(self,blacklevel):
        pass

    def set_pixel_format(self,format):
        pass 
        
    def setBinning(self, binning=1):
        # Unfortunately this does not work
        # self.camera.BinningHorizontal.set(binning)
        # self.camera.BinningVertical.set(binning)
        self.binning = binning

    def getLast(self, is_resize=True):
        # only return fresh frames
        self.frame = self.camera.read()[1]
        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        return self.frame

    def flushBuffer(self):
        return 
    
    def getLastChunk(self):
        # get frames from camera'S buffer => e.g. for Hdf5 saving
        frame = self.camera.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        chunk = np.expand_dims(frame, 0)
        
        return chunk
    
    def setROI(self,hpos=None,vpos=None,hsize=None,vsize=None):
        return hpos,vpos,hsize,vsize


    def setPropertyValue(self, property_name, property_value):
        # Check if the property exists.
        if property_name == "gain":
            self.set_gain(property_value)
        elif property_name == "exposure":
            self.set_exposure_time(property_value)
        elif property_name == "blacklevel":
            self.set_blacklevel(property_value)
        elif property_name == "roi_size":
            self.roi_size = property_value
        elif property_name == "frame_rate":
            self.set_frame_rate(property_value)
        elif property_name == "trigger_source":
            self.setTriggerSource(property_value)
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def getPropertyValue(self, property_name):
        # Check if the property exists.
        if property_name == "gain":
            property_value = 0# self.camera.Gain.get()
        elif property_name == "exposure":
            property_value = 0# self.camera.ExposureTime.get()
        elif property_name == "blacklevel":
            property_value = self.camera.BlackLevel.get()            
        elif property_name == 0:# "image_width":
            property_value = self.camera.Width.get()//self.binning         
        elif property_name == "image_height":
            property_value = 0 #self.camera.Height.get()//self.binning
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def setTriggerSource(self, trigger_source):
        pass
            
    
    def openPropertiesGUI(self):
        pass
    
    

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