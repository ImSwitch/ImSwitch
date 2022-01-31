# image processing libraries
import numpy as np
import time
import cv2, queue, threading
from imswitch.imcommon.model import initLogger

class CameraJETSON:
    def __init__(self):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=False)

        # many to be purged
        self.model = "JetsonCamera"
        
        # camera parameters
        self.blacklevel = 0
        self.exposure_time = 10
        self.analog_gain = 0
        self.pixel_format = "Mono8"

        self.frame_id_last = 0

        self.PreviewWidthRatio = 4
        self.PreviewHeightRatio = 4
        

        self.SensorWidth = 1920
        self.SensorHeight = 1080
        # self.camera = self.openCamera(self.SensorWidth, self.SensorHeight)
        
        #%% starting the camera 
        # thhis is going to be suuper hacky, but opencv in an environemnt does not have gstreamer so we stream it through IP! 
        try:
            import os
            #os.system("sudo systemctl restart nvargus-daemon")
            os.system("/usr/bin/python3 /home/uc2/Downloads/imswitch/imswitch/imcontrol/model/interfaces/jetsonstreamer/jetsonstreamer.py &")
        except Exception as e:
            self.__logger.error(e)
            self.__logger.error("Did you run 'sudo systemctl restart nvargus-daemon' ?")
        self.camera = self.openCamera(self.SensorWidth, self.SensorHeight)


    def start_live(self):
        # check if camera is open
        if not self.camera_is_open:
            self.camera_is_open = True
            self.openCamera(self.SensorWidth, self.SensorHeight)
        
         
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
        frame = np.mean(self.camera.read()[1], -1)
        return frame
        '''
        self.__logger.debug("Frame", str(frame.shape))
        return cv2.resize(frame, dsize=None, 
                fx=1/self.PreviewWidthRatio, fy=1/self.PreviewHeightRatio, 
                interpolation= cv2.INTER_LINEAR)
        '''

    def getLastChunk(self):
        return np.mean(self.camera.read()[1], -1)
       
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

    def openCamera(self, width, height):
        # open camera
        time.sleep(2) # wait until stream starts
        camera = cv2.VideoCapture("http://0.0.0.0:8000")
        self.__logger.debug("Camera is open")

        # let the camera warm up
        for i in range(5):
            _, img = camera.read() 

        self.__logger.debug("Camera is warmed up")

        self.SensorHeight = img.shape[0]
        self.SensorWidth = img.shape[1]
        self.shape = (self.SensorWidth,self.SensorHeight)
        self.camera_is_open = True
        
        return camera 
        

    
    # gstreamer pipeline for the jetson IMX219 camera
    def gstreamer_pipeline(self,
        capture_width=640,
        capture_height=480,
        display_width=640,
        display_height=480,
        exposuretime=1,
        framerate=120,
        flip_method=0
    ):
        #gst-launch-1.0 
        # nvarguscamerasrc awblock=true aelock=false  exposuretimerange="100000 100000"  gainrange="1 1" ispdigitalgainrange="1 1"  ! 'video/x-raw(memory:NVMM),width=1920,height=1080,format=NV12' ! nvoverlaysink
        # nvarguscamerasrc awblock=true aelock=false width=(int)640, height=(int)480, exposuretimerange="(int)100000 (int)100000" gainrange="1 1" ispdigitalgainrange="1 1" format=(string)NV12, framerate=(fraction)120/1 ! nvvidconv flip-method=0 ! video/x-raw, width=(int)640, height=(int)480, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsinkvideo/x-raw(memory:NVMM), 

        exposuretime = int(exposuretime*100000)
        return (
            'nvarguscamerasrc '
            'exposuretimerange="%d %d" gainrange="1 1" ispdigitalgainrange="1 1" '
            'awblock=true aelock=true '
            '! video/x-raw(memory:NVMM), '
            #"width=(int)%d, height=(int)%d, "
            'width=(int)%d, height=(int)%d, ' #" ##exposurecompensation=-2, aelock=true, "  #exposuretimerange=34000 35873300, 
            "format=(string)NV12, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink"
            % (
                exposuretime,
                exposuretime,
                capture_width,
                capture_height, 
                framerate,
                flip_method,
                display_width,
                display_height,
            )
        )



