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
    SOFTWARE = 'software trigger'
    HARDWARE = 'external exposure start & software trigger'
    CONTINUOUS = 'auto sequence'

class CameraPCO:
    def __init__(self,cameraNo=None, exposure_time = 10000, gain = 0, frame_rate=10, blacklevel=100, binning=1):
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
        
        # dict for different trigger mode
        self.trigger_type = ['software trigger', 
                             'auto sequence',
                             'external exposure start & software trigger',
                             'external exposure control'
                             ]

        # reserve some space for the framebuffer
        self.NBuffer = 30
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
        #☺pco.Camera(debuglevel='verbose', timestamp='on')

        # set exposure
        # self.camera.set_exposure_time(self.exposure_time*1e-6)

        # get dummy frame
        self.start_live()
       
        frame = self.camera.image()[0]
        # get framesize 
        self.SensorHeight = frame.shape[0] #self.camera._Camera__roi['x1']//self.binning
        self.SensorWidth = frame.shape[0] #self.camera._Camera__roi['y1']//self.binning
        
    
    def get_triggered_framebuffer(self, nFrames: int = 9):
        '''
        Here we want to get the exact number of frames e.g. in case of triggering events
        '''
        preTriggerMode = self.camera.sdk.get_trigger_mode()
        self.camera.stop()
        self.camera.configuration = {'trigger': 'external exposure start & software trigger'}
        self.camera.record(nFrames,'ring buffer')
        self.camera.wait_for_first_image()
        imageStack, stackMetadata = self.camera.images(blocksize=nFrames) #meta data will also returned
        self.camera.configuration = {'trigger': preTriggerMode}
        return imageStack, stackMetadata
    
        
    def start_live(self, waitForFirstImage=True):
        if not self.is_streaming:
            # start data acquisition    
            try:
                self.camera.record(number_of_images=self.NBuffer,mode='ring buffer')
            except:
                self.camera.stop()
                self.camera.record(number_of_images=self.NBuffer,mode='ring buffer')
            if waitForFirstImage: self.camera.wait_for_first_image()
            self.is_streaming = True

    def stop_live(self):
        if self.is_streaming or self.camera.is_recording:
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
            self.camera.exposure_time = self.exposure_time*1e-3
            #self.camera.sdk.set_frame_rate(274, int(self.exposure_time*1e3))
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
        while self.frame_id_last >= self.frameID and self.camera.is_recording:
            self.frame_raw_metadata = self.camera.image(image_index=-1)
            #time.sleep(0.001)
            self.frame = self.frame_raw_metadata[0]
            self.frameID = self.frame_raw_metadata[1]["recorder image number"]
            #self.__logger.debug("Frame ID..."+str(self.frame_id_last))
        self.frame_id_last = self.frameID
        return self.frame
    
    def getLastFrameId(self):
        return self.frameID

    def flushBuffer(self):
        self.frameid_buffer.clear()
        self.frame_buffer.clear()
        
    def getLastChunk(self, timeout=-1):
        # save on disk
        if self.camera.is_recording:
            images, metadatas = self.camera.images() 
            self.frame = self.camera.images()[0] # FIXME: Sneaky but should at least update the viewer if it's called from the main loop
            return images
    
    def setROI(self,hpos=None,vpos=None,hsize=None,vsize=None):
        return hpos,vpos,hsize,vsize

    def setPropertyValue(self, property_name, property_value):
        # Check if the property exists.
        if property_name == "exposure":
            self.camera.exposure_time = property_value*1e-3
        elif property_name == 'trigger_source':
            self.setTriggerSource(property_value)
        elif property_name == "buffer_size":
            self.setFrameBuffer(property_value)
        elif property_name == "roi_size":
            self.camera.skd.set_roi(0,0,property_value)
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def getPropertyValue(self, property_name):
        # Check if the property exists.
        #if property_name == "exposure":
            #property_value = self.camera.exposure_time * 1e3
        if property_name == "image_width":
            property_value = self.camera.Width.get()//self.binning         
        elif property_name == "image_height":
            property_value = self.camera.Height.get()//self.binning
        elif property_name == "roi_size":
            property_value = self.roi_size 
        elif property_name == "framerate":
            property_value = format(1 / self.camera.exposure_time, '.1f')
             #property_value = self.camera.sdk.get_frame_rate() 
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def openPropertiesGUI(self):
        pass

    def setTriggerSource(self, source):
        self.stop_live()
        if source == 'Continous':
            self.camera.configuration = {'trigger': self.trigger_type[0]}
        elif source == 'Internal trigger':
            self.camera.configuration = {'trigger': self.trigger_type[1]}
        elif source == 'External start':
            self.camera.configuration = {'trigger': self.trigger_type[2]}
            self.start_live(waitForFirstImage=False)
            return
        elif source == 'External control':
            self.camera.configuration = {'trigger': self.trigger_type[3]}
            self.start_live(waitForFirstImage=False)
            return            
        else:
            raise ValueError(f'Invalid trigger source "{source}"')
        self.start_live()
        
    def setFrameBuffer(self, nFrameBuffer=10, waitForFirstImage=False):
        self.stop_live()
        self.NBuffer = nFrameBuffer
        self.camera.record(self.NBuffer, "ring buffer")
        if waitForFirstImage: self.camera.wait_for_first_image()        
        

    

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