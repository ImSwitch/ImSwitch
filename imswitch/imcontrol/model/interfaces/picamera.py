import numpy as np
import time
from imswitch.imcommon.model import initLogger
import socket
from imswitch.imcontrol.model.interfaces.restapicamera import RestPiCamera


class CameraPiCam:
    def __init__(self, host, port):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

        # URL for the remote camera
        self.host = host
        self.port = port

        # many to be purged
        self.model = "PiCamera"
        self.shape = (0, 0)

        # camera parameters
        self.blacklevel = 100
        self.exposure_time = 0
        self.analog_gain = 0

        self.SensorWidth = 640
        self.SensorHeight = 480
        # starting the camera thread

        self.camera = RestPiCamera(self.host, self.port)

    def start_live(self):
        # most likely the camera already runs
        pass #TODO:         self.camera.start_live()

    def stop_live(self):
        pass         #TODO: self.camera.stop_live()

    def suspend_live(self):
        pass        #TODO: self.camera.stop_live()

    def prepare_live(self):
        pass

    def close(self):
        pass #TODO: self.camera.close()

    def set_exposure_time(self, exposure_time):
        self.exposure_time = exposure_time
        self.camera.set_exposuretime(self.exposure_time*1000)

    def set_analog_gain(self, analog_gain):
        self.analog_gain = analog_gain
        self.camera.set_iso(self.analog_gain)

    def set_blacklevel(self, blacklevel):
        pass

    def set_pixel_format(self, format):
        pass

    def getLast(self):
        # get frame and save
        return self.camera.get_preview()

    def getLastChunk(self):
        return self.camera.get_snap()

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