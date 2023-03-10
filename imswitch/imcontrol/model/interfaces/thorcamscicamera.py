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


        '''
        # set exposure
        self.camera.ExposureTime.set(self.exposure_time)

        # set gain
        self.camera.Gain.set(self.gain)
        
        # set framerate
        self.set_frame_rate(self.frame_rate)
        
        # set blacklevel
        self.camera.BlackLevel.set(self.blacklevel)

        # set the acq buffer count
        self.camera.data_stream[0].set_acquisition_buffer_number(1)
        
        # set camera to mono12 mode
        try:
            self.camera.PixelFormat.set(gx.GxPixelFormatEntry.MONO10)
        # set camera to mono8 mode
        except:
            self.camera.PixelFormat.set(gx.GxPixelFormatEntry.MONO8)

        # get framesize 
        self.SensorHeight = self.camera.HeightMax.get()//self.binning
        self.SensorWidth = self.camera.WidthMax.get()//self.binning
        
        # register the frame callback
        user_param = None
        self.camera.register_capture_callback(user_param, callback_fct)
        '''
        
    def start_live(self):
        if not self.is_streaming:
            # start data acquisition
            self.is_streaming = True
            pass
            self.camera.stream_on()
            

    def stop_live(self):
        if self.is_streaming:
            # start data acquisition
            self.is_streaming = False
            pass
            self.camera.stream_off()

    def suspend_live(self):
        if self.is_streaming:
        # start data acquisition
            try:
                pass
                self.camera.stream_off()
            except:
                # camera was disconnected? 
                pass

            self.is_streaming = False
        
    def prepare_live(self):
        pass

    def close(self):
        self.camera.disarm()
        
    def set_exposure_time(self,exposure_time):
        self.exposure_time = exposure_time
        pass
        #self.camera.ExposureTime.set(self.exposure_time*1000)

    def set_gain(self,gain):
        self.gain = gain
        pass
        #self.camera.Gain.set(self.gain)

    def set_frame_rate(self, frame_rate):
        if frame_rate == -1:
            frame_rate = 10000 # go as fast as you can
        self.frame_rate = frame_rate
        
        # temporary
        pass
        
    def set_blacklevel(self,blacklevel):
        self.blacklevel = blacklevel
        pass
        #self.camera.BlackLevel.set(self.blacklevel)

    def set_pixel_format(self,format):
        pass
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

    def setBinning(self, binning=1):
        # Unfortunately this does not work
        # self.camera.BinningHorizontal.set(binning)
        # self.camera.BinningVertical.set(binning)
        self.binning = binning

    def getLast(self, is_resize=True):
        # get frame and save
#        frame_norm = cv2.normalize(self.frame, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)       
        #TODO: Napari only displays 8Bit?
        
        # only return fresh frames
        self.frame = self.camera.get_pending_frame_or_null()
        pass
        if not self.lastFrameId == self.frameNumber:    
            self.lastFrameId = self.frameNumber 
            return self.frame

    def flushBuffer(self):
        pass
        self.frameid_buffer.clear()
        self.frame_buffer.clear()
        
    def getLastChunk(self):
        pass
        chunk = np.array(self.frame_buffer)
        frameids = np.array(self.frameid_buffer)
        self.flushBuffer()
        self.__logger.debug("Buffer: "+str(chunk.shape)+" IDs: " + str(frameids))
        return chunk
    
    def setROI(self,hpos=None,vpos=None,hsize=None,vsize=None):
        #hsize = max(hsize, 25)*10  # minimum ROI size
        #vsize = max(vsize, 3)*10  # minimum ROI size
        pass
        hpos = self.camera.OffsetX.get_range()["inc"]*((hpos)//self.camera.OffsetX.get_range()["inc"])
        vpos = self.camera.OffsetY.get_range()["inc"]*((vpos)//self.camera.OffsetY.get_range()["inc"])  
        hsize = int(np.min((self.camera.Width.get_range()["inc"]*((hsize*self.binning)//self.camera.Width.get_range()["inc"]),self.camera.WidthMax.get())))
        vsize = int(np.min((self.camera.Height.get_range()["inc"]*((vsize*self.binning)//self.camera.Height.get_range()["inc"]),self.camera.HeightMax.get())))

        if vsize is not None:
            self.ROI_width = hsize
            # update the camera setting
            if self.camera.Width.is_implemented() and self.camera.Width.is_writable():
                message = self.camera.Width.set(self.ROI_width)
                self.__logger.debug(message)
            else:
                self.__logger.debug("OffsetX is not implemented or not writable")

        if hsize is not None:
            self.ROI_height = vsize
            # update the camera setting
            if self.camera.Height.is_implemented() and self.camera.Height.is_writable():
                message = self.camera.Height.set(self.ROI_height)
                self.__logger.debug(message)
            else:
                self.__logger.debug("Height is not implemented or not writable")

        if hpos is not None:
            self.ROI_hpos = hpos
            # update the camera setting
            if self.camera.OffsetX.is_implemented() and self.camera.OffsetX.is_writable():
                message = self.camera.OffsetX.set(self.ROI_hpos)
                self.__logger.debug(message)
            else:
                self.__logger.debug("OffsetX is not implemented or not writable")

        if vpos is not None:
            self.ROI_vpos = vpos
            # update the camera setting
            if self.camera.OffsetY.is_implemented() and self.camera.OffsetY.is_writable():
                message = self.camera.OffsetY.set(self.ROI_vpos)
                self.__logger.debug(message)
            else:
                self.__logger.debug("OffsetX is not implemented or not writable")

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
        pass
            
    def getFrameNumber(self):
        return self.frameNumber 

    def send_trigger(self):
        pass

    def openPropertiesGUI(self):
        pass
    
    def set_frame(self, user_param, frame):
        pass
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