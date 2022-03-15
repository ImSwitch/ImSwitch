from logging import raiseExceptions
import numpy as np
import time
import cv2
from imswitch.imcommon.model import initLogger

import imswitch.imcontrol.model.interfaces.gxipy as gx
import collections
class CameraGXIPY:
    def __init__(self,cameraNo=None, exposure_time = 10000, gain = 0, blacklevel=100):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

        # many to be purged
        self.model = "CameraGXIPY"
        self.shape = (0, 0)
        
        self.is_connected = False
        self.is_streaming = False

        # unload CPU? 
        self.downsamplepreview = 1

        # camera parameters
        self.blacklevel = blacklevel
        self.exposure_time = exposure_time
        self.gain = gain
        self.preview_width = 600
        self.preview_height = 600 
        self.cameraNo = cameraNo

        # reserve some space for the framebuffer
        self.frame_buffer = collections.deque(maxlen=20)
        self.frameid_buffer = collections.deque(maxlen=20)
        
        #%% starting the camera thread
        self.camera = None

        self.device_manager = gx.DeviceManager()
        dev_num, dev_info_list = self.device_manager.update_device_list()

        if dev_num  != 0:
            self._init_cam(cameraNo=self.cameraNo, callback_fct=self.set_frame)
        else:
            raise Exception("No camera GXIPY connected")
        

    def _init_cam(self, cameraNo=1, callback_fct=None):
        # start camera
        self.is_connected = True
        
        # open the first device
        self.camera = self.device_manager.open_device_by_index(cameraNo)

        # exit when the camera is a color camera
        if self.camera.PixelColorFilter.is_implemented() is True:
            print("This sample does not support color camera.")
            self.camera.close_device()
            return
            
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
        self.SensorHeight = self.camera.HeightMax.get()
        self.SensorWidth = self.camera.WidthMax.get()
        
        # register the frame callback
        user_param = None
        self.camera.register_capture_callback(user_param, self.set_frame)

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
            try:
                self.camera.stream_off()
            except:
                # camera was disconnected? 
                self.camera.unregister_capture_callback()
                self.camera.close_device()
                self._init_cam(cameraNo=self.cameraNo, callback_fct=self.set_frame)

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

    def getLast(self, is_resize=True):
        # get frame and save
#        frame_norm = cv2.normalize(self.frame, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)       
        #TODO: Napari only displays 8Bit?
        return self.frame

    def getLastChunk(self):
        chunk = np.array(self.frame_buffer)
        frameids = np.array(self.frameid_buffer)
        self.frameid_buffer.clear()
        self.frame_buffer.clear()
        self.__logger.debug("Buffer: "+str(chunk.shape)+" IDs: " + str(frameids))
        return chunk
    
    def setROI(self,hpos=None,vpos=None,hsize=None,vsize=None):
        #hsize = max(hsize, 25)*10  # minimum ROI size
        #vsize = max(vsize, 3)*10  # minimum ROI size
        hpos = 8*(hpos//8)
        vpos = 2*(vpos//2)     
        hsize = 8*(hsize//8)   
        vsize = 2*(vsize//2) 

        if hsize is not None:
            self.ROI_width = hsize
            # update the camera setting
            if self.camera.Width.is_implemented() and self.camera.Width.is_writable():
                self.camera.Width.set(self.ROI_width)
            else:
                print("OffsetX is not implemented or not writable")

        if vsize is not None:
            self.ROI_height = vsize
            # update the camera setting
            if self.camera.Height.is_implemented() and self.camera.Height.is_writable():
                self.camera.Height.set(self.ROI_height)
            else:
                print("Height is not implemented or not writable")

        if hpos is not None:
            self.ROI_hpos = hpos
            # update the camera setting
            if self.camera.OffsetX.is_implemented() and self.camera.OffsetX.is_writable():
                self.camera.OffsetX.set(self.ROI_hpos)
            else:
                print("OffsetX is not implemented or not writable")

        if vpos is not None:
            self.ROI_vpos = vpos
            # update the camera setting
            if self.camera.OffsetY.is_implemented() and self.camera.OffsetY.is_writable():
                self.camera.OffsetY.set(self.ROI_vpos)
            else:
                print("OffsetX is not implemented or not writable")


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
            property_value = self.camera.Width.get()            
        elif property_name == "image_height":
            property_value = self.camera.Height.get()    
        elif property_name == "roi_size":
            property_value = self.roi_size 
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def openPropertiesGUI(self):
        pass
    
    def set_frame(self, user_param, frame):
        if frame is None:
            self.__logger.error("Getting image failed.")
            return
        if frame.get_status() != 0:
            self.__logger.error("Got an incomplete frame")
            return
        numpy_image = frame.get_numpy_array()
        if numpy_image is None:
            return
        self.frame = numpy_image
        self.frame_id = frame.get_frame_id()
        self.timestamp = time.time()
        
        self.frame_buffer.append(numpy_image)
        self.frameid_buffer.append(self.frame_id)
    

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