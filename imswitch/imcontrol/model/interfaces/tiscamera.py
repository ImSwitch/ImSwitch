import numpy as np
from .pyicic import IC_ImagingControl


class CameraTIS:
    def __init__(self, cameraNo):
        super().__init__()

        ic_ic = IC_ImagingControl.IC_ImagingControl()
        ic_ic.init_library()
        cam_names = ic_ic.get_unique_device_names()
        self.model = cam_names[cameraNo]
        self.cam = ic_ic.get_device(cam_names[cameraNo])

        self.cam.open()

        self.shape = (0,0)
        self.cam.colorenable = 0

        self.cam.enable_continuous_mode(True)  # image in continuous mode
        self.cam.enable_trigger(False)  # camera will wait for trigger

        self.roi_filter = self.cam.create_frame_filter('ROI'.encode('utf-8'))
        self.cam.add_frame_filter_to_device(self.roi_filter)

    def start_live(self):
        self.cam.start_live()  # start imaging

    def stop_live(self):
        self.cam.stop_live()  # stop imaging

    def suspend_live(self):
        self.cam.suspend_live()  # suspend imaging into prepared state

    def prepare_live(self):
        self.cam.prepare_live()  # prepare prepared state for live imaging

    def grabFrame(self):
        #self.cam.wait_til_frame_ready(20)  # wait for frame ready
        frame, width, height, depth = self.cam.get_image_data()
        frame = np.array(frame, dtype='float64')
        # Check if below is giving the right dimensions out
        #TODO: do this smarter, as I can just take every 3rd value instead of creating a reshaped 3D array and taking the first plane of that
        frame = np.reshape(frame, (height, width, depth))[:,:,0]
        frame = np.transpose(frame)
        return frame

    def setROI(self, hpos, vpos, hsize, vsize):
        hsize = max(hsize, 256)  # minimum ROI size
        vsize = max(vsize, 24)  # minimum ROI size
        #print(f'{self.model}: setROI started with {hsize}x{vsize} at {hpos},{vpos}.')
        self.cam.frame_filter_set_parameter(self.roi_filter, 'Top'.encode('utf-8'), vpos)
        self.cam.frame_filter_set_parameter(self.roi_filter, 'Left'.encode('utf-8'), hpos)
        self.cam.frame_filter_set_parameter(self.roi_filter, 'Height'.encode('utf-8'), vsize)
        self.cam.frame_filter_set_parameter(self.roi_filter, 'Width'.encode('utf-8'), hsize)
        top = self.cam.frame_filter_get_parameter(self.roi_filter, 'Top'.encode('utf-8'))
        left = self.cam.frame_filter_get_parameter(self.roi_filter, 'Left'.encode('utf-8'))
        hei = self.cam.frame_filter_get_parameter(self.roi_filter, 'Height'.encode('utf-8'))
        wid = self.cam.frame_filter_get_parameter(self.roi_filter, 'Width'.encode('utf-8'))
        print(f'{self.model}: setROI finished, following params are set: w{wid}xh{hei} at l{left},t{top}')

    def setPropertyValue(self, property_name, property_value):
        # Check if the property exists.
        if property_name == "gain":
            self.cam.gain = property_value
        elif property_name == "brightness":
            self.cam.brightness = property_value
        elif property_name == "exposure":
            self.cam.exposure = property_value
        elif property_name == 'image_height':
            self.shape = (self.shape[0], property_value)
        elif property_name == 'image_width':
            self.shape = (property_value, self.shape[1])
        else:
            print('Property', property_name, 'does not exist')
            return False
        return property_value

    def getPropertyValue(self, property_name):
        # Check if the property exists.
        if property_name == "gain":
            property_value = self.cam.gain.value
        elif property_name == "brightness":
            property_value = self.cam.brightness.value
        elif property_name == "exposure":
            property_value = self.cam.exposure.values
        elif property_name == "image_width":
            property_value = self.shape[0]
        elif property_name == "image_height":
            property_value = self.shape[1]
        else:
            print('Property', property_name, 'does not exist')
            return False
        return property_value

    def openPropertiesGUI(self):
        self.cam.show_property_dialog()


# Copyright (C) 2020, 2021 TestaLab
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
