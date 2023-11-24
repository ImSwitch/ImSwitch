# image processing libraries
from dataclasses_json.api import _process_class
import numpy as np
import time
import cv2, queue, threading
from imswitch.imcommon.model import initLogger
from threading import Thread

import collections

class CameraOpenCV:
    def __init__(self, cameraindex=0, isRGB=False):
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
        self.NBuffer = 1
        self.frame_buffer = collections.deque(maxlen=self.NBuffer)

        #%% starting the camera => self.camera  will be created
        self.cameraindex = cameraindex
        self.isRGB = isRGB
        self.openCamera(self.cameraindex, self.SensorWidth, self.SensorHeight, self.isRGB)


    def start_live(self):
        # check if camera is open
        if not self.camera_is_open:
            self.camera_is_open = True
            self.openCamera(self.cameraindex, self.SensorWidth, self.SensorHeight, self.isRGB)

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

    def set_exposure_time(self,exposure_time):
        self.exposure_time = exposure_time
        try:
            self.camera.set(cv2.CAP_PROP_EXPOSURE, self.exposure_time)
        except Exception as e:
            self.__logger.error(e)
            self.__logger.debug("Error setting Exposure time in opencv camera")

    def set_analog_gain(self,analog_gain):
        self.analog_gain = analog_gain
        try:
            self.camera.set(cv2.CAP_PROP_EXPOSURE, self.analog_gain)
        except Exception as e:
            self.__logger.error(e)
            self.__logger.debug("Error setting Exposure time in opencv camera")

    def set_blacklevel(self,blacklevel):
        self.blacklevel = blacklevel
        self.__logger.debug("Error setting blacklevel time in opencv camera")

    def set_pixel_format(self,format):
        self.pixelformat = format
        self.__logger.debug("Error setting pixelformat time in opencv camera")

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

    def openCamera(self, cameraindex, width, height, isRGB):
        # open camera
        self.camera = cv2.VideoCapture(cameraindex, cv2.CAP_DSHOW)
        self.__logger.debug("Camera is open")
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920.0) # 4k/high_res
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080.0) # 4k/high_res
        # let the camera warm up
        for i in range(5):
            _, img = self.camera.read()
        width = self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(width, height)
        self.__logger.debug("Camera is warmed up")

        self.SensorHeight = img.shape[0]
        self.SensorWidth = img.shape[1]
        self.shape = (self.SensorWidth,self.SensorHeight)
        self.camera_is_open = True
        

        # starting thread
        self.frameGrabberThread = Thread(target = self.setFrameBuffer, args=(isRGB,))
        self.frameGrabberThread.start()



    def setFrameBuffer(self, isRGB=True):
        while(self.camera_is_open):
            try:
                self.frame = self.camera.read()[1]
                if not isRGB and len(self.frame.shape)>2:
                    self.frame = np.uint8(np.mean(self.frame, -1))
                self.frame_buffer.append(self.frame)
            except Exception as e:
                self.camera_is_open = False
                self.__logger.debug(e)
