from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model.interfaces.restapicamera import RestPiCamera

from PIL import Image
import io
import requests
import time
import cv2
import numpy as np
from threading import Thread
import urllib

class CameraESP32Cam:
    def __init__(self, host, port):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

        # URL for the remote camera
        self.host = host
        self.port = port

        # many to be purged
        self.model = "ESP32Camera"
        self.shape = (0, 0)

        # camera parameters
        self.framesize = 100
        self.exposure_time = 0
        self.analog_gain = 0

        self.SensorWidth = 640
        self.SensorHeight = 480
        #%% starting the camera thread
        
        self.camera = ESP32Camera(self.host, self.port, is_debug=True)
        
        self.frame = np.zeros((self.SensorHeight,self.SensorWidth))
        
    def put_frame(self, frame):
        self.frame = frame
        return frame

    def start_live(self):
        # most likely the camera already runs
        self.camera.start_stream(self.put_frame)
        
    def stop_live(self):
        self.camera.stop_stream()

    def suspend_live(self):
        self.camera.stop_stream()
        
    def prepare_live(self):
        pass

    def close(self):
        pass #TODO: self.camera.close()
        
    def set_exposure_time(self,exposure_time):
        self.exposure_time=exposure_time
        self.camera.setExposureTime(self.exposure_time)

    def set_analog_gain(self,analog_gain):
        self.analog_gain=analog_gain
        self.camera.setGain(self.analog_gain)
        
    def set_framesize(self,framesize):
        self.framesize=framesize

    def set_pixel_format(self,format):
        pass
        
    def getLast(self):
        # get frame and save
        return self.frame

    def getLastChunk(self):
        return self.camera.getframe()
       
    def setROI(self, hpos, vpos, hsize, vsize):
        hsize = max(hsize, 256)  # minimum ROI size
        vsize = max(vsize, 24)  # minimum ROI size
        pass
        # self.__logger.debug(
        #     f'{self.model}: setROI started with {hsize}x{vsize} at {hpos},{vpos}.'
        # )
        #self.camera.setROI(vpos, hpos, vsize, hsize)


    def setPropertyValue(self, property_name, property_value):
        # Check if the property exists.
        if property_name == "gain":
            self.set_analog_gain(property_value)
        elif property_name == "exposure":
            self.set_exposure_time(property_value)
        elif property_name == "framesize":
            self.set_framesize(property_value)
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def getPropertyValue(self, property_name):
        # Check if the property exists.
        if property_name == "gain":
            property_value = self.camera.gain
        elif property_name == "exposure":
            property_value = self.camera.exposuretime
        elif property_name == "framesize":
            property_value = self.camera.framesize
        elif property_name == "image_width":
            property_value = self.camera.SensorWidth
        elif property_name == "image_height":
            property_value = self.camera.SensorHeight
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def openPropertiesGUI(self):
        pass
    

