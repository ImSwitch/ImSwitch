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

    def local_init(self, px_format_value: str) -> None:
        """
        Initializes the camera device and sets various properties. This is
        important for the reinitialization due to the change of pixel format.

        Args:
            px_format_value (str): The value to set for the
                'pixel_format' property.

        Returns:
            None
        """
        if self.cam.is_device_open:
            reinit = True  # flag if pixel format needs to be set
            self.__logger.info('this is a RE-init')
            self.cam.device_close()
            print('reinit, is sink attached:', self.snapSink.is_attached)
        else:
            reinit = False
        self.cam.device_open(self.model)

        # query exposure_time internal unit from the camera
        self.exposureUnit = self.cam.device_property_map.find_float(
            ic4.PropId.EXPOSURE_TIME,
            ).unit

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
            self.setPropertyValue('pixel_format', px_format_value)
        # set auto gain off
        self.cam.device_property_map.set_value(
            ic4.PropId.GAIN_AUTO,
            False,
        )
        # set exposure time AUTO false
        self.cam.device_property_map.set_value(
            ic4.PropId.EXPOSURE_AUTO,
            False,
        )

    def start_live(self):
        """ Starts the live video stream from the camera.

        This method starts the live video stream from the camera.
        If the camera stream is already set, it calls the `acquisition_start`
        method to resume the acquisition. Otherwise, it sets up the
        stream using the `stream_setup` method and starts the acquisition.

        Note:
            The camera must be connected and initialized before calling
            this method.
        """
        self.__logger.debug('start live method called')
        # Defer acquisition means that, self.cam.start_acquisition
        # needs to be called
        if self.cam.is_streaming:
            self.cam.acquisition_start()
        else:
            self.cam.stream_setup(
                self.snapSink,
                setup_option=ic4.StreamSetupOption.ACQUISITION_START,
            )

    def stop_live(self):
        """
        Stops the live imaging.

        This method stops the live imaging by calling the `acquisition_stop`
        method of the camera object.

        Returns:
            None
        """
        self.__logger.debug('stop live method called')
        self.cam.acquisition_stop()  # stop imaging

    def grabFrame(self, frame_rate: float) -> np.ndarray:
        """
        Grabs a single frame from the camera. In case of 12-bit pixel format,
        the bits are shifted to the right by 4. The frame is rotated if
        the `rotate_frame` property is set to a value other than 'No'.

        Args:
            frame_rate (float): The desired frame rate in frames per second.

        Returns:
            np.ndarray: The grabbed frame as a NumPy array.
        """
        # timeout in ms linked to the frame rate, not exposure.
        image = self.snapSink.snap_single(int(np.ceil((3/frame_rate) * 1000)))
        frame = image.numpy_copy()[:, :, 0]

        # shift bits if necessary, works
        if self.pixel_format == '12bit':
            frame = frame >> 4

        # rotating frame, works, but not for saving snaps to h5
        if self.rotate_frame != 'No':
            frame = self.rotate(frame)
        return frame

    def rotate(self, arr: np.ndarray) -> np.ndarray:
        """
        Rotate the input array based on the specified rotation value.

        Parameters:
        arr (numpy.ndarray): The input array to be rotated.

        Returns:
        numpy.ndarray: The rotated array.

        """
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

    def setPropertyValue(self, property_name: str, property_value):
        """
        Sets the value of a camera property. Valid properties are 'gain',
        'exposure', 'image_height', 'image_width', 'pixel_format', and
        'rotate_frame'.

        Args:
            property_name (str): The name of the property to set.
            property_value: The value to set for the property.

        Returns:
            The value that was set for the property.
        """
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
            self.exposure = ExposureTimeToUs.convert(
                property_value,
                self.exposureUnit,
                )
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

    def getPropertyValue(self, property_name: str):
        """
        Get the value of a camera property. Valid properties are 'gain',
        'exposure', 'frame_rate', 'image_height', 'image_width',
        'pixel_format', and 'rotate_frame'.

        Args:
            property_name (str): The name of the property to retrieve.

        Returns:
            The value of the specified property.
        """
        # Check if the property exists.
        if property_name == "gain":
            property_value = self.cam.device_property_map.get_value_float(
                                ic4.PropId.GAIN)
        elif property_name == "exposure":
            property_value = ExposureTimeToUs.convert(
                                self.cam.device_property_map.get_value_float(
                                    ic4.PropId.EXPOSURE_TIME),
                                self.exposureUnit,
                                )
        # get frame rate, this does not have setter
        elif property_name == 'frame_rate':
            property_value = self.cam.device_property_map.get_value_float(
                                ic4.PropId.ACQUISITION_FRAME_RATE)
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
        """ Opens ic4 device settings dialog. """
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
