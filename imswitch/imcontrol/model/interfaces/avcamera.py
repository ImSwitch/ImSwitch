import numpy as np
import time
from imswitch.imcommon.model import initLogger

from imswitch.imcontrol.model.interfaces.pymbacamera import AVCamera
 
class CameraAV:
    def __init__(self,cameraNo=None):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

        # many to be purged
        self.model = "AVCamera"
        self.shape = (0, 0)

        # camera parameters
        self.blacklevel = 100
        self.exposure_time = 0
        self.analog_gain = 0

        self.GAIN_MAX = 24
        self.GAIN_MIN = 0
        self.GAIN_STEP = 1

        self.frame_id_last = 0
        
        #%% starting the camera thread
        self.camera = AVCamera()
        

    def start_live(self):
        # check if camera is open
        if(not self.camera.is_alive()):
            self.camera.start()
        self.camera.start_live()

    def stop_live(self):
        self.camera.stop_live()
        

    def suspend_live(self):
        self.camera.stop_live()
        
        
    def prepare_live(self):
        pass

    def close(self):
        self.camera.close()
        self.camera.join()
        
    def set_exposure_time(self,exposure_time):
        self.exposure_time = exposure_time
        self.camera.setExposureTime(self.exposure_time*1000)

    def set_analog_gain(self,analog_gain):
        self.analog_gain = analog_gain
        self.camera.setGain(self.analog_gain)
        
    def set_blacklevel(self,blacklevel):
        self.blacklevel = blacklevel
        self.camera.setBlacklevel(self.blacklevel)

    def set_pixel_format(self,format):
        #TODO: Implement
        pass
        
    def getLast(self):
        # get frame and save
        if self.frame_id_last != self.camera.frame_id:
            return  self.camera.last_frame_preview
        else:
            self.__logger.debug("No new camera frame available")
            return None

    def getLastChunk(self):
        return self.camera.last_frame
       
    def setROI(self, hpos, vpos, hsize, vsize):
        #hsize = max(hsize, 256)  # minimum ROI size
        #vsize = max(vsize, 24)  # minimum ROI size
        image_Height = self.camera.feature("Height")
        image_Width = self.camera.feature("Width")
        image_Height.value = hsize
        image_Width.value = vsize
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
        elif property_name == "blacklevel":
            self.set_blacklevel(property_value)
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
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def openPropertiesGUI(self):
        pass

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