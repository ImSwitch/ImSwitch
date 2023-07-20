from logging import raiseExceptions
import numpy as np
import time
import cv2
import collections

from imswitch.imcommon.model import initLogger

try:
    import pco
    from pco import sdk
except:
    raise("PCO not installed")



class TriggerMode:
    SOFTWARE = 'Software Trigger'
    HARDWARE = 'Hardware Trigger'
    CONTINUOUS = 'Continuous Acqusition'

class CameraPCO:
    def __init__(self,cameraNo=None, exposure_time = 10000, gain = 0, frame_rate=-1, blacklevel=100, binning=1):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

        # many to be purged
        self.model = "CameraPCO"
        self.shape = (0, 0)
        
        self.is_connected = False
        self.is_streaming = False

        # unload CPU? 
        self.downsamplepreview = 1

        # camera parameters
        self.exposure_time = exposure_time
        self.preview_width = 600
        self.preview_height = 600

        # reserve some space for the framebuffer
        self.NBuffer = 20
        self.frame_buffer = collections.deque(maxlen=self.NBuffer)
        self.frameid_buffer = collections.deque(maxlen=self.NBuffer)
        self.frameID = -1
        self.frame_id_last = -1

        #%% starting the camera thread
        self.camera = None

        # binning 
        self.binning = binning

        try:
            self._init_cam()
        except Exception as e:
            self.__logger.error(e)
            raise("Camera not found")
            
    def _init_cam(self):
        # start camera
        self.is_connected = True
        
        # open the first device
        self.camera = pco.Camera()

        # set exposure
        # self.camera.set_exposure_time(self.exposure_time*1e-6)

        # get dummy frame
        self.camera.record(number_of_images=self.NBuffer,mode='ring buffer')
        self.camera.wait_for_first_image()
        frame = self.camera.image()[0]
        # get framesize 
        self.SensorHeight = frame.shape[0] #self.camera._Camera__roi['x1']//self.binning
        self.SensorWidth = frame.shape[0] #self.camera._Camera__roi['y1']//self.binning
        
        
    def start_live(self):
        if not self.is_streaming:
            # start data acquisition
            self.camera.record(number_of_images=self.NBuffer,mode='ring buffer')
            self.camera.wait_for_first_image()
            self.is_streaming = True

    def stop_live(self):
        if self.is_streaming:
            # start data acquisition
            self.camera.stop()
            self.is_streaming = False

    def suspend_live(self):
        pass
        
    def prepare_live(self):
        pass

    def close(self):
        self.camera.close()
        
    def set_exposure_time(self,exposure_time):
        self.exposure_time = exposure_time
        try:
            self.camera.set_exposure_time(self.exposure_time*1e-3)
        except:
            self.__logger.error("Not possible to set exposure time now...(PCO)")

    def setBinning(self, binning=1):
        # Unfortunately this does not work
        # self.camera.BinningHorizontal.set(binning)
        # self.camera.BinningVertical.set(binning)
        self.binning = binning

    def getLast(self, is_resize=True):
        # Display in the liveview
        # ensure that only fresh frames are being returned
        while self.frame_id_last >= self.frameID:
            self.frame_raw_metadata = self.camera.image(image_number=-1)

            self.frame = self.frame_raw_metadata[0]
            self.frameID = self.frame_raw_metadata[1]["recorder image number"]
            #self.__logger.debug("Waiting for frame..."+str(self.frame_id_last))
        self.frame_id_last = self.frameID
        return self.frame
    
    def getLastFrameId(self):
        return self.frameID

    def flushBuffer(self):
        self.frameid_buffer.clear()
        self.frame_buffer.clear()
        
    def getLastChunk(self):
        # save on disk
        images, metadatas = self.camera.images()[0]
        chunk = np.array(images).mean()
        self.__logger.debug("Buffer: "+str(chunk.shape))
        return chunk
    
    def setROI(self,hpos=None,vpos=None,hsize=None,vsize=None):
        return hpos,vpos,hsize,vsize

    def setPropertyValue(self, property_name, property_value):
        # Check if the property exists.
        if property_name == "exposure":
            self.set_exposure_time(property_value)
        elif property_name == "roi_size":
            self.roi_size = property_value
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def getPropertyValue(self, property_name):
        # Check if the property exists.
        if property_name == "exposure":
            property_value = self.camera.ExposureTime.get()
        elif property_name == "image_width":
            property_value = self.camera.Width.get()//self.binning         
        elif property_name == "image_height":
            property_value = self.camera.Height.get()//self.binning
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
        
        if self.binning > 1:
            numpy_image = cv2.resize(numpy_image, dsize=None, fx=1/self.binning, fy=1/self.binning, interpolation=cv2.INTER_AREA)
    
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