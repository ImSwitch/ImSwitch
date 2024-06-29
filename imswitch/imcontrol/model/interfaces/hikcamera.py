from logging import raiseExceptions
import numpy as np
import time
import cv2
from imswitch.imcommon.model import initLogger
from skimage.filters import gaussian, median

import sys
import threading
from ctypes import *
import collections

from sys import platform
try:
    if platform == "linux" or platform == "linux2":
        # linux
        from imswitch.imcontrol.model.interfaces.hikrobotMac.MvCameraControl_class import *
    elif platform == "darwin":
        # OS X
        from imswitch.imcontrol.model.interfaces.hikrobotMac.MvCameraControl_class import *
        pass
    elif platform == "win32":
        import msvcrt
        from imswitch.imcontrol.model.interfaces.hikrobotWin.MvCameraControl_class import *
except Exception as e:
    print(e)
    
    




class CameraHIK:
    def __init__(self,cameraNo=None, exposure_time = 10000, gain = 0, frame_rate=-1, blacklevel=100, isRGB=False, binning=2):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=False)

        # many to be purged
        self.model = "CameraHIK"
        self.shape = (0, 0)
        
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

        # reserve some space for the framebuffer
        self.NBuffer = 1
        self.frame_buffer = collections.deque(maxlen=self.NBuffer)
        self.frameid_buffer = collections.deque(maxlen=self.NBuffer)
        self.flatfieldImage = None
        #%% starting the camera thread
        self.camera = None

        # binning 
        if platform in ("darwin", "linux2", "linux"):
            binning = 2
        self.binning = binning

        self.SensorHeight = 0
        self.SensorWidth = 0
        self.frame = np.zeros((self.SensorHeight, self.SensorWidth))
        
        self.lastFrameId = -1
        self.frameNumber = -1
        
        
        # thread switch
        self.g_bExit = False

        self.isRGB = isRGB
        self.isFlatfielding = False
        self._init_cam(cameraNo=self.cameraNo, callback_fct=None)

    def _init_cam(self, cameraNo=1, callback_fct=None):
        # start camera
        self.is_connected = True

        deviceList = MV_CC_DEVICE_INFO_LIST()
        tlayerType = MV_USB_DEVICE

        # Enum device
        ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
        if ret != 0:
            raise Exception("enum devices fail! ret[0x%x]", ret)

        if deviceList.nDeviceNum == 0:
            raise Exception("No camera HIK connected")

        # open the first device
        self.camera = MvCamera()

        # Select device and create handle
        self.stDeviceList = cast(deviceList.pDeviceInfo[int(cameraNo)], POINTER(MV_CC_DEVICE_INFO)).contents
                            
        ret = self.camera.MV_CC_CreateHandle(self.stDeviceList)
        if ret != 0:
            raise Exception("create handle fail! ret[0x%x]", ret)
                
        #  Open device
        ret = self.camera.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0:
            raise Exception("open device fail! ret[0x%x]", ret)            
        # bin to speed up?
        self.setBinning(binning=self.binning)

        stBool = c_bool(False)
        ret = self.camera.MV_CC_GetBoolValue("AcquisitionFrameRateEnable", stBool)
        if ret != 0:
            self.__logger.debug("get AcquisitionFrameRateEnable fail! ret[0x%x]" % ret)

        #  Set trigger mode as off
        ret = self.camera.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
        if ret != 0:
            self.__logger.debug("set trigger mode fail! ret[0x%x]" % ret)
            sys.exit()

        # get framesize 
        stFloatParam_height = MVCC_INTVALUE()
        memset(byref(stFloatParam_height), 0, sizeof(MVCC_INTVALUE))
        stFloatParam_width = MVCC_INTVALUE()
        memset(byref(stFloatParam_width), 0, sizeof(MVCC_INTVALUE))
        
        #stOutFrame = MV_FRAME_OUT()  # stOutFrame.stFrameInfo.nHeight
        self.SensorHeight = self.camera.MV_CC_GetIntValue("Height", stFloatParam_height)
        self.SensorWidth = self.camera.MV_CC_GetIntValue("Width", stFloatParam_width)
        #if self.isRGB:
        #    self.camera.MV_CC_SetEnumValue("PixelFormat", PixelType_Gvsp_BayerGB8) 

        '''
        # set exposure
        self.camera.ExposureTime.set(self.exposure_time)

        # set gain
        self.camera.Gain.set(self.gain)
        
        # set framerate
        self.set_frame_rate(self.frame_rate)
        
        # set blacklevel
        self.camera.BlackLevel.set(self.blacklevel)

        # set the acq buffer count
        self.camera.data_stream[0].set_acquisition_buffer_number(1)
        
        # set camera to mono12 mode
        # self.camera.PixelFormat.set(gx.GxPixelFormatEntry.MONO10)
        # set camera to mono8 mode
        self.camera.PixelFormat.set(gx.GxPixelFormatEntry.MONO8)
        
        # register the frame callback
        user_param = None
        self.camera.register_capture_callback(user_param, self.set_frame)

        '''
    def start_live(self):
        if not self.is_streaming:
            # start data acquisition
            self.g_bExit = False
            # Start grab image
            ret = self.camera.MV_CC_StartGrabbing()
            self.__logger.debug("start grabbing")
            self.__logger.debug(ret)
            try:
                self.hThreadHandle = threading.Thread(target=self.work_thread, args=(self.camera, None, None))
                self.hThreadHandle.start()
            except Exception:
                self.__logger.error("Coul dnot start frame grabbing")
            
            if ret != 0:
                self.__logger.debug("start grabbing fail! ret[0x%x]" % ret)
                return
            self.is_streaming = True

    def stop_live(self):
        if self.is_streaming:
            # stop data acquisition
            self.g_bExit = True
            self.hThreadHandle.join()
            self.is_streaming = False

    def suspend_live(self):
        if self.is_streaming:
        # start data acquisition
            try:
               # Stop grab image
                ret = self.camera.MV_CC_StopGrabbing()
            except:
                pass
            self.is_streaming = False
        
    def prepare_live(self):
        pass

    def close(self):
        ret = self.camera.MV_CC_CloseDevice()
        ret = self.camera.MV_CC_DestroyHandle()
    
    def set_exposure_time(self,exposure_time):
        self.exposure_time = exposure_time
        self.camera.MV_CC_SetFloatValue("ExposureTime", self.exposure_time*1000)
        
    def set_exposure_mode(self, exposure_mode="manual"):
        if exposure_mode == "manual":
            self.camera.MV_CC_SetEnumValue("ExposureAuto", MV_EXPOSURE_AUTO_MODE_OFF)
        elif exposure_mode == "auto":
            self.camera.MV_CC_SetEnumValue("ExposureAuto", MV_EXPOSURE_AUTO_MODE_CONTINUOUS)
        elif exposure_mode == "once":
            self.camera.MV_CC_SetEnumValue("ExposureAuto", MV_EXPOSURE_AUTO_MODE_ONCE)
        else:
            self.__logger.warning("Exposure mode not recognized")
                    
            
    def set_gain(self,gain):
        self.gain = gain
        self.camera.MV_CC_SetFloatValue("Gain", self.gain)

    def set_frame_rate(self, frame_rate):
        ret = self.camera.MV_CC_SetBoolValue("AcquisitionFrameRateEnable", True)
        if ret != 0:
            self._logger.error("set AcquisitionFrameRateEnable fail! ret[0x%x]" % ret)
        ret = self.camera.MV_CC_SetFloatValue("AcquisitionFrameRate", 5.0)
        if ret != 0:
            self._logger.error("set AcquisitionFrameRate fail! ret[0x%x]" % ret)
    
    def set_flatfielding(self, is_flatfielding):
        self.isFlatfielding = is_flatfielding
        # record the flatfield image if needed
        if self.isFlatfielding:
            self.recordFlatfieldImage() 
            
    def setFlatfieldImage(self, flatfieldImage, isFlatfieldEnabeled=True):
        '''
        Set a flatfield image to be used for flatfielding
        '''
        self.flatfieldImage = flatfieldImage
        self.isFlatfielding = isFlatfieldEnabeled
        
    def set_blacklevel(self,blacklevel):
        self.blacklevel = blacklevel
        self.camera.MV_CC_SetFloatValue("BlackLevel", self.blacklevel)

    def set_pixel_format(self,format):
        self.camera.MV_CC_SetEnumValue("PixelFormat", PixelType_Gvsp_Mono8_Signed)

    def setBinning(self, binning=1):
        # Unfortunately this does not work
        try:
            self.camera.MV_CC_SetIntValue("BinningX", binning)
            self.camera.MV_CC_SetIntValue("BinningY", binning)
            self.binning = binning
        except Exception as e:
            self._logger.error(e)

    def getLast(self, returnFrameNumber=False, timeout=1):
        # get frame and save 
        '''
        t0 = time.time()
        while(self.lastFrameId >= self.frameNumber and self.frame is None):
            time.sleep(.01) # wait for fresh frame
            if time.time()-t0>timeout:
                return
        if self.isFlatfielding and self.flatfieldImage is not None:
            self.frame = self.frame/self.flatfieldImage
        self.lastFrameId = self.frameNumber
        print(self.frameNumber)
        '''
        cTime = time.time()
        while len(self.frame_buffer)==0:
            time.sleep(0.02)
            if time.time() - cTime > timeout:
                return None
        frame = self.frame_buffer[-1]
        frameNumber = self.frameid_buffer[-1]
        if returnFrameNumber:
            return np.array(frame), frameNumber
        return np.array(frame)  

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
        elif property_name == "exposure_mode":
            self.set_exposure_mode(property_value)
        elif property_name == "blacklevel":
            self.set_blacklevel(property_value)
        elif property_name == "roi_size":
            self.roi_size = property_value
        elif property_name == "frame_rate":
            self.set_frame_rate(property_value)
        elif property_name == "flat_fielding":
            self.set_flatfielding(property_value)
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
        elif property_name == "exposure_mode":
            property_value = self.camera.ExposureAuto.get()
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
        pass

    def send_trigger(self):
        pass

    def openPropertiesGUI(self):
        pass
    
    def work_thread(self, cam=0, pData=0, nDataSize=0):
        if platform == "win32":

            if self.isRGB:
                stOutFrame = MV_FRAME_OUT()  
                memset(byref(stOutFrame), 0, sizeof(stOutFrame))
                memset(byref(self.stDeviceList), 0, sizeof(self.stDeviceList))
                

                while True:
                    if self.g_bExit == True:
                        break

                    ret = cam.MV_CC_GetImageBuffer(stOutFrame, 1000)
                    if None != stOutFrame.pBufAddr and 0 == ret :
                        
                        nRGBSize = stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight * 3
                        stConvertParam = MV_CC_PIXEL_CONVERT_PARAM_EX()
                        memset(byref(stConvertParam), 0, sizeof(stConvertParam))
                        stConvertParam.nWidth = stOutFrame.stFrameInfo.nWidth
                        stConvertParam.nHeight = stOutFrame.stFrameInfo.nHeight
                        stConvertParam.pSrcData = stOutFrame.pBufAddr
                        stConvertParam.nSrcDataLen = stOutFrame.stFrameInfo.nFrameLen
                        stConvertParam.enSrcPixelType = stOutFrame.stFrameInfo.enPixelType  
                        stConvertParam.enDstPixelType = PixelType_Gvsp_RGB8_Packed
                        stConvertParam.pDstBuffer = (c_ubyte * nRGBSize)()
                        stConvertParam.nDstBufferSize = nRGBSize

                        ret = cam.MV_CC_ConvertPixelTypeEx(stConvertParam)
                        if ret != 0:
                            self.__logger.error("convert pixel fail! ret[0x%x]" % ret)
                            return

                        cam.MV_CC_FreeImageBuffer(stOutFrame)

                        try:
                            img_buff = (c_ubyte * stConvertParam.nDstLen)()
                            cdll.msvcrt.memcpy(byref(img_buff), stConvertParam.pDstBuffer, stConvertParam.nDstLen)
                            
                            data = np.frombuffer(img_buff, count=int(nRGBSize),dtype=np.uint8)
                            self.frame = data.reshape((stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nWidth, -1))
                            self.SensorHeight, self.SensorWidth = self.frame.shape[0], self.frame.shape[1] #stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nWidth
                            self.frameNumber = stOutFrame.stFrameInfo.nFrameNum
                            self.timestamp = time.time()
                            self.frame_buffer.append(self.frame)
                            self.frameid_buffer.append(self.frameNumber)
                            
                        except Exception as e:
                            self.__logger.error(e)
                        finally:
                            pass
                    

            else:
                stOutFrame = MV_FRAME_OUT()  # 
                memset(byref(stOutFrame), 0, sizeof(stOutFrame))
                while True:
                    ret = cam.MV_CC_GetImageBuffer(stOutFrame, 1000)
                    if None != stOutFrame.pBufAddr and 0 == ret:
                        nRet = cam.MV_CC_FreeImageBuffer(stOutFrame)

                        pData = (c_ubyte * stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight)()
                        cdll.msvcrt.memcpy(byref(pData), stOutFrame.pBufAddr,
                                stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight)
                        data = np.frombuffer(pData, count=int(stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight),
                                    dtype=np.uint8)
                        self.frame = data.reshape((stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nWidth))

                        self.SensorHeight, self.SensorWidth = self.frame.shape[0], self.frame.shape[1] #stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nWidth
                        self.frameNumber = stOutFrame.stFrameInfo.nFrameNum 
                        self.timestamp = time.time()
                        self.frame_buffer.append(self.frame)
                        self.frameid_buffer.append(self.lastFrameId)
                    else:
                        pass 
                    if self.g_bExit == True:
                        break

        if platform in ("darwin", "linux2", "linux"):
            
            # en:Get payload size
            stParam =  MVCC_INTVALUE()
            memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))
            
            ret = cam.MV_CC_GetIntValue("PayloadSize", stParam)
            if ret != 0:
                self.__logger.error("get payload size fail! ret[0x%x]" % ret)
            
            nPayloadSize = stParam.nCurValue
            stDeviceList = MV_FRAME_OUT_INFO_EX()
            memset(byref(stDeviceList), 0, sizeof(stDeviceList))
            data_buf = (c_ubyte * nPayloadSize)()

            ret = cam.MV_CC_GetOneFrameTimeout(byref(data_buf), nPayloadSize, stDeviceList, 1000)
            while True:
                if self.isRGB:
                    try:
                        stDeviceList = MV_FRAME_OUT_INFO_EX()
                        memset(byref(stDeviceList), 0, sizeof(stDeviceList))
                        data_buf = (c_ubyte * nPayloadSize)()

                        ret = cam.MV_CC_GetOneFrameTimeout(byref(data_buf), nPayloadSize, stDeviceList, 1000)
                        if ret == 0:
                            
                            nRGBSize = stDeviceList.nWidth * stDeviceList.nHeight*3
                            
                            stConvertParam = MV_CC_PIXEL_CONVERT_PARAM()
                            memset(byref(stConvertParam), 0, sizeof(stConvertParam))
                            stConvertParam.nWidth = stDeviceList.nWidth
                            stConvertParam.nHeight = stDeviceList.nHeight
                            stConvertParam.pSrcData = data_buf
                            stConvertParam.nSrcDataLen = stDeviceList.nFrameLen
                            stConvertParam.enSrcPixelType = stDeviceList.enPixelType  
                            stConvertParam.enDstPixelType = PixelType_Gvsp_RGB8_Packed 
                            stConvertParam.pDstBuffer = (c_ubyte * nRGBSize)()
                            stConvertParam.nDstBufferSize = nRGBSize
                            
                            ret = cam.MV_CC_ConvertPixelType(stConvertParam)

                            if ret != 0:
                                self.__logger.error("convert pixel fail! ret[0x%x]" % ret)
                                del data_buf
                                sys.exit()
                                
                            img_buff = (c_ubyte * stConvertParam.nDstLen)()
                            memmove(byref(img_buff), stConvertParam.pDstBuffer, stConvertParam.nDstLen)

                            data = np.frombuffer(img_buff, count=int(nRGBSize),dtype=np.uint8)
                            self.frame = data.reshape((stDeviceList.nHeight, stDeviceList.nWidth, -1))
                            

                    except:
                        pass
                else:
                    img_buff = (c_ubyte * nPayloadSize)()
                    ret = cam.MV_CC_GetOneFrameTimeout(byref(data_buf), nPayloadSize, stDeviceList, 100)
                    data = np.frombuffer(data_buf, count=int(stDeviceList.nWidth * stDeviceList.nHeight), dtype=np.uint8)
                    self.frame = data.reshape((stDeviceList.nHeight, stDeviceList.nWidth))

                self.SensorHeight, self.SensorWidth = stDeviceList.nWidth, stDeviceList.nHeight  
                self.frameNumber = stDeviceList.nFrameNum
                self.timestamp = time.time()
                self.frame_buffer.append(self.frame)
                self.frameid_buffer.append(self.lastFrameId)
                
                if self.g_bExit == True:
                    break


    def recordFlatfieldImage(self, nFrames=10, nGauss=5, nMedian=5):
        # record a flatfield image and save it in the flatfield variable
        for iFrame in range(nFrames):
            frame = self.getLast()
            if iFrame == 0:
                flatfield = frame
            else:
                flatfield += frame
        # normalize and smooth using scikit image
        flatfield = flatfield/nFrames
        flatfield = gaussian(flatfield, sigma=nGauss)
        flatfield = median(flatfield, selem=np.ones((nMedian, nMedian)))
        self.flatfieldImage = flatfield
        
        
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