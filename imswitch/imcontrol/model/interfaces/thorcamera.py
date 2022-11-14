from logging import raiseExceptions
import numpy as np
import time
import cv2
from imswitch.imcommon.model import initLogger

import collections


import numpy as np
import matplotlib.pyplot as plt

# init devwraps 
#import devwraps

# removes all DLLs
#devwraps.remove_dlls()

# look for DLLs according to the paths specified in `dll_paths.py`
#devwraps.look_for_dlls()

# print the root folder of this module
#self.__logger.debug(devwraps.get_root_folder)

from devwraps.thorcam import ThorCam

class TriggerMode:
    SOFTWARE = 'Software Trigger'
    HARDWARE = 'Hardware Trigger'
    CONTINUOUS = 'Continuous Acqusition'

class ThorCamera:
    def __init__(self,cameraNo=None, exposure_time = 10000, gain = 0, blacklevel=100, binning=2):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)



        
        # many to be purged
        self.model = "ThorCamera"
        self.shape = (0, 0)
        
        self.is_connected = False
        self.is_streaming = False

        # unload CPU? 
        self.downsamplepreview = 1

        # camera parameters
        self.blacklevel = blacklevel
        self.exposure_time = exposure_time
        self.gain = gain
        self.cameraNo = cameraNo

        # reserve some space for the framebuffer
        NBuffer = 60
        self.frame_buffer = collections.deque(maxlen=NBuffer)
        self.frameid_buffer = collections.deque(maxlen=NBuffer)
        
        #%% starting the camera thread
        self.camera = None

        # binning 
        self.binning = binning

        self._init_cam(cameraNo=self.cameraNo)
        

    def _init_cam(self, cameraNo=1, callback_fct=None):
        # start camera
        self.is_connected = True
        
        # open the first device
        self.camera = ThorCam()
        cameraNo = self.camera.get_number_of_cameras()
        cdevices = self.camera.get_devices()
        self.camera.open(cdevices[0])

        # set exposure
        self.camera.set_exposure(self.exposure_time)

        # set gain
        # not available? self.camera.Gain.set(self.gain)
        
        # set blacklevel
        # not available? self.camera.BlackLevel.set(self.blacklevel)

        # get framesize 
        self.SensorHeight = self.camera.shape()[0]
        self.SensorWidth = self.camera.shape()[1]
        
    def start_live(self):
        pass

    def stop_live(self):
        pass
    
    def suspend_live(self):
        pass 
    
    def prepare_live(self):
        pass

    def close(self):
        self.camera.close()
        
    def set_exposure_time(self,exposure_time):
        self.exposure_time = exposure_time
        self.camera.set_exposure(self.exposure_time)

    def set_gain(self,gain):
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
        # get frame and save
#        frame_norm = cv2.normalize(self.frame, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)       
        #TODO: Napari only displays 8Bit?
        try:
            return self.camera.grab_image(wait=1)
        except:
            pass

    def getLastChunk(self):
        chunk = np.expand_dims(self.camera.grab_image(),0)
        return chunk
    
    def setROI(self,hpos=None,vpos=None,hsize=None,vsize=None):
        pass

    def setPropertyValue(self, property_name, property_value):
        # Check if the property exists.
        if property_name == "exposure":
            self.set_exposure_time(property_value)
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def getPropertyValue(self, property_name):
        # Check if the property exists.
        if property_name == "exposure":
            property_value = self.camera.get_exposure()
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

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