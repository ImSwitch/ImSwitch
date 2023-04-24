from logging import raiseExceptions
import numpy as np
import time
import cv2
import os
import sys
import pathlib
from imswitch.imcommon.model import initLogger
import collections

def configure_path():
    absolute_path_to_dlls = str(pathlib.Path(__file__).resolve().parent)+"\\thorlabs_tsi_sdk\\dll\\"
    os.environ['PATH'] = absolute_path_to_dlls + os.pathsep + os.environ['PATH']

    try:
        # Python 3.8 introduces a new method to specify dll directory
        os.add_dll_directory(absolute_path_to_dlls)
    except AttributeError:
        pass

configure_path()

from thorlabs_tsi_sdk.tl_camera import TLCameraSDK
from thorlabs_tsi_sdk.tl_mono_to_color_processor import MonoToColorProcessorSDK
from thorlabs_tsi_sdk.tl_camera_enums import SENSOR_TYPE

TAG_BITDEPTH = 32768
TAG_EXPOSURE = 32769

class CameraThorCamSci:
    def __init__(self,cameraNo=None, exposure_time = 10000, gain = 0, frame_rate=-1, blacklevel=100, binning=1):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

        # many to be purged
        self.model = "CameraThorCamSci"
        self.shape = (0, 0)
        
        # set some flags        
        self.is_connected = False
        self.is_streaming = False

        # camera parameters
        self.blacklevel = blacklevel
        self.exposure_time = exposure_time
        self.gain = gain
        self.preview_width = 600
        self.preview_height = 600
        self.frame_rate = frame_rate 
        self.cameraNo = cameraNo

        # reserve some space for the software-based framebuffer
        self.NBuffer = 200
        self.frame_buffer = collections.deque(maxlen=self.NBuffer)
        self.frameid_buffer = collections.deque(maxlen=self.NBuffer)
        self.lastFrameId = -1
                
        #%% starting the camera thread
        self.camera = None

        # binning 
        self.binning = binning

        try:
            self._init_cam(cameraNo=self.cameraNo, callback_fct=self.set_frame)
        except:
            raise Exception("No camera ThorCamSci connected")
        

        

    def _init_cam(self, cameraNo=1, callback_fct=None):
        # start camera
        self.is_connected = True
        
        # open the first device
        self.sdk = TLCameraSDK()
        cameras = self.sdk.discover_available_cameras()
        self.camera = self.sdk.open_camera(cameras[cameraNo])
        
        self.camera.frames_per_trigger_zero_for_unlimited = 0
        self.camera.image_poll_timeout_ms = 2000  # 2 second timeout
        self.camera.arm(2)

        # save these values to place in our custom TIFF tags later
        bit_depth = self.camera.bit_depth
        
        exposure = self.camera.exposure_time_us

        # need to save the image width and height for color processing
        image_width = self.camera.image_width_pixels
        image_height = self.camera.image_height_pixels

        # initialize a mono to color processor if this is a color self.camera
        is_color_camera = (self.camera.camera_sensor_type == SENSOR_TYPE.BAYER)
        mono_to_color_sdk = None
        mono_to_color_processor = None
        if is_color_camera:
            mono_to_color_sdk = MonoToColorProcessorSDK()
            mono_to_color_processor = mono_to_color_sdk.create_mono_to_color_processor(
                self.camera.self.camera_sensor_type,
                self.camera.color_filter_array_phase,
                self.camera.get_color_correction_matrix(),
                self.camera.get_default_white_balance_matrix(),
                self.camera.bit_depth
            )

        # get framesize 
        self.SensorHeight = self.camera.sensor_height_pixels
        self.SensorWidth = self.camera.sensor_width_pixels
        
        self.camera.issue_software_trigger()

        # set exposure
        self.camera.exposure_time_us=int(self.exposure_time*1000)

        # set gain
        self.camera.gain=int(self.gain)
        
        # set blacklevel
        self.camera.blacklevel=int(self.blacklevel)
        
    def start_live(self):
        if not self.is_streaming:
            # start data acquisition
            self.is_streaming = True
            return
            
    def stop_live(self):
        if self.is_streaming:
            # start data acquisition
            self.is_streaming = False
            return

    def suspend_live(self):
        if self.is_streaming:
        # start data acquisition
            try:
                return
                self.camera.stream_off()
            except:
                # camera was disconnected? 
                return

            self.is_streaming = False
        
    def prepare_live(self):
        return

    def close(self):
        self.camera.disarm()
        
    def set_exposure_time(self,exposure_time):
        self.exposure_time = exposure_time
        self.camera.exposure_time_us=int(exposure_time*1000)

    def set_gain(self,gain):
        self.gain = gain
        self.camera.gain = gain

    def set_frame_rate(self, frame_rate):
        pass
        
        
    def set_blacklevel(self,blacklevel):
        self.blacklevel = blacklevel
        self.camera.black_level=blacklevel
        
    def set_pixel_format(self,format):
        pass
    
    def setBinning(self, binning=1):
        # Unfortunately this does not work
        # self.camera.BinningHorizontal.set(binning)
        # self.camera.BinningVertical.set(binning)
        self.camera.binx=binnning
        self.camera.biny=binning
        self.binning = binning

    def getLast(self, is_resize=True):
        # get frame and save
        framebuffer = self.camera.get_pending_frame_or_null()
        self.frame = framebuffer.image_buffer
        return self.frame 

    def flushBuffer(self):
        self.frameid_buffer.clear()
        self.frame_buffer.clear()
        
    def getLastChunk(self):
        return
        chunk = np.array(self.frame_buffer)
        frameids = np.array(self.frameid_buffer)
        self.flushBuffer()
        self.__logger.debug("Buffer: "+str(chunk.shape)+" IDs: " + str(frameids))
        return chunk
    
    def setROI(self,hpos=None,vpos=None,hsize=None,vsize=None):
        pass

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
            property_value = self.camera.Gain.get()
        elif property_name == "exposure":
            property_value = self.camera.ExposureTime.get()
        elif property_name == "blacklevel":
            property_value = self.camera.BlackLevel.get()            
        elif property_name == "image_width":
            property_value = self.camera.Width.get()//self.binning         
        elif property_name == "image_height":
            property_value = self.camera.Height.get()//self.binning
        elif property_name == "roi_size":
            property_value = self.roi_size 
        elif property_name == "frame_Rate":
            property_value = self.frame_rate 
        elif property_name == "trigger_source":
            property_value = self.trigger_source
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def setTriggerSource(self, trigger_source):
        return
            
    def getFrameNumber(self):
        return self.frameNumber 

    def send_trigger(self):
        return

    def openPropertiesGUI(self):
        return
    
    def set_frame(self, user_param, frame):
        return
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
        self.frameNumber = frame.get_frame_id()
        self.timestamp = time.time()
        
        if self.binning > 1:
            numpy_image = cv2.resize(numpy_image, dsize=None, fx=1/self.binning, fy=1/self.binning, interpolation=cv2.INTER_AREA)
    
        self.frame_buffer.append(numpy_image)
        self.frameid_buffer.append(self.frameNumber)
    

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