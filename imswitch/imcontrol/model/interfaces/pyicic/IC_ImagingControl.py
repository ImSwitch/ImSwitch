#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .IC_GrabberDLL import IC_GrabberDLL
from .IC_Camera import IC_Camera
from .IC_Exception import IC_Exception


class IC_ImagingControl:
    
    def init_library(self):
        """
        Initialise the IC Imaging Control library.
        """
        # remember list of unique device names
        self._unique_device_names = None
        
        # remember device objects by unique name
        self._devices = {}        
        
        # no license key needed anymore
        err = IC_GrabberDLL.init_library(None)
        if err != 1:
            raise IC_Exception(err)
    
    def get_unique_device_names(self):
        """
        Gets unique names (i.e. model + label + serial) of devices.
        
        :returns: list -- unique devices names.
        """
        if self._unique_device_names is None:
                   
            # make new list
            self._unique_device_names = []
            
            # get num devices, must be called before get_unique_name_from_list()!
            num_devices = IC_GrabberDLL.get_device_count()
            if num_devices < 0:
                raise IC_Exception(num_devices)
            
            # populate list
            for i in range(num_devices):
                self._unique_device_names.append(IC_GrabberDLL.get_unique_name_from_list(i).decode('ascii'))
        
        return self._unique_device_names
    
    def get_device(self, unique_device_name):
        """
        Gets camera device object based on unique name string.
        Will create one only if it doesn't already exist.

        :param device_name: string -- the unique name of the device.

        :returns: IC_Camera object -- the camera device object requested.	
        """
        # check name is valid
        if unique_device_name in self.get_unique_device_names():
            
            # check if already have a ref to device
            if unique_device_name not in self._devices:
                
                # if not, create one
                self._devices[unique_device_name] = IC_Camera(unique_device_name)
                
            return self._devices[unique_device_name]
        
        raise IC_Exception(-106)
    
    def close_library(self):
        """
        Close the IC Imaging Control library, and close and release all references to camera devices.
        """        
        # release handle grabber objects of cameras as they won't be needed again.
        # try to close & delete each known device, but only if we own the reference to it!
        for unique_device_name in self.get_unique_device_names():
            if unique_device_name in self._devices:
                # close camera device if open
                if self._devices[unique_device_name].is_open():
                    self._devices[unique_device_name].close()
                
                # release grabber of camera device
                IC_GrabberDLL.release_grabber(self._devices[unique_device_name]._handle)
        
        # kill refs
        self._unique_device_names = None
        self._devices = None
        
        # close lib        
        IC_GrabberDLL.close_library()


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
