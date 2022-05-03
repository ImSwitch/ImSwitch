# image processing libraries
import numpy as np
import time
import cv2, queue, threading
from imswitch.imcommon.model import initLogger
from threading import Thread

import collections

class CameraOpenCV:
    def __init__(self, cameraindex=0):
        super().__init__()
        # we are aiming to interface with webcams or arducams 
        self.__logger = initLogger(self, tryInheritParent=False)

        # many to be purged
        self.model = "CameraOpenCV"
        
        # camera parameters
        self.blacklevel = 0
        self.exposure_time = 10
        self.analog_gain = 0
        self.pixel_format = "Mono8"

        self.frame_id_last = 0

        self.PreviewWidthRatio = 4
        self.PreviewHeightRatio = 4

        self.SensorWidth = 1000
        self.SensorHeight = 1000
        
        # reserve some space for the framebuffer
        self.buffersize = 60
        self.frame_buffer = collections.deque(maxlen=self.buffersize)
        
        #%% starting the camera => self.camera  will be created
        self.cameraindex = cameraindex
        self.openCamera(self.cameraindex, self.SensorWidth, self.SensorHeight)


    def start_live(self):
        # check if camera is open
        if not self.camera_is_open:
            self.camera_is_open = True
            self.openCamera(self.cameraindex, self.SensorWidth, self.SensorHeight)
        
    def stop_live(self):
        self.camera.release()
        self.camera_is_open = False

    def suspend_live(self):
        self.camera.release()
        self.camera_is_open = False

    def prepare_live(self):
        pass

    def close(self):
        self.camera.release()
        self.camera_is_open = False
        
    def set_value(self ,feature_key, feature_value):
        # Need to change acquisition parameters?
        self.camera.set(cv2.CAP_PROP_EXPOSURE, feature_value) 
        try:
            pass
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
        
    def getLast(self, is_resize=True):
        # get frame and save
        #TODO: Napari only displays 8Bit?
        return self.frame

    def getLastChunk(self):
        chunk = np.array(self.frame_buffer)
        #frameids = self.frame_buffer[1]
        self.__logger.debug("Buffer: "+str(len(self.frame_buffer))+"  "+str(chunk.shape))
        self.frame_buffer.clear()
        return chunk
    
    def setROI(self, hpos, vpos, hsize, vsize):
        pass

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
            property_value = self.gain
        elif property_name == "exposure":
            property_value = self.exposure
        elif property_name == "blacklevel":
            property_value = self.blacklevel
        elif property_name == "image_width":
            property_value = self.SensorWidth
        elif property_name == "image_height":
            property_value = self.SensorHeight
        elif property_name == "pixel_format":
            property_value = self.PixelFormat
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def openPropertiesGUI(self):
        pass

    def openCamera(self, cameraindex, width, height):
        # open camera
        self.camera = cv2.VideoCapture(cameraindex)
        self.__logger.debug("Camera is open")

        # let the camera warm up
        for i in range(5):
            _, img = self.camera.read() 

        self.__logger.debug("Camera is warmed up")

        self.SensorHeight = img.shape[0]
        self.SensorWidth = img.shape[1]
        self.shape = (self.SensorWidth,self.SensorHeight)
        self.camera_is_open = True
        
        # starting thread
        self.frameGrabberThread = Thread(target = self.setFrameBuffer)
        self.frameGrabberThread.start()
        
    

    def setFrameBuffer(self):
        while(self.camera_is_open):
            try:
                self.frame = np.mean(self.camera.read()[1], -1)
                self.frame_buffer.append(self.frame)
            except Exception as e:
                self.camera_is_open = False
                self.__logger.debug(e)
                
                
            
            