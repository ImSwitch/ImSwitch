# -- coding: utf-8 --

import sys
import threading
import msvcrt

from ctypes import *

sys.path.append("../MvImport")
from MvCameraControl_class import *

g_bExit = False

# 为线程定义一个函数
def work_thread(cam=0, pData=0, nDataSize=0):
    stOutFrame = MV_FRAME_OUT()  
    memset(byref(stOutFrame), 0, sizeof(stOutFrame))

    stInputFrameInfo = MV_CC_INPUT_FRAME_INFO()
    memset(byref(stInputFrameInfo), 0 ,sizeof(MV_CC_INPUT_FRAME_INFO))
    while True:
        ret = cam.MV_CC_GetImageBuffer(stOutFrame, 1000)
        if None != stOutFrame.pBufAddr and 0 == ret:
            print ("get one frame: Width[%d], Height[%d], nFrameNum[%d]"  % (stOutFrame.stFrameInfo.nWidth, stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nFrameNum))
            stInputFrameInfo.pData = cast(stOutFrame.pBufAddr, POINTER(c_ubyte))
            stInputFrameInfo.nDataLen = stOutFrame.stFrameInfo.nFrameLen
            # ch:输入一帧数据到录像接口 | en:Input a frame of data to the video interface
            ret = cam.MV_CC_InputOneFrame(stInputFrameInfo)
            if ret != 0:
                print ("input one frame fail! nRet [0x%x]" % ret)
            nRet = cam.MV_CC_FreeImageBuffer(stOutFrame)
        else:
            print ("no data[0x%x]" % ret)
        if g_bExit == True:
                break

