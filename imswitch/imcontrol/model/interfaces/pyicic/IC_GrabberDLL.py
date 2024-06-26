#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ctypes.util
from ctypes import *
import os
import sys

from . import IC_Structures as structs


class IC_GrabberDLL:
    """
    ctypes funcs to talk to tisgrabber.dll.
    """
    
    GrabberHandlePtr = POINTER(structs.GrabberHandle)
    
    # win64
    if sys.maxsize > 2**32:
        # _ic_grabber_dll = windll.LoadLibrary(ctypes.util.find_library('tisgrabber_x64.dll'))
        _ic_grabber_dll = cdll.LoadLibrary("tisgrabber_x64.dll")

    # win32
    else:
        _ic_grabber_dll = windll.LoadLibrary(ctypes.util.find_library('tisgrabber.dll'))


    #//////////////////////////////////////////////////////////////////////////
    #/*! Initialize the ICImagingControl class library. This function must be called
    #    only once before any other functions of this library are called.
    #    @param szLicenseKey IC Imaging Control license key or NULL if only a trial version is available.
    #    @retval IC_SUCCESS on success.
    #    @retval IC_ERROR on wrong license key or other errors.
    #    @sa IC_CloseLibrary
    #
    #*/
    #int AC IC_InitLibrary( char* szLicenseKey );///<Initialize the library.
    init_library = _ic_grabber_dll.IC_InitLibrary
    init_library.restype = c_int
    init_library.argtypes = (c_char_p,)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Creates a new grabber handle and returns it. A new created grabber should be
    #    release with a call to IC_ReleaseGrabber if it is no longer needed.
    #    @retval Nonzero on success.
    #    @retval NULL if an error occurred.
    #    @sa IC_ReleaseGrabber
    #*/
    #HGRABBER AC IC_CreateGrabber();///<Create a new grabber handle
    create_grabber = _ic_grabber_dll.IC_CreateGrabber
    ###create_grabber.restype = GrabberHandle
    create_grabber.restype = GrabberHandlePtr
    create_grabber.argtypes = None
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Release the grabber object. Must be called, if the calling application
    #    does no longer need the grabber.
    #    @param hGrabber The handle to grabber to be released.
    #    @sa IC_CreateGrabber
    #*/
    #void AC IC_ReleaseGrabber( HGRABBER *hGrabber ); ///< Releas an HGRABBER object.
    release_grabber = _ic_grabber_dll.IC_ReleaseGrabber
    release_grabber.restype = None
    release_grabber.argtypes = (POINTER(GrabberHandlePtr),)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*    Must be called at the end of the application to release allocated memory.
    #    @sa IC_InitLibrary
    #*/
    #void AC IC_CloseLibrary(); ///< Closes the library, cleans up memory. 
    close_library = _ic_grabber_dll.IC_CloseLibrary
    close_library.restype = None
    close_library.argtypes = None
        
    #//////////////////////////////////////////////////////////////////////////
    #/*! Open a video capture device. The hGrabber handle must have been created previously by
    #    a call to IC_CreateGrabber(). Once a hGrabber handle has been created it can be
    #    recycled to open different video capture devices in sequence. 
    #    @param hGrabber The handle to grabber object, that has been created by a call to IC_CreateGrabber
    #    @param szDeviceName Friendly name of the video capture device e.g. "DFK 21F04".
    #    @retval IC_SUCCESS on success.
    #    @retval IC_ERROR on errors.
    #    @sa IC_CloseVideoCaptureDevice
    #
    #    @code
    #    #include "tisgrabber.h"
    #    void main()
    #    {
    #        HGRABBER hGrabber;
    #        if( IC_InitLibrary(0) == IC_SUCCESS )
    #        {
    #            hGrabber = IC_CreateGrabber();
    #            if( hGrabber )
    #            {
    #                if( IC_OpenVideoCaptureDevice(hGrabber,"DFK 21F04") == IC_SUCCESS )
    #                {
    #
    #                // .. do something with the video capture device.
    #
    #                // Now clean up.
    #                IC_CloseVideoCaptureDevice( hGrabber );
    #                IC_ReleaseGrabber( hGrabber );
    #            }
    #            IC_CloseLibrary();
    #        }
    #    }
    #    @endcode
    #*/
    #int AC IC_OpenVideoCaptureDevice( HGRABBER hGrabber, char *szDeviceName ); ///< Opens a video capture device.
    open_device = _ic_grabber_dll.IC_OpenVideoCaptureDevice
    open_device.restype = c_int                                
    open_device.argtypes = (GrabberHandlePtr,            
                            c_char_p)                        
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Close the current video capture device. The HGRABBER object will not be deleted.
    #    It can be used again for opening another video capture device.
    #    @param hGrabber The handle to the grabber object.
    #*/
    #void AC IC_CloseVideoCaptureDevice( HGRABBER hGrabber ); ///<Closes a video capture device.
    close_device = _ic_grabber_dll.IC_CloseVideoCaptureDevice
    close_device.restype = None
    close_device.argtypes = (GrabberHandlePtr,)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Retrieve the name of the current video capture device. If the device is
    #    invalid, NULL is returned.
    #    @param hGrabber The handle to the grabber object.
    #    @retval char* The name of the video capture device
    #    @retval NULL  If no video capture device is currently opened.
    #*/
    #char* AC IC_GetDeviceName(HGRABBER hGrabber ); ///<Returns the name of the current video capture device.
    get_device_name = _ic_grabber_dll.IC_GetDeviceName
    get_device_name.restype = c_char_p
    get_device_name.argtypes = (GrabberHandlePtr,)
    
    #int AC IC_GetVideoFormatWidth( HGRABBER hGrabber); ///<Returns the width of the video format.
    get_video_format_width = _ic_grabber_dll.IC_GetVideoFormatWidth
    get_video_format_width.restype = c_int
    get_video_format_width.argtypes = (GrabberHandlePtr,)
    
    #int AC IC_GetVideoFormatHeight( HGRABBER hGrabber);///<returns the height of the video format.
    get_video_format_height = _ic_grabber_dll.IC_GetVideoFormatHeight
    get_video_format_height.restype = c_int
    get_video_format_height.argtypes = (GrabberHandlePtr,)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Set the sink type. A sink type must be set before images can be snapped.
    #    The sink type basically describes the format of the buffer where the snapped 
    #    images are stored. 
    #
    #    Possible values for format are:
    #    @li Y800    
    #    @li RGB24
    #    @li RGB32
    #    @li UYVY
    #
    #    The sink type may differ from the currently set video format.
    #
    #    @param hGrabber The handle to the grabber object.
    #    @param format The desired color format. Possible values for format are:
    #        @li Y800    
    #        @li RGB24
    #        @li RGB32
    #        @li UYVY
    #    @retval IC_SUCCESS on success
    #    @retval IC_ERROR if something went wrong.
    #
    #    @note Please note that UYVY can only be used in conjunction with a UYVY video format.
    #
    #
    #*/
    #int AC IC_SetFormat( HGRABBER hGrabber, COLORFORMAT format ); ///< Sets the color format of the sink. 
    set_format = _ic_grabber_dll.IC_SetFormat
    set_format.restype = c_int
    set_format.argtypes = (GrabberHandlePtr,
                           #structs.ColorFormat)
                           c_int) # todo enum
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Retrieves the format of the sink type currently set (See IC_SetFormat()
    #    for possible formats). If no sink type is set
    #    or an error occurred, NONE is returned.
    #    @param hGrabber The handle to the grabber object.
    #    @return The current sink color format.
    #*/
    #COLORFORMAT AC IC_GetFormat( HGRABBER hGrabber ); ///<Returns the current color format of the sink.
    get_format = _ic_grabber_dll.IC_GetFormat
    #get_format.restype = structs.ColorFormat
    get_format.restype = c_int # todo enum
    get_format.argtypes = (GrabberHandlePtr,)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Set a video format for the current video capture device. The video format
    #    must be supported by the current video capture device.
    #    @param hGrabber The handle to the grabber object.
    #    @param szFormat A string that contains the desired video format.
    #    @retval IC_SUCCESS on success
    #    @retval IC_ERROR if something went wrong.
    #
    #    @code
    #    #include "tisgrabber.h"
    #    void main()
    #    {
    #        HGRABBER hGrabber;
    #        if( IC_InitLibrary(0) == IC_SUCCESS )
    #        {
    #            hGrabber = IC_CreateGrabber();
    #            if( hGrabber )
    #            {
    #                if( IC_OpenVideoCaptureDevice(hGrabber,"DFK 21F04") == IC_SUCCESS )
    #                {
    #                    if( IC_SetVideoFormat(hGrabber,"UYVY (640x480)" == IC_SUCCESS )
    #                    {
    #                        // .. do something with the video capture device.
    #                    }
    #                    // Now clean up.
    #                    IC_CloseVideoCaptureDevice( hGrabber );
    #                    IC_ReleaseGrabber( hGrabber );
    #                }
    #                IC_CloseLibrary();
    #            }
    #        }
    #    }
    #    @endcode
    #*/
    #int AC IC_SetVideoFormat( HGRABBER hGrabber, char *szFormat ); ///<Sets the video format.
    set_video_format = _ic_grabber_dll.IC_SetVideoFormat
    set_video_format.restype = c_int
    set_video_format.argtypes = (GrabberHandlePtr,
                                 c_char_p)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Set a video norm for the current video capture device.
    #    @note  The current video capture device must support video norms. 
    #    @param hGrabber The handle to the grabber object.
    #    @param szNorm A string that contains the desired video format.
    #    @retval IC_SUCCESS on success
    #    @retval IC_ERROR if something went wrong.
    #*/
    #int AC IC_SetVideoNorm( HGRABBER hGrabber, char *szNorm ); ///<Set the video norm.
    set_video_norm = _ic_grabber_dll.IC_SetVideoNorm
    set_video_norm.restype = c_int
    set_video_norm.restype = c_int
    set_video_norm.argtypes = (GrabberHandlePtr,
                               c_char_p)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Set a input channel for the current video capture device. 
    #    @note  The current video capture device must support input channels.. 
    #    @param hGrabber The handle to the grabber object.
    #    @param szChannel A string that contains the desired video format.
    #    @retval IC_SUCCESS on success
    #    @retval IC_ERROR if something went wrong.
    #*/
    #int AC IC_SetInputChannel( HGRABBER hGrabber, char *szChannel ); ///<Sets an input channel.
    #
    #
    #//////////////////////////////////////////////////////////////////////////
    #/*! Start the live video. 
    #    @param hGrabber The handle to the grabber object.
    #    @param iShow The parameter indicates:   @li 1 : Show the video    @li 0 : Do not show the video, but deliver frames. (For callbacks etc.)
    #    @retval IC_SUCCESS on success
    #    @retval IC_ERROR if something went wrong.
    #    @sa IC_StopLive
    #*/
    #int AC IC_StartLive( HGRABBER hGrabber, int iShow ); ///<Starts the live video.
    start_live = _ic_grabber_dll.IC_StartLive
    start_live.restype = c_int
    start_live.argtypes = (GrabberHandlePtr,
                           c_int)
    
    #int AC IC_PrepareLive( HGRABBER hGrabber, int iShow); ///<Prepare the grabber for starting the live video.
    prepare_live = _ic_grabber_dll.IC_PrepareLive
    prepare_live.restype = c_int
    prepare_live.argtypes = (GrabberHandlePtr,
                             c_int)
        
    #int AC IC_SuspendLive(HGRABBER hGrabber); ///<Suspends an image stream and puts it into prepared state. 
    suspend_live = _ic_grabber_dll.IC_SuspendLive
    suspend_live.restype = c_int
    suspend_live.argtypes = (GrabberHandlePtr,)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Stop the live video.
    #    @param hGrabber The handle to the grabber object.
    #    @sa IC_StartLive
    #*/
    #void AC IC_StopLive( HGRABBER hGrabber ); ///<Stops the live video.
    stop_live = _ic_grabber_dll.IC_StopLive
    stop_live.restype = None
    stop_live.argtypes = (GrabberHandlePtr,)
    
    #int AC IC_IsCameraPropertyAvailable( HGRABBER hGrabber, CAMERA_PROPERTY eProperty ); ///< Check whether a camera property is available.
    is_camera_property_available = _ic_grabber_dll.IC_IsCameraPropertyAvailable
    is_camera_property_available.restype = c_int
    is_camera_property_available.argtypes = (GrabberHandlePtr,
                                             c_int)    
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Set a camera property like exposure, zoom.
    #    
    #    @param hGrabber The handle to the grabber object.
    #    @param eProperty The property to be set. It can have following values:
    #        @li PROP_CAM_PAN    
    #        @li PROP_CAM_TILT,
    #        @li PROP_CAM_ROLL,
    #        @li PROP_CAM_ZOOM,
    #        @li PROP_CAM_EXPOSURE,
    #        @li PROP_CAM_IRIS,
    #        @li PROP_CAM_FOCUS
    #    @param lValue The value the property is to be set to.
    #    @retval IC_SUCCESS on success
    #    @retval IC_ERROR if something went wrong.
    #
    #    @note  lValue should be in the range of the specified property.
    #    If the value could not be set (out of range, auto is currently enabled), the
    #    function returns 0. On success, the functions returns 1.
    #*/
    #int AC IC_SetCameraProperty( HGRABBER hGrabber, CAMERA_PROPERTY eProperty, long lValue ); ///< Set a camera property.
    set_camera_property = _ic_grabber_dll.IC_SetCameraProperty
    set_camera_property.restype = c_int
    set_camera_property.argtypes = (GrabberHandlePtr,
                                    c_int,
                                    c_long)
    
    #int AC IC_CameraPropertyGetRange( HGRABBER hGrabber, CAMERA_PROPERTY eProperty, long *lMin, long *lMax); ///<Get the minimum and maximum value of a camera property
    camera_property_get_range = _ic_grabber_dll.IC_CameraPropertyGetRange
    camera_property_get_range.restype = c_int
    camera_property_get_range.argtypes = (GrabberHandlePtr,
                                          c_int,
                                          POINTER(c_long),
                                          POINTER(c_long))
                                          
    #int AC IC_GetCameraProperty( HGRABBER hGrabber, CAMERA_PROPERTY eProperty, long *lValue);  ///< Get a camera property's value.
    get_camera_property = _ic_grabber_dll.IC_GetCameraProperty
    get_camera_property.restype = c_int
    get_camera_property.argtypes = (GrabberHandlePtr,
                                    c_int,
                                    POINTER(c_long))
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Enable or disable automatic for a camera property. 
    #    @param hGrabber The handle to the grabber object.
    #    @param iProperty  The property to be set. It can have following values:
    #    @li PROP_CAM_PAN    
    #    @li PROP_CAM_TILT,
    #    @li PROP_CAM_ROLL,
    #    @li PROP_CAM_ZOOM,
    #    @li PROP_CAM_EXPOSURE,
    #    @li PROP_CAM_IRIS,
    #    @li PROP_CAM_FOCUS
    #    @param iOnOFF Enables or disables the automation. Possible values ar
    #    @li 1 : Enable automatic
    #    @li 0 : Disable Automatic
    #    @retval IC_SUCCESS on success
    #    @retval IC_ERROR if something went wrong.
    #
    #    @note If the property is not supported by the current video capture device or
    #    automation of the property is not available with the current video capture
    #    device, the function returns 0. On success, the function returns 1.
    #*/
    #int AC IC_EnableAutoCameraProperty( HGRABBER hGrabber, int iProperty, int iOnOff ); ///<Enables or disables property automation.
    enable_auto_camera_property = _ic_grabber_dll.IC_EnableAutoCameraProperty
    enable_auto_camera_property.restype = c_int
    enable_auto_camera_property.argtypes = (GrabberHandlePtr,
                                           c_int,
                                           c_int)
    
    #int AC IC_IsCameraPropertyAutoAvailable( HGRABBER hGrabber, CAMERA_PROPERTY iProperty ); ///<Check whether automation for a camera property is available.
    is_camera_property_auto_available = _ic_grabber_dll.IC_IsCameraPropertyAutoAvailable
    is_camera_property_auto_available.restype = c_int
    is_camera_property_auto_available.argtypes = (GrabberHandlePtr,
                                                  c_int)
    
    #int AC IC_GetAutoCameraProperty( HGRABBER hGrabber, int iProperty, int *iOnOff ); ///<Retrieve whether automatic is enabled for the specifield camera property.
    get_auto_camera_property = _ic_grabber_dll.IC_GetAutoCameraProperty
    get_auto_camera_property.restype = c_int
    get_auto_camera_property.argtypes = (GrabberHandlePtr,
                                         c_int,
                                         POINTER(c_int))
    
    
    #int AC IC_IsVideoPropertyAvailable( HGRABBER hGrabber, VIDEO_PROPERTY eProperty ); ///<Check whether the specified video property is available.
    is_video_property_available = _ic_grabber_dll.IC_IsVideoPropertyAvailable
    is_video_property_available.restype = c_int
    is_video_property_available.argtypes = (GrabberHandlePtr,
                                            c_int)      # todo
    
    #int AC IC_VideoPropertyGetRange( HGRABBER hGrabber, VIDEO_PROPERTY eProperty, long *lMin, long *lMax); ///<Retrieve the lower and upper limit of a video property.
    video_property_get_range = _ic_grabber_dll.IC_VideoPropertyGetRange
    video_property_get_range.restype = c_int
    video_property_get_range.argtypes = (GrabberHandlePtr,
                                         c_int,    # todo
                                         POINTER(c_long),
                                         POINTER(c_long))
    
    #int AC IC_GetVideoProperty( HGRABBER hGrabber, VIDEO_PROPERTY eProperty, long *lValue ); ///< Retrieve the the current value of the specified video property.
    get_video_property = _ic_grabber_dll.IC_GetVideoProperty
    get_video_property.restype = c_int
    get_video_property.argtypes = (GrabberHandlePtr,
                                   c_int,   # todo
                                   POINTER(c_long))
    
    #int AC IC_IsVideoPropertyAutoAvailable( HGRABBER hGrabber, VIDEO_PROPERTY eProperty ); ///<Check whether the specified video property supports automation.
    is_video_property_auto_available = _ic_grabber_dll.IC_IsVideoPropertyAutoAvailable
    is_video_property_auto_available.restype = c_int
    is_video_property_auto_available.argtypes = (GrabberHandlePtr,
                                                 c_int)     # todo    
    
    #int AC IC_GetAutoVideoProperty( HGRABBER hGrabber, int iProperty, int *iOnOff ); ///<Get the automation state of a video property.
    get_auto_video_property = _ic_grabber_dll.IC_GetAutoVideoProperty
    get_auto_video_property.restype = c_int
    get_auto_video_property.argtypes = (GrabberHandlePtr,
                                        c_int,   # todo enum
                                        POINTER(c_int))
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Set a video property like brightness, contrast.
    #
    #    @param hGrabber The handle to the grabber object.
    #    @param eProperty The property to be set. It can have following values:
    #    @li PROP_VID_BRIGHTNESS ,
    #    @li PROP_VID_CONTRAST,
    #    @li PROP_VID_HUE,
    #    @li PROP_VID_SATURATION,
    #    @li PROP_VID_SHARPNESS,
    #    @li PROP_VID_GAMMA,
    #    @li PROP_VID_COLORENABLE,
    #    @li PROP_VID_WHITEBALANCE,
    #    @li PROP_VID_BLACKLIGHTCOMPENSATION,
    #    @li PROP_VID_GAIN
    #    @param lValue The value the property is to be set to.
    #    @retval IC_SUCCESS on success
    #    @retval IC_ERROR if something went wrong.
    #
    #    @note lValue should be in the range of the specified property.
    #    If the value could not be set (out of range, auto is currently enabled), the
    #    function returns 0. On success, the functions returns 1.
    #*/
    #int AC IC_SetVideoProperty( HGRABBER hGrabber, VIDEO_PROPERTY eProperty, long lValue ); ///<Set a video property.
    set_video_property = _ic_grabber_dll.IC_SetVideoProperty
    set_video_property.restype = c_int
    set_video_property.argtypes = (GrabberHandlePtr,
                                   c_int,
                                   c_long)   # todo enum
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Enable or disable automatic for a video propertery.
    #    @param hGrabber The handle to the grabber object.
    #    @param iProperty The property to be set. It can have following values:
    #    @li PROP_VID_BRIGHTNESS,
    #    @li PROP_VID_CONTRAST,
    #    @li PROP_VID_HUE,
    #    @li PROP_VID_SATURATION,
    #    @li PROP_VID_SHARPNESS,
    #    @li PROP_VID_GAMMA,
    #    @li PROP_VID_COLORENABLE,
    #    @li PROP_VID_WHITEBALANCE,
    #    @li PROP_VID_BLACKLIGHTCOMPENSATION,
    #    @li PROP_VID_GAIN
    #    @param iOnOFF Enables or disables the automation. Possible values ar
    #    @li 1 : Enable automatic
    #    @li 0 : Disable Automatic
    #    @retval IC_SUCCESS on success
    #    @retval IC_ERROR if something went wrong.
    #
    #    @note If the property is not supported by the current video capture device or
    #    automation of the property is not available with the current video capture
    #    device, the function reurns 0. On success, the function returns 1.
    #*/
    #int AC IC_EnableAutoVideoProperty( HGRABBER hGrabber, int iProperty, int iOnOff ); ///< Switch automatition for a video property,
    enable_auto_video_property = _ic_grabber_dll.IC_EnableAutoVideoProperty
    enable_auto_video_property.restype = c_int
    enable_auto_video_property.argtypes = (GrabberHandlePtr,
                                           c_int,   # todo enum
                                           c_int)
    
    #
    #//////////////////////////////////////////////////////////////////////////
    #/*! Retrieve the properties of the current video format and sink type 
    #    @param hGrabber The handle to the grabber object.
    #    @param *lWidth  This recieves the width of the image buffer.
    #    @param *lHeight  This recieves the height of the image buffer.
    #    @param *iBitsPerPixel  This recieves the count of bits per pixel.
    #    @param *format  This recieves the current color format.
    #    @retval IC_SUCCESS on success
    #    @retval IC_ERROR if something went wrong.
    #*/
    #int AC IC_GetImageDescription( HGRABBER hGrabber, long *lWidth, long *lHeight, int *iBitsPerPixel, COLORFORMAT *format );///<Retrieve the properties of the current video format and sink typ.
    get_image_description = _ic_grabber_dll.IC_GetImageDescription
    get_image_description.restype = c_int
    get_image_description.argtypes = (GrabberHandlePtr,
                                      POINTER(c_long),
                                      POINTER(c_long),
                                      POINTER(c_int),
                                      POINTER(c_int))   # todo colorformat
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Snaps an image. The video capture device must be set to live mode and a 
    #    sink type has to be set before this call. The format of the snapped images depend on
    #    the selected sink type. 
    #
    #    @param hGrabber The handle to the grabber object.
    #    @param iTimeOutMillisek The Timeout time is passed in milli seconds. A value of -1 indicates, that
    #                            no time out is set.
    #
    #    
    #    @retval IC_SUCCESS if an image has been snapped
    #    @retval IC_ERROR if something went wrong.
    #    @retval IC_NOT_IN_LIVEMODE if the live video has not been started.
    #
    #    @sa IC_StartLive 
    #    @sa IC_SetFormat
    #
    #*/
    #int AC IC_SnapImage( HGRABBER hGrabber, int iTimeOutMillisek); ///<Snaps an image from the live stream. 
    snap_image = _ic_grabber_dll.IC_SnapImage
    snap_image.restype = c_int
    snap_image.argtypes = (GrabberHandlePtr,
                           c_int)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Save the contents of the last snapped image by IC_SnapImage into a file. 
    #    @param hGrabber The handle to the grabber object.
    #    @param szFileName String containing the file name to be saved to.
    #    @param ft File type if the image, It have be
    #        @li FILETYPE_BMP for bitmap files
    #        @li FILETYPE_JPEG for JPEG file.
    #    @param quality If the JPEG format is used, the image quality must be specified in a range from 0 to 100.
    #    @retval IC_SUCCESS if an image has been snapped
    #    @retval IC_ERROR if something went wrong.
    #
    #    @remarks
    #    The format of the saved images depend on the sink type. If the sink type 
    #    is set to Y800, the saved image will be an 8 Bit grayscale image. In any
    #    other case the saved image will be a 24 Bit RGB image.
    #
    #    @note IC Imaging Control 1.41 only supports FILETYPE_BMP.
    #    @sa IC_SnapImage
    #    @sa IC_SetFormat
    #*/
    #int AC IC_SaveImage( HGRABBER hGrabber, char *szFileName, IMG_FILETYPE ft, long quality ); ///< Saves an image to a file.
    save_image = _ic_grabber_dll.IC_SaveImage
    save_image.restype = c_int
    save_image.argtypes = (GrabberHandlePtr,
                           c_char_p,
                           c_int,    # 1 = jpeg
                           c_long)    # eg. 75 (75%)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Retrieve a byte pointer to the image data (pixel data) of the last snapped
    #    image (see SnapImage()). If the function fails, the return value is NULL
    #    otherwise the value is a pointer to the first byte in the lowest image line
    #    (the image is saved bottom up!).
    #    @param hGrabber The handle to the grabber object.
    #    @retval Nonnull Pointer to the image data
    #    @retval NULL Indicates that an error occurred.
    #    @sa IC_SnapImage
    #    @sa IC_SetFormat
    #*/
    #unsigned char* AC IC_GetImagePtr( HGRABBER hGrabber ); ///< Retuns a pointer to the image data
    get_image_ptr = _ic_grabber_dll.IC_GetImagePtr
    get_image_ptr.restype = POINTER(c_void_p)
    get_image_ptr.argtypes = (GrabberHandlePtr,)    
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Assign an Window handle to display the video in.
    #    @param hGrabber The handle to the grabber object.
    #    @param hWnd The handle of the window where to display the live video in.
    #    @retval IC_SUCCESS if an image has been snapped
    #    @retval IC_ERROR if something went wrong.
    #*/
    #int AC IC_SetHWnd( HGRABBER hGrabber, __HWND hWnd ); ///< Sets a window handle for live display
    #
    #
    #//////////////////////////////////////////////////////////////////////////
    #/*! Return the serialnumber of the current device. Memory for the serialnumber
    #    must has been allocated by the application:
    #
    #    @code
    #    char szSerial[20];
    #    GetSerialNumber( hGrabber, szSerial );
    #    @endcode
    #
    #    This function decodes the The Imaging Source serialnumbers.
    #    @param hGrabber The handle to the grabber object.
    #    @param szSerial char array that recieves the serial number.
    #*/
    #void AC IC_GetSerialNumber( HGRABBER hGrabber, char* szSerial );///<Return the video capture device's serial number.
    #get_serial_number = _ic_grabber_dll.IC_GetSerialNumber
    #get_serial_number.restype = None
    #get_serial_number.argtypes = (GrabberHandlePtr,
    #                              c_char_p)
    # ^ doesn't seem to work... returns consistent but wrong number...
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Count all connected video capture devices. If the Parameter szDeviceList
    #    is NULL, only the number of devices is queried. The Parameter szDeviceList
    #    must be a two dimensional array of char. The iSize parameter specifies the
    #    length of the strings, that are used in the array.
    #    
    #    @param szDeviceList A two dimensional char array that recieves the list. Or NULL if only the count of devices is to be returned.
    #    @param iSize Not used.
    #    @retval >= 0 Success, count of found devices
    #    @retval <0 An error occurred.
    #    
    #    Simple sample to list the video capture devices:
    #    @code
    #    char szDeviceList[20][40];
    #    int iDeviceCount;
    #
    #    iDeviceCount = IC_ListDevices( (char*)szDeviceList,40 );
    #    for( i = 0; i < iDeviceCount; i++ )
    #    {
    #        printf("%2d. %s\n",i+1,szDeviceList[i]);
    #    }
    #    @endcode
    #*/
    #int AC IC_ListDevices( char *szDeviceList, int iSize );///< Count and list devices.
    list_devices = _ic_grabber_dll.IC_ListDevices
    list_devices.restype = c_int
    list_devices.argtypes = (POINTER((c_char * 20) * 40),    # hardcoded 40 devices, each with 20 characters
                             c_int)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Count all available video formats. If the Parameter szFormatList
    #    is NULL, only the number of formats is queried. The Parameter szFormatList
    #    must be a two dimensional array of char. The iSize parameter specifies the
    #    length of the strings, that are used in the array to store the format names.
    #
    #    @param hGrabber The handle to the grabber object.
    #    @param szFormatList A two dimensional char array that recieves the list. Or NULL if only the count of formats is to be returned.
    #
    #    @retval >= 0 Success, count of found video formats
    #    @retval <0 An error occurred.
    #    
    #    Simple sample to list the video capture devices:
    #    @code
    #    char szFormatList[80][40];
    #    int iFormatCount;
    #    HGRABBER hGrabber;
    #    hGrabber = IC_CreateGrabber();
    #    IC_OpenVideoCaptureDevice(hGrabber, "DFK 21F04" );
    #    iFormatCount = IC_ListDevices(hGrabber, (char*)szFormatList,40 );
    #    for( i = 0; i < min( iFormatCount, 80); i++ )
    #    {
    #        printf("%2d. %s\n",i+1,szFormatList[i]);
    #    }
    #    IC_ReleaseGrabber( hGrabber );
    #    @endcode
    #*/
    #int AC IC_ListVideoFormats( HGRABBER hGrabber, char *szFormatList, int iSize );///<List available video formats.
    list_video_formats = _ic_grabber_dll.IC_ListVideoFormats
    list_video_formats.restype = c_int
    list_video_formats.argtypes = (GrabberHandlePtr,
                                   POINTER((c_char * 40) * 80),
                                   c_int)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Get the number of the currently available devices. This function creates an
    #    internal array of all connected video capture devices. With each call to this 
    #    function, this array is rebuild. The name and the unique name can be retrieved 
    #    from the internal array using the functions IC_GetDevice() and IC_GetUniqueNamefromList.
    #    They are usefull for retrieving device names for opening devices.
    #    
    #    @retval >= 0 Success, count of found devices.
    #    @retval <0 An error occurred.
    #
    #    @sa IC_GetDevice
    #    @sa IC_GetUniqueNamefromList
    #*/
    #int AC IC_GetDeviceCount(); ///<Get the number of the currently available devices. 
    get_device_count = _ic_grabber_dll.IC_GetDeviceCount
    get_device_count.restype = c_int
    
    #todo check that a static variable in class is fully live, ie a reference to it updates..
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Get a string representation of a device specified by iIndex. iIndex 
    #    must be between 0 and IC_GetDeviceCount(). IC_GetDeviceCount() must 
    #    have been called before this function, otherwise it will always fail.
    #    
    #    @param iIndex The number of the device whose name is to be returned. It must be
    #                  in the range from 0 to IC_GetDeviceCount(),
    #    @return Returns the string representation of the device on success, NULL
    #            otherwise.
    #
    #    @sa IC_GetDeviceCount
    #    @sa IC_GetUniqueNamefromList
    #*/
    #char* AC IC_GetDevice( int iIndex ); ///< Get the name of a video capture device.
    get_device = _ic_grabber_dll.IC_GetDevice
    get_device.restype = c_char_p
    get_device.argtypes = (c_int,)    
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Get unique device name of a device specified by iIndex. The unique device name
    #    consist from the device name and its serial number. It allows to differ between 
    #    more then one device of the same type connected to the computer. The unique device name
    #    is passed to the function IC_OpenDevByUniqueName
    #
    #    @param iIndex The number of the device whose name is to be returned. It must be
    #                in the range from 0 to IC_GetDeviceCount(),
    #    @return Returns the string representation of the device on success, NULL
    #                otherwise.
    #
    #    @sa IC_GetDeviceCount
    #    @sa IC_GetUniqueNamefromList
    #    @sa IC_OpenDevByUniqueName
    #*/
    #char* AC IC_GetUniqueNamefromList( int iIndex );///< Get the unique name of a video capture device.
    get_unique_name_from_list = _ic_grabber_dll.IC_GetUniqueNamefromList
    get_unique_name_from_list.restype = c_char_p
    get_unique_name_from_list.argtypes = (c_int,)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Get the number of the available input channels for the current device.
    #    A video    capture device must have been opened before this call.
    #
    #    @param hGrabber The handle to the grabber object.
    #
    #    @retval >= 0 Success
    #    @retval < 0 An error occured.
    #
    #    @sa IC_GetInputChannel
    #*/
    #int AC IC_GetInputChannelCount( HGRABBER hGrabber ); ///<Get the number of the available input channels.
    get_input_channel_count = _ic_grabber_dll.IC_GetInputChannelCount
    get_input_channel_count.restype = c_int
    get_input_channel_count.argtypes = (GrabberHandlePtr,)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Get a string representation of the input channel specified by iIndex. 
    #    iIndex must be between 0 and IC_GetInputChannelCount().
    #    IC_GetInputChannelCount() must have been called before this function,
    #    otherwise it will always fail.        
    #    @param hGrabber The handle to the grabber object.
    #    @param iIndex Number of the input channel to be used..
    #
    #    @retval Nonnull The name of the specified input channel
    #    @retval NULL An error occured.
    #    @sa IC_GetInputChannelCount
    #*/
    #char* AC IC_GetInputChannel( HGRABBER hGrabber, int iIndex ); ///<Get the name of an input channel.
    get_input_channel = _ic_grabber_dll.IC_GetInputChannel
    get_input_channel.restype = c_char_p
    get_input_channel.argtypes = (GrabberHandlePtr,
                                  c_int)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Get the number of the available video formats for the current device. 
    #    A video capture device must have been opened before this call.
    #    
    #    @param hGrabber The handle to the grabber object.
    #
    #    @retval >= 0 Success
    #    @retval < 0 An error occured.
    #    
    #    @sa IC_GetVideoNorm
    #*/
    #int AC IC_GetVideoNormCount( HGRABBER hGrabber ); ///<Get the count of available video norms.
    get_video_norm_count = _ic_grabber_dll.IC_GetVideoNormCount
    get_video_norm_count.restype = c_int
    get_video_norm_count.argtypes = (GrabberHandlePtr,)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Get a string representation of the video norm specified by iIndex. 
    #    iIndex must be between 0 and IC_GetVideoNormCount().
    #    IC_GetVideoNormCount() must have been called before this function,
    #    otherwise it will always fail.        
    #    
    #    @param hGrabber The handle to the grabber object.
    #    @param iIndex Number of the video norm to be used.
    #
    #    @retval Nonnull The name of the specified video norm.
    #    @retval NULL An error occured.
    #    @sa IC_GetVideoNormCount
    #
    #*/
    #char* AC IC_GetVideoNorm( HGRABBER hGrabber, int iIndex ); ///<Get the name of a video norm.
    get_video_norm = _ic_grabber_dll.IC_GetVideoNorm
    get_video_norm.restype = c_char_p
    get_video_norm.argtypes = (GrabberHandlePtr,
                               c_int)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Get the number of the available video formats for the current device. 
    #    A video capture device must have been opened before this call.
    #    
    #    @param hGrabber The handle to the grabber object.
    #
    #    @retval >= 0 Success
    #    @retval < 0 An error occured.
    #
    #    @sa IC_GetVideoFormat
    #*/
    #int AC IC_GetVideoFormatCount( HGRABBER hGrabber ); ///< Returns the count of available video formats.
    get_video_format_count = _ic_grabber_dll.IC_GetVideoFormatCount
    get_video_format_count.restype = c_int
    get_video_format_count.argtypes = (GrabberHandlePtr,)
    
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Get a string representation of the video format specified by iIndex. 
    #    iIndex must be between 0 and IC_GetVideoFormatCount().
    #    IC_GetVideoFormatCount() must have been called before this function,
    #    otherwise it will always fail.    
    #
    #    @param hGrabber The handle to the grabber object.
    #    @param iIndex Number of the video format to be used.
    #
    #    @retval Nonnull The name of the specified video format.
    #    @retval NULL An error occured.
    #    @sa IC_GetVideoFormatCount
    #*/
    #char* AC IC_GetVideoFormat( HGRABBER hGrabber, int iIndex ); ///<Return the name of a video format.
    get_video_format = _ic_grabber_dll.IC_GetVideoFormat
    get_video_format.restype = c_char_p
    get_video_format.argtypes = (GrabberHandlePtr,
                                 c_int)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Save the state of a video capture device to a file. 
    #    
    #    @param hGrabber The handle to the grabber object.
    #    @param szFileName Name of the file where to save to.
    #
    #    @retval IC_SUCCESS if an image has been snapped
    #    @retval IC_ERROR if something went wrong.
    #
    #    @sa IC_LoadDeviceStateFromFile
    #*/
    #int AC IC_SaveDeviceStateToFile(HGRABBER hGrabber, char* szFileName);///<Save the state of a video capture device to a file. 
    save_device_state_to_file = _ic_grabber_dll.IC_SaveDeviceStateToFile
    save_device_state_to_file.restype = c_int
    save_device_state_to_file.argtypes = (GrabberHandlePtr,
                                          c_char_p)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Load a device settings file. On success the device is opened automatically.
    #
    #    @param hGrabber The handle to the grabber object. If it is NULL then a new HGRABBER handle is
    #                    created. This should be released by a call to IC_ReleaseGrabber when it is no longer needed.
    #    @param szFileName Name of the file where to load from.
    #
    #    @return HGRABBER The handle of the grabber object, that contains the new opened video capture device.
    #
    #    @sa IC_SaveDeviceStateToFile
    #    @sa IC_ReleaseGrabber
    #*/
    #HGRABBER AC IC_LoadDeviceStateFromFile(HGRABBER hGrabber, char* szFileName); ///<Load a device settings file.
    load_device_state_from_file = _ic_grabber_dll.IC_LoadDeviceStateFromFile
    load_device_state_from_file.restype = GrabberHandlePtr
    load_device_state_from_file.argtypes = (GrabberHandlePtr,
                                            c_char_p)

    #//////////////////////////////////////////////////////////////////////////
    #/*! Save the device settings to a file specified by szFilename. When used 
    #    with IC Imaging Control 1.41 the device name, the input channel, the 
    #    video norm and the video format are saved. When used with IC Imaging 
    #    Control 2.0, the VCDProperties are saved as well. Returns 1 on success,
    #    0 otherwise.
    #    Notice that in IC Imaging Control 1.41 the device name includes the trailing 
    #    number if there is more than one device of the same type available. This can
    #    cause IC_OpenDeviceBySettings() to fail if one of those devices is unplugged.
    #    When used with IC Imaging Control 2.0, this cannot happen because the device 
    #    name is stored without the trailing number. Instead the first device that 
    #    matches the type specified in the settings file is opened.
    #
    #    @deprecated Use IC_SaveDeviceStateToFile instead.
    #    
    #*/
    #int AC IC_SaveDeviceSettings( HGRABBER hGrabber, char* szFilename );
    #
    #
    #//////////////////////////////////////////////////////////////////////////
    #/*! Open a device by a settings file specified by szFilename. If succedeed,
    #    1 is returned and a device specified in the settings file is opened and
    #    initialized with the settings data. If failed, 0 is returned. 
    #
    #    @deprecated Use IC_LoadDeviceStateFromFile instead.
    #*/
    #int AC IC_OpenDeviceBySettings( HGRABBER hGrabber, char* szFilename );
    #
    #
    #//////////////////////////////////////////////////////////////////////////
    #/*! Load device settings from a file specified by szFilename. A device must 
    #    have been opened before this function is called. A check is performed whether
    #    the current device matches the device type stored in the settings file.
    #    If so, the settings are loaded and set.
    #    Returns 1 on success, 0 otherwise.
    #    Notice: This function will only work with IC Imaging Control 2.0. When used
    #    with IC Imaging Control 1.41, it will always return 0.
    #
    #    @deprecated Use IC_LoadDeviceStateFromFile instead.
    #*/
    #int AC IC_LoadDeviceSettings( HGRABBER hGrabber, char* szFilename );
    #
    #//////////////////////////////////////////////////////////////////////////
    #/*! Open a video capture by using its DisplayName. 
    #    @param hGrabber The handle to the grabber object.
    #    @param szDisplayname Displayname of the device. Can be retrieved by a call to IC_GetDisplayName().
    #
    #    @retval IC_SUCCESS if an image has been snapped
    #    @retval IC_ERROR if something went wrong.
    #
    #    @sa IC_GetDisplayName
    #*/
    #int AC IC_OpenDevByDisplayName( HGRABBER hGrabber, char *szDisplayname); ///<Open a video capture by using its DisplayName. 
    #
    #//////////////////////////////////////////////////////////////////////////
    #/*! Get a DisplayName from a currently open device. The display name of a
    #    device can be another on different computer for the same video capture
    #    device. 
    #    
    #    @param hGrabber       Handle to a grabber object
    #    @param szDisplayName  Memory that will take the display name. If it is NULL, the
    #                          length of the display name will be returned.
    #    @param iLen           Size in Bytes of the memory allocated by szDisplayName.
    #
    #    
    #    @retval IC_SUCCESS     On success. szDisplayName contains the display name of the device.
    #    @retval IC_ERROR       iLen is less than the length of the retrieved display name. 
    #    @retval IC_NO_HANDLE   hGrabber is not a valid handle. GetGrabber was not called.
    #    @retval IC_NO_DEVICE   No device opened. Open a device, before this function can be used.
    #    @retval >1             Length of the display name, if szDisplayName is NULL.
    #
    #    @sa IC_OpenDevByDisplayName
    #    @sa IC_ReleaseGrabber
    #
    #*/
    #int AC IC_GetDisplayName( HGRABBER hGrabber, char *szDisplayname, int iLen); ///<Get the display name of a device.
    get_display_name = _ic_grabber_dll.IC_GetDisplayName
    get_display_name.restype = c_int
    get_display_name.argtypes = (GrabberHandlePtr,
                                 #c_char_p,
                                 POINTER(c_char),
                                 c_int)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Open a video capture by using its UniqueName. Use IC_GetUniqueName() to
    #    retrieve the unique name of a camera.
    #
    #    @param hGrabber       Handle to a grabber object
    #    @param szDisplayName  Memory that will take the display name.
    #
    #    @sa IC_GetUniqueName
    #    @sa IC_ReleaseGrabber
    #
    #*/
    #int AC IC_OpenDevByUniqueName( HGRABBER hGrabber, char *szDisplayname);
    open_device_by_unique_name = _ic_grabber_dll.IC_OpenDevByUniqueName
    open_device_by_unique_name.restype = c_int
    open_device_by_unique_name.argtypes = (GrabberHandlePtr,
                                           c_char_p)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Get a UniqueName from a currently open device.
    #    
    #    @param hGrabber      Handle to a grabber object
    #    @param szUniqueName  Memory that will take the Unique name. If it is NULL, the
    #                         length of the Unique name will be returned.
    #    @param iLen          Size in Bytes of the memory allocated by szUniqueName.
    #
    #    
    #    @retval IC_SUCCESS    On success. szUniqueName contains the Unique name of the device.
    #    @retval IC_ERROR      iLen is less than the length of the retrieved Unique name. 
    #    @retval IC_NO_HANDLE  hGrabber is not a valid handle. GetGrabber was not called.
    #    @retval IC_NO_DEVICE  No device opened. Open a device, before this function can be used.
    #    @retval >1            Length of the Unique name, if szUniqueName is NULL.
    #    
    #*/
    #int AC IC_GetUniqueName( HGRABBER hGrabber, char *szUniquename, int iLen); ///<Get a UniqueName from a currently open device.
    get_unique_name = _ic_grabber_dll.IC_GetUniqueName
    get_unique_name.restype = c_int
    get_unique_name.argtypes = (GrabberHandlePtr,
                                c_char_p,
                                c_int)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! This returns 1, if a valid device has been opened, otherwise it is 0.
    #
    #    @param hGrabber      Handle to a grabber object.
    #
    #    @retval 0 There is no valid video capture device opened
    #    @retval 1 There is a valid video capture device openend.
    #*/
    #int AC IC_IsDevValid( HGRABBER hGrabber); ///<Returns whether a video capture device is valid.
    is_dev_valid = _ic_grabber_dll.IC_IsDevValid
    is_dev_valid.restype = c_int
    is_dev_valid.argtypes = (GrabberHandlePtr,)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Show the VCDProperty dialog. 
    #
    #    @param hGrabber      Handle to a grabber object.
    #    @retval IC_SUCCESS on success
    #    @retval IC_ERROR on error.
    #
    #    @note This function will only work with IC Imaging Control 2.0 or higher. When used
    #    with IC Imaging Control 1.41, it will always return 0.
    #*/
    #int AC IC_ShowPropertyDialog( HGRABBER hGrabber ); ///<Show the VCDProperty dialog. 
    show_property_dialog = _ic_grabber_dll.IC_ShowPropertyDialog
    show_property_dialog.restype = c_int
    show_property_dialog.argtypes = (GrabberHandlePtr,)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Show the device selection dialog. This dialogs enables to select the 
    #    video capture device, the video norm, video format, input channel and
    #    frame rate.
    #
    #    @param hGrabber      Handle to a grabber object.
    #
    #    @return The passed hGrabber object or a new created if hGrabber was NULL.
    #
    #    @code
    #    HGRABBER hTheGrabber;
    #    hTheGrabber = IC_ShowDeviceSelectionDialog( NULL );
    #    if( hTheGrabber != NULL )
    #    {
    #        IC_StartLive( hTheGrabber, 1 ); // Show the live video of this grabber
    #        IC_ShowPropertyDialog( hTheGrabber );    // Show the property page of this grabber
    #    }
    #    @endcode
    #*/
    #HGRABBER AC IC_ShowDeviceSelectionDialog( HGRABBER hGrabber ); ///<Show the device selection dialog.
    show_dev_selection_dialog = _ic_grabber_dll.IC_ShowDeviceSelectionDialog
    show_dev_selection_dialog.restype = GrabberHandlePtr
    show_dev_selection_dialog.argtypes = (GrabberHandlePtr,)

    #//////////////////////////////////////////////////////////////////////////
    #/*!    
    #    Return whether the current video capture device supports an external 
    #    trigger. 
    #
    #    @param hGrabber      Handle to a grabber object.
    #    @retval 1 An external trigger is supported
    #    @retval 0 No external trigger is supported.
    #
    #    @sa IC_EnableTrigger
    #*/
    #int AC IC_IsTriggerAvailable( HGRABBER hGrabber ); ///<Check for external trigger support.
    is_trigger_available = _ic_grabber_dll.IC_IsTriggerAvailable
    is_trigger_available.restype = c_int
    is_trigger_available.argtypes = (GrabberHandlePtr,)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*!    Enable or disable the external trigger. 
    #    @param hGrabber      Handle to a grabber object.
    #    @param iEnable 1 = enable the trigger, 0 = disable the trigger
    #
    #    @retval IC_SUCCESS    On success. 
    #    @retval IC_ERROR      An error occurred. 
    #
    #    @sa IC_IsTriggerAvailable
    #*/
    #int AC IC_EnableTrigger( HGRABBER hGrabber, int iEnable );
    enable_trigger = _ic_grabber_dll.IC_EnableTrigger
    enable_trigger.restype = c_int
    enable_trigger.argtypes = (GrabberHandlePtr,
                               c_int)

    #//////////////////////////////////////////////////////////////////////////
    #/*!    Remove or insert the  the overlay bitmap to the grabber object. If
    #    Y16 format is used, the overlay must be removed,
    #
    #    @param hGrabber      Handle to a grabber object.
    #    @param iEnable = 1 inserts overlay, 0 removes the overlay.
    #*/
    #void AC IC_RemoveOverlay( HGRABBER hGrabber, int iEnable );
    remove_overlay = _ic_grabber_dll.IC_RemoveOverlay
    remove_overlay.restype = None
    enable_trigger.argtypes = (GrabberHandlePtr,
                               c_int)

    #//////////////////////////////////////////////////////////////////////////
    #/*!    Enable or disable the overlay bitmap on the live video
    #    @param hGrabber      Handle to a grabber object.
    #    @param iEnable = 1 enables the overlay, 0 disables the overlay.
    #*/
    #void AC IC_EnableOverlay( HGRABBER hGrabber, int iEnable ); ///<Enable or disable the overlay bitmap.
    #
    #//////////////////////////////////////////////////////////////////////////
    #/*!  BeginPaint returns an HDC for GDI painting purposes (like TextOut() etc.)
    #    When the paintings are finished, the function IC_EndPaint must be called.
    #
    #    @param hGrabber      Handle to a grabber object.
    #
    #    @return HDC The function returns not NULL, if the HDC could be retrieved. If the HDC 
    #            could not be retrieved or an error has occured, the function returns 0.
    #
    #    Sample code:
    #    @code
    #    HDC hPaintDC;
    #    hPaintDC = IC_BeginPaint(hGrabber);
    #    if( hPaintDC != NULL )
    #    {
    #        TextOut( hPaintDC,10,10,"Text",4);
    #    }
    #    IC_EndPaint(hGrabber)
    #    @endcode
    #
    #    @sa IC_EndPaint
    #*/
    #long AC IC_BeginPaint( HGRABBER hGrabber ); ///< BeginPaint returns an HDC for GDI painting purposes.
    #
    #//////////////////////////////////////////////////////////////////////////
    #/*!  The EndPaint functions must be called, after BeginPaint has been called,
    #    and the painting operations have been finished.
    #    @param hGrabber      Handle to a grabber object.
    #    @sa IC_BeginPaint
    #*/
    #void AC IC_EndPaint( HGRABBER hGrabber ); ///< End painting functions on the overlay bitmap.
    #//////////////////////////////////////////////////////////////////////////
    #/*! Display a windows messagebox.
    #    @param szText Message text
    #    @param zsTitle Title of the messagebox.
    #*/
    #void AC IC_MsgBox( char * szText, char* szTitle ); ///<Display a windows messagebox.
    msg_box = _ic_grabber_dll.IC_MsgBox
    msg_box.argtypes = (c_char_p,
                        c_char_p)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Type declaration for the frame ready callback function. 
    #    @sa IC_SetFrameReadyCallback
    #    @sa IC_SetCallbacks
    #*/
    #typedef void (*FRAME_READY_CALLBACK)
    #    (HGRABBER hGrabber, unsigned char* pData, unsigned long frameNumber, void* );
    #
    #//////////////////////////////////////////////////////////////////////////
    #/*! Type declaration for the device lost callback function. 
    #    @sa IC_SetCallbacks
    #*/
    #typedef void (*DEVICE_LOST_CALLBACK)(HGRABBER hGrabber, void* );
    #
    #
    #//////////////////////////////////////////////////////////////////////////
    #/*!    Enable frame ready callback.
    #    @param hGrabber      Handle to a grabber object.
    #    @param cb Callback function of type FRAME_READY_CALLBACK
    #    @param x1_argument_in_void_userdata Pointer to some userdata.
    #
    #    @sa FRAME_READY_CALLBACK
    #
    #*/
    #int AC IC_SetFrameReadyCallback(
    #    HGRABBER                hGrabber,
    #    FRAME_READY_CALLBACK    cb,
    #    void*                    x1_argument_in_void_userdata);
    set_frame_ready_callback = _ic_grabber_dll.IC_SetFrameReadyCallback
    set_frame_ready_callback.restype = c_int
    set_frame_ready_callback.argtypes = (GrabberHandlePtr,
                                         c_void_p,
                                         c_void_p)
    
    #/*!    Set callback function
    #    @param hGrabber      Handle to a grabber object.
    #    @param cb Callback function of type FRAME_READY_CALLBACK, can be NULL, if no callback is needed
    #    @param dlcb Callback function of type DEVICE:LOST_CALLBACK, can be NULL, if no device lost handler is needed
    #    @param x1_argument_in_void_userdata Pointer to some userdata.
    #
    #    @sa FRAME_READY_CALLBACK
    #*/
    #int AC IC_SetCallbacks(
    #    HGRABBER                hGrabber,
    #    FRAME_READY_CALLBACK    cb,
    #    void*                    x1_argument_in_void_userdata,
    #    DEVICE_LOST_CALLBACK    dlCB,
    #    void*                    x2_argument_in_void_userdata);
    #
    #
    #
    #
    #/////////////////////////////////////////////////////////////////////////
    #/*!    Set Continuous mode
    # 
    #     In continuous mode, the callback is called for each frame,
    #     so that there is no need to use IC_SnapImage etc.
    # 
    #    @param hGrabber      Handle to a grabber object.
    #    @param cont            0 : Snap continouos, 1 : do not automatically snap.
    #
    #    @remarks
    #     Not available in live mode.
    # 
    # */
    #int AC IC_SetContinuousMode( HGRABBER hGrabber, int cont ); ///<Set Continuous mode.
    set_continuous_mode = _ic_grabber_dll.IC_SetContinuousMode
    set_continuous_mode.restype = c_int
    set_continuous_mode.argtypes = (GrabberHandlePtr,
                                    c_int)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! SignalDetected
    #
    #    Detects whether a video signal is available.
    #
    #    @param hGrabber      Handle to a grabber object.
    #
    #    @retval IC_SUCCESS   Signal detected
    #    @retval IC_ERROR  No video signal detected
    #    @retval IC_NO_HANDLE  Invalid grabber handle
    #    @retval IC_NO_DEVICE    No video capture device opened
    #    @retval IC_NOT_IN_LIVEMODE  No live mode, startlive was not called
    #*/
    #int AC IC_SignalDetected( HGRABBER hGrabber  ); ///<Detects whether a video signal is available.
    #
    #
    #//////////////////////////////////////////////////////////////////////////
    #/*! Get trigger modes.
    #    Simple sample to list the video capture devices:
    #
    #    @param hGrabber      Handle to a grabber object.
    #    @param szModeList    Twodimensional array of char that will recieve the mode list.
    #    @param iSze            Size of the array (first dimension)
    #
    #    @retval 0 : No trigger modes available
    #    @retval >0 : Count of available trigger modes
    #    @retval IC_ERROR  No video signal detected
    #    @retval IC_NO_HANDLE  Invalid grabber handle
    #    @retval IC_NO_DEVICE    No video capture device opened
    #
    #    @code
    #    char szModes[20][10];
    #    int iModeCount;
    #
    #    iModeCount = IC_GetTriggerModes(hGrabber, (char*)szModes,20);
    #    for( int i = 0; i < min( iModeCount, 20); i++ )
    #    {
    #        printf("%2d. %s\n",i+1,szModes[i]);
    #    }
    #    @endcode
    #*/
    #int AC IC_GetTriggerModes( HGRABBER hGrabber,  char *szModeList, int iSize  ); ///<Get trigger modes.
    get_trigger_modes = _ic_grabber_dll.IC_GetTriggerModes
    get_trigger_modes.restype = c_int
    get_trigger_modes.argtypes = (GrabberHandlePtr,
                                  POINTER((c_char * 20) * 10),    # hardcoded 10 values, each with 20 characters)
                                  c_int)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*!  Set the trigger mode.
    #    Sets the mode that has been retrieved  by a call to IC_GetTriggerModes.
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param szMode    String containing the name of the mode.    
    #
    #    @retval IC_SUCCESS        Success.
    #    @retval IC_ERROR        An error occurred
    #    @retval IC_NO_HANDLE    Invalid grabber handle
    #    @retval IC_NO_DEVICE    No video capture device opened
    #
    #*/
    #int AC IC_SetTriggerMode( HGRABBER hGrabber, char* szMode  ); ///<Set the trigger mode.
    set_trigger_mode = _ic_grabber_dll.IC_SetTriggerMode
    set_trigger_mode.restype = c_int
    set_trigger_mode.argtypes = (GrabberHandlePtr,
                                 c_char_p)
    
    #//////////////////////////////////////////////////////////////////////////
    #/*! Set the trigger polarity
    #    
    #    Sample:
    #    @code
    #    IC_SetTriggerPolarity(hGrabber, 0);
    #    @endcode
    #    or
    #    @code
    #    IC_SetTriggerPolarity(hGrabber, 1);
    #    @endcode
    #    @param hGrabber    Handle to a grabber object.
    #    @param iPolarity 
    #        @li 0 : Polarity on direction
    #        @li 1 : Polarity the other direction
    #
    #    @retval 0 : No trigger polarity available
    #    @retval 1 : Count of available trigger modes
    #    @retval IC_NO_HANDLE    Invalid grabber handle
    #    @retval IC_NO_DEVICE    No video capture device opened
    #*/
    #int AC IC_SetTriggerPolarity( HGRABBER hGrabber, int iPolarity ); ///< Set the trigger polarity.
    set_trigger_polarity = _ic_grabber_dll.IC_SetTriggerPolarity
    set_trigger_polarity.restype = c_int
    set_trigger_polarity.argtypes = (GrabberHandlePtr,
                                     c_int)
    
    #int AC IC_GetExpRegValRange( HGRABBER hGrabber, long *lMin, long *lMax ); ///< Retrieve exposure register values lower and upper limits.
    get_exp_reg_val_range = _ic_grabber_dll.IC_GetExpRegValRange
    get_exp_reg_val_range.restype = c_int
    get_exp_reg_val_range.argtypes = (GrabberHandlePtr,
                                      POINTER(c_long),
                                      POINTER(c_long))
        
    #int AC IC_GetExpRegVal( HGRABBER hGrabber, long *lValue ); ///< Retrieve the current register value of exposure.
    get_exp_reg_val = _ic_grabber_dll.IC_GetExpRegVal
    get_exp_reg_val.restype = c_int
    get_exp_reg_val.argtypes = (GrabberHandlePtr,
                                POINTER(c_long))
    
    #int AC IC_SetExpRegVal( HGRABBER hGrabber, long lValue ); ///<Set a register value for exposure.
    set_exp_reg_val = _ic_grabber_dll.IC_SetExpRegVal
    set_exp_reg_val.restype = c_int
    set_exp_reg_val.argtypes = (GrabberHandlePtr,
                                c_long)
    
    
    #int AC IC_EnableExpRegValAuto( HGRABBER hGrabber, int iOnOff ); ///<Enable or disable automatic of exposure.
    enable_exp_reg_val_auto = _ic_grabber_dll.IC_EnableExpRegValAuto
    enable_exp_reg_val_auto.restype = c_int
    enable_exp_reg_val_auto.argtypes = (GrabberHandlePtr,
                                        c_int)
    
    #int AC IC_GetExpRegValAuto( HGRABBER hGrabber, int *iOnOff );///<Check whether automatic exposure is enabled.
    get_exp_reg_val_auto = _ic_grabber_dll.IC_GetExpRegValAuto
    get_exp_reg_val_auto.restype = c_int
    get_exp_reg_val_auto.argtypes = (GrabberHandlePtr,
                                     POINTER(c_int))

    
    
    #
    #
    #//////////////////////////////////////////////////////////////////////////
    #/*! Functions for the absolute values interface of exposure.
    #*/
    #int AC IC_IsExpAbsValAvailable( HGRABBER hGrabber);
    is_exp_abs_val_available = _ic_grabber_dll.IC_IsExpAbsValAvailable
    is_exp_abs_val_available.restype = c_int
    is_exp_abs_val_available.argtypes = (GrabberHandlePtr,)    
    
    #int AC IC_GetExpAbsValRange(HGRABBER hGrabber, float *fMin, float *fMax);
    get_exp_abs_val_range = _ic_grabber_dll.IC_GetExpAbsValRange
    get_exp_abs_val_range.restype = c_int
    get_exp_abs_val_range.argtypes = (GrabberHandlePtr,
                                      POINTER(c_float),
                                      POINTER(c_float))    
    
    #int AC IC_GetExpAbsVal(HGRABBER hGrabber, float *fValue);
    get_exp_abs_val = _ic_grabber_dll.IC_GetExpAbsVal
    get_exp_abs_val.restype = c_int
    get_exp_abs_val.argtypes = (GrabberHandlePtr,
                                POINTER(c_float))
    
    #int AC IC_SetExpAbsVal(HGRABBER hGrabber,  float fValue );
    set_exp_abs_val = _ic_grabber_dll.IC_SetExpAbsVal
    set_exp_abs_val.restype = c_int
    set_exp_abs_val.argtypes = (GrabberHandlePtr,
                                c_float)
    
    
    #
    #
    #///////////////////////////////////////////////////////////////////
    #/*! Gets the current value of Colorenhancement property
    #    Sample:
    #    @code
    #    int OnOFF
    #    IC_GetColorEnhancement(hGrabber, &OnOFF);
    #    @endcode
    #    @param hGrabber    Handle to a grabber object.
    #    @param OnOff 
    #        @li 0 : Color enhancement is off
    #        @li 1 : Color enhancement is on
    #
    #    @retval IC_SUCCESS : Success
    #    @retval IC_NOT:AVAILABLE : The property is not supported by the current device
    #    @retval IC_NO_HANDLE    Invalid grabber handle
    #    @retval IC_NO_DEVICE    No video capture device opened
    #*/
    #int AC IC_GetColorEnhancement(HGRABBER hGrabber, int *OnOff);
    get_color_enhancement = _ic_grabber_dll.IC_GetColorEnhancement
    get_color_enhancement.restype = c_int
    get_color_enhancement.argtypes = (GrabberHandlePtr,
                                      POINTER(c_int))
    
    #///////////////////////////////////////////////////////////////////
    #/*! Sets the  value of Colorenhancement property
    #    Sample:
    #    @code
    #    int OnOFF = 1
    #    IC_GetColorEnhancement(hGrabber, OnOFF);
    #    @endcode
    #    @param hGrabber    Handle to a grabber object.
    #    @param OnOff 
    #        @li 0 : Color enhancement is off
    #        @li 1 : Color enhancement is on
    #
    #    @retval IC_SUCCESS : Success
    #    @retval IC_NOT:AVAILABLE : The property is not supported by the current device
    #    @retval IC_NO_HANDLE    Invalid grabber handle
    #    @retval IC_NO_DEVICE    No video capture device opened
    #*/
    #int AC IC_SetColorEnhancement(HGRABBER hGrabber, int OnOff);
    set_color_enhancement = _ic_grabber_dll.IC_SetColorEnhancement
    set_color_enhancement.restype = c_int
    set_color_enhancement.argtypes = (GrabberHandlePtr,
                                      c_int)
    
    #///////////////////////////////////////////////////////////////////
    #/*! Sends a software trigger to the camera. The camera must support
    #    external trigger. The external trigger has to be enabled previously
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @retval IC_SUCCESS : Success
    #    @retval IC_NOT:AVAILABLE : The property is not supported by the current device
    #    @retval IC_NO_HANDLE    Invalid grabber handle
    #    @retval IC_NO_DEVICE    No video capture device opened
    #
    #    @seealso IC_EnableTrigger
    #
    #*/
    #int AC IC_SoftwareTrigger(HGRABBER hGrabber);
    software_trigger = _ic_grabber_dll.IC_SoftwareTrigger
    software_trigger.restype = c_int
    software_trigger.argtypes = (GrabberHandlePtr,)
    
    #///////////////////////////////////////////////////////////////////
    #/*! Sets a new frame rate. 
    #    @param hGrabber    Handle to a grabber object.
    #    @param FrameRate The new frame rate.
    #    @retval IC_SUCCESS : Success
    #    @retval IC_NOT_AVAILABLE : The property is not supported by the current device
    #    @retval IC_NO_HANDLE    Invalid grabber handle
    #    @retval IC_NO_DEVICE    No video capture device opened
    #    @retval IC_NOT_IN_LIVEMODE Frame rate can not set, while live video is shown. Stop Live video first!
    #*/
    #int AC IC_SetFrameRate(HGRABBER hGrabber,float FrameRate);
    set_frame_rate = _ic_grabber_dll.IC_SetFrameRate
    set_frame_rate.restype = c_int
    set_frame_rate.argtypes = (GrabberHandlePtr,
                               c_float)
    
    #///////////////////////////////////////////////////////////////////
    #/*! Retrieves the current frame rate
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @retval The current frame rate. If it is 0.0, then frame rates are not supported.
    #*/
    #float AC IC_GetFrameRate(HGRABBER hGrabber);
    get_frame_rate = _ic_grabber_dll.IC_GetFrameRate
    get_frame_rate.restype = c_float
    get_frame_rate.argtypes = (GrabberHandlePtr,)
    
    #int AC IC_SetWhiteBalanceAuto( HGRABBER hGrabber, int iOnOff);
    #
    #///////////////////////////////////////////////////////////////////
    #/*! Sets the value for white balance red.
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param Value    Value of the red white balance to be set
    #    @retval IC_SUCCESS            : Success
    #    @retval IC_NO_HANDLE        : Invalid grabber handle
    #    @retval IC_NO_DEVICE        : No video capture device opened
    #    @retval IC_NOT_AVAILABLE    : The property is not supported by the current device
    #
    #*/
    #int AC IC_SetWhiteBalanceRed(HGRABBER hGrabber, long Value);
    #///////////////////////////////////////////////////////////////////
    #/*! Sets the value for white balance green.
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param Value    Value of the green white balance to be set
    #    @retval IC_SUCCESS            : Success
    #    @retval IC_NO_HANDLE        : Invalid grabber handle
    #    @retval IC_NO_DEVICE        : No video capture device opened
    #    @retval IC_NOT_AVAILABLE    : The property is not supported by the current device
    #
    #*/
    #int AC IC_SetWhiteBalanceGreen(HGRABBER hGrabber, long Value);
    #///////////////////////////////////////////////////////////////////
    #/*! Sets the value for white balance blue.
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param Value    Value of the blue white balance to be set
    #    @retval IC_SUCCESS            : Success
    #    @retval IC_NO_HANDLE        : Invalid grabber handle
    #    @retval IC_NO_DEVICE        : No video capture device opened
    #    @retval IC_NOT_AVAILABLE    : The property is not supported by the current device
    #
    #*/
    #int AC IC_SetWhiteBalanceBlue(HGRABBER hGrabber, long Value);
    #
    #///////////////////////////////////////////////////////////////////
    #/*! Performs the one push  for Focus
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param Value    Value of the blue white balance to be set
    #    @retval IC_SUCCESS            : Success
    #    @retval IC_NO_HANDLE        : Invalid grabber handle
    #    @retval IC_NO_DEVICE        : No video capture device opened
    #    @retval IC_NOT_AVAILABLE    : The property is not supported by the current device
    #
    #*/
    #int AC IC_FocusOnePush(HGRABBER hGrabber);
    focus_one_push = _ic_grabber_dll.IC_FocusOnePush
    focus_one_push.restype = c_int
    focus_one_push.argtypes = (GrabberHandlePtr,)

    #
    #
    #
    #///////////////////////////////////////////////////////////////////
    #/*! Show the internal property page of the camera
    #*/
    #int AC IC_ShowInternalPropertyPage(HGRABBER hGrabber);
    #
    #
    #///////////////////////////////////////////////////////////////////
    #/*! Resets all properties to their default values. If a property has
    #    automation, the automatic will be enabled.
    #    If the device supports external trigger, the external trigger will
    #    be disabled.
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @retval IC_SUCCESS            Success
    #    @retval IC_NO_HANDLE        Invalid grabber handle
    #    @retval IC_NO_DEVICE        No video capture device opened
    #
    #*/
    #int AC IC_ResetProperties(HGRABBER hGrabber);
    reset_properties = _ic_grabber_dll.IC_ResetProperties
    reset_properties.restype = c_int
    reset_properties.argtypes = (GrabberHandlePtr,)
    
    #
    #
    #///////////////////////////////////////////////////////////////////
    #/*! Resets the driver. Do not use, for internl purposes only.
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @retval IC_SUCCESS            Success
    #    @retval IC_NO_HANDLE        Invalid grabber handle
    #    @retval IC_NO_DEVICE        No video capture device opened
    #*/
    #int AC IC_ResetUSBCam(HGRABBER hGrabber);
    #
    #
    #///////////////////////////////////////////////////////////////////
    #/*! This function queries the internal property set (KsPropertySet) of the driver. 
    #    It allows an application to access all properties of a video capture devices
    #    using the enums and GUIDs from the header files fwcam1394propguid.h and 
    #    fwcam1394props.h.
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @retval IC_SUCCESS            Success
    #    @retval IC_NO_HANDLE        Invalid grabber handle
    #    @retval IC_NO_DEVICE        No video capture device opened
    #    @retval IC_ERROR            The property could not have been retrieved
    #
    #*/
    #int AC IC_QueryPropertySet(HGRABBER hGrabber);
    #
    #
    #///////////////////////////////////////////////////////////////////
    #/*! This function sets a value or structure to the internal property set
    #    of the video capture device. The properties and structures are defined
    #    in the header file fwcam1394props.h. Before using this function, the
    #    properties set must have been queried once using the function IC_QueryPropertySet().
    #
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @retval IC_SUCCESS            Success
    #    @retval IC_ERROR            Setting of the values failed
    #    @retval IC_NO_PROPERTYSET    The property set was not retrieved or is not available.
    #    @retval IC_NO_HANDLE        Invalid grabber handle
    #    @retval IC_NO_DEVICE        No video capture device opened
    #
    #    @sa IC_QueryPropertySet
    #*/
    #//int AC IC_PropertySet_Set(HGRABBER hGrabber, FWCAM1394_CUSTOM_PROP prop, FWCAM1394_CUSTOM_PROP_S& rstruct );
    #
    #
    #
    #///////////////////////////////////////////////////////////////////
    #/*! Enables or disables the default window size lock of the video window. 
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param Default    0 = disable, custome size can be set, 1 = enable, the standard size, which is video format, is used.
    #
    #    @retval IC_SUCCESS            Success
    #    @retval IC_ERROR            Setting of the values failed
    #    @retval IC_NO_PROPERTYSET    The property set was not retrieved or is not available.
    #    @retval IC_NO_HANDLE        Invalid grabber handle
    #    @retval IC_NO_DEVICE        No video capture device opened
    #
    #*/
    #int AC IC_SetDefaultWindowPosition(HGRABBER hGrabber, int Default);
    #
    #///////////////////////////////////////////////////////////////////
    #/*! This function Sets the position and size of the video window. 
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param PosX  Specifies the x-coordinate of the upper left hand corner of the video window. It defaults to 0. 
    #    @param PosY  Specifies the y-coordinate of the upper left hand corner of the video window. It defaults to 0. 
    #    @param width  Specifies the width of the video window. 
    #    @param height  Specifies the height of the video window. 
    #
    #     @retval IC_SUCCESS            Success
    #    @retval IC_ERROR            Setting of the values failed
    #    @retval IC_DEFAULT_WINDOW_SIZE_SET    The property set was not retrieved or is not available.
    #    @retval IC_NO_HANDLE        Invalid grabber handle
    #    @retval IC_NO_DEVICE        No video capture device opened
    #
    #*/
    #int AC IC_SetWindowPosition(HGRABBER hGrabber, int PosX, int PosY, int Width, int Height );
    #
    #///////////////////////////////////////////////////////////////////
    #/*! Check, whether a property is available..  For a list of properties and elements
    #    use the VCDPropertyInspector of IC Imaging Control.
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param Property  The name of the property, e.g. Gain, Exposure
    #    @param Element  The type of the interface, e.g. Value, Auto. If NULL, it is not checked.
    #
    #     @retval IC_SUCCESS            Success
    #    @retval IC_NO_HANDLE        Invalid grabber handle
    #    @retval IC_NO_DEVICE        No video capture device opened
    #    @retval IC_PROPERTY_ELEMENT_NOT_AVAILABLE        A requested element of a given property item is not available
    #    @retval IC_PROPERTY_ELEMENT_WRONG_INTERFACE        requested element has not the interface, which is needed.
    #    
    #    Simple call:
    #    @code
    #    if( IC_IsPropertyAvailable( hGrabber, "Brightness",NULL) == IC_SUCCESS )
    #    {
    #        printf("Brightness is supported\n");
    #    }
    #    else
    #    {
    #        printf("Brightness is not supported\n");
    #    }
    #    @endcode
    #
    #    Complex call for a special element:
    #    @code
    #    if( IC_IsPropertyAvailable( hGrabber, "Trigger","Software Trigger") == IC_SUCCESS )
    #    {
    #        printf("Software trigger is supported\n");
    #    }
    #    else
    #    {
    #        printf("Software trigger is not supported\n");
    #    }
    #    @endcode
    #*/
    #int AC IC_IsPropertyAvailable(HGRABBER hGrabber, char* Property, char *Element );
    is_property_available = _ic_grabber_dll.IC_IsPropertyAvailable
    is_property_available.restype = c_int
    is_property_available.argtypes = (GrabberHandlePtr,
                                      c_char_p,
                                      c_char_p)
    
    #///////////////////////////////////////////////////////////////////
    #/*! This returns the range of a property.  For a list of properties and elements
    #    use the VCDPropertyInspector of IC Imaging Control.
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param Property  The name of the property, e.g. Gain, Exposure
    #    @param Element  The type of the interface, e.g. Value, Auto. If NULL, it is "Value".
    #    @param Min  Receives the min value of the property
    #    @param Max  Receives the max value of the property
    #
    #     @retval IC_SUCCESS            Success
    #    @retval IC_NO_HANDLE        Invalid grabber handle
    #    @retval IC_NO_DEVICE        No video capture device opened
    #    @retval IC_PROPERTY_ITEM_NOT_AVAILABLE        A requested property item is not available
    #    @retval IC_PROPERTY_ELEMENT_NOT_AVAILABLE        A requested element of a given property item is not available
    #    @retval IC_PROPERTY_ELEMENT_WRONG_INTERFACE        requested element has not the interface, which is needed.
    #
    #    @code
    #    HGRABBER hGrabber; // The handle of the grabber object.
    #
    #    int Min;
    #    int Max;
    #    int Result = IC_ERROR;
    #    HGRABBER hGrabber;
    #
    #    if( IC_InitLibrary(0) )
    #    {
    #        hGrabber = IC_CreateGrabber();
    #        IC_OpenVideoCaptureDevice(hGrabber, "DFx 31BG03.H");
    #
    #        if( hGrabber )
    #        {
    #            Result = IC_GetPropertyValueRange(hGrabber,"Exposure","Auto Reference", &Min, &Max );
    #
    #            if( Result == IC_SUCCESS )
    #                printf("Expsure Auto Reference Min %d, Max %d\n", Min, Max);
    #
    #            Result = IC_GetPropertyValueRange(hGrabber,"Exposure",NULL, &Min, &Max );
    #
    #            if( Result == IC_SUCCESS )
    #                printf("Exposure Value Min %d, Max %d\n", Min, Max);
    #    }
    #    IC_ReleaseGrabber( hGrabber );
    #    @endcode
    #
    #
    #*/
    #int AC IC_GetPropertyValueRange(HGRABBER hGrabber, char* Property, char *Element, int *Min, int *Max );
    get_property_value_range = _ic_grabber_dll.IC_GetPropertyValueRange
    get_property_value_range.restype = c_int
    get_property_value_range.argtypes = (GrabberHandlePtr,
                                         c_char_p,
                                         c_char_p,
                                         POINTER(c_int),
                                         POINTER(c_int))
    
    #///////////////////////////////////////////////////////////////////
    #/*! This returns the current value of a property. For a list of properties and elements
    #    use the VCDPropertyInspector of IC Imaging Control.
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param Property  The name of the property, e.g. Gain, Exposure
    #    @param Element  The type of the interface, e.g. Value, Auto. If NULL, it is "Value".
    #    @param Value  Receives the value of the property
    #
    #     @retval IC_SUCCESS            Success
    #    @retval IC_NO_HANDLE        Invalid grabber handle
    #    @retval IC_NO_DEVICE        No video capture device opened
    #    @retval IC_PROPERTY_ITEM_NOT_AVAILABLE        A requested property item is not available
    #    @retval IC_PROPERTY_ELEMENT_NOT_AVAILABLE        A requested element of a given property item is not available
    #    @retval IC_PROPERTY_ELEMENT_WRONG_INTERFACE        requested element has not the interface, which is needed.
    #*/
    #int AC IC_GetPropertyValue(HGRABBER hGrabber, char* Property, char *Element, int *Value );
    get_property_value = _ic_grabber_dll.IC_GetPropertyValue
    get_property_value.restype = c_int
    get_property_value.argtypes = (GrabberHandlePtr,
                                   c_char_p,
                                   c_char_p,
                                   POINTER(c_int))
    
    #///////////////////////////////////////////////////////////////////
    #/*! This sets a new value of a property.  For a list of properties and elements
    #    use the VCDPropertyInspector of IC Imaging Control.
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param Property  The name of the property, e.g. Gain, Exposure
    #    @param Element  The type of the interface, e.g. Value, Auto. If NULL, it is "Value".
    #    @param Value  Receives the value of the property
    #
    #     @retval IC_SUCCESS            Success
    #    @retval IC_NO_HANDLE        Invalid grabber handle
    #    @retval IC_NO_DEVICE        No video capture device opened
    #    @retval IC_PROPERTY_ITEM_NOT_AVAILABLE        A requested property item is not available
    #    @retval IC_PROPERTY_ELEMENT_NOT_AVAILABLE        A requested element of a given property item is not available
    #    @retval IC_PROPERTY_ELEMENT_WRONG_INTERFACE        requested element has not the interface, which is needed.
    #*/
    #int AC IC_SetPropertyValue(HGRABBER hGrabber, char* Property, char *Element, int Value );
    set_property_value = _ic_grabber_dll.IC_SetPropertyValue
    set_property_value.restype = c_int
    set_property_value.argtypes = (GrabberHandlePtr,
                                   c_char_p,
                                   c_char_p,
                                   c_int)
    
    #///////////////////////////////////////////////////////////////////
    #/*! This returns the range of an absolute value property. Usually it is used for exposure. 
    #    a list of properties and elements use the VCDPropertyInspector of IC Imaging Control.
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param Property  The name of the property, e.g. Gain, Exposure
    #    @param Element  The type of the interface, e.g. Value, Auto. If NULL, it is "Value".
    #    @param Min  Receives the min value of the property
    #    @param Max  Receives the max value of the property
    #
    #     @retval IC_SUCCESS            Success
    #    @retval IC_NO_HANDLE        Invalid grabber handle
    #    @retval IC_NO_DEVICE        No video capture device opened
    #    @retval IC_PROPERTY_ITEM_NOT_AVAILABLE        A requested property item is not available
    #    @retval IC_PROPERTY_ELEMENT_NOT_AVAILABLE        A requested element of a given property item is not available
    #    @retval IC_PROPERTY_ELEMENT_WRONG_INTERFACE        requested element has not the interface, which is needed.
    #*/
    #int AC IC_GetPropertyAbsoluteValueRange(HGRABBER hGrabber, char* Property, char *Element, float *Min, float *Max );
    get_property_absolute_value_range = _ic_grabber_dll.IC_GetPropertyAbsoluteValueRange
    get_property_absolute_value_range.restype = c_int
    get_property_absolute_value_range.argtypes = (GrabberHandlePtr,
                                                  c_char_p,
                                                  c_char_p,
                                                  POINTER(c_float),
                                                  POINTER(c_float))
    
    #///////////////////////////////////////////////////////////////////
    #/*! This returns the current value of an absolute value property.
    #    Usually it is used for exposure. For a list of properties and elements
    #    use the VCDPropertyInspector of IC Imaging Control.
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param Property  The name of the property, e.g. Gain, Exposure
    #    @param Element  The type of the interface, e.g. Value, Auto. If NULL, it is "Value".
    #    @param Value  Receives the value of the property
    #
    #     @retval IC_SUCCESS            Success
    #    @retval IC_NO_HANDLE        Invalid grabber handle
    #    @retval IC_NO_DEVICE        No video capture device opened
    #    @retval IC_PROPERTY_ITEM_NOT_AVAILABLE        A requested property item is not available
    #    @retval IC_PROPERTY_ELEMENT_NOT_AVAILABLE        A requested element of a given property item is not available
    #    @retval IC_PROPERTY_ELEMENT_WRONG_INTERFACE        requested element has not the interface, which is needed.
    #*/
    #int AC IC_GetPropertyAbsoluteValue(HGRABBER hGrabber, char* Property, char *Element, float *Value );
    get_property_absolute_value = _ic_grabber_dll.IC_GetPropertyAbsoluteValue
    get_property_absolute_value.restype = c_int
    get_property_absolute_value.argtypes = (GrabberHandlePtr,
                                            c_char_p,
                                            c_char_p,
                                            POINTER(c_float))
    
    #///////////////////////////////////////////////////////////////////
    #/*! This sets a new value of an absolute value property. Usually it is used for exposure. 
    #    a list of properties and elements
    #    use the VCDPropertyInspector of IC Imaging Control.
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param Property  The name of the property, e.g. Gain, Exposure
    #    @param Element  The type of the interface, e.g. Value, Auto. If NULL, it is "Value".
    #    @param Value  Receives the value of the property
    #
    #     @retval IC_SUCCESS            Success
    #    @retval IC_NO_HANDLE        Invalid grabber handle
    #    @retval IC_NO_DEVICE        No video capture device opened
    #    @retval IC_PROPERTY_ITEM_NOT_AVAILABLE        A requested property item is not available
    #    @retval IC_PROPERTY_ELEMENT_NOT_AVAILABLE        A requested element of a given property item is not available
    #    @retval IC_PROPERTY_ELEMENT_WRONG_INTERFACE        requested element has not the interface, which is needed.
    #*/
    #int AC IC_SetPropertyAbsoluteValue(HGRABBER hGrabber, char* Property, char *Element, float Value );
    set_property_absolute_value = _ic_grabber_dll.IC_SetPropertyAbsoluteValue
    set_property_absolute_value.restype = c_int
    set_property_absolute_value.argtypes = (GrabberHandlePtr,
                                            c_char_p,
                                            c_char_p,
                                            c_float)
    
    #///////////////////////////////////////////////////////////////////
    #/*! This returns the current value of a switch property. Switch properties
    #    are usually used for enabling and disabling of automatics.
    #     For a list of properties and elements
    #    use the VCDPropertyInspector of IC Imaging Control.
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param Property  The name of the property, e.g. Gain, Exposure
    #    @param Element  The type of the interface, e.g. Value, Auto. If NULL, it is "Auto".
    #    @param On  Receives the value of the property
    #
    #     @retval IC_SUCCESS            Success
    #    @retval IC_NO_HANDLE        Invalid grabber handle
    #    @retval IC_NO_DEVICE        No video capture device opened
    #    @retval IC_PROPERTY_ITEM_NOT_AVAILABLE        A requested property item is not available
    #    @retval IC_PROPERTY_ELEMENT_NOT_AVAILABLE        A requested element of a given property item is not available
    #    @retval IC_PROPERTY_ELEMENT_WRONG_INTERFACE        requested element has not the interface, which is needed.
    #*/
    #int AC IC_GetPropertySwitch(HGRABBER hGrabber, char* Property, char *Element, int *On );
    get_property_switch = _ic_grabber_dll.IC_GetPropertySwitch
    get_property_switch.restype = c_int
    get_property_switch.argtypes = (GrabberHandlePtr,
                                    c_char_p,
                                    c_char_p,
                                    POINTER(c_int))
    
    #///////////////////////////////////////////////////////////////////
    #/*! This sets the  value of a switch property. Switch properties
    #    are usually used for enabling and disabling of automatics.
    #     For a list of properties and elements
    #    use the VCDPropertyInspector of IC Imaging Control.
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param Property  The name of the property, e.g. Gain, Exposure
    #    @param Element  The type of the interface, e.g. Value, Auto. If NULL, it is "Auto".
    #    @param On  Receives the value of the property
    #
    #     @retval IC_SUCCESS            Success
    #    @retval IC_NO_HANDLE        Invalid grabber handle
    #    @retval IC_NO_DEVICE        No video capture device opened
    #    @retval IC_PROPERTY_ITEM_NOT_AVAILABLE        A requested property item is not available
    #    @retval IC_PROPERTY_ELEMENT_NOT_AVAILABLE        A requested element of a given property item is not available
    #    @retval IC_PROPERTY_ELEMENT_WRONG_INTERFACE        requested element has not the interface, which is needed.
    #*/
    #int AC IC_SetPropertySwitch(HGRABBER hGrabber, char* Property, char *Element, int On );
    set_property_switch = _ic_grabber_dll.IC_SetPropertySwitch
    set_property_switch.restype = c_int
    set_property_switch.argtypes = (GrabberHandlePtr,
                                    c_char_p,
                                    c_char_p,
                                    c_int)
    
    #//////////////////////////////////////////////////////////////////
    #/*! This executes the on push on a property. These properties are used
    #    for white balance one push or for software trigger.
    #    For a list of properties and elements
    #    use the VCDPropertyInspector of IC Imaging Control.
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param Property  The name of the property, e.g. "Trigger"
    #    @param Element  The type of the interface, e.g. "Software Trigger" 
    #    @param On  Receives the value of the property
    #
    #     @retval IC_SUCCESS            Success
    #    @retval IC_NO_HANDLE        Invalid grabber handle
    #    @retval IC_NO_DEVICE        No video capture device opened
    #    @retval IC_PROPERTY_ITEM_NOT_AVAILABLE        A requested property item is not available
    #    @retval IC_PROPERTY_ELEMENT_NOT_AVAILABLE        A requested element of a given property item is not available
    #    @retval IC_PROPERTY_ELEMENT_WRONG_INTERFACE        requested element has not the interface, which is needed.
    #*/
    #int AC IC_PropertyOnePush(HGRABBER hGrabber, char* Property, char *Element  );
    #
    #
    #//////////////////////////////////////////////////////////////////
    #/*! 
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param Property  The name of the property, e.g. "Strobe"
    #    @param Element  The type of the interface, e.g. "Mode" 
    #    @param StringCount  Receives the count of strings, that is modes, availble
    #    @param Strings pointer to an array of char*, that will contain the mode strings. The array size should be StringCount * 20. Parameter can be null in order to query the number of strings
    #
    #     @retval IC_SUCCESS            Success
    #    @retval IC_NO_HANDLE        Invalid grabber handle
    #    @retval IC_NO_DEVICE        No video capture device opened
    #    @retval IC_PROPERTY_ITEM_NOT_AVAILABLE        A requested property item is not available
    #    @retval IC_PROPERTY_ELEMENT_NOT_AVAILABLE        A requested element of a given property item is not available
    #    @retval IC_PROPERTY_ELEMENT_WRONG_INTERFACE        requested element has not the interface, which is needed.
    #*/
    #int AC IC_GetPropertyMapStrings(HGRABBER hGrabber, char* Property, char *Element, int *StringCount, char **Strings  );
    #
    #
    #//////////////////////////////////////////////////////////////////
    #/*! Return the current set string of a mapstring interface
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param Property  The name of the property, e.g. "Strobe"
    #    @param Element  The type of the interface, e.g. "Mode" 
    #    @param String     pointer to a char*. Size should be atleast 50. There is no check! This contains the result.
    #
    #     @retval IC_SUCCESS            Success
    #    @retval IC_NO_HANDLE        Invalid grabber handle
    #    @retval IC_NO_DEVICE        No video capture device opened
    #    @retval IC_PROPERTY_ITEM_NOT_AVAILABLE        A requested property item is not available
    #    @retval IC_PROPERTY_ELEMENT_NOT_AVAILABLE        A requested element of a given property item is not available
    #    @retval IC_PROPERTY_ELEMENT_WRONG_INTERFACE        requested element has not the interface, which is needed.
    #*/
    #int AC  IC_GetPropertyMapString(HGRABBER hGrabber, char* Property, char *Element,  char *String );
    #
    #//////////////////////////////////////////////////////////////////
    #/*! Set the string of a mapstring interface
    #
    #    @param hGrabber    Handle to a grabber object.
    #    @param Property  The name of the property, e.g. "Strobe"
    #    @param Element  The type of the interface, e.g. "Mode" 
    #    @param String     pointer to a char*. Size should be atleast 50. There is no check! This contains the result.
    #
    #     @retval IC_SUCCESS            Success
    #    @retval IC_NO_HANDLE        Invalid grabber handle
    #    @retval IC_NO_DEVICE        No video capture device opened
    #    @retval IC_PROPERTY_ITEM_NOT_AVAILABLE        A requested property item is not available
    #    @retval IC_PROPERTY_ELEMENT_NOT_AVAILABLE        A requested element of a given property item is not available
    #    @retval IC_PROPERTY_ELEMENT_WRONG_INTERFACE        requested element has not the interface, which is needed.
    #*/
    #int AC  IC_SetPropertyMapString(HGRABBER hGrabber, char* Property, char *Element,  char *String );
    #
    #
    #//////////////////////////////////////////////////////////////////
    #/*! Query number of avaialable frame filters
    #
    #    @retval The count of found frame filters.
    #*/
    #int AC IC_GetAvailableFrameFilterCount();
    get_available_frame_filter_count = _ic_grabber_dll.IC_GetAvailableFrameFilterCount
    get_available_frame_filter_count.restype = c_int
    get_available_frame_filter_count.argtypes = None
    
    #//////////////////////////////////////////////////////////////////
    #/*! Query a list of framefilters
    #
    #    @param szFilterList A two dimensional char array that recieves the list of found frame filters
    #    @param iSize The number of entries in the above list.
    #@code
    #    char szFilterList[80][40];
    #    int iCount;
    #    iCount = IC_GetAvailableFrameFilterCount();
    #
    #    iFormatCount = IC_GetAvailableFrameFilters(szFormatList,iCount );
    #
    #    for( i = 0; i < iCount; i++ )
    #    {
    #        printf("%2d. %s\n",i+1,szFormatList[i]);
    #    }
    #    @endcode
    #*/
    #int AC IC_GetAvailableFrameFilters(char **szFilterList, int iSize );
    get_available_frame_filters = _ic_grabber_dll.IC_GetAvailableFrameFilters
    get_available_frame_filters.restype = c_int
    get_available_frame_filters.argtypes = (POINTER(POINTER((c_char * 80) * 40)),
                                            c_int)
    
    #//////////////////////////////////////////////////////////////////
    #/*! Create a frame filter
    #    @param szFilterName Name of the filter to create
    #    @param FilterHandle Address of a pointer, that will receive the handle of the created filter
    #
    #    @retval IC_SUCCESS    Success
    #    @retval IC_ERROR    If the filter creation failed.
    #*/
    #
    #int AC IC_CreateFrameFilter(char *szFilterName, HFRAMEFILTER *FilterHandle );
    create_frame_filter = _ic_grabber_dll.IC_CreateFrameFilter
    create_frame_filter.restype = c_int
    create_frame_filter.argtypes = (c_char_p, POINTER(structs.FrameFilterHandle))
    
    #//////////////////////////////////////////////////////////////////
    #/*! Add the frame filter to the device
    #    @param hGrabber    Handle to a grabber object.
    #    @param FilterHandle    Handle to a frame filter object.
    #
    #    @retval IC_SUCCESS    Success
    #    @retval IC_ERROR Either hGrabber or FilterHandle was NULL
    #*/
    #int AC IC_AddFrameFilterToDevice(HGRABBER hGrabber, HFRAMEFILTER FilterHandle );
    add_frame_filter_to_device = _ic_grabber_dll.IC_AddFrameFilterToDevice
    add_frame_filter_to_device.restype = c_int
    add_frame_filter_to_device.argtypes = (GrabberHandlePtr,
                                           POINTER(structs.FrameFilterHandle))
    
    #//////////////////////////////////////////////////////////////////
    #/*! Deletes a previously created frame filter.
    #    @param FilterHandle    Handle to a frame filter object.
    #*/
    #void AC IC_DeleteFrameFilter( HFRAMEFILTER FilterHandle );
    #
    #///////////////////////////////////////////////////////////////
    #/* Delete the memory allocated by the HFRAMEFILTER structure. Please remove the frame filter from the HGrabber, 
    #   before deleting it.
    #
    #    @param FilterHandle    Handle to a frame filter object.
    #
    #    @retval IC_SUCCESS    Success
    #    @retval IC_ERROR Either hGrabber or FilterHandle was NULL or the frame filter has no dialog.
    #
    #*/
    #int AC IC_FrameFilterShowDialog( HFRAMEFILTER FilterHandle );
    #
    #///////////////////////////////////////////////////////////////
    #/*! Query a parameter value of a frame filter
    #    @param FilterHandle    Handle to a frame filter object.
    #    @param ParameterName Name of the parameter whose value is to be queried
    #    @param Data pointer to the data, that receives the value. Memory must be allocated before.
    #
    #    @retval IC_SUCCESS    Success
    #    @retval IC_ERROR  Maybe the parameter name does not exist.
    #
    #*/
    #int AC IC_FrameFilterGetParameter(HFRAMEFILTER FilterHandle, char* ParameterName, void* Data );
    frame_filter_get_parameter = _ic_grabber_dll.IC_FrameFilterGetParameter
    frame_filter_get_parameter.restype = c_int
    frame_filter_get_parameter.argtypes = (POINTER(structs.FrameFilterHandle),
                                           c_char_p,
                                           c_void_p)
    
    #/*! Set an int parameter value of a frame filter
    #    @param FilterHandle    Handle to a frame filter object.
    #    @param ParameterName Name of the parameter whose value is to be set
    #    @param Data The data, that contains the value.
    #
    #    @retval IC_SUCCESS    Success
    #    @retval IC_PROPERTY_ITEM_NOT_AVAILABLE the parameter givven by ParameterName does not exist
    #    @retval IC_PROPERTY_ELEMENT_WRONG_INTERFACE The data type, e.g. int does not match to the parameter type, e.g. float
    #    @retval IC_ERROR  Unknown error
    #*/
    #int AC IC_FrameFilterSetParameterInt(HFRAMEFILTER FilterHandle, char* ParameterName, int Data );
    frame_filter_set_parameter_int = _ic_grabber_dll.IC_FrameFilterSetParameterInt
    frame_filter_set_parameter_int.restype = c_int
    frame_filter_set_parameter_int.argtypes = (POINTER(structs.FrameFilterHandle),
                                               c_char_p,
                                               c_int)
    
    #/*! Set a float parameter value of a frame filter
    #    @param FilterHandle    Handle to a frame filter object.
    #    @param ParameterName Name of the parameter whose value is to be set
    #    @param Data The data, that contains the value.
    #
    #    @retval IC_SUCCESS    Success
    #    @retval IC_PROPERTY_ITEM_NOT_AVAILABLE the parameter givven by ParameterName does not exist
    #    @retval IC_PROPERTY_ELEMENT_WRONG_INTERFACE The data type, e.g. int does not match to the parameter type, e.g. float
    #    @retval IC_ERROR  Unknown error
    #*/
    #int AC IC_FrameFilterSetParameterFloat(HFRAMEFILTER FilterHandle, char* ParameterName, float Data );
    #
    #/*! Set a boolean parameter value of a frame filter. boolean means int here.
    #    @param FilterHandle    Handle to a frame filter object.
    #    @param ParameterName Name of the parameter whose value is to be set
    #    @param Data The data, that contains the value.
    #
    #    @retval IC_SUCCESS    Success
    #    @retval IC_PROPERTY_ITEM_NOT_AVAILABLE the parameter givven by ParameterName does not exist
    #    @retval IC_PROPERTY_ELEMENT_WRONG_INTERFACE The data type, e.g. int does not match to the parameter type, e.g. float
    #    @retval IC_ERROR  Unknown error
    #*/
    #int AC IC_FrameFilterSetParameterBoolean(HFRAMEFILTER FilterHandle, char* ParameterName, int Data );
    #
    #/*! Set a string parameter value of a frame filter
    #    @param FilterHandle    Handle to a frame filter object.
    #    @param ParameterName Name of the parameter whose value is to be set
    #    @param Data The data, that contains the value.
    #
    #    @retval IC_SUCCESS    Success
    #    @retval IC_PROPERTY_ITEM_NOT_AVAILABLE the parameter givven by ParameterName does not exist
    #    @retval IC_PROPERTY_ELEMENT_WRONG_INTERFACE The data type, e.g. int does not match to the parameter type, e.g. float
    #    @retval IC_ERROR  Unknown error
    #*/
    #int AC IC_FrameFilterSetParameterString(HFRAMEFILTER FilterHandle, char* ParameterName, char* Data );
    #
    #////////////////////////////////////////////////////////////////////////////
    #/*! Remove all frame filters from the Grabber's device path
    #    @param hGrabber    Handle to a grabber object.
    #
    #*/
    #int AC IC_FrameFilterDeviceClear(HGRABBER hGrabber );
    #
    #
    #typedef struct CODECHANDLE_t__ { int unused; } CODECHANDLE_t; ///<Internal structure of the grabber object handle.
    #
    #//////////////////////////////////////////////////////////////////////////
    #/*! 
    #*/
    ##define    HCODEC CODECHANDLE_t* ///< Type of grabber object handle. Used for all functions. 
    #
    #
    #////////////////////////////////////////////////////////////////////////////
    #/*! Callback type definition for the codec enumenration callback called by
    #    IC_enumCodecs
    #    @retval 1 : Terminate the enumeration, 0 continue enumrating
    #*/
    #
    #typedef int  _cdecl ENUMCODECCB( char* CodecName, void*);
    #
    #////////////////////////////////////////////////////////////////////////////
    #/*! Enumerate all installed codecs. It calls the callback function passed by 
    #    the cb parameter. It ends, if cb returns 0 or all codecs have been enumerated.
    #
    #    @param cb pallack function of type ENUMCODECCB
    #    @param data Pointer to user data
    #*/
    #void AC IC_enumCodecs(ENUMCODECCB cb, void* data);
    #
    #////////////////////////////////////////////////////////////////////////////
    #/*! Creates the codec by the passed name
    #
    #    @param Name Name of the codec to be created
    #    @retval NULL on error, otherwise the created HCODEC
    #*/
    #HCODEC IC_Codec_Create(char* Name);
    #void AC IC_Codec_Release(HCODEC Codec);
    #
    #////////////////////////////////////////////////////////////////////////////
    #/*! Queries a name of a codec passed by _Codec
    #
    #    @param _Codec Handle to the codec
    #    @param l Size in bytes of the memory allocated for name
    #    @param name String that will receive the name of the codec terminated by a \0
    #
    #    @retval IC_SUCCESS on success
    #    @retval IC_NO_HANDLE if _Codec or Name is NULL
    #*/
    #int AC IC_Codec_getName(HCODEC Codec, int l, char* Name);
    #
    #////////////////////////////////////////////////////////////////////////////
    #/*! Return whether a codec passed by _Codec has a property dialog
    #
    #    @param _Codec Handle to the codec
    #
    #    @retval IC_SUCCESS The codec has a dialog
    #    @retval IC_ERROR The codec has no dialog
    #    @retval IC_NO_HANDLE  _Codec is NULL
    #*/
    #int AC IC_Codec_hasDialog(HCODEC Codec);
    #
    #////////////////////////////////////////////////////////////////////////////
    #/*! Shows the property dialog of a codec passed by _Codec
    #
    #    @param name String that will receive the name of the codec terminated by a \0
    #
    #    @retval IC_SUCCESS on success
    #    @retval IC_ERROR On error, e.g. something went wrong with the codec's dialog.
    #    @retval IC_NO_HANDLE if _Codec or Name is NULL
    #*/
    #int AC IC_Codec_showDialog(HCODEC Codec);
    #
    #
    #////////////////////////////////////////////////////////////////////////////
    #/*! Assigns the selected Codec to the Grabber. AVI Capture is prepared. Image
    #    capture does not work anymore.
    #
    #    After doing so, a call to IC_Startlive() starts AVI Capture and IC_Stoplive stopps it,
    #
    #    @param hlGrabber Handle to a grabber with a valid device
    #    @param Codec Handle to the selected codec.
    #
    #    @retval IC_SUCCESS on success
    #*/
    #int AC IC_SetCodec(HGRABBER hlGrabber,HCODEC Codec);
    #
    #
    #////////////////////////////////////////////////////////////////////////////
    #/*! Set the file name for the AVI file
    #
    #    After doing so, a call to IC_Startlive() starts AVI Capture and IC_Stoplive stopps it,
    #
    #    @param hlGrabber Handle to a grabber with a valid device
    #    @param FileName Filename
    #
    #    @retval IC_SUCCESS on success
    #    @retval IC_NO_HANDLE if the grabber is invalid
    #
    #*/
    #int IC_SetAVIFileName(HGRABBER hlGrabber,char * FileName);
    #
    #////////////////////////////////////////////////////////////////////////////
    #/*! Pauses or continues AVI Capture. This allows, to start the stream and see the live video
    #    but images are not saved into the AVI file.
    #
    #    
    #    @param hlGrabber Handle to a grabber with a valid device
    #    @param pause  1 = Pause, nothing saved, 0 = save images!
    #
    #    @retval IC_SUCCESS on success
    #    @retval IC_NO_HANDLE if the grabber is invalid
    #*/
    #
    #int IC_enableAVICapturePause(HGRABBER hlGrabber, int Pause );
    #
    
    def __init__(self):
        raise Exception("You probably don't want to instantiate this class!")


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
