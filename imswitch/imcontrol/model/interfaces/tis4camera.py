import numpy as np

from imswitch.imcommon.model import initLogger
import imagingcontrol4 as ic4
import pdb
import time


class CameraTIS4:
    def __init__(self, cameraNo, pixel_format):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)
        ic4.Library.init(api_log_level=4, log_targets=1)
        self.pixel_formats = {'8bit': ic4.PixelFormat.Mono8,
                              '12bit': ic4.PixelFormat.Mono16,
                              '16bit': ic4.PixelFormat.Mono16}
        self.rotate_frame = 'No'
        ic4.PropertyDialogFlags.ALLOW_STREAM_RESTART
        cam_names = ic4.DeviceEnum.devices()
        self.model = cam_names[cameraNo]
        self.cam = ic4.Grabber()
        self.sink = ic4.SnapSink()

        self.local_init(pixel_format)

    def local_init(self, value):
        try:
            print('Device open', self.cam.is_device_open)
            self.cam.stream_stop()
            self.cam.device_close()
            self.__logger.info('this is a RE-init')
        except:
            self.__logger.info('this is an init')
        self.cam.device_open(self.model)

        self.setPropertyValue('video format', value)
        # Defer acquisition means that, self.cam.start_acquisition needs to be called
        self.cam.stream_setup(self.sink,
                              setup_option=ic4.StreamSetupOption.DEFER_ACQUISITION_START,
                              )
        print('grabber', self.cam, id(self.cam))
        print('SINK', self.cam.sink, id(self.cam.sink))
        # set auto gain off
        self.cam.device_property_map.set_value(
            ic4.PropId.GAIN_AUTO, False
        )

    def start_live(self):
        self.cam.acquisition_start()  # start imaging

    def stop_live(self):
        self.cam.acquisition_stop()  # stop imaging

    def grabFrame(self):
        image = self.sink.snap_single(10000)
        frame = image.numpy_wrap()[:, :, 0]

        # shift bits if necessary, works
        if self.video_format == '12bit':
            print('before shift', np.amin(frame), np.amax(frame))
            frame = frame >> 4
            print('after shift', np.amin(frame), np.amax(frame))
        else:
            print('no shift', np.amin(frame), np.amax(frame))

        # rotating frame, works, but not for saving snaps, because of mismatched
        # dimension, but that should be easy to fix.
        if self.rotate_frame != 'No':
            frame = self.rotate(frame)
        self.__logger.info(f'image format: {frame.dtype, frame.shape}')
        self.__logger.info(self.cam.device_property_map.get_value_float(ic4.PropId.EXPOSURE_TIME))
        return frame

    def rotate(self, arr):
        if self.rotate_frame == '90':
            return np.rot90(arr, k=1)
        elif self.rotate_frame == '180':
            return np.rot90(arr, k=2)
        elif self.rotate_frame == '270':
            return np.rot90(arr, k=3)
        else:
            return arr

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
        elif property_name == 'video format':
            self.cam.device_property_map.set_value(
                            ic4.PropId.PIXEL_FORMAT,
                            self.pixel_formats[property_value])
            self.video_format = property_value
            self.__logger.info(f'set format: {self.cam.device_property_map.get_value_int(ic4.PropId.PIXEL_FORMAT)}')
            # return self.video_format
        elif property_name == 'rotate frame':
            self.rotate_frame = property_value
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
            property_value = self.cam.device_property_map.get_value_float(
                                ic4.PropId.EXPOSURE_TIME)
        elif property_name == "image_width":
            property_value = self.cam.device_property_map.get_value_int(
                                ic4.PropId.WIDTH)
        elif property_name == "image_height":
            property_value = self.cam.device_property_map.get_value_int(
                                ic4.PropId.HEIGHT)
        elif property_name == 'video format':
            return self.video_format
        elif property_name == 'rotate frame':
            property_value = self.rotate_frame
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def openPropertiesGUI(self):
        ic4.Dialogs.grabber_device_properties(self.cam, 43)


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
