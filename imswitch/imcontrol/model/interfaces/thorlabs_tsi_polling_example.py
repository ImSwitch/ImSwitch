"""
Tiff Writing Example - tifffile

This example shows how to use Thorlabs TSI Cameras to write images to a disk using the tifffile library,
see https://pypi.org/project/tifffile/ for more information.

There are many TIFF-writing libraries for python, this example is meant to show how to integrate with tifffile.
The process should generally be the same with most TIFF-writing libraries, but results may vary.

In this example 10 images are going to be taken and saved to a single multipage TIFF file. The program will detect
if the camera has a color filter and will perform color processing if so.

One thing to note is that this program will save TIFFs in the camera's bit depth. Some image viewers may not recognize
this and will show the images as being much darker than expected. If you are experiencing dark images, we recommend
trying out various image viewers designed for scientific imaging such as ThorCam or ImageJ.

"""

import os
import sys
import pathlib


def configure_path():
    absolute_path_to_dlls = str(pathlib.Path(__file__).resolve().parent)+"\\thorlabs_tsi_sdk\\dll\\"
    os.environ['PATH'] = absolute_path_to_dlls + os.pathsep + os.environ['PATH']

    try:
        # Python 3.8 introduces a new method to specify dll directory
        os.add_dll_directory(absolute_path_to_dlls)
    except AttributeError:
        pass

configure_path()

import os
import tifffile

from thorlabs_tsi_sdk.tl_camera import TLCameraSDK
from thorlabs_tsi_sdk.tl_mono_to_color_processor import MonoToColorProcessorSDK
from thorlabs_tsi_sdk.tl_camera_enums import SENSOR_TYPE

NUMBER_OF_IMAGES = 10  # Number of TIFF images to be saved
OUTPUT_DIRECTORY = os.path.abspath(r'.')  # Directory the TIFFs will be saved to
FILENAME = 'image.tif'  # The filename of the TIFF

TAG_BITDEPTH = 32768
TAG_EXPOSURE = 32769

# delete image if it exists
if os.path.exists(OUTPUT_DIRECTORY + os.sep + FILENAME):
    os.remove(OUTPUT_DIRECTORY + os.sep + FILENAME)

with TLCameraSDK() as sdk:
    cameras = sdk.discover_available_cameras()
    if len(cameras) == 0:
        print("Error: no cameras detected!")

    with sdk.open_camera(cameras[0]) as camera:
        #  setup the camera for continuous acquisition
        camera.frames_per_trigger_zero_for_unlimited = 0
        camera.image_poll_timeout_ms = 2000  # 2 second timeout
        camera.arm(2)

        # save these values to place in our custom TIFF tags later
        bit_depth = camera.bit_depth
        exposure = camera.exposure_time_us

        # need to save the image width and height for color processing
        image_width = camera.image_width_pixels
        image_height = camera.image_height_pixels

        # initialize a mono to color processor if this is a color camera
        is_color_camera = (camera.camera_sensor_type == SENSOR_TYPE.BAYER)
        mono_to_color_sdk = None
        mono_to_color_processor = None
        if is_color_camera:
            mono_to_color_sdk = MonoToColorProcessorSDK()
            mono_to_color_processor = mono_to_color_sdk.create_mono_to_color_processor(
                camera.camera_sensor_type,
                camera.color_filter_array_phase,
                camera.get_color_correction_matrix(),
                camera.get_default_white_balance_matrix(),
                camera.bit_depth
            )

        # begin acquisition
        camera.issue_software_trigger()
        frames_counted = 0
        while frames_counted < NUMBER_OF_IMAGES:
            frame = camera.get_pending_frame_or_null()
            if frame is None:
                raise TimeoutError("Timeout was reached while polling for a frame, program will now exit")

            frames_counted += 1

            image_data = frame.image_buffer
            if is_color_camera:
                # transform the raw image data into RGB color data
                image_data = mono_to_color_processor.transform_to_48(image_data, image_width, image_height)
                image_data = image_data.reshape(image_height, image_width, 3)

            with tifffile.TiffWriter(OUTPUT_DIRECTORY + os.sep + FILENAME, append=True) as tiff:
                """
                    Setting append=True here means that calling tiff.save will add the image as a page to a multipage TIFF. 
                """
                tiff.save(data=image_data  # np.ushort image data array from the camera
                          )
                """
                    If compress > 0 tifffile will compress the image using zlib - deflate compression.
                    Instead of an int a str can be supplied to specify a different compression algorithm;
                        e.g. compress = 'lzma'
                    View the tifffile source or online to see what is supported.
                """
                """
                    The extratags parameter allows the user to specify additional tags. Programs will typically ignore 
                    any tags from 32768 onward, which is where the bit depth and exposure have been placed. The 
                    syntax for extra tags is (tag_code, data_type_of_value, number_of_values, value, write_once).
                    View the tifffile source for more information.
                """
        camera.disarm()

        # we did not use context manager for color processor, so manually dispose of it
        if is_color_camera:
            try:
                mono_to_color_processor.dispose()
            except Exception as exception:
                print("Unable to dispose mono to color processor: " + str(exception))
            try:
                mono_to_color_sdk.dispose()
            except Exception as exception:
                print("Unable to dispose mono to color sdk: " + str(exception))

"""
Reading tiffs - to test that the tags from before worked, we're going to read back the tags on the first page. 
Note that custom TIFF tags are not going to be picked up by normal TIFF viewers, but can be read programmatically 
if the tag code is known.
"""
# open file

with tifffile.TiffFile(OUTPUT_DIRECTORY + os.sep + FILENAME) as tiff_read:
    if len(tiff_read.pages) < 1:
        raise ValueError("No pages were found in multipage TIFF")
    page_one = tiff_read.pages[0]
    print("First Image: Bit Depth = {} bpp, Exposure Time = {} ms".format(page_one.tags[str(TAG_BITDEPTH)].value,
                                                                          page_one.tags[str(TAG_EXPOSURE)].value/1000))
