import numpy as np
import time
import cv2
from imswitch.imcommon.model import initLogger

import threading
from pypylon import pylon
from pypylon import genicam

class CameraBasler:
    def __init__(self,cameraNo=None, exposure_time = 1000, gain = 0, blacklevel=100):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

        # many to be purged
        self.model = "CameraBasler"
        self.shape = (0, 0)
        
        self.is_connected = False
        self.is_streaming = False

        # camera parameters
        self.blacklevel = blacklevel
        self.exposure_time = exposure_time
        self.gain = gain
        self.preview_width = 600
        self.preview_height = 600

        #%% starting the camera thread
        self.camera = None
        self._init_cam()
        self.last_frame = np.zeros((self.preview_height,self.preview_width))
        

    def _init_cam(self):
        # Create an instant camera object with the camera device found first.
        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.camera.Open()

        # start camera
        self.is_connected = True
        
        # set exposure
        self.set_exposure_time(self.exposure_time)

        # set gain
        self.set_gain(self.gain)
        
        # set blacklevel
        self.set_blacklevel(self.blacklevel)

        # set the acq buffer count
        self.camera.MaxNumBuffer = 5
        
        # set camera to mono12 mode
        try:
            self.camera.PixelFormat.SetValue('Mono12')
        except:
            # we have a RGB camera
            self.camera.PixelFormat.SetValue('RGB8')
            pass

        # get framesize 
        self.SensorHeight = self.camera.HeightMax.GetValue()
        self.SensorWidth = self.camera.WidthMax.GetValue()


    def frame_grabber(self):
        try:
            self.camera.StartGrabbing()
        except:
            self.camera.Close()
            self._init_cam()

        self.__logger.debug("Starting the frame grabber")
        while self.camera.IsGrabbing():
            # Wait for an image and then retrieve it. A timeout of 5000 ms is used.
            try:
                #self.__logger.debug("BASLER: Grabbing frame")
                grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            
                # Image grabbed successfully?
                if grabResult.GrabSucceeded():
                    # Access the image data.
                    img = grabResult.Array
                    self.last_frame = img

                else:
                    self.__logger.error("Error: ", grabResult.ErrorCode, grabResult.ErrorDescription)
                grabResult.Release()
            except Exception as e:
                self.__logger.error(e)
                break

    def start_live(self):
        if not self.is_streaming:
            # start data acquisition
            self.frame_grabber_thread = threading.Thread(target=self.frame_grabber, args=())
            self.frame_grabber_thread.start()
            
            self.is_streaming = True

    def stop_live(self):
        if self.is_streaming:
            # start data acquisition
            self.camera.StopGrabbing()
            self.frame_grabber_thread.join()
            del self.frame_grabber_thread 
            self.is_streaming = False

    def suspend_live(self):
        if self.is_streaming:
        # start data acquisition
            try:
                self.camera.StopGrabbing()
                self.frame_grabber_thread.join()
                del self.frame_grabber_thread 
            except:
                # camera was disconnected? 
                self.camera.Close()
                self._init_cam()

            self.is_streaming = False
        
    def prepare_live(self):
        pass

    def close(self):
        self.camera.Close()
        
    def set_exposure_time(self,exposure_time):
        self.exposure_time = exposure_time
        try:
            self.camera.ExposureTime.SetValue(self.exposure_time*1000)
        except Exception as e:
            self.__logger.error(e)
        
    def set_gain(self,gain):
        self.gain = gain
        try:
            self.camera.Gain.SetValue(self.gain)
        except Exception as e:
            self.__logger.error(e)

    def set_blacklevel(self,blacklevel):
        self.blacklevel = blacklevel
        try:
            self.camera.BlackLevel.SetValue(self.blacklevel)
        except Exception as e:
            self.__logger.error(e)

    def set_pixel_format(self,format):
        pass
        '''
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
        '''

    def getLast(self, is_resize=True):
        # get frame and save
        try:
            self.last_frame_preview = self.last_frame
            
            minHeight = int(self.SensorHeight//2-self.roi_size//2)
            maxHeight = int(self.SensorHeight//2+self.roi_size//2)
            minWidth = int(self.SensorWidth//2-self.roi_size//2)
            maxWidth = int(self.SensorWidth//2+self.roi_size//2)
            self.last_frame_preview = self.last_frame_preview[minHeight:maxHeight,minWidth:maxWidth]
            
            if is_resize:
                self.last_frame_preview = cv2.resize(self.last_frame_preview , dsize=None, fx=.25, fy=.25, interpolation= cv2.INTER_LINEAR)
#                self.last_frame_preview = cv2.resize(self.last_frame_preview , dsize=None(self.preview_width,self.preview_height), interpolation= cv2.INTER_LINEAR)
        except:
            pass # TODO: What if the very first frame is corrupt?
        return self.last_frame_preview 

    def getLastChunk(self):
        return self.getLast(is_resize=False)

    def setROI(self,hpos=None,vpos=None,hsize=None,vsize=None):
        #hsize = max(hsize, 25)*10  # minimum ROI size
        #vsize = max(vsize, 3)*10  # minimum ROI size
        hpos = 8*(hpos//8)
        vpos = 2*(vpos//2)     
        hsize = 8*(hsize//8)   
        vsize = 2*(vsize//2) 

        if hsize is not None:
            self.ROI_width = hsize
            # update the camera setting
            if self.camera.Width.is_implemented() and self.camera.Width.is_writable():
                self.camera.Width.set(self.ROI_width)
            else:
                print("OffsetX is not implemented or not writable")

        if vsize is not None:
            self.ROI_height = vsize
            # update the camera setting
            if self.camera.Height.is_implemented() and self.camera.Height.is_writable():
                self.camera.Height.set(self.ROI_height)
            else:
                print("Height is not implemented or not writable")

        if hpos is not None:
            self.ROI_hpos = hpos
            # update the camera setting
            if self.camera.OffsetX.is_implemented() and self.camera.OffsetX.is_writable():
                self.camera.OffsetX.set(self.ROI_hpos)
            else:
                print("OffsetX is not implemented or not writable")

        if vpos is not None:
            self.ROI_vpos = vpos
            # update the camera setting
            if self.camera.OffsetY.is_implemented() and self.camera.OffsetY.is_writable():
                self.camera.OffsetY.set(self.ROI_vpos)
            else:
                print("OffsetX is not implemented or not writable")


    def setPropertyValue(self, property_name, property_value):
        # Check if the property exists.
        if property_name == "gain":
            self.set_gain(property_value)
        elif property_name == "exposure":
            self.set_exposure_time(property_value)
        elif property_name == "blacklevel":
            self.set_blacklevel(property_value)
        elif property_name == "roi_size":
            self.roi_size = property_value
        elif property_name == "isRGB":
            self.isRGB = property_value
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def getPropertyValue(self, property_name):
        # Check if the property exists.
        if property_name == "gain":
            property_value = self.camera.Gain.GetValue()
        elif property_name == "exposure":
            property_value = self.camera.ExposureTime.GetValue()
        elif property_name == "blacklevel":
            property_value = self.camera.BlackLevel.GetValue()            
        elif property_name == "image_width":
            property_value = self.camera.Width.GetValue()            
        elif property_name == "image_height":
            property_value = self.camera.Height.GetValue()    
        elif property_name == "roi_size":
            property_value = self.roi_size 
        elif property_name == "isRGB":
            property_value = self.isRGB
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def openPropertiesGUI(self):
        pass


    class ImageEventPrinter(pylon.ImageEventHandler):
        img  = None
        def OnImagesSkipped(self, camera, countOfSkippedImages):
            print("OnImagesSkipped event for device ", camera.GetDeviceInfo().GetModelName())
            print(countOfSkippedImages, " images have been skipped.")
            print()

        def OnImageGrabbed(self, camera, grabResult):
            print("OnImageGrabbed event for device ", camera.GetDeviceInfo().GetModelName())

            # Image grabbed successfully?
            if grabResult.GrabSucceeded():
                print("SizeX: ", grabResult.GetWidth())
                print("SizeY: ", grabResult.GetHeight())
                img = grabResult.GetArray()
                self.img = img
                print("Gray values of first row: ", img[0])
                print()
            else:
                print("Error: ", grabResult.GetErrorCode(), grabResult.GetErrorDescription())

        def getFrame(self):
            return self.img


# Copyright (C) ImSwitch developers 2021
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