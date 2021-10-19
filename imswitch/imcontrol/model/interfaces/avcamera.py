import argparse
import cv2
import time
import numpy as np
import copy
import threading
import queue
import os
from PIL import Image

from typing import Optional
from vimba import *

from imswitch.imcommon.model import initLogger
from .pyicic import IC_ImagingControl

from imswitch.imcontrol.model.interfaces.vimbapy.vicamera_frameproducer import *
from imswitch.imcontrol.model.interfaces.vimbapy.vicamera_frameconsumer import *
from imswitch.imcontrol.model.interfaces.vimbapy.vicamera import VimbaCameraThread

FRAME_HEIGHT = 1088
FRAME_WIDTH = 1456

# Camera Settings
#CAM_GAIN = 20 # dB
T_EXPOSURE_MAX = 1e6 # µs => 1s
ExposureTime = 50e3

class CameraAV:
    def __init__(self,cameraNo=None):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

        # many to be purged
        self.model = "AV Camera"
        self.shape = (0, 0)

        self.blacklevel = 00
        self.exposure_time = 0
        self.analog_gain = 0
        self.frame_ID = -1
        self.frame_ID_software = -1
        self.frame_ID_offset_hardware_trigger = 0
        self.timestamp = 0

        self.image_locked = False
        self.current_frame = None

        self.callback_is_enabled = False
        self.callback_was_enabled_before_autofocus = False
        self.callback_was_enabled_before_multipoint = False
        self.is_streaming = False

        self.GAIN_MAX = 24
        self.GAIN_MIN = 0
        self.GAIN_STEP = 1
        self.EXPOSURE_TIME_MS_MIN = 0.01
        self.EXPOSURE_TIME_MS_MAX = 4000

        self.ROI_offset_x = CAMERA.ROI_OFFSET_X_DEFAULT
        self.ROI_offset_y = CAMERA.ROI_OFFSET_X_DEFAULT
        self.ROI_width = CAMERA.ROI_WIDTH_DEFAULT
        self.ROI_height = CAMERA.ROI_HEIGHT_DEFAULT

    def start_live(self):
        # no camera thread open, generate one!
        self.camera = VimbaCameraThread()
        # temporary
        self.camera.start()
        self.camera.setExposureTime(1000)

    def stop_live(self):
        self.camera.stop_preview()
        self.camera.close()
        self.device_info_list = None
        self.camera = None
        self.is_color = None
        self.gamma_lut = None
        self.contrast_lut = None
        self.color_correction_param = None
        self.last_raw_image = None
        self.last_converted_image = None
        self.last_numpy_image = None

    def suspend_live(self):
        pass

    def prepare_live(self):
        pass

    def set_exposure_time(self,exposure_time):
        self.exposure_time = exposure_time
        self.camera.setExposureTime(self.exposure_time*1000)

    def set_analog_gain(self,analog_gain):
        self.analog_gain = analog_gain
        self.camera.setGain(self.analog_gain)
        
    def get_awb_ratios(self):
        '''
        self.camera.BalanceWhiteAuto.set(2)
        self.camera.BalanceRatioSelector.set(0)
        awb_r = self.camera.BalanceRatio.get()
        self.camera.BalanceRatioSelector.set(1)
        awb_g = self.camera.BalanceRatio.get()
        self.camera.BalanceRatioSelector.set(2)
        awb_b = self.camera.BalanceRatio.get()
        '''
        awb_r, awb_g, awb_b = 1,1,1
        return (awb_r, awb_g, awb_b)

    def set_wb_ratios(self, wb_r=None, wb_g=None, wb_b=None):
        pass

    def start_streaming(self):
        self.is_streaming = True

    def stop_streaming(self):
        self.is_streaming = False

    def set_pixel_format(self,format):
        #TODO: Implement
        '''
        if self.is_streaming == True:
            was_streaming = True
            self.stop_streaming()
        else:
            was_streaming = False
        if self.camera.PixelFormat.is_implemented() and self.camera.PixelFormat.is_writable():
            if format == 'MONO8':
                self.camera.PixelFormat.set(gx.GxPixelFormatEntry.MONO8)
            if format == 'MONO12':
                self.camera.PixelFormat.set(gx.GxPixelFormatEntry.MONO12)
            if format == 'MONO14':
                self.camera.PixelFormat.set(gx.GxPixelFormatEntry.MONO14)
            if format == 'MONO16':
                self.camera.PixelFormat.set(gx.GxPixelFormatEntry.MONO16)
            if format == 'BAYER_RG8':
                self.camera.PixelFormat.set(gx.GxPixelFormatEntry.BAYER_RG8)
            if format == 'BAYER_RG12':
                self.camera.PixelFormat.set(gx.GxPixelFormatEntry.BAYER_RG12)
        else:
            print("pixel format is not implemented or not writable")
        if was_streaming:
           self.start_streaming()
        '''
        pass

    def set_continuous_acquisition(self):
        '''
        self.camera.TriggerMode.set(gx.GxSwitchEntry.OFF)
        '''
        pass

    def set_software_triggered_acquisition(self):
        '''
        self.camera.TriggerMode.set(gx.GxSwitchEntry.ON)
        self.camera.TriggerSource.set(gx.GxTriggerSourceEntry.SOFTWARE)
        '''
        pass
    
    def set_hardware_triggered_acquisition(self):
        '''
        self.camera.TriggerMode.set(gx.GxSwitchEntry.ON)
        self.camera.TriggerSource.set(gx.GxTriggerSourceEntry.LINE2)
        # self.camera.TriggerSource.set(gx.GxTriggerActivationEntry.RISING_EDGE)
        self.frame_ID_offset_hardware_trigger = self.frame_ID
        '''
        pass

    def send_trigger(self):
        '''
        if self.is_streaming:
            self.camera.TriggerSoftware.send_command()
        else:
        	print('trigger not sent - camera is not streaming')
        '''
        pass

    def grabFrame(self):
        # get frame and save
        numpy_image = np.squeeze(self.camera.getLatestFrame(is_raw=True))
        return numpy_image


    def setROI(self, hpos, vpos, hsize, vsize):
        hsize = max(hsize, 256)  # minimum ROI size
        vsize = max(vsize, 24)  # minimum ROI size
        # self.__logger.debug(
        #     f'{self.model}: setROI started with {hsize}x{vsize} at {hpos},{vpos}.'
        # )
        '''
        self.cam.frame_filter_set_parameter(self.roi_filter, 'Top'.encode('utf-8'), vpos)
        self.cam.frame_filter_set_parameter(self.roi_filter, 'Left'.encode('utf-8'), hpos)
        self.cam.frame_filter_set_parameter(self.roi_filter, 'Height'.encode('utf-8'), vsize)
        self.cam.frame_filter_set_parameter(self.roi_filter, 'Width'.encode('utf-8'), hsize)
        top = self.cam.frame_filter_get_parameter(self.roi_filter, 'Top'.encode('utf-8'))
        left = self.cam.frame_filter_get_parameter(self.roi_filter, 'Left'.encode('utf-8'))
        hei = self.cam.frame_filter_get_parameter(self.roi_filter, 'Height'.encode('utf-8'))
        wid = self.cam.frame_filter_get_parameter(self.roi_filter, 'Width'.encode('utf-8'))
        self.__logger.debug(
            f'{self.model}: '
            f'setROI finished, following params are set: w{wid}xh{hei} at l{left},t{top}'
        )
        '''
        #TODO: Impelment 

    def setPropertyValue(self, property_name, property_value):
        # Check if the property exists.
        if property_name == "gain":
            self.set_analog_gain(property_value)
        elif property_name == "exposure":
            self.set_exposure_time(property_value)
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def getPropertyValue(self, property_name):
        # Check if the property exists.
        if property_name == "gain":
            property_value = self.camera.gain
        elif property_name == "exposure":
            property_value = self.camera.gain
        elif property_name == "image_width":
            property_value = FRAME_WIDTH
        elif property_name == "image_height":
            property_value = FRAME_HEIGHT
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def openPropertiesGUI(self):
        pass