class ESP32Camera(object):
    # headers = {'ESP32-version': '*'}
    headers={"Content-Type":"application/json"}

    def __init__(self, host, port=80, is_debug=False):
        self.host = host
        self.port = port
        #self.get_json(self.base_uri)
        #self.populate_extensions()
        self.is_stream = False
        self.latest_frame = None
        self.is_debug = is_debug
        self.setup_id = -1
        
        self.SensorWidth = 640
        self.SensorHeight = 460
        self.exposuretime = 0
        self.gain = 0
        self.framesize = 0
        
        self.frame = np.zeros((self.SensorHeight,self.SensorWidth))
        
        self.__logger = initLogger(self, tryInheritParent=True)

        
    @property
    def base_uri(self):
        return f"http://{self.host}:{self.port}"

    def get_json(self, path):
        """Perform an HTTP GET request and return the JSON response"""
        if not path.startswith("http"):
            path = self.base_uri + path
        r = requests.get(path)
        r.raise_for_status()
        return r.json()

    def post_json(self, path, payload={}, headers=None, timeout=10):
        """Make an HTTP POST request and return the JSON response"""
        if not path.startswith("http"):
            path = self.base_uri + path
        if headers is None:
            headers = self.headers
            
        r = requests.post(path, json=payload, headers=headers,timeout=timeout)
        r.raise_for_status()
        r = r.json()
        return r

    def post(self, path, payload={}, headers=None, timeout=1):
        """Make an HTTP POST request and return the JSON response"""
        if not path.startswith("http"):
            path = self.base_uri + path
        if headers is None:
            headers = self.headers
        
        try:    
            r = requests.post(path, json=payload, headers=headers,timeout=timeout)
            r.raise_for_status()
        except Exception as e:
            self.__logger.error(e)
            r = -1
        return r

    
    #% LED
    def set_led(self, state=0):
        payload = {
            "value": state
        }
        path = '/led'
        if state:
            self.__logger.debug("WARNING: TRIGGER won't work if LED is turned on!")
        r = self.post_json(path, payload)
        return r
    
    def set_flash(self, state=0):
        payload = {
            "value": state
        }
        path = '/flash'
        r = self.post_json(path, payload)
        return r
    
    def set_id(self, m_id=0):
        payload = {
            "value": m_id
        }
        path = '/setID'
        r = self.post_json(path, payload)
        self.setup_id = r
        return r
    
    def setGain(self, gain=0):
        payload = {
            "gain": gain
        }
        path = '/postjson'
        r = self.post(path, payload)
        return r
    
    def setExposureTime(self, exposureTime=0):
        payload = {
            "exposuretime": exposureTime
        }
        path = '/postjson'
        r = self.post(path, payload)
        return r
    
    def get_id(self):
        path = '/getID'
        r = self.get_json(path)
        self.setup_id = r
        return r
    
    def is_omniscope(self):
        path = '/identifier'
        r = self.post_json(path)
        return r.find("OMNISCOPE")>=0

    def restart(self):
        path = '/restart'
        r = self.post_json(path)
        return r

    def start_stream(self, callback_fct = None):
        # Create and launch a thread    
        self.stream_url = "http://"+self.host+":81/stream.mjpeg"
        
        self.is_stream = True
        self.frame_receiver_thread = Thread(target = self.getframes, args=(self.stream_url,), daemon=True)
        self.frame_receiver_thread.start() 
        self.callback_fct = callback_fct

    def stop_stream(self):
        # Create and launch a thread    
        self.is_stream = False
        self.frame_receiver_thread.join()

    def getframe(self, is_triggered=False):
        url = "http://"+self.host+":80/capture"
        response = requests.get(url)
        bytes_im = io.BytesIO(response.content)
        frame = np.uint8(np.mean(np.array(Image.open(bytes_im)), -1))
        return frame
        
    def getframes(self, url):           
        bytesJPEG = bytes()
        try:
            stream = urllib.request.urlopen(url, timeout=2)
        except Exception as e:
            self.is_stream = False
            self.__logger.error("Stream could not be opened")
            self.__logger.error(e)
        frameId = 0
        errorCounter = 0
        while self.is_stream:
            try:
                bytesJPEG += stream.read(2**14)
                a = bytesJPEG.find(b'\xff\xd8')
                b = bytesJPEG.find(b'\xff\xd9')
                if a != -1 and b != -1:
                    jpg = bytesJPEG[a:b+2]
                    bytesJPEG = bytesJPEG[b+2:]
                    try:
                        frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                        frame = np.mean(frame,-1)
                        # flush stream and reset bytearray
                        stream.flush()
                        bytesJPEG = bytes() 
                        if self.is_debug:  
                            self.__logger.debug("Frame#"+str(frameId))
                            self.__logger.debug("Error#"+str(errorCounter))
                        frameId += 1
                        
                        if self.callback_fct is not None:
                            self.callback_fct(frame)
                        
                    except Exception as e:
                        errorCounter+=1
                    
                    # limit thread workload
                    time.sleep(.1)

                    
            except Exception as e:
                # reopen stream?
                self.__logger.error(e)
                stream = urllib.request.urlopen(url, timeout=2)


        
    def soft_trigger(self):
        path = '/softtrigger'
        r = self.post_json(path)
        return r

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