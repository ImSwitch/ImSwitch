import numpy as np

from imswitch.imcommon.model import initLogger
from .pyicic import IC_ImagingControl
import imagingcontrol4 as ic4
import pdb


class CameraTIS4:
    def __init__(self, cameraNo):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

        ic4.Library.init()
        cam_names = ic4.DeviceEnum.devices()
        self.model = cam_names[cameraNo]
        self.cam = ic4.Grabber()
        self.cam.device_open(self.model)
        # pdb.set_trace()

        self.sink = ic4.SnapSink()
        # Defer acquisition means that, self.cam.start_acquisition needs to be called
        self.cam.stream_setup(self.sink,
                              setup_option=ic4.StreamSetupOption.DEFER_ACQUISITION_START,
                              )

        # set auto gain off
        self.cam.device_property_map.set_value(
            ic4.PropId.GAIN_AUTO, False
        )
        # can I set format here?
        try:
            self.cam.device_property_map.set_value(
                            ic4.PropId.PIXEL_FORMAT,
                            ic4.PixelFormat.Mono16)
        except Exception as e:
            self.__logger.warn('Could not set the pixel format')
            self.__logger.debug(e)

    def start_live(self):
        self.cam.acquisition_start()  # start imaging

    def stop_live(self):
        self.cam.acquisition_stop()  # stop imaging

    def suspend_live(self):
        # self.cam.suspend_live()  # suspend imaging into prepared state
        self.cam.acquisition_stop()

    def prepare_live(self):
        self.cam.prepare_live()  # prepare prepared state for live imaging

    def grabFrame(self):
        image = self.sink.snap_single(10000)
        # if image.image_type.pixel_format == ic4.PixelFormat.Mono8:
        #     frame = np.array(frame, dtype='float64')
        frame = image.numpy_wrap()[:, :, 0]
        self.__logger.info(f'image format: {frame.dtype, frame.shape}')
        return np.transpose(frame)
        # ic4.PixelFormat.Mono8
        # # self.cam.wait_til_frame_ready(20)  # wait for frame ready
        # frame, width, height, depth = self.cam.get_image_data()
        # frame = np.array(frame, dtype='float64')
        # # Check if below is giving the right dimensions out
        # # TODO: do this smarter, as I can just take every 3rd value instead of creating a reshaped
        # #       3D array and taking the first plane of that
        # frame = np.reshape(frame, (height, width, depth))[:, :, 0]
        # frame = np.transpose(frame)
        # return frame

    def setROI(self, hpos, vpos, hsize, vsize):
        hsize = max(hsize, 256)  # minimum ROI size
        vsize = max(vsize, 24)  # minimum ROI size
        pass

    def setPropertyValue(self, property_name, property_value):
        # Check if the property exists.
        if property_name == "gain":
            self.cam.device_property_map.set_value(
                                ic4.PropId.GAIN,
                                property_value)
        elif property_name == "exposure":
            self.cam.device_property_map.set_value(
                                ic4.PropId.EXPOSURE_TIME,
                                property_value)
        elif property_name == 'image_height':
            self.cam.device_property_map.set_value(
                                ic4.PropId.HEIGHT,
                                property_value)
        elif property_name == 'image_width':
            self.cam.device_property_map.set_value(
                                ic4.PropId.WIDTH,
                                property_value)
        elif property_name == 'video_format':
            if property_value == '8bit':
                self.cam.device_property_map.set_value(
                                ic4.PropId.PIXEL_FORMAT,
                                ic4.PixelFormat.Mono8)
            elif property_value == '16bit':
                self.cam.device_property_map.set_value(
                                ic4.PropId.PIXEL_FORMAT,
                                ic4.PixelFormat.Mono16)
            else:
                self.__logger.warning(f'Invalid Property value {property_value}')
            return False
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def getPropertyValue(self, property_name):
        # Check if the property exists.
        if property_name == "gain":
            property_value = self.cam.device_property_map.get_value_float(
                                ic4.PropId.GAIN)
        elif property_name == "exposure":
            property_value = self.cam.device_property_map.get_value_int(
                                ic4.PropId.EXPOSURE_TIME)
        elif property_name == "image_width":
            property_value = self.cam.device_property_map.get_value_int(
                                ic4.PropId.WIDTH)
        elif property_name == "image_height":
            property_value = self.cam.device_property_map.get_value_int(
                                ic4.PropId.HEIGHT)
        elif property_name == 'video_format':
            property_value = self.cam.device_property_map.get_value_int(
                                ic4.PropId.PIXEL_FORMAT)
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def openPropertiesGUI(self):
        ic4.Dialogs.grabber_device_properties(self.cam, 43)
        # self.cam.show_property_dialog()


# Copyright (C) 2020-2021 ImSwitch developers
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
