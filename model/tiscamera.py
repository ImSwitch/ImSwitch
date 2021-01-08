# -*- coding: utf-8 -*-
"""
Created on Thu Jan 07 14:11:00 2021

@author: jonatanalvelid
"""

from pyicic import IC_ImagingControl
import mockers


class CameraTIS(mockers.MockHamamatsu):
    def __init__(self, cameraNo, exposure, gain, brightness):
        super().__init__()

        self.properties['subarray_vpos'] = 0
        self.properties['subarray_hpos'] = 0
        self.properties['exposure_time'] = 0.03
        self.properties['subarray_vsize'] = 1024
        self.properties['subarray_hsize'] = 1280

        ic_ic = IC_ImagingControl.IC_ImagingControl()
        ic_ic.init_library()
        cam_names = ic_ic.get_unique_device_names()
        print(cam_names)
        self.cam = ic_ic.get_device(cam_names[cameraNo])
        # print(self.cam.list_property_names())

        self.cam.open()

        self.cam.colorenable = 0
        self.cam.gain.auto = False
        self.cam.exposure.auto = False
        if cameraNo == 1:
            self.cam.exposure = exposure  # exposure in ms
            self.cam.gain = gain  # gain in dB
            self.cam.brightness = brightness  # brightness in arbitrary units
            self.properties['subarray_vsize'] = 2048
            self.properties['subarray_hsize'] = 2448
        self.cam.enable_continuous_mode(True)  # image in continuous mode
        self.cam.start_live(show_display=False)  # start imaging
        # self.cam.enable_trigger(True)  # camera will wait for trigger
        # self.cam.send_trigger()
        if not self.cam.callback_registered:
            self.cam.register_frame_ready_callback()  # needed to wait for frame ready callback

    def grab_image(self):
        self.cam.reset_frame_ready()  # reset frame ready flag
        self.cam.send_trigger()
        # self.cam.wait_til_frame_ready(0)  # wait for frame ready due to trigger
        frame = self.cam.get_image_data()
        # y0 = self.properties['subarray_vpos']
        # x0 = self.properties['subarray_hpos']
        # y_size = self.properties['subarray_vsize']
        # x_size = self.properties['subarray_hsize']
        # now = time.time()
        # Old way, averaging the RGB image to a grayscale. Very slow for the big camera (2480x2048).
        #frame = np.average(frame, 2)
#        print(type(frame))
#        print(frame)
        # New way, just take the R-component, this should anyway contain most information in both cameras. Change this if we want to look at another color, like GFP!
        frame = np.array(frame[0], dtype='float64')
        # Check if below is giving the right dimensions out
        frame = np.reshape(frame,(self.properties['subarray_vsize'],self.properties['subarray_hsize'],3))[:,:,0]
        # print(frame)
        # now = time.time()
        # print("Avg RGB took: ", now-then, " seconds")
        # return frame_cropped
        # print(x_size)
        # print(y_size)
        # frame_cropped = np.average(frame[0:0+x_size, 0:0+y_size], 2)
        # return frame_cropped
        return frame

    def setPropertyValue(self, property_name, property_value):
        # Check if the property exists.
        if not (property_name in self.properties):
            print('Property', property_name, 'does not exist')
            return False

        # if property_name == 'exposure_time':

        # If the value is text, figure out what the
        # corresponding numerical property value is.

        self.properties[property_name] = property_value
        return property_value

    def getPropertyValue(self, property_name):

        # Check if the property exists.
        if not (property_name in self.properties):
            print(" unknown property name:", property_name)
            return False
        prop_value = self.properties[property_name]

        return prop_value

    def show_dialog(self):
        self.cam.show_property_dialog()
