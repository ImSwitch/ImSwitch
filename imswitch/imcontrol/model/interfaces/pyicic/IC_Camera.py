#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from builtins import object
from ctypes import *
import time

from .IC_GrabberDLL import IC_GrabberDLL
from .IC_Exception import IC_Exception
from .IC_Property import IC_Property
from . import IC_Structures as structs


GrabberHandlePtr = POINTER(structs.GrabberHandle)

# "typedefs"
IMG_FILETYPE = ['FILETYPE_BMP',
                'FILETYPE_JPG']
COLOR_FORMAT = ['Y800',
                'RGB24',
                'RGB32',
                'UYVY',
                'Y16',
                'NONE']

# c function type for frame callback
# outside of class so it can be called by unbound function
C_FRAME_READY_CALLBACK = CFUNCTYPE(None, GrabberHandlePtr, POINTER(c_ubyte), c_ulong, c_void_p)

class IC_Camera:
    
    @property
    def callback_registered(self):
        return self._callback_registered
  
    def __init__(self, unique_device_name):
        
        self._unique_device_name = unique_device_name
        
        self._handle = IC_GrabberDLL.create_grabber()
        if not self._handle:
            raise IC_Exception(todo)
        
        self._callback_registered = False
        self._frame = {'num'    :   -1,
                       'ready'  :   False}

    def __getattr__(self, attr):
    
        if attr in IC_Property.get_all_property_names():
            return IC_Property(self._handle, attr)
        else:
            raise AttributeError
    
    # not needed if we use props directly
    #def __setattr__(self, attr, val):
    #    
    #    if attr.startswith('_'):
    #        super(IC_Camera, self).__setattr__(attr, val)
    #
    #    # if it's an actual device property
    #    elif attr in self.get_all_property_names():
    #        IC_Property(self._handle, attr).value = val
    #
    #    # otherwise just set the attribute value as normal
    #    else:
    #        super(IC_Camera, self).__setattr__(attr, val)
        
    def open(self):
        """
        Open the camera device, required for most functions.
        """
        err = IC_GrabberDLL.open_device_by_unique_name(self._handle,
                                                       self._unique_device_name.encode('ascii'))
        if err != 1:
            raise IC_Exception(err)
    
    def close(self):
        """
        Close the camera device.
        """
        IC_GrabberDLL.close_device(self._handle)
 
 
        ## don't use, returns wrong number..?
        #def get_serial_number(self):
        #    
        #    #serial = create_string_buffer(20)
        #    serial = (c_char * 20)()
        #    
        #    IC_GrabberDLL.get_serial_number(self._handle,
        #                                    serial)
        #
        #    return serial.value
    
    
    def is_open(self):
        """
        Check if the camera device is currently open.
        
        :returns: boolean -- True if camera is open.
        """
        return bool(IC_GrabberDLL.is_dev_valid(self._handle))
    
    def show_property_dialog(self):
        """
        Show property dialog for device.
        """
        err = IC_GrabberDLL.show_property_dialog(self._handle)
        if err != 1:
            raise IC_Exception(err)
    
    def list_property_names(self):
        return IC_Property.get_all_property_names()
    
    # use props instead, e.g. cam.gain.range
    #def get_property_range(self, property_name):
    #    return IC_Property(self._handle, property_name).range
    #
    #def is_property_available(self, property_name):
    #    return IC_Property(self._handle, property_name).is_available
    #
    #def is_property_auto_available(self, property_name):
    #    return IC_Property(self._handle, property_name).is_auto_available
    #
    #def get_property_type(self, property_name):
    #    return IC_Property(self._handle, property_name).type
    
    def reset_properties(self):
        """
        Resets all properties to their default values. If a property has
        automation, the automatic will be enabled.
        If the device supports external trigger, the external trigger will
        be disabled.
        """
        return IC_GrabberDLL.reset_properties(self._handle)
        
    def save_device_state_to_file(self, filename):
        """
        Save the state of a video capture device to a file.
        
        :param filename: string -- name of the file where to save to.
        """
        err = IC_GrabberDLL.save_device_state_to_file(self._handle,
                                                      c_char_p(filename.encode('ascii')))
        if err != 1:
            raise IC_Exception(err)
            
    def load_device_state_from_file(self, filename):
        """
        Load a device settings file. On success the device is opened automatically.
        
        :param filename: string -- name of the file where to load from.
        """
        self._handle = IC_GrabberDLL.load_device_state_from_file(self._handle,
                                                                 c_char_p(filename.encode('ascii')))
        if not self._handle:
            raise IC_Exception(todo)
        
    def list_video_formats(self):
        """
        :returns: list -- available video formats.
        """
        return [self.get_video_format(idx) for idx in range(self.get_video_format_count())]
    
    def get_video_norm_count(self):
        """
        Get the number of the available video norm formats for the current device. 
        A video capture device must have been opened before this call.
        
        :returns: int -- number of available video norms.
        """
        vn_count = IC_GrabberDLL.get_video_norm_count(self._handle)
        if vn_count < 0:
            raise IC_Exception(vn_count)
        return vn_count
    
    def get_video_norm(self, norm_index):
        """
        Get a string representation of the video norm specified by norm_index. 
        norm_index must be between 0 and get_video_norm_count().
        
        :returns: string -- name of video norm of specified index.
        """
        # DLL says need to call this first for it to work
        num_vns = self.get_video_norm_count()
        if norm_index >= num_vns:
            raise IC_Exception(-102)
        vn = IC_GrabberDLL.get_video_norm(self._handle, c_int(norm_index))
        if vn is None:
            raise IC_Exception(-104)
        return vn
    
    def get_video_format_count(self):
        """
        Get the number of the available video formats for the current device. 
        A video capture device must have been opened before this call.
        
        :returns: int -- number of available video formats.
        """
        vf_count = IC_GrabberDLL.get_video_format_count(self._handle)
        if vf_count < 0:
            raise IC_Exception(vf_count)
        return vf_count
    
    def get_video_format(self, format_index):
        """
        Get a string representation of the video format specified by format_index. 
        format_index must be between 0 and get_video_format_count().
        """
        # DLL says need to call this first for it to work
        num_vfs = self.get_video_format_count()
        if format_index >= num_vfs:
            raise IC_Exception(-103)
        vf = IC_GrabberDLL.get_video_format(self._handle, c_int(format_index))
        if vf is None:
            raise IC_Exception(-105)
        return vf.decode('ascii')
    
    def set_video_format(self, video_format):
        """
        Set a video format for the device. Must be supported.
        
        :param video_format: string -- video format to use.
        """
        err = IC_GrabberDLL.set_video_format(self._handle, c_char_p(video_format.encode('ascii')))
        if err != 1:
            raise IC_Exception(err)

    def set_video_norm(self, video_norm):
        """
        Sets video norm format, whatver that means.
        
        :param video_norm: string -- video norm to use.
        """
        err = IC_GrabberDLL.set_video_norm(self._handle, c_char_p(video_norm.encode('ascii')))
        if err != 1:
            raise IC_Exception(err)
    
    def get_video_format_width(self):
        """
        """
        return IC_GrabberDLL.get_video_format_width(self._handle)
        
    def get_video_format_height(self):
        """
        """
        return IC_GrabberDLL.get_video_format_height(self._handle)
        
    def get_format(self):
        """
        """
        return IC_GrabberDLL.get_format(self._handle)
    
    def set_format(self, color_format):
        """
        """
        err = IC_GrabberDLL.set_format(self._handle, c_int(color_format))
        if err != 1:
            raise IC_Exception(err)
            
    def is_triggerable(self):
        """
        """
        return bool(IC_GrabberDLL.is_trigger_available(self._handle))
        
    def get_frame_rate(self):
        """
        """
        return IC_GrabberDLL.get_frame_rate(self._handle)
    
    def set_frame_rate(self, frame_rate):
        """
        """
        err = IC_GrabberDLL.set_frame_rate(self._handle, c_float(frame_rate))
        if err != 1:
            raise IC_Exception(err)

    def focus_one_push(self):
        """
        Performs the one push for focus.
        :return: None
        """
        err = IC_GrabberDLL.focus_one_push(self._handle)
        if err != 1:
            raise IC_Exception(err)

    def enable_trigger(self, enable):
        """
        Enable or disable camera triggering.

        :param enable: boolean -- True to enable the trigger, False to disable.
        """
        err = IC_GrabberDLL.enable_trigger(self._handle, c_int(int(enable)))
        if err != 1:
            #raise IC_Exception(err)
            pass # todo, always raises false error for some reason...?
    
    def enable_continuous_mode(self, enable):
        """
        Enable or disable continuous mode.
        
        :param enable: boolean -- True to enable continuous mode, False to disable.
        """
        actual = not enable
        #print actual, enable, c_int(int(actual))
        err = IC_GrabberDLL.set_continuous_mode(self._handle, c_int(int(actual)))
        if err != 1:
            #raise IC_Exception(err)
            pass # todo, always raises false error for some reason...?
            
    def get_available_frame_filter_count(self):
        """
        Query number of avaialable frame filters
        """
        return IC_GrabberDLL.get_available_frame_filter_count()
        
    def get_available_frame_filters(self, number_of_filters):
        # TODO: Didn't manage to implement this function as of yet.
        # It requires a pointer to an array of pointers to arrays of chars.
        pass
        
    def create_frame_filter(self, name):
        frame_filter_handle = structs.FrameFilterHandle()

        err = IC_GrabberDLL.create_frame_filter(c_char_p(name.encode('ascii')), byref(frame_filter_handle))
        if err != 1:
            raise IC_Exception(err)
            
        return frame_filter_handle
        
    def add_frame_filter_to_device(self, frame_filter_handle):
        err = IC_GrabberDLL.add_frame_filter_to_device(self._handle, frame_filter_handle)
        if err != 1:
            raise IC_Exception(err)
            
    def frame_filter_get_parameter(self, frame_filter_handle, parameter_name):
        data = c_int()
        
        err = IC_GrabberDLL.frame_filter_get_parameter(frame_filter_handle, parameter_name.encode('ascii'), byref(data))
        if err != 1:
            raise IC_Exception(err)
            
        return data
            
    def frame_filter_set_parameter(self, frame_filter_handle, parameter_name, data):
        if type(data) is int:
            err = IC_GrabberDLL.frame_filter_set_parameter_int(frame_filter_handle,
                                                               c_char_p(parameter_name.encode('ascii')),
                                                               c_int(data))
        else:
            IC_Exception('Unknown set parameter type')
            
        if err != 1:
            raise IC_Exception(err)

    def send_trigger(self):
        """
        Send a software trigger to fire the device when in triggered mode.
        """
        err = IC_GrabberDLL.software_trigger(self._handle)
        if err != 1:
            raise IC_Exception(err)
        
    def prepare_live(self, show_display=False):
        """
        Prepare the device for live video.
        """
        err = IC_GrabberDLL.prepare_live(self._handle, c_int(int(show_display)))
        if err != 1:
            raise IC_Exception(err)
            
    def start_live(self, show_display=False):
        """
        Start the live video.
        """
        err = IC_GrabberDLL.start_live(self._handle, c_int(int(show_display)))
        if err != 1:
            raise IC_Exception(err)
    
    def suspend_live(self):
        """
        Suspend the live video and put into a prepared state.
        """
        err = IC_GrabberDLL.suspend_live(self._handle)
        if err != 1:
            raise IC_Exception(err)
        
    def stop_live(self):
        """
        Stop the live video.
        """
        IC_GrabberDLL.stop_live(self._handle)
        
    def get_image_description(self):
        """
        Get image info.
        
        :returns: tuple -- (image width, image height, image depth, color format).
        """
        
        img_width = c_long()
        img_height = c_long()
        img_depth = c_int()
        color_format = c_int()
        
        err = IC_GrabberDLL.get_image_description(self._handle,
                                                  byref(img_width),
                                                  byref(img_height),
                                                  byref(img_depth),
                                                  byref(color_format),
                                                  )
        
        return (img_width.value, img_height.value, img_depth.value, color_format.value)
    
    def snap_image(self, timeout=1000):
        """
        Snap an image. Device must be set to live mode and a format must be set.
        
        :param timeout: int -- time out in milliseconds.
        """
        err = IC_GrabberDLL.snap_image(self._handle, c_int(timeout))
        if err != 1:
            raise IC_Exception(err)
    
    def get_image_ptr(self):
        """
        Get image buffer from camera.
        
        :returns: ctypes pointer -- pointer to image data.
        """
        img_ptr = IC_GrabberDLL.get_image_ptr(self._handle)
        if img_ptr is None:
            raise IC_Exception(todo)
        
        #img_data = cast(img_ptr, POINTER(c_ubyte * buffer_size))
        ####array = (c_ubyte * iheight * iwidth * 3).from_address(addressof(data.contents))
        #array = img_data.contents

        return img_ptr
    
    def get_image_data(self):
        """
        Get image data.
        
        :returns: ctypes.c_ubyte array -- the image data.
        """
        image_size = self.get_image_description()[:3]
        
        img_width = image_size[0]
        img_height = image_size[1]
        img_depth = image_size[2] // 8
        buffer_size = img_width * img_height * img_depth * sizeof(c_uint8)

        img_ptr = self.get_image_ptr()
        data = cast(img_ptr, POINTER(c_ubyte * buffer_size))
        
        return (data.contents, img_width, img_height, img_depth)
        
        #img = np.ndarray(buffer = data.contents,
        #                 dtype = np.uint8,
        #                 shape = (img_height,
        #                          img_width,
        #                          img_depth))
        #return img

    def save_image(self, filename, filetype=1, jpeq_quality=75):
        """
        Save the contents of the last snapped image into a file.
        
        :param filename: string -- filename to name saved file.
        :param filetype: int -- 0 = BMP, 1 = JPEG.
        :param jpeq_quality: int -- JPEG file quality, 0-100.
        """
        err = IC_GrabberDLL.save_image(self._handle,
                                       c_char_p(filename.encode('ascii')),
                                       c_int(filetype),
                                       c_long(jpeq_quality))
        if err != 1:
            raise IC_Exception(err)
    
    # generate callback function so it is not a bound method
    # (cb_func cannot have the self parameter)
    def _get_callback_func(self):
        def cb_func(handle_ptr, p_data, frame_num, data):
            self._frame['ready'] = True
            self._frame['num'] = frame_num

        return C_FRAME_READY_CALLBACK(cb_func)
    
    def register_frame_ready_callback(self, callback=None):
        """
        Register the frame ready callback with the device.
        """
        if callback is None:
            # keep ref to prevent garbage collection
            self._rfrc_func = self._get_callback_func()
        else:
            self._rfrc_func = callback
        
        # register callback function with DLL
        # instead of passing pointer to a variable (3rd param) we will set the flag ourselves
        IC_GrabberDLL.set_frame_ready_callback(self._handle, self._rfrc_func, None)
        self._callback_registered = True
        
    def reset_frame_ready(self):
        """
        Reset the frame ready flag to False, generally so
        that wait_til_frame_ready() can be called again.
        """
        self._frame['ready'] = False
        self._frame['num'] = -1
        
    def wait_til_frame_ready(self, timeout=0):
        """
        Wait until the devices announces a frame as being ready.
        Requires register_frame_ready_callback() being called.
        
        :param timeout: int -- timeout in milliseconds. Set to 0 for no timeout.
        
        :returns: int -- frame number that was announced as ready.
        """
        if timeout:        
            start = time.clock()
            elapsed = (time.clock() - start) * 1000
            while not self._frame['ready'] and elapsed < timeout:
                time.sleep(0.001)
                elapsed = (time.clock() - start) * 1000
        else:
            while not self._frame['ready']:
                time.sleep(0.001)

        return self._frame['num']
    
    def remove_overlay(self, enable):
        """
        Enables or disables the overlay. Disable the overlay to capture Y16 images.

        :param enable: 1 to enable the overlay; 0 to disable the overlay.

        :returns: Nothing.
        """
        IC_GrabberDLL.remove_overlay(self._handle, enable)
        return


# MIT License
#
# Copyright (c) 2017 morefigs
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
