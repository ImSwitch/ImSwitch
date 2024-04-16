import numpy as np
import imagingcontrol4 as ic4
from imswitch.imcontrol.model.managers.detectors.DetectorManager import (
    ExposureTimeToUs
)

from imswitch.imcommon.model import initLogger


class CameraTIS4:
    def __init__(self, cameraNo, pixel_format):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)
        ic4.Library.init(api_log_level=5, log_targets=1)
        self.pixel_formats = {'8bit': ic4.PixelFormat.Mono8,
                              '12bit': ic4.PixelFormat.Mono16,
                              '16bit': ic4.PixelFormat.Mono16}
        ic4.PropertyDialogFlags.ALLOW_STREAM_RESTART
        cam_names = ic4.DeviceEnum.devices()
        # this is not json compatible
        self.model = cam_names[cameraNo]
        self.name = cam_names[cameraNo].model_name
        self.cam = ic4.Grabber()
        self.buffers = ic4.SnapSink.AllocationStrategy(
                            num_buffers_alloc_on_connect=1,
                            num_buffers_allocation_threshold=0,
                            num_buffers_free_threshold=3,
                            num_buffers_max=2)
        self.snapSink = ic4.SnapSink(strategy=self.buffers)

        self.local_init(pixel_format)

    def local_init(self, value):
        if self.cam.is_device_open:
            reinit = True  # flag if pixel format needs to be set
            self.__logger.info('this is a RE-init')
            self.cam.device_close()
            print('reinit, is sink attached:', self.snapSink.is_attached)
        else:
            reinit = False
        self.cam.device_open(self.model)

        # query exposure_time internal unit from the camera
        self.exposureUnit = self.cam.device_property_map.find_float(ic4.PropId.EXPOSURE_TIME).unit

        # convert exposure time to us using the ExposureTimeToUs class
        self.exposure = ExposureTimeToUs.convert(
                                self.cam.device_property_map.get_value_float(
                                        ic4.PropId.EXPOSURE_TIME,
                                        ),
                                self.exposureUnit,
                                )
        print('exposure in localInit:', self.exposure)

        # set pixel format, not needed because it gets set in the manager
        if reinit:
            self.setPropertyValue('pixel_format', value)
        # set auto gain off
        self.cam.device_property_map.set_value(
            ic4.PropId.GAIN_AUTO, False
        )
        # set exposure time AUTO false
        self.cam.device_property_map.set_value(
            ic4.PropId.EXPOSURE_AUTO, False
        )

    def start_live(self):
        self.__logger.debug('start live method called')
        # Defer acquisition means that, self.cam.start_acquisition needs to be called
        if self.cam.is_streaming:
            self.cam.acquisition_start()
        else:
            self.cam.stream_setup(
                self.snapSink,
                setup_option=ic4.StreamSetupOption.ACQUISITION_START,
            )

    def stop_live(self):
        self.__logger.debug('stop live method called')
        self.cam.acquisition_stop()  # stop imaging

    def grabFrame(self):
        # self.exposure is always us, but the camera needs ms -> factor 1000
        # the constant 30 is found experimentally for short exposure times
        image = self.snapSink.snap_single(np.ceil(30 + 1.2 * self.exposure/1000).astype(int))
        frame = image.numpy_copy()[:, :, 0]

        # shift bits if necessary, works
        if self.pixel_format == '12bit':
            frame = frame >> 4

        # rotating frame, works, but not for saving snaps to h5
        if self.rotate_frame != 'No':
            frame = self.rotate(frame)
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
        "not implemented"
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
            # GUI sends exposure in us, no conversion needed
            self.cam.device_property_map.set_value(
                ic4.PropId.EXPOSURE_TIME,
                ExposureTimeToUs.convert(property_value, self.exposureUnit),
                )
            self.exposure = ExposureTimeToUs.convert(property_value, self.exposureUnit)
        elif property_name == 'image_height':
            self.cam.device_property_map.set_value(
                                ic4.PropId.HEIGHT,
                                property_value)
        elif property_name == 'image_width':
            self.cam.device_property_map.set_value(
                                ic4.PropId.WIDTH,
                                property_value)
        elif property_name == 'pixel_format':
            self.cam.device_property_map.set_value(
                            ic4.PropId.PIXEL_FORMAT,
                            self.pixel_formats[property_value])
            self.pixel_format = property_value
            self.__logger.debug(f'pixel format set: {self.pixel_format}')
        elif property_name == 'rotate_frame':
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
            # property_value = int(self.cam.device_property_map.get_value_float(
            #                     ic4.PropId.EXPOSURE_TIME) * self.exposure_conv_factor)
            property_value = ExposureTimeToUs.convert(
                                self.cam.device_property_map.get_value_float(
                                    ic4.PropId.EXPOSURE_TIME),
                                self.exposureUnit,
                                )
        elif property_name == "image_width":
            property_value = self.cam.device_property_map.get_value_int(
                                ic4.PropId.WIDTH)
        elif property_name == "image_height":
            property_value = self.cam.device_property_map.get_value_int(
                                ic4.PropId.HEIGHT)
        elif property_name == 'pixel_format':
            return self.pixel_format
        elif property_name == 'rotate_frame':
            return self.rotate_frame
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