if __name__ == "__main__":

    deviceList = MV_CC_DEVICE_INFO_LIST()
    tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
    
    # ch:枚举设备 | en:Enum device
    ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
    if ret != 0:
        print ("enum devices fail! ret[0x%x]" % ret)
        sys.exit()

    if deviceList.nDeviceNum == 0:
        print ("find no device!")
        sys.exit()

    print ("Find %d devices!" % deviceList.nDeviceNum)

    for i in range(0, deviceList.nDeviceNum):
        mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
        if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
            print ("\ngige device: [%d]" % i)
            strModeName = ""
            for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
                strModeName = strModeName + chr(per)
            print ("device model name: %s" % strModeName)

            nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
            nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
            nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
            nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
            print ("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
        elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
            print ("\nu3v device: [%d]" % i)
            strModeName = ""
            for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
                if per == 0:
                    break
                strModeName = strModeName + chr(per)
            print ("device model name: %s" % strModeName)

            strSerialNumber = ""
            for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                if per == 0:
                    break
                strSerialNumber = strSerialNumber + chr(per)
            print ("user serial number: %s" % strSerialNumber)

    nConnectionNum = input("please input the number of the device to connect:")

    if int(nConnectionNum) >= deviceList.nDeviceNum:
        print ("intput error!")
        sys.exit()

    # ch:创建相机实例 | en:Creat Camera Object
    cam = MvCamera()
    
    # ch:选择设备并创建句柄 | en:Select device and create handle
    stDeviceList = cast(deviceList.pDeviceInfo[int(nConnectionNum)], POINTER(MV_CC_DEVICE_INFO)).contents

    ret = cam.MV_CC_CreateHandle(stDeviceList)
    if ret != 0:
        print ("create handle fail! ret[0x%x]" % ret)
        sys.exit()

    # ch:打开设备 | en:Open device
    ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
    if ret != 0:
        print ("open device fail! ret[0x%x]" % ret)
        sys.exit()
    
    # ch:探测网络最佳包大小(只对GigE相机有效) | en:Detection network optimal package size(It only works for the GigE camera)
    if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
        nPacketSize = cam.MV_CC_GetOptimalPacketSize()
        if int(nPacketSize) > 0:
            ret = cam.MV_CC_SetIntValue("GevSCPSPacketSize",nPacketSize)
            if ret != 0:
                print ("Warning: Set Packet Size fail! ret[0x%x]" % ret)
        else:
            print ("Warning: Get Packet Size fail! ret[0x%x]" % nPacketSize)

    stBool = c_bool(False)
    ret =cam.MV_CC_GetBoolValue("AcquisitionFrameRateEnable", stBool)
    if ret != 0:
        print ("get AcquisitionFrameRateEnable fail! ret[0x%x]" % ret)

    # ch:设置触发模式为off | en:Set trigger mode as off
    ret = cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
    if ret != 0:
        print ("set trigger mode fail! ret[0x%x]" % ret)
        sys.exit()

    stParam =  MVCC_INTVALUE()
    memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))
    stRecordPar = MV_CC_RECORD_PARAM()
    memset(byref(stRecordPar), 0, sizeof(MV_CC_RECORD_PARAM))
    # ch:获取图像高度 | en:Get the width of the image
    ret = cam.MV_CC_GetIntValue("Width", stParam)
    if ret != 0: 
        print ("get width fail! nRet [0x%x]" % ret)
        sys.exit()
    stRecordPar.nWidth = stParam.nCurValue

    # ch:获取图像高度 | en:Get the height of the image
    ret = cam.MV_CC_GetIntValue("Height", stParam)
    if ret != 0: 
        print ("get height fail! nRet [0x%x]"% ret)
        sys.exit()
    stRecordPar.nHeight = stParam.nCurValue

    # ch:获取图像像素 | en:Get the pixelFormat of the image
    stEnumValue = MVCC_ENUMVALUE()
    memset(byref(stEnumValue), 0 ,sizeof(MVCC_ENUMVALUE))
    ret = cam.MV_CC_GetEnumValue("PixelFormat", stEnumValue)
    if ret != 0: 
        print ("get PixelFormat fail! nRet [0x%x]" % ret)
        sys.exit()
    stRecordPar.enPixelType = MvGvspPixelType(stEnumValue.nCurValue)

    # ch:获取图像帧率 | en:Get the resultingFrameRate of the image
    stFloatValue = MVCC_FLOATVALUE()
    memset(byref(stFloatValue), 0 ,sizeof(MVCC_FLOATVALUE))
    ret = cam.MV_CC_GetFloatValue("ResultingFrameRate", stFloatValue)
    if ret != 0: 
        print ("get ResultingFrameRate value fail! nRet [0x%x]" % ret)
        sys.exit()
    stRecordPar.fFrameRate = stFloatValue.fCurValue

    # ch:录像结构体赋值 | en:Video structure assignment
    stRecordPar.nBitRate = 1000
    stRecordPar.enRecordFmtType = MV_FormatType_AVI
    stRecordPar.strFilePath= 'Recording.avi'.encode('ascii')

    # ch:开始录像 | en:Start Recording
    nRet = cam.MV_CC_StartRecord(stRecordPar)
    if ret != 0: 
        print ("Start Record fail! nRet [0x%x]\n", nRet)
        sys.exit()

    # ch:开始取流 | en:Start grab image
    ret = cam.MV_CC_StartGrabbing()
    if ret != 0:
        print ("start grabbing fail! ret[0x%x]" % ret)
        sys.exit()

    try:
        hThreadHandle = threading.Thread(target=work_thread, args=(cam, None, None))
        hThreadHandle.start()
    except:
        print ("error: unable to start thread")
        
    print ("press a key to stop grabbing.")
    msvcrt.getch()

    g_bExit = True
    hThreadHandle.join()

    # ch:停止取流 | en:Stop grab image
    ret = cam.MV_CC_StopGrabbing()
    if ret != 0:
        print ("stop grabbing fail! ret[0x%x]" % ret)
        sys.exit()

    # ch:停止录像 | en:Stop recording
    ret = cam.MV_CC_StopRecord()
    if ret != 0:
        print ("stop Record fail! ret[0x%x]" % ret)
        sys.exit()

    # ch:关闭设备 | Close device
    ret = cam.MV_CC_CloseDevice()
    if ret != 0:
        print ("close deivce fail! ret[0x%x]" % ret)
        sys.exit()

    # ch:销毁句柄 | Destroy handle
    ret = cam.MV_CC_DestroyHandle()
    if ret != 0:
        print ("destroy handle fail! ret[0x%x]" % ret)
        sys.exit()

