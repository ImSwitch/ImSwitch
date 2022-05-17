#!/usr/bin/python
# -*- coding:utf-8 -*-
# -*-mode:python ; tab-width:4 -*- ex:set tabstop=4 shiftwidth=4 expandtab: -*-
#

from ctypes import *
import sys

if sys.platform == 'linux2' or sys.platform == 'linux':
    try:
        dll = CDLL('/usr/lib/libgxiapi.so')
    except OSError:
        print('Cannot find libgxiapi.so.')
else:
    try:
        dll = WinDLL('DxImageProc.dll')
    except OSError:
        print('Cannot find DxImageProc.dll.')


# status  definition
class DxStatus:
    OK = 0                               # Operation is successful
    PARAMETER_INVALID = -101             # Invalid input parameter
    PARAMETER_OUT_OF_BOUND = -102        # The input parameter is out of bounds
    NOT_ENOUGH_SYSTEM_MEMORY = -103      # System out of memory
    NOT_FIND_DEVICE = -104               # not find device
    STATUS_NOT_SUPPORTED = -105          # operation is not supported
    CPU_NOT_SUPPORT_ACCELERATE = -106    # CPU does not support acceleration
  
    def __init__(self):
        pass


if sys.platform == 'linux2' or sys.platform == 'linux':
    # Bayer layout
    class DxPixelColorFilter:
        NONE = 0                                # Isn't bayer format
        RG = 1                                  # The first row starts with RG
        GB = 2                                  # The first line starts with GB
        GR = 3                                  # The first line starts with GR
        BG = 4                                  # The first line starts with BG

        def __init__(self):
            pass
else:
    # Bayer layout
    class DxPixelColorFilter:
        NONE = 0                                # Isn't bayer format
        BG = 1                                  # The first row starts with BG
        GR = 2                                  # The first line starts with GR
        GB = 3                                  # The first line starts with GB
        RG = 4                                  # The first line starts with RG

        def __init__(self):
            pass


# image actual bits
class DxActualBits:
    BITS_10 = 10             # 10bit
    BITS_12 = 12             # 12bit
    BITS_14 = 14             # 14bit
    BITS_16 = 16             # 16bit

    def __init__(self):
        pass


'''
# mono8 image process structure
class MonoImgProcess(Structure):
    _fields_ = [
        ('defective_pixel_correct',     c_bool),        # Pixel correct switch
        ('sharpness',                   c_bool),        # Sharpness switch　
        ('accelerate',                  c_bool),        # Accelerate switch
        ('sharp_factor',                c_float),       # Sharpen the intensity factor
        ('pro_lut',                     c_char_p),      # Lookup table
        ('lut_length',                  c_ushort),      # Lut Buffer length
        ('array_reserved',              c_ubyte * 32),  # Reserved
    ]

    def __str__(self):
        return "MonoImgProcess\n%s" % "\n".join("%s:\t%s" % (n, getattr(self, n[0])) for n in self._fields_)


# Raw8 Image process structure
class ColorImgProcess(Structure):
    _fields_ = [
        ('defective_pixel_correct',     c_bool),        # Pixel correct switch
        ('denoise',                     c_bool),        # Noise reduction switch
        ('sharpness',                   c_bool),        # Sharpness switch
        ('accelerate',                  c_bool),        # Accelerate switch
        ('arr_cc',                      c_void_p),      # Color processing parameters
        ('cc_buf_length',               c_ubyte),       # Color processing parameters length（sizeof(VxInt16)*9）
        ('sharp_factor',                c_float),       # Sharpen the intensity factor
        ('pro_lut',                     c_char_p),      # Lookup table
        ('lut_length',                  c_ushort),      # The length of the lookup table
        ('cv_type',                     c_uint),        # Interpolation algorithm
        ('layout',                      c_uint),        # Bayer format
        ('flip',                        c_bool),        # Image flip flag
        ('array_reserved',              c_ubyte*32),    # Reserved
    ]

    def __str__(self):
        return "ColorImgProcess\n%s" % "\n".join("%s:\t%s" % (n, getattr(self, n[0])) for n in self._fields_)


if hasattr(dll, 'DxGetLut'):
    def gx_get_lut(contrast_param, gamma, lightness):
        """
        :brief calculating lookup table of 8bit image
        :param contrast_param:  contrast param,range(-50~100)
        :param gamma:           gamma param,range(0.1~10)
        :param lightness:       lightness param,range(-150~150)
        :return: status         State return value, See detail in DxStatus
                 lut            lookup table
                 lut_length     lookup table length(unit:byte)
        """
        contrast_param_c = c_int()
        contrast_param_c.value = contrast_param

        gamma_c = c_double()
        gamma_c.value = gamma

        lightness_c = c_int()
        lightness_c.value = lightness

        lut_length_c = c_int()
        lut_length_c.value = 0

        # Get length of the lookup table
        dll.DxGetLut(contrast_param_c, gamma_c, lightness_c, None, byref(lut_length_c))

        # Create buff to get LUT data
        lut_c = (c_ubyte * lut_length_c.value)()
        status = dll.DxGetLut(contrast_param_c, gamma_c, lightness_c,  byref(lut_c), byref(lut_length_c))

        return status, lut_c, lut_length_c.value
'''

