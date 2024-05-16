import numpy as np

from imswitch.imcommon.model import initLogger
# from .pyicic import IC_ImagingControl
import time
from arena_api.system import system
from arena_api.buffer import *
import ctypes
import numpy as np
import cv2
from datetime import datetime
from arena_api.enums import PixelFormat
from arena_api.__future__.save import Writer
from datetime import datetime

class CameraTIS:
    def __init__(self, cameraNo):
        super().__init__()
        
        self.__logger = initLogger(self, tryInheritParent=True)
        
        device = []
        system.destroy_device()
        
        # cameraNo is a two digit number unique to our cams (LUCID)
        cameraNo_string = "{}".format(cameraNo)
        camerNo_num_digit = len(cameraNo_string)
        camera_found = False
        
        device_infos = None
        selected_index = None
        
        device_infos = system.device_infos
        print(device_infos)
        for i in range(len(device_infos)):
            if cameraNo_string == device_infos[i]['serial'][-camerNo_num_digit:]:
            # serial_number = "224602765"
            # if serial_number == device_infos[i]['serial']:
                device_info = device_infos[i]
                serial_number =  device_info['serial']
                selected_index = i
                camera_found = True
                break
        print("---Here---")
        if camera_found == True:
            device = system.create_device(device_infos=device_infos[selected_index])[0]
        else:
            raise Exception(f"Serial number {serial_number} cannot be found")
        
        # nodemap = device.nodemap
        
        self.device = device
        self.nodemap = device.nodemap
        
        self.nodes = self.nodemap.get_node(['Width', 'Height', 'PixelFormat', 
                                       'ExposureAuto','ExposureTime','DeviceStreamChannelPacketSize', 'OffsetX', 'OffsetY','Gamma','Gain'])
        self.model = device_info['model']
        self.nodes['ExposureAuto'].value = 'Off'
        
        self.exposure = 100.1
        self.gain = 0.0
        self.brightness = 1
        self.SensorHeight = 512
        self.SensorWidth = 512
        self.shape = (self.SensorHeight,self.SensorWidth)
        
        self.properties = {
            'image_height': self.nodes['Height'].value,
            'image_width': self.nodes['Width'].value,
            'subarray_vpos': self.nodes['OffsetX'].value,
            'subarray_hpos': self.nodes['OffsetY'].value,
            'exposure_time': self.nodes['ExposureTime'].min,
            'subarray_vsize': 512,
            'subarray_hsize': 512,
            'SensorHeight': 4600,
            'SensorWidth': 5320
        }
        
        print(device)

        # return device
        
        # ic_ic = IC_ImagingControl.IC_ImagingControl()
        # ic_ic.init_library()
        # cam_names = ic_ic.get_unique_device_names()
        # self.model = cam_names[cameraNo]
        # self.cam = ic_ic.get_device(cam_names[cameraNo])

        # self.cam.open()

        # self.shape = (0, 0)
        # self.cam.colorenable = 0

        # self.cam.enable_continuous_mode(True)  # image in continuous mode
        # self.cam.enable_trigger(False)  # camera will wait for trigger

        # self.roi_filter = self.cam.create_frame_filter('ROI')
        # self.cam.add_frame_filter_to_device(self.roi_filter)

    def create_device_from_serial_number(self, serial_number):
        
        device = []
        camera_found = False

        device_infos = None
        selected_index = None

        device_infos = system.device_infos
        for i in range(len(device_infos)):
            if serial_number == device_infos[i]['serial']:
                selected_index = i
                camera_found = True
                break

        if camera_found == True:
            device = system.create_device(device_infos=device_infos[selected_index])[0]
        else:
            raise Exception(f"Serial number {serial_number} cannot be found")

        return device
    
    def start_live(self):
        print("start_live")
        num_buffers = 4
        # with self.device.start_stream(num_buffers):
            
        #     """ 'device.get_buffer(arg)' returns arg number of buffers
        #     the buffer is in the rgb layout """
            
        #     print('\tGet 500 buffers')

        #     # Grab images --------------------------------------------------------
        #     buffers = self.device.get_buffer(num_buffers)

        #     # Print image buffer info
        #     for count, buffer in enumerate(buffers):
        #         print(f'\t\tbuffer{count:{2}} received | '
        #             f'Width = {buffer.width} pxl, '
        #             f'Height = {buffer.height} pxl, '
        #             f'Pixel Format = {buffer.pixel_format.name}')
                    
        #     self.device.requeue_buffer(buffers)
        #     print(f'Requeued {num_buffers} buffers')
        self.device.start_stream(num_buffers)    
        # self.device.stop_stream()

    def stop_live(self):
        print("stop_live")
        self.device.stop_stream()
        # self.cam.stop_live()  # stop imaging

    def suspend_live(self):
        print("suspend_live")
        self.device.stop_stream()
        # self.cam.suspend_live()  # suspend imaging into prepared state

    def prepare_live(self):
        print("prepare_live")
        self.device.start_stream()
        # self.cam.prepare_live()  # prepare prepared state for live imaging

    def grabFrame(self):
        # self.cam.wait_til_frame_ready(20)  # wait for frame ready
        # self.device.stop_stream()
        # self.device.start_stream()
        print("grabFrame")
        curr_frame_time = time.time()
        
        buffer = self.device.get_buffer()
        """
        Copy buffer and requeue to avoid running out of buffers
        """
        item = BufferFactory.copy(buffer)
        self.device.requeue_buffer(buffer)
        print(len(item.data))
        buffer_bytes_per_pixel = int(len(item.data)/(item.width * item.height))
        """
        Buffer data as cpointers can be accessed using buffer.pbytes
        """
        num_channels = 1
        prev_frame_time = 0
        array = (ctypes.c_ubyte * num_channels * item.width * item.height).from_address(ctypes.addressof(item.pbytes))
        
        """
        Create a reshaped NumPy array to display using OpenCV
        """
        frame = np.ndarray(buffer=array, dtype=np.uint8, shape=(item.height, item.width, buffer_bytes_per_pixel))
        # print(np.shape(frame))
        width = item.width
        height = item.height
        depth = 0

        fps = str(1/(curr_frame_time - prev_frame_time))
        
        # frame, width, height, depth = self.cam.get_image_data()
        # frame = np.array(frame, dtype='float64')
        # Check if below is giving the right dimensions out
        # TODO: do this smarter, as I can just take every 3rd value instead of creating a reshaped
        #       3D array and taking the first plane of that
        # frame = np.reshape(frame, (height, width, depth))[:, :, 0]
        frame = np.transpose(frame)
        # self.device.stop_stream()
        """
            Destroy the copied item toa prevent memory leaks
        """
        # BufferFactory.destroy(item)
        # time.sleep(.25)        
            
        return frame

    def setROI(self, hpos, vpos, hsize, vsize):
        hsize = max(hsize, 256)  # minimum ROI size
        vsize = max(vsize, 24)  # minimum ROI size
        self.__logger.debug(
            f'{self.model}: setROI started with {hsize}x{vsize} at {hpos},{vpos}.'
        )
        #Replaces what si below
        if self.nodes['Width'].is_readable and self.nodes['Width'].is_writable:
            self.nodes['Width'].value = vsize
        if self.nodes['Height'].is_readable and self.nodes['Height'].is_writable:
            self.nodes['Height'].value = hsize
        if self.nodes['OffsetX'].is_readable and self.nodes['OffsetX'].is_writable:    
            self.nodes['OffsetX'].value = vpos
        if self.nodes['OffsetY'].is_readable and self.nodes['OffsetY'].is_writable:       
            self.nodes['OffsetY'].value = hpos
        
        #self.cam.frame_filter_set_parameter(self.roi_filter, 'Top'.encode('utf-8'), vpos)        # self.cam.frame_filter_set_parameter(self.roi_filter, 'Top', vpos)
        # self.cam.frame_filter_set_parameter(self.roi_filter, 'Left', hpos)
        # self.cam.frame_filter_set_parameter(self.roi_filter, 'Height', vsize)
        # self.cam.frame_filter_set_parameter(self.roi_filter, 'Width', hsize)
        top = self.nodes['OffsetX']
        left = self.nodes['OffsetY']
        hei = self.nodes['Height']
        wid = self.nodes['Width']
        self.__logger.info(
            f'ROI set: w{wid} x h{hei} at l{left},t{top}'
        )

    def setPropertyValue(self, property_name, property_value):
        # Check if the property exists.
        if property_name == "gain":
            self.nodes['Gain'].value = property_value
            # self.cam.gain = property_value
        elif property_name == "brightness":
            self.nodes['Gamma'].value = property_value
            # self.cam.brightness = property_value
        elif property_name == "exposure":
            self.nodes['ExposureTime'].value = property_value
            # self.cam.exposure = property_value
        elif property_name == 'image_height':
            self.shape = (self.shape[0], property_value)
        elif property_name == 'image_width':
            self.shape = (property_value, self.shape[1])
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def getPropertyValue(self, property_name):
        # Check if the property exists.
        if property_name == "gain":
            property_value = self.nodes['Gain'].value
        elif property_name == "brightness":
            property_value = self.nodes['Gamma'].value
        elif property_name == "exposure":
            property_value = self.nodes['ExposureTime'].value
        elif property_name == "image_width":
            property_value = self.shape[0]
        elif property_name == "image_height":
            property_value = self.shape[1]
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def openPropertiesGUI(self):
        pass
        # self.cam.show_property_dialog()


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
