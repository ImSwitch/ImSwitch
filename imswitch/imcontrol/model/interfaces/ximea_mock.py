from dataclasses import dataclass
import numpy as np
import time
from imswitch.imcommon.model.logging import initLogger

class MockXimea:
    """Mock Ximea camera
    """
    
    def __init__(self) -> None:
        self.__logger = initLogger(self, tryInheritParent=True)
        self._device_info = {
            "device_name" : "MockXimea",
            "device_type" : "Ximea camera mock object"
        }
        self._device_id = "Mock Ximea camera"
        self._exposure = 0
        self._width = 1280
        self._height = 864
        self._ofs_x = 0
        self._ofs_y = 0

        self._mock_data_max_value = (2**10)-1
        self._mock_acquisition_running = False
        self._mock_start_time = time.time_ns()

    def open_device(self):
        self.__logger.info("Mock object opened")
    
    def close_device(self):
        self.__logger.info("Mock object closed")
    
    def set_param(self, param, value):
        # todo: implement ... ?
        pass
    
    def get_device_info_string(self, info):
        return self._device_info[info]

    def get_device_model_id(self):
        return "Mock Ximea camera"

    def set_exposure(self, exposure):
        self._exposure = exposure
    
    def get_image(self, image):
        # todo: does this work?
        image = MockImage(self._width - self._ofs_x
                        , self._height - self._ofs_y
                        , self._mock_data_max_value)

    def start_acquisition(self):
        self._mock_acquisition_running = True

    def stop_acquisition(self):
        self._mock_acquisition_running = False

    def get_width_maximum(self):
        return 1280

    def get_height_maximum(self):
        return 864

    def set_offsetX(self, ofs_x):
        self._ofs_x = ofs_x

    def set_offsetY(self, ofs_y):
        self._ofs_x = ofs_y

    def set_width(self, width):
        self._width = width

    def set_height(self, height):
        self._height = height
    
    def get_width(self):
        return self._width
    
    def get_height(self):
        return self._height

@dataclass
class MockImage:
    width   : int = 1280
    height  : int = 864
    max_val : int = (2**10)-1

    def get_image_data_numpy(self):
        return np.random.randint(0, self.max_val, (self.height, self.width), np.uint16)

# Copyright (C) 2021 Eggeling Group
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