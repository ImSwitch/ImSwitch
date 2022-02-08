import numpy as np
import time
import cv2
from imswitch.imcommon.model import initLogger
try:
    from pymba import Vimba, VimbaException
except:
    print("No pymba installed..")
    
import collections

 
class CameraAV:
    def __init__(self,cameraNo=None):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

        # many to be purged
        self.model = "AVCamera"
        
        # camera parameters
        self.blacklevel = 100
        self.exposure_time = 10
        self.analog_gain = 0
        self.pixel_format = "Mono12"

        self.frame_id_last = 0

        self.PreviewWidthRatio = 2
        self.PreviewHeightRatio = 2
        
        # reserve some space for the framebuffer
        self.frame_buffer = collections.deque(maxlen=10)
        
        
        #%% starting the camera thread
        self.vimba = self.startVimba()
        self.openCamera(self.set_frame,is_init=True) # open camera and set callback for frame grabbing

    def start_live(self):
        # check if camera is open
        try:
            if not self.camera._is_armed:
                self.camera.arm("Continuous", self.set_frame)
        except:
            # try reconnecting the camera via software 
            try:
                self.camera.close()
                self.vimba.shutdown()
                del self.vimba
                del self.camera
                self.vimba = self.startVimba()
                self.openCamera(self.set_frame) # open camera and set callback for frame grabbing
            except Exception as e:
                self.__logger.error("Restarting the camera failed")
                self.__logger.error(e)
        self.camera.start_frame_acquisition()

    def stop_live(self):
        try:
            self.camera.stop_frame_acquisition()
            if self.camera._is_armed:
                self.camera.disarm()
        except Exception as e:
                self.__logger.error("Stopping Camera failed - nothing connected?")
                self.__logger.error(e)

    def suspend_live(self):
        try:
            self.camera.stop_frame_acquisition()
        except Exception as e:
            self.__logger.error("Suspending live failed - nothing connected?")
            self.__logger.error(e)

    def prepare_live(self):
        pass

    def close(self):
        try:
            self.camera.stop_frame_acquisition()
        except:
            pass
        
        try:
            if self.camera._is_armed:
                self.camera.disarm()
            self.camera.close()
        except Exception as e:
                self.__logger.error("Closing Camera failed - nothing connected?")
                self.__logger.error(e)

    def set_value(self ,feature_key, feature_value):
        # Need to change acquisition parameters?
        try:
            feature = self.camera.feature(feature_key)
            feature.value = feature_value
        except Exception as e:
            self.__logger.error(e)
            self.__logger.error(feature_key)
            self.__logger.debug("Value not available?")
    
    def set_exposure_time(self,exposure_time):
        self.exposure_time = exposure_time
        self.set_value("ExposureTime", self.exposure_time*1000)

    def set_analog_gain(self,analog_gain):
        self.analog_gain = analog_gain
        self.set_value("Gain", self.analog_gain)
        
    def set_blacklevel(self,blacklevel):
        self.blacklevel = blacklevel
        self.set_value("BlackLevel", blacklevel)

    def set_pixel_format(self,format):
        self.pixelformat = format
        self.set_value("PixelFormat", format)
        
    def getLast(self):
        # get frame and save
#        frame_norm = cv2.normalize(self.frame, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)       
        #TODO: Napari only displays 8Bit?
        return cv2.resize(self.frame, dsize=None, 
                fx=1/self.PreviewWidthRatio, fy=1/self.PreviewHeightRatio, 
                interpolation= cv2.INTER_LINEAR)
                
        '''
        if self.frame_id_last != self.camera.frame_id:
            return  self.camera.last_frame_preview
        else:
            self.__logger.debug("No new camera frame available")
            return None
        '''
        
    def getLastChunk(self):
        return self.frame_buffer
       
    def setROI(self, hpos, vpos, hsize, vsize):
        hsize = max(hsize, 256)  # minimum ROI size
        vsize = max(vsize, 256)  # minimum ROI size
        self.__logger.debug(
             f'{self.model}: setROI started with {hsize}x{vsize} at {hpos},{vpos}.')
        try:
            image_Height = self.camera.feature("Height")
            image_Width = self.camera.feature("Width")
            image_Height.value = hsize
            image_Width.value = vsize
            self.shape = (image_Width.value,image_Height.value)
        except Exception as e:
            self.__logger.error("Setting the ROI")
            self.__logger.error(e)

    def setPropertyValue(self, property_name, property_value):
        # Check if the property exists.
        if property_name == "gain":
            self.set_analog_gain(property_value)
        elif property_name == "exposure":
            self.set_exposure_time(property_value)
        elif property_name == "blacklevel":
            self.set_blacklevel(property_value)
        elif property_name == "pixel_format":
            self.stop_live()
            self.set_pixel_format(property_value)
            self.start_live()
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def getPropertyValue(self, property_name):
        # Check if the property exists.
        if property_name == "gain":
            property_value = self.camera.gain
        elif property_name == "exposure":
            property_value = self.camera.gain
        elif property_name == "blacklevel":
            property_value = self.camera.blacklevel
        elif property_name == "image_width":
            property_value = self.camera.SensorWidth
        elif property_name == "image_height":
            property_value = self.camera.SensorHeight
        elif property_name == "pixel_format":
            property_value = self.camera.PixelFormat
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def openPropertiesGUI(self):
        pass

    def startVimba(self, is_restart = False):
        '''
        get the camera instance
        NOTE: This has to be closed before the programm is done! 
        '''
        if is_restart:
            try:
                self.vimba.shutdown()
                del self.vimba
            except:
                pass
        vimba = Vimba()
        vimba.startup()
        return vimba

    def openCamera(self, callback_fct, is_init=False):
        try:
            self.camera = self.vimba.camera(0)
            self.camera.open()
            try:
                feature = self.camera.feature("PixelFormat")
                feature.value = "Mono12"
            except Exception as e:
                self.__logger.error(e)
                self.__logger.debug("Pixel Format could not be set")
            
            self.needs_reconnect = False
            self.is_camera_open = True
            self.camera.arm('Continuous',callback_fct)
            self.__logger.debug("camera connected")
            self.SensorHeight = self.camera.feature("SensorHeight").value
            self.SensorWidth = self.camera.feature("SensorWidth").value
            #self.shape = (np.min((self.SensorHeight,self.SensorWidth)),np.min((self.SensorHeight,self.SensorWidth)))
            self.shape = (self.SensorWidth,self.SensorHeight)

        except Exception as e:
            self.__logger.debug(e)
            if is_init:
                # make sure mock gets called when initilizing
                self.vimba.shutdown()
                raise Exception

    def set_frame(self, frame):
        self.frame = frame.buffer_data_numpy()
        self.frame_id = frame.data.frameID
        if self.frame is None:
            self.frame = np.zeros(self.shape)
        self.frame_buffer.append(self.frame)
    

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