if hasattr(dll, "DxGetGammatLut"):
    def dx_get_gamma_lut(gamma_param):
        """
        :brief  calculating gamma lookup table (RGB24)
        :param  gamma_param:    gamma param,range(0.1 ~ 10)
        :return: status:        State return value, See detail in DxStatus
                gamma_lut:      gamma lookup table
                lut_length:     gamma lookup table length(unit:byte)
        """
        gamma_param_c = c_double()
        gamma_param_c.value = gamma_param

        lut_length_c = c_int()
        status = dll.DxGetGammatLut(gamma_param_c, None, byref(lut_length_c))

        gamma_lut = (c_ubyte * lut_length_c.value)()
        status = dll.DxGetGammatLut(gamma_param_c, byref(gamma_lut), byref(lut_length_c))

        return status, gamma_lut, lut_length_c.value


if hasattr(dll, "DxGetContrastLut"):
    def dx_get_contrast_lut(contrast_param):
        """
        :brief  ccalculating contrast lookup table (RGB24)
        :param  contrast_param: contrast param,range(-50 ~ 100)
        :return: status：       State return value, See detail in DxStatus
                 contrast_lut： contrast lookup table
                 lut_length：   contrast lookup table length(unit:byte)
        """
        contrast_param_c = c_int()
        contrast_param_c.value = contrast_param

        lut_length_c = c_int()
        status = dll.DxGetContrastLut(contrast_param_c, None, byref(lut_length_c))

        contrast_lut = (c_ubyte * lut_length_c.value)()
        status = dll.DxGetContrastLut(contrast_param_c, byref(contrast_lut), byref(lut_length_c))

        return status, contrast_lut, lut_length_c.value


if hasattr(dll, 'DxRaw8toRGB24'):
    def dx_raw8_to_rgb24(input_address, output_address, width, height, convert_type, bayer_type, flip):
        """
        :brief  Convert Raw8 to Rgb24
        :param input_address:      The input raw image buff address, buff size = width * height
        :param output_address:     The output rgb image buff address, buff size = width * height * 3
        :param width:           Image width
        :param height:          Image height
        :param convert_type:    Bayer convert type, See detail in DxBayerConvertType
        :param bayer_type:      pixel color filter, See detail in DxPixelColorFilter
        :param flip:            Output image flip flag
                                True: turn the image upside down
                                False: do not flip
        :return: status         State return value, See detail in DxStatus
                 data_array     Array of output images, buff size = width * height * 3
        """
        width_c = c_uint()
        width_c.value = width

        height_c = c_uint()
        height_c.value = height

        convert_type_c = c_uint()
        convert_type_c.value = convert_type

        bayer_type_c = c_uint()
        bayer_type_c.value = bayer_type

        flip_c = c_bool()
        flip_c.value = flip

        input_address_p = c_void_p()
        input_address_p.value = input_address

        output_address_p = c_void_p()
        output_address_p.value = output_address

        status = dll.DxRaw8toRGB24(input_address_p, output_address_p,
                                   width_c, height_c, convert_type_c, bayer_type_c, flip_c)
        return status


if hasattr(dll, 'DxRaw16toRaw8'):
    def dx_raw16_to_raw8(input_address, out_address, width, height, valid_bits):
        """
        :biref  Raw16 converted to Raw8
        :param  input_address:     The input image buff address, buff size = width * height * 2
        :param  out_address:       The output image buff address, buff size = width * height
        :param  width:          Image width
        :param  height:         Image height
        :param  valid_bits:     Data valid digit, See detail in DxValidBit
        :return: status         State return value, See detail in DxStatus
                 data_array     Array of output images, buff size = width * height
        """
        width_c = c_uint()
        width_c.value = width

        height_c = c_uint()
        height_c.value = height

        valid_bits_c = c_uint()
        valid_bits_c.value = valid_bits

        input_address_p = c_void_p()
        input_address_p.value = input_address

        out_address_p = c_void_p()
        out_address_p.value = out_address

        status = dll.DxRaw16toRaw8(input_address_p, out_address_p,
                                   width_c, height_c, valid_bits_c)
        return status


if hasattr(dll, "DxImageImprovment"):
    def dx_image_improvement(input_address, output_address, width, height,
                             color_correction_param, contrast_lut, gamma_lut):
        """
        :brief      image quality improvement
        :param      input_address:              input buffer address, buff size = width * height *3
        :param      output_address:             input buffer address, buff size = width * height *3
        :param      width:                      image width
        :param      height:                     image height
        :param      color_correction_param:     color correction param(get from camera)
        :param      contrast_lut:               contrast lookup table
        :param      gamma_lut:                  gamma lookup table
        :return:    status                      State return value, See detail in DxStatus
                    data_array                  Array of output images, buff size = width * height * 3
        """
        width_c = c_uint()
        width_c.value = width

        height_c = c_uint()
        height_c.value = height

        input_address_p = c_void_p()
        input_address_p.value = input_address

        output_address_p = c_void_p()
        output_address_p.value = output_address

        color_correction_param_p = c_int64()
        color_correction_param_p.value = color_correction_param

        status = dll.DxImageImprovment(input_address_p, output_address_p, width_c, height_c,
                                       color_correction_param_p, contrast_lut, gamma_lut)
        return status

