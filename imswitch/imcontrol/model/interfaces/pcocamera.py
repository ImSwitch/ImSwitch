from logging import raiseExceptions
import numpy as np
import time
import cv2
import collections

from imswitch.imcommon.model import initLogger
import threading
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

        # unload CPU? 
        self.downsamplepreview = 1

        # camera parameters
        self.exposure_time = exposure_time
        self.preview_width = 600
        self.preview_height = 600
        self.defaultBufferSize = 30
        # dict for different trigger mode
        self.trigger_type = ['software trigger', 
                             'auto sequence',
                             'external exposure start & software trigger',
                             'external exposure control'
                             ]
        self.current_trigger_type = self.trigger_type[0]
        self.frameID = -1
        self.camera = None
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
        

    def start_live(self, waitForFirstImage=True, nFrameBuffer=None):
        if not self.camera.is_recording:
            if nFrameBuffer is None:
                nFrameBuffer = self.defaultBufferSize
            # start data acquisition    
            try:
                self.camera.record(number_of_images=nFrameBuffer,mode='ring buffer')
            except Exception as e:
                print(e)
                self.camera.stop()
                self.camera.record(number_of_images=nFrameBuffer,mode='ring buffer')
            if  0 and waitForFirstImage: # TODO: this is not working
                try: 
                    self.camera.wait_for_first_image(timeout=1)
                except Exception as e:
                    self.__logger.error(e)

    def stop_live(self):
        if self.camera.is_recording:
            self.camera.stop()
            
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
        if self.camera.configuration['trigger'] in [self.trigger_type[3], self.trigger_type[2]]:
            # in that case we want to return the last frame of the buffer ?
            if self.frames is not None and len(self.frames)>0:
                return self.frames[-1]
            else: 
                return None
        else:
            self.frame_raw_metadata = self.camera.image(image_index=-1)
            #time.sleep(0.001)
            self.frame = self.frame_raw_metadata[0]
            self.frameID = self.frame_raw_metadata[1]["recorder image number"]
            return self.frame
        
    
    def getLastFrameId(self):
        return self.frameID

    def flushBuffer(self):
        pass
        
    def getLastChunk(self, timeout=2):
        # save on disk
        self.frames = None
        if self.camera.is_recording:
            # Create a thread to run the call_images function
            def retreiveChunkInBackground():
                # TODO: if we are in triggered mode this can be a blocking function :(
                self.frames, metadatas = self.camera.images() 
                self.frame = self.camera.images()[0] # FIXME: Sneaky but should at least update the viewer if it's called from the main loop
                self.frameID = metadatas[0]["recorder image number"]
            thread = threading.Thread(target=retreiveChunkInBackground)

            # Start the thread             # Wait for the thread to complete or timeout
            thread.start()
            thread.join(timeout)

            if thread.is_alive():
                print("The images function call has timed out and will continue running in its thread.")
            else:
                print("The images function call completed successfully.")
        return self.frames
    
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
        wasRunning = self.camera.is_recording
        if wasRunning: self.stop_live()
        if source == 'Continous':
            self.camera.configuration = {'trigger': self.trigger_type[0]}
        elif source == 'Internal trigger':
            self.camera.configuration = {'trigger': self.trigger_type[1]}
        elif source == 'External start':
            self.camera.configuration = {'trigger': self.trigger_type[2]}
            if wasRunning: 
                self.start_live(waitForFirstImage=False)
            return
        elif source == 'External control':
            self.camera.configuration = {'trigger': self.trigger_type[3]}
            if wasRunning: 
                self.start_live(waitForFirstImage=False)
            return            
        else:
            raise ValueError(f'Invalid trigger source "{source}"')
        self.start_live()
        
    def setFrameBuffer(self, nFrameBuffer=10, waitForFirstImage=False):
        wasRunning = self.camera.is_recording
        if wasRunning:
            self.stop_live()
        if nFrameBuffer == -1:
            nFrameBuffer = self.defaultBufferSize
        self.start_live(waitForFirstImage=waitForFirstImage, nFrameBuffer=nFrameBuffer)
            

    

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