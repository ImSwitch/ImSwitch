from logging import raiseExceptions
import numpy as np
import time
import cv2
from imswitch.imcommon.model import initLogger
from PIL import Image

from skimage.filters import gaussian, median
import imswitch.imcontrol.model.interfaces.gxipy as gx
import collections

class TriggerMode:
    SOFTWARE = 'Software Trigger'
    HARDWARE = 'Hardware Trigger'
    CONTINUOUS = 'Continuous Acqusition'

class CameraGXIPY:
    def __init__(self,cameraNo=None, exposure_time = 10000, gain = 0, frame_rate=-1, blacklevel=100, binning=1, flipImage=(False, False), isRGB=False):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

        # many to be purged
        self.model = "CameraGXIPY"
        self.shape = (0, 0)
        self.isRGB = isRGB
        self.is_connected = False
        self.is_streaming = False

        # unload CPU?
        self.downsamplepreview = 1

        # camera parameters
        self.blacklevel = blacklevel
        self.exposure_time = exposure_time
        self.gain = gain
        self.preview_width = 600
        self.preview_height = 600
        self.frame_rate = frame_rate
        self.cameraNo = cameraNo
        self.flipImage = flipImage

        # reserve some space for the framebuffer
        self.NBuffer = 10
        self.frame_buffer = collections.deque(maxlen=self.NBuffer)
        self.frameid_buffer = collections.deque(maxlen=self.NBuffer)
        self.flatfieldImage = None
        self.isFlatfielding = False
        self.lastFrameId = -1
        self.frameNumber = -1
        self.frame = None
        
        # For RGB
        self.contrast_lut = None        
        self.gamma_lut = None
        self.color_correction_param = 0


        #%% starting the camera thread
        self.camera = None

        # binning
        self.binning = binning

        self.device_manager = gx.DeviceManager()
        dev_num, dev_info_list = self.device_manager.update_device_list()

        if dev_num  != 0:
            self.__logger.debug("Trying to connect to camera: ")
            self.__logger.debug(dev_info_list)
            self._init_cam(cameraNo=self.cameraNo, binning=self.binning, callback_fct=self.set_frame)
        else :
            raise Exception("No camera GXIPY connected")


    def _init_cam(self, cameraNo=1, binning = 1, callback_fct=None):
        # start camera
        self.is_connected = True

        self.camera = self.device_manager.open_device_by_index(cameraNo)

        # reduce pixel number
        self.setBinning(binning)

        # set triggermode
        self.camera.TriggerMode.set(gx.GxSwitchEntry.OFF)

        # set exposure
        self.camera.ExposureTime.set(self.exposure_time)

        # set gain
        self.camera.Gain.set(self.gain)

        # set framerate
        self.set_frame_rate(self.frame_rate)

        # set blacklevel
        self.camera.BlackLevel.set(self.blacklevel)

        # set camera to mono12 mode
        availablePixelFormats = self.camera.PixelFormat.get_range()
        if self.camera.PixelColorFilter.is_implemented() is True: 
            self.isRGB = True
        else: 
            self.isRGB = False # TODO: Need to have an effect of the super class
        try: 
            self.set_pixel_format(list(availablePixelFormats)[-1]) # last one is at highest bitrate
        except Exception as e: 
            self.__logger.error(e)

        # get framesize
        self.SensorHeight = self.camera.HeightMax.get()//self.binning
        self.SensorWidth = self.camera.WidthMax.get()//self.binning

        # set the acq buffer count
        #data_stream = self.camera.data_stream[0]
        #data_stream.set_acquisition_buffer_number(1)
        #data_stream.register_capture_callback(callback_fct)
        user_param = None
        # set the acq buffer count
        self.camera.data_stream[0].set_acquisition_buffer_number(1)

        self.camera.register_capture_callback(user_param, callback_fct)

        # set things if RGB camera is used
        # get param of improving image quality
        if self.camera.GammaParam.is_readable():
            gamma_value = self.camera.GammaParam.get()
            self.gamma_lut = gx.Utility.get_gamma_lut(gamma_value)
        if self.camera.ContrastParam.is_readable():
            contrast_value = self.camera.ContrastParam.get()
            self.contrast_lut = gx.Utility.get_contrast_lut(contrast_value)
        if self.camera.ColorCorrectionParam.is_readable():
            self.color_correction_param = self.camera.ColorCorrectionParam.get()

    def start_live(self):
        if not self.is_streaming:
            # start data acquisition
            self.camera.stream_on()
            self.is_streaming = True

    def stop_live(self):
        if self.is_streaming:
            # start data acquisition
            self.camera.stream_off()
            self.is_streaming = False

    def suspend_live(self):
        if self.is_streaming:
        # start data acquisition
            try:
                self.camera.stream_off()
            except:
                # camera was disconnected?
                self.camera.unregister_capture_callback()
                self.camera.close_device()
                self._init_cam(cameraNo=self.cameraNo, binning=self.binning, callback_fct=self.set_frame)

            self.is_streaming = False

    def prepare_live(self):
        pass

    def close(self):
        self.camera.close_device()

    def set_flatfielding(self, is_flatfielding):
        self.isFlatfielding = is_flatfielding
        # record the flatfield image if needed
        if self.isFlatfielding:
            self.recordFlatfieldImage() 

    def set_exposure_time(self,exposure_time):
        self.exposure_time = exposure_time
        self.camera.ExposureTime.set(self.exposure_time*1000)

    def set_gain(self,gain):
        self.gain = gain
        self.camera.Gain.set(self.gain)

    def set_frame_rate(self, frame_rate):
        if frame_rate == -1:
            frame_rate = 10000 # go as fast as you can
        self.frame_rate = frame_rate

        # temporary
        self.camera.AcquisitionFrameRate.set(self.frame_rate)
        self.camera.AcquisitionFrameRateMode.set(gx.GxSwitchEntry.ON)

    def set_blacklevel(self,blacklevel):
        self.blacklevel = blacklevel
        self.camera.BlackLevel.set(self.blacklevel)
    
    def set_pixel_format(self,format):
        format = format.upper()
        if self.camera.PixelFormat.is_implemented() and self.camera.PixelFormat.is_writable():
            if format == 'MONO8':
                return self.camera.PixelFormat.set(gx.GxPixelFormatEntry.MONO8)
            if format == 'MONO10':
                return self.camera.PixelFormat.set(gx.GxPixelFormatEntry.MONO10)
            if format == 'MONO12':
                return self.camera.PixelFormat.set(gx.GxPixelFormatEntry.MONO12)
            if format == 'MONO14':
                return self.camera.PixelFormat.set(gx.GxPixelFormatEntry.MONO14)
            if format == 'MONO16':
                return self.camera.PixelFormat.set(gx.GxPixelFormatEntry.MONO16)
            if format == 'BAYER_RG8':
                return self.camera.PixelFormat.set(gx.GxPixelFormatEntry.BAYER_RG8)
            if format == 'BAYER_RG10':
                return self.camera.PixelFormat.set(gx.GxPixelFormatEntry.BAYER_RG10)
            if format == 'BAYER_RG12':
                return self.camera.PixelFormat.set(gx.GxPixelFormatEntry.BAYER_RG12)
        else:
            self.__logger.debug("pixel format is not implemented or not writable")
            return -1

    def setBinning(self, binning=1):
        # Unfortunately this does not work
        self.camera.BinningHorizontal.set(binning)
        self.camera.BinningVertical.set(binning)
        self.binning = binning

    def getLast(self, is_resize=True, returnFrameNumber=False, timeout=1):
        # get frame and save
        # only return fresh frames
        # print(self.lastFrameId, self.frameNumber)
        cTime = time.time()
        while(self.lastFrameId > self.frameNumber and self.frame is None):
            time.sleep(.01) # wait for fresh frame
            if time.time()-cTime > timeout:
                self.__logger.warning("Timeout in getLast")
                if returnFrameNumber:
                    return None, -1
        if self.isFlatfielding and self.flatfieldImage is not None:
            self.frame = self.frame/self.flatfieldImage
        self.lastFrameId = self.frameNumber
        if returnFrameNumber:
            return self.frame, self.frameNumber
        return self.frame

    def flushBuffer(self):
        self.frameid_buffer.clear()
        self.frame_buffer.clear()

    def getLastChunk(self):
        chunk = np.array(self.frame_buffer)
        frameids = np.array(self.frameid_buffer)
        self.flushBuffer()
        self.__logger.debug("Buffer: "+str(chunk.shape)+" IDs: " + str(frameids))
        return chunk

    def setROI(self,hpos=None,vpos=None,hsize=None,vsize=None):
        #hsize = max(hsize, 25)*10  # minimum ROI size
        #vsize = max(vsize, 3)*10  # minimum ROI size
        hpos = self.camera.OffsetX.get_range()["inc"]*((hpos)//self.camera.OffsetX.get_range()["inc"])
        vpos = self.camera.OffsetY.get_range()["inc"]*((vpos)//self.camera.OffsetY.get_range()["inc"])
        hsize = int(np.min((self.camera.Width.get_range()["inc"]*((hsize*self.binning)//self.camera.Width.get_range()["inc"]),self.camera.WidthMax.get())))
        vsize = int(np.min((self.camera.Height.get_range()["inc"]*((vsize*self.binning)//self.camera.Height.get_range()["inc"]),self.camera.HeightMax.get())))

        if vsize is not None:
            self.ROI_width = hsize
            # update the camera setting
            if self.camera.Width.is_implemented() and self.camera.Width.is_writable():
                message = self.camera.Width.set(self.ROI_width)
                self.__logger.debug(message)
            else:
                self.__logger.debug("OffsetX is not implemented or not writable")

        if hsize is not None:
            self.ROI_height = vsize
            # update the camera setting
            if self.camera.Height.is_implemented() and self.camera.Height.is_writable():
                message = self.camera.Height.set(self.ROI_height)
                self.__logger.debug(message)
            else:
                self.__logger.debug("Height is not implemented or not writable")

        if hpos is not None:
            self.ROI_hpos = hpos
            # update the camera setting
            if self.camera.OffsetX.is_implemented() and self.camera.OffsetX.is_writable():
                message = self.camera.OffsetX.set(self.ROI_hpos)
                self.__logger.debug(message)
            else:
                self.__logger.debug("OffsetX is not implemented or not writable")

        if vpos is not None:
            self.ROI_vpos = vpos
            # update the camera setting
            if self.camera.OffsetY.is_implemented() and self.camera.OffsetY.is_writable():
                message = self.camera.OffsetY.set(self.ROI_vpos)
                self.__logger.debug(message)
            else:
                self.__logger.debug("OffsetX is not implemented or not writable")

        return hpos,vpos,hsize,vsize


    def setPropertyValue(self, property_name, property_value):
        # Check if the property exists.
        if property_name == "gain":
            self.set_gain(property_value)
        elif property_name == "exposure":
            self.set_exposure_time(property_value)
        elif property_name == "blacklevel":
            self.set_blacklevel(property_value)
        elif property_name == "flat_fielding":
            self.set_flatfielding(property_value)
        elif property_name == "roi_size":
            self.roi_size = property_value
        elif property_name == "frame_rate":
            self.set_frame_rate(property_value)
        elif property_name == "trigger_source":
            self.setTriggerSource(property_value)
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def getPropertyValue(self, property_name):
        # Check if the property exists.
        if property_name == "gain":
            property_value = self.camera.Gain.get()
        elif property_name == "exposure":
            property_value = self.camera.ExposureTime.get()
        elif property_name == "blacklevel":
            property_value = self.camera.BlackLevel.get()
        elif property_name == "image_width":
            property_value = self.camera.Width.get()//self.binning
        elif property_name == "image_height":
            property_value = self.camera.Height.get()//self.binning
        elif property_name == "roi_size":
            property_value = self.roi_size
        elif property_name == "frame_Rate":
            property_value = self.frame_rate
        elif property_name == "trigger_source":
            property_value = self.trigger_source
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def setTriggerSource(self, trigger_source):
        if trigger_source =='Continous':
            self.set_continuous_acquisition()
        elif trigger_source =='Internal trigger':
            self.set_software_triggered_acquisition()
        elif trigger_source =='External trigger':
            self.set_hardware_triggered_acquisition()

    def set_continuous_acquisition(self):
        self.camera.TriggerMode.set(gx.GxSwitchEntry.OFF)
        self.trigger_mode = TriggerMode.CONTINUOUS

    def set_software_triggered_acquisition(self):
        self.camera.TriggerMode.set(gx.GxSwitchEntry.ON)
        self.camera.TriggerSource.set(gx.GxTriggerSourceEntry.SOFTWARE)
        self.trigger_mode = TriggerMode.SOFTWARE

    def set_hardware_triggered_acquisition(self):
                # set continuous acquisition
        self.camera.TriggerMode.set(gx.GxSwitchEntry.ON)

        # set trigger source with line2
        self.camera.TriggerSource.set(3)

        # set line selector with linw
        self.camera.LineSelector.set(2)

        # set line mode input
        self.camera.LineMode.set(0)

        # set line source
        #cam.LineSource.set(2)

        status = False
        status = self.camera.LineStatus.get()

        # User Set Selector
        self.camera.UserSetSelector.set(1)
        # User Set Save
        self.camera.UserSetSave.send_command()

        '''
        self.camera.TriggerMode.set(gx.GxSwitchEntry.ON)
        self.camera.TriggerSource.set(gx.GxTriggerSourceEntry.LINE2)
        #self.camera.TriggerSource.set(gx.GxTriggerActivationEntry.RISING_EDGE)
        '''
        self.trigger_mode = TriggerMode.HARDWARE

        self.flushBuffer()

    def getFrameNumber(self):
        return self.frameNumber

    def send_trigger(self):
        if self.is_streaming:
            self.camera.TriggerSoftware.send_command()
        else:
        	self.__logger.debug('trigger not sent - camera is not streaming')

    def openPropertiesGUI(self):
        pass

    def set_frame(self, params, frame):
        if frame is None:
            self.__logger.error("Getting image failed.")
            return
        if frame.get_status() != 0:
            self.__logger.error("Got an incomplete frame")
            return

        
        # if RGB
        if self.isRGB:
            rgb_image = frame.convert("RGB")
            if rgb_image is None:
                return

            # improve image quality
            rgb_image.image_improvement(self.color_correction_param, self.contrast_lut, self.gamma_lut)

            # create numpy array with data from raw image
            numpy_image = rgb_image.get_numpy_array()
            if numpy_image is None:
                return

        else:
            #breakpoint()
            numpy_image = frame.get_numpy_array()

        # flip image if needed
        if self.flipImage[0]: # Y
            numpy_image = np.flip(numpy_image, axis=0)
        if self.flipImage[1]: # X
            numpy_image = np.flip(numpy_image, axis=1)
        if numpy_image is None:
            self.__logger.error("Got a None frame")
            return
        self.frame = numpy_image.copy()
        self.frameNumber = frame.get_frame_id()
        self.timestamp = time.time()

        #if self.binning > 1:
        #    numpy_image = cv2.resize(numpy_image, dsize=None, fx=1/self.binning, fy=1/self.binning, interpolation=cv2.INTER_AREA)
        self.frame_buffer.append(numpy_image)
        self.frameid_buffer.append(self.frameNumber)

    def recordFlatfieldImage(self, nFrames=10, nGauss=5, nMedian=5):
        # record a flatfield image and save it in the flatfield variable
        flatfield = []
        for iFrame in range(nFrames):
            flatfield.append(self.getLast())
        flatfield = np.mean(np.array(flatfield),0)
        # normalize and smooth using scikit image
        flatfield = gaussian(flatfield, sigma=nGauss)
        flatfield = median(flatfield, selem=np.ones((nMedian, nMedian)))
        self.flatfieldImage = flatfield
        
    def setFlatfieldImage(self, flatfieldImage, isFlatfieldEnabeled=True):
        self.flatfieldImage = flatfieldImage
        self.isFlatfielding = isFlatfieldEnabeled


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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
