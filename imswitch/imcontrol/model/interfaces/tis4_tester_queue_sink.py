import imagingcontrol4 as ic4
import numpy as np
import time
import matplotlib.pyplot as plt
import cv2
import sys

ic4.Library.init()
print(ic4.DeviceEnum.devices())

# Create a Grabber object
grabber = ic4.Grabber()

# Open the first available video capture device
first_device_info = ic4.DeviceEnum.devices()[0]
grabber.device_open(first_device_info)

# Configure the device to output images in the Mono8 pixel format
grabber.device_property_map.set_value(ic4.PropId.PIXEL_FORMAT,
                                      ic4.PixelFormat.Mono8)

sink = ic4.QueueSink()

# Setup data stream from the video capture device to the sink and start image acquisition.

# Set the resolution to 640x480
grabber.device_property_map.set_value(ic4.PropId.WIDTH, 2048)
grabber.device_property_map.set_value(ic4.PropId.HEIGHT, 1536)
for i in range(5):
    try:
        grabber.stream_setup(sink,
                     setup_option=1)#ic4.StreamSetupOption.DEFER_ACQUISITION_START)
        # Grab a single image out of the data stream.
        grabber.acquisition_start()
        image = sink.snap_single(4000)
        time.sleep(.3)
        # print(dir(image))
        arr = image.numpy_wrap()
        print(np.amin(arr), np.amax(arr), arr.shape)
        print(ic4.PixelFormat.Mono8)
        print(arr.dtype)
        print(image.image_type.pixel_format == 17301505)
        print(image.image_type.pixel_format)
        

        arr2 = cv2.flip(arr >> 4, 0)
        plt.subplot(131)
        plt.imshow(np.transpose(arr[:, :, 0]))
        plt.colorbar()

        plt.subplot(132)
        plt.imshow(np.flip(np.transpose(arr[:, :, 0] >> 4), 1))
        plt.colorbar()

        plt.subplot(133)
        plt.imshow(np.rot90(arr[:, :, 0], k=-1))
        plt.show()

        # Print image information.
        print(f"Received an image. ImageType: {image.image_type}")

        # Save the image.
        image.save_as_bmp("test.bmp")

    except ic4.IC4Exception as ex:
        print(ex.message)

    # Stop the data stream.
    grabber.stream_stop()

try:
    grabber.stream_setup(sink,
                     setup_option=1)
    # Grab a single image out of the data stream.
    grabber.acquisition_start()
    image = sink.snap_single(4000)
    time.sleep(.3)
    # print(dir(image))
    arr = image.numpy_wrap()
    print(np.amin(arr), np.amax(arr), arr.shape)
    print(ic4.PixelFormat.Mono8)
    print(arr.dtype)
    print(image.image_type.pixel_format == 17301505)
    print(image.image_type.pixel_format)

except ic4.IC4Exception as ex:
    print(ex.message)


