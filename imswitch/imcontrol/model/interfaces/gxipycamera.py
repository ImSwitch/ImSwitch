import numpy as np
import time
import cv2
from imswitch.imcommon.model import initLogger

import imswitch.imcontrol.model.interfaces.gxipy as gx
 
class CameraGXIPY:
    def __init__(self,cameraNo=None, exposure_time = 10000, gain = 0, blacklevel=100):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

        # many to be purged
        self.model = "CameraGXIPY"
        self.shape = (0, 0)
        
        self.is_connected = False
        self.is_streaming = False

        # camera parameters
        self.blacklevel = blacklevel
        self.exposure_time = exposure_time
        self.gain = gain
        
        self.shape = (1200,1200) # TODO: Attention: Hardcoded!!
        self.SensorHeight = self.shape[0]
        self.SensorWidth = self.shape[1]
        self.preview_width = 600
        self.preview_height = 600

        #%% starting the camera thread
        self.camera = None
        self.device_manager = gx.DeviceManager()
        dev_num, dev_info_list = self.device_manager.update_device_list()
        if dev_num  != 0:
            # start camera
            self.is_connected = True
            
            # open the first device
            self.camera = self.device_manager.open_device_by_index(1)

            # exit when the camera is a color camera
            self.camera.TriggerMode.set(gx.GxSwitchEntry.OFF)

            # set exposure
            self.camera.ExposureTime.set(self.exposure_time)

            # set gain
            self.camera.Gain.set(self.gain)
            
            # set blacklevel
            self.camera.BlackLevel.set(self.blacklevel)

            # set the acq buffer count
            self.camera.data_stream[0].set_acquisition_buffer_number(1)
            
            # set camera to mono12 mode
            self.camera.PixelFormat.set(gx.GxPixelFormatEntry.MONO10)

            # get framesize 
            self.SensorHeight = self.camera.Height.get()
            self.SensorWidth = self.camera.Width.get()

    def start_live(self):
        if not self.is_streaming:
            # start data acquisition
            self.camera.stream_on()
            self.is_streaming = True

    def stop_live(self):
        if self.is_streaming:
            # start data acquisition
            self.camera.stream_off()
            self.is_streaming = False

    def suspend_live(self):
        if self.is_streaming:
        # start data acquisition
            self.camera.stream_off()
            self.is_streaming = False
        
    def prepare_live(self):
        pass

    def close(self):
        self.camera.close_device()
        
    def set_exposure_time(self,exposure_time):
        self.exposure_time = exposure_time
        self.camera.ExposureTime.set(self.exposure_time*1000)

    def set_gain(self,gain):
        self.gain = gain
        self.camera.Gain.set(self.gain)
        
    def set_blacklevel(self,blacklevel):
        self.blacklevel = blacklevel
        self.camera.BlackLevel.set(self.blacklevel)

    def set_pixel_format(self,format):
        if self.camera.PixelFormat.is_implemented() and self.camera.PixelFormat.is_writable():
            if format == 'MONO8':
                self.camera.PixelFormat.set(gx.GxPixelFormatEntry.MONO8)
            if format == 'MONO12':
                self.camera.PixelFormat.set(gx.GxPixelFormatEntry.MONO12)
            if format == 'MONO14':
                self.camera.PixelFormat.set(gx.GxPixelFormatEntry.MONO14)
            if format == 'MONO16':
                self.camera.PixelFormat.set(gx.GxPixelFormatEntry.MONO16)
            if format == 'BAYER_RG8':
                self.camera.PixelFormat.set(gx.GxPixelFormatEntry.BAYER_RG8)
            if format == 'BAYER_RG12':
                self.camera.PixelFormat.set(gx.GxPixelFormatEntry.BAYER_RG12)
        else:
            print("pixel format is not implemented or not writable")

    def getLast(self):
        # get frame and save
        raw_image = self.camera.data_stream[0].get_image().get_numpy_array()

        last_frame_preview = raw_image.copy()[self.SensorHeight//2-self.shape[0]//2:self.SensorHeight//2+self.shape[0]//2,
                                    self.SensorWidth//2-self.shape[1]//2:self.SensorWidth//2+self.shape[1]//2]
        last_frame_preview = cv2.resize(last_frame_preview , (self.preview_width,self.preview_height), interpolation= cv2.INTER_LINEAR)
        return last_frame_preview

    def getLastChunk(self):
        return self.camera.data_stream[0].get_image().get_numpy_array()[:,
                                    self.SensorWidth//2-self.SensorHeight//2:self.SensorWidth//2+self.SensorHeight//2]
       # TODO: This is odd
    def setROI(self, hpos, vpos, hsize, vsize):
        hsize = max(hsize, 256)  # minimum ROI size
        vsize = max(vsize, 24)  # minimum ROI size
        pass
        # self.__logger.debug(
        #     f'{self.model}: setROI started with {hsize}x{vsize} at {hpos},{vpos}.'
        # )
        #self.camera.setROI(vpos, hpos, vsize, hsize)

    def setPropertyValue(self, property_name, property_value):
        # Check if the property exists.
        if property_name == "gain":
            self.set_gain(property_value)
        elif property_name == "exposure":
            self.set_exposure_time(property_value)
        elif property_name == "blacklevel":
            self.set_blacklevel(property_value)
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def getPropertyValue(self, property_name):
        # Check if the property exists.
        if property_name == "gain":
            property_value = self.camera.Gain.get()
        elif property_name == "exposure":
            property_value = self.camera.ExposureTime.get()
        elif property_name == "blacklevel":
            property_value = self.camera.BlackLevel.get()            
        elif property_name == "image_width":
            property_value = self.camera.Height.get()            
        elif property_name == "image_height":
            property_value = self.camera.Height.get()            
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