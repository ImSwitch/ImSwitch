"""
Color Example

This example shows how to work with the mono to color processor module. It will open a camera and poll for an image,
but the focus will be on explaining how to color the image from the camera.

"""

try:
    # if on Windows, use the provided setup script to add the DLLs folder to the PATH
    from windows_setup import configure_path
    configure_path()
except ImportError:
    configure_path = None

from thorlabs_tsi_sdk.tl_camera import TLCameraSDK
from thorlabs_tsi_sdk.tl_mono_to_color_processor import MonoToColorProcessorSDK
from thorlabs_tsi_sdk.tl_mono_to_color_enums import COLOR_SPACE
from thorlabs_tsi_sdk.tl_color_enums import FORMAT

"""
    The MonoToColorProcessorSDK and MonoToColorProcessor objects can be used with context managers for automatic 
    clean up. This multi-context-manager 'with' statement opens both the camera sdk and the mono to color sdk at 
    once. 
"""
with TLCameraSDK() as camera_sdk, MonoToColorProcessorSDK() as mono_to_color_sdk:
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

        """
            When creating a mono to color processor, we want to initialize it using parameters from the camera.
        """
        with mono_to_color_sdk.create_mono_to_color_processor(
            camera.camera_sensor_type,
            camera.color_filter_array_phase,
            camera.get_color_correction_matrix(),
            camera.get_default_white_balance_matrix(),
            camera.bit_depth
        ) as mono_to_color_processor:
            """
                Once it is created, we can change the color space and output format properties. sRGB is the default 
                color space, and will usually give the best looking image. The output format will determine how the 
                transform image data will be structured.
            """
            mono_to_color_processor.color_space = COLOR_SPACE.SRGB  # sRGB color space
            mono_to_color_processor.output_format = FORMAT.RGB_PIXEL  # data is returned as sequential RGB values
            """
                We can also adjust the Red, Green, and Blue gains. These values amplify the intensity of their 
                corresponding colors in the transformed image. For example, if Blue and Green gains are set to 0 
                and the Red gain is 10, the resulting image will look entirely Red. The most common use case for these 
                properties will be for white balancing. By default they are set to model-specific values that gives 
                reasonably good white balance in typical lighting.
            """
            print("Red Gain = {red_gain}\nGreen Gain = {green_gain}\nBlue Gain = {blue_gain}\n".format(
                red_gain=mono_to_color_processor.red_gain,
                green_gain=mono_to_color_processor.green_gain,
                blue_gain=mono_to_color_processor.blue_gain
            ))
            """
                When we have all the settings we want for the mono to color processor, we call one of the transform_to 
                functions to get a color image. 
            """
            # this will give us a resulting image with 3 channels (RGB) and 16 bits per channel, resulting in 48 bpp
            color_image_48_bpp = mono_to_color_processor.transform_to_48(frame.image_buffer, image_width, image_height)

            # this will give us a resulting image with 4 channels (RGBA) and 8 bits per channel, resulting in 32 bpp
            color_image_32_bpp = mono_to_color_processor.transform_to_32(frame.image_buffer, image_width, image_height)

            # this will give us a resulting image with 3 channels (RGB) and 8 bits per channel, resulting in 24 bpp
            color_image_24_bpp = mono_to_color_processor.transform_to_24(frame.image_buffer, image_width, image_height)

            # from here, perform any actions you need to using the color image

#  Because we are using the 'with' statement context-manager, disposal has been taken care of.

print("program completed")
