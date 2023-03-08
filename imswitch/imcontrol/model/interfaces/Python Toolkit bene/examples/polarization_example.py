"""
Polarization Example

This example shows how to work with the polarization processor module. It will open a camera and poll for an image,
but the focus will be on explaining how to process the image from the camera. At the end, 4 consecutive images should
pop up showing intensity data, azimuth data, degree of linear polarization (DoLP) data, and a Quad View.

"""

try:
    # if on Windows, use the provided setup script to add the DLLs folder to the PATH
    from windows_setup import configure_path
    configure_path()
except ImportError:
    configure_path = None

import numpy as np
from PIL import Image

from thorlabs_tsi_sdk.tl_camera import TLCameraSDK
from thorlabs_tsi_sdk.tl_camera_enums import SENSOR_TYPE
from thorlabs_tsi_sdk.tl_polarization_processor import PolarizationProcessorSDK

"""
    The PolarizationProcessorSDK and PolarizationProcessor objects can be used with context managers for automatic 
    clean up. This multi-context-manager 'with' statement opens both the camera sdk and the polarization sdk at 
    once. 
"""
with TLCameraSDK() as camera_sdk, PolarizationProcessorSDK() as polarization_sdk:
    available_cameras = camera_sdk.discover_available_cameras()
    if len(available_cameras) < 1:
        raise ValueError("no cameras detected")

    with camera_sdk.open_camera(available_cameras[0]) as camera:
        camera.frames_per_trigger_zero_for_unlimited = 0  # start camera in continuous mode
        camera.image_poll_timeout_ms = 2000  # 2 second timeout
        camera.arm(2)

        """
            In a real-world scenario, we want to save the image width and height before color processing so that we 
            do not have to query it from the camera each time it is needed, which would slow down the process. It is 
            safe to save these after arming since the image width and height cannot change while the camera is armed.
        """
        image_width = camera.image_width_pixels
        image_height = camera.image_height_pixels

        camera.issue_software_trigger()

        frame = camera.get_pending_frame_or_null()
        if frame is not None:
            print("frame received!")
        else:
            raise ValueError("No frame arrived within the timeout!")

        camera.disarm()

        if camera.camera_sensor_type is not SENSOR_TYPE.MONOCHROME_POLARIZED:
            raise ValueError("Polarization processing should only be done with polarized cameras")

        camera_polar_phase = camera.polar_phase
        camera_bit_depth = camera.bit_depth
        """
        We're scaling to 8-bits in this example so we can easily convert to PIL Image objects.
        """
        max_output_value = 255

        with polarization_sdk.create_polarization_processor() as polarization_processor:
            """
            Convert the raw sensor data to polarization image data. We will convert to each of the available outputs: 
            intensity, azimuth, and degree of linear polarization (DoLP).
            """
            output_intensity = polarization_processor.transform_to_intensity(camera_polar_phase,
                                                                             frame.image_buffer,
                                                                             0,  # origin x
                                                                             0,  # origin y
                                                                             image_width,
                                                                             image_height,
                                                                             camera_bit_depth,
                                                                             max_output_value)
            output_azimuth = polarization_processor.transform_to_azimuth(camera_polar_phase,
                                                                         frame.image_buffer,
                                                                         0,  # origin x
                                                                         0,  # origin y
                                                                         image_width,
                                                                         image_height,
                                                                         camera_bit_depth,
                                                                         max_output_value)
            output_dolp = polarization_processor.transform_to_dolp(camera_polar_phase,
                                                                   frame.image_buffer,
                                                                   0,  # origin x
                                                                   0,  # origin y
                                                                   image_width,
                                                                   image_height,
                                                                   camera_bit_depth,
                                                                   max_output_value)
            """
            Convert from 16-bit to 8-bit
            """
            output_intensity = output_intensity.astype(np.ubyte)
            output_azimuth = output_azimuth.astype(np.ubyte)
            output_dolp = output_dolp.astype(np.ubyte)
            """
            Reshape the 1D output arrays to be 2D arrays (image_width x image_height)
            """
            output_intensity = output_intensity.reshape(image_height, image_width)
            output_azimuth = output_azimuth.reshape(image_height, image_width)
            output_dolp = output_dolp.reshape(image_height, image_width)
            """
            Convert the polarization image data to PIL Image types
            """
            intensity_image = Image.fromarray(output_intensity)
            azimuth_image = Image.fromarray(output_azimuth)
            dolp_image = Image.fromarray(output_dolp)
            """
            We're going to display each of the images created using PIL's show() method. This tries to open the images 
            using your default image viewer, and may fail on some configurations.
            """
            intensity_image.show()
            azimuth_image.show()
            dolp_image.show()
            """
            Lastly, we'll construct a QuadView image that is useful for visualizing each polar rotation: 0, 45, 90, and 
            -45 degrees. The sensor on the polarized camera has a filter in front of it that is composed of 2x2 pixel 
            sections that look like the following pattern: 

            -------------
            | +45 | +90 |
            -------------
            | + 0 | -45 |
            -------------

            It is always 2x2, but the ordering of the rotations may differ depending on your camera model. The top left 
            rotation (the 'origin' rotation) is always equal to the camera_polar_phase that was queried earlier. We'll 
            use array splicing to extract each of the rotations and separate them visually. If you are familiar with 
            manipulating color image arrays, this is similar to pulling out the R, G, and B components of an RGB image.
            """
            unprocessed_image = frame.image_buffer.reshape(image_height, image_width)  # this is the raw image data
            unprocessed_image = unprocessed_image >> camera_bit_depth - 8  # scale to 8 bits for easier displaying
            output_quadview = np.zeros(shape=(image_height, image_width))  # initialize array for QuadView data
            # Top Left Quadrant =
            output_quadview[0:int(image_height / 2), 0:int(image_width / 2)] = \
                unprocessed_image[0::2, 0::2]  # (0,0): top left rotation == camera_polar_phase
            # Top Right Quadrant =
            output_quadview[0:int(image_height / 2), int(image_width / 2):image_width] = \
                unprocessed_image[0::2, 1::2]  # (0,1): top right rotation
            # Bottom Left Quadrant =
            output_quadview[int(image_height / 2):image_height, 0:int(image_width / 2)] = \
                unprocessed_image[1::2, 0::2]  # (1,0): bottom left rotation
            # Bottom Right Quadrant =
            output_quadview[int(image_height / 2):image_height, int(image_width / 2):image_width] = \
                unprocessed_image[1::2, 1::2]  # (1,1): bottom right rotation
            # Display QuadView
            quadview_image = Image.fromarray(output_quadview)
            quadview_image.show()

#  Because we are using the 'with' statement context-manager, disposal has been taken care of.

print("program completed")
