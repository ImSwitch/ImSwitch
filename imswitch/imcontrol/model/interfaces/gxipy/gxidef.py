#!/usr/bin/python
# -*- coding:utf-8 -*-
# -*-mode:python ; tab-width:4 -*- ex:set tabstop=4 shiftwidth=4 expandtab: -*-
#

GAMMA_MIN = 0.1
GAMMA_MAX = 10.0
CONTRAST_MIN = -50
CONTRAST_MAX = 100
UNSIGNED_INT_MAX = 0xFFFFFFFF
UNSIGNED_LONG_LONG_MAX = 0xFFFFFFFFFFFFFFFF


# frame state code
class GxFrameStatusList:
    SUCCESS = 0                 # Normal frame
    INCOMPLETE = -1             # Residual frame
    INVALID_IMAGE_INFO = -2     # invalid image info

    def __init__(self):
        pass


# Device type code
class GxDeviceClassList:
    UNKNOWN = 0                 # Unknown device type
    USB2 = 1                    # USB2.0 vision device
    GEV = 2                     # Gige vision device
    U3V = 3                     # USB3.0 vision device
    SMART = 4                   # Smart device

    def __init__(self):
        pass


class GxAccessMode:
    READONLY = 2                # Open the device in read-only mode
    CONTROL = 3                 # Open the device in controlled mode
    EXCLUSIVE = 4               # Open the device in exclusive mode

    def __init__(self):
        pass


class GxAccessStatus:
    UNKNOWN = 0                # The device's current status is unknown
    READWRITE = 1              # The device currently supports reading and writing
    READONLY = 2               # The device currently only supports reading
    NOACCESS = 3               # The device currently does neither support reading nor support writing

    def __init__(self):
        pass


class GxIPConfigureModeList:
    DHCP = 0x6                 # Enable the DHCP mode to allocate the IP address by the DHCP server
    LLA = 0x4                  # Enable the LLA mode to allocate the IP addresses
    STATIC_IP = 0x5            # Enable the static IP mode to configure the IP address
    DEFAULT = 0x7              # Enable the default mode to configure the IP address

    def __init__(self):
        pass


class GxPixelSizeEntry:
    BPP8 = 8
    BPP10 = 10
    BPP12 = 12
    BPP14 = 14
    BPP16 = 16
    BPP24 = 24
    BPP30 = 30
    BPP32 = 32
    BPP36 = 36
    BPP48 = 48
    BPP64 = 64

    def __init__(self):
        pass


class GxPixelColorFilterEntry:
    NONE = 0
    BAYER_RG = 1
    BAYER_GB = 2
    BAYER_GR = 3
    BAYER_BG = 4

    def __init__(self):
        pass


GX_PIXEL_MONO = 0x01000000
GX_PIXEL_COLOR = 0x02000000
GX_PIXEL_8BIT = 0x00080000
GX_PIXEL_10BIT = 0x000A0000
GX_PIXEL_12BIT = 0x000C0000
GX_PIXEL_16BIT = 0x00100000
GX_PIXEL_24BIT = 0x00180000
GX_PIXEL_30BIT = 0x001E0000
GX_PIXEL_32BIT = 0x00200000
GX_PIXEL_36BIT = 0x00240000
GX_PIXEL_48BIT = 0x00300000
GX_PIXEL_64BIT = 0x00400000


class GxPixelFormatEntry:
    UNDEFINED = 0
    MONO8 = (GX_PIXEL_MONO | GX_PIXEL_8BIT | 0x0001)  # 0x1080001
    MONO8_SIGNED = (GX_PIXEL_MONO | GX_PIXEL_8BIT | 0x0002)  # 0x1080002
    MONO10 = (GX_PIXEL_MONO | GX_PIXEL_16BIT | 0x0003)  # 0x1100003
    MONO12 = (GX_PIXEL_MONO | GX_PIXEL_16BIT | 0x0005)  # 0x1100005
    MONO14 = (GX_PIXEL_MONO | GX_PIXEL_16BIT | 0x0025)  # 0x1100025
    MONO16 = (GX_PIXEL_MONO | GX_PIXEL_16BIT | 0x0007)  # 0x1100007
    BAYER_GR8 = (GX_PIXEL_MONO | GX_PIXEL_8BIT | 0x0008)  # 0x1080008
    BAYER_RG8 = (GX_PIXEL_MONO | GX_PIXEL_8BIT | 0x0009)  # 0x1080009
    BAYER_GB8 = (GX_PIXEL_MONO | GX_PIXEL_8BIT | 0x000A)  # 0x108000A
    BAYER_BG8 = (GX_PIXEL_MONO | GX_PIXEL_8BIT | 0x000B)  # 0x108000B
    BAYER_GR10 = (GX_PIXEL_MONO | GX_PIXEL_16BIT | 0x000C)  # 0x110000C
    BAYER_RG10 = (GX_PIXEL_MONO | GX_PIXEL_16BIT | 0x000D)  # 0x110000D
    BAYER_GB10 = (GX_PIXEL_MONO | GX_PIXEL_16BIT | 0x000E)  # 0x110000E
    BAYER_BG10 = (GX_PIXEL_MONO | GX_PIXEL_16BIT | 0x000F)  # 0x110000F
    BAYER_GR12 = (GX_PIXEL_MONO | GX_PIXEL_16BIT | 0x0010)  # 0x1100010
    BAYER_RG12 = (GX_PIXEL_MONO | GX_PIXEL_16BIT | 0x0011)  # 0x1100011
    BAYER_GB12 = (GX_PIXEL_MONO | GX_PIXEL_16BIT | 0x0012)  # 0x1100012
    BAYER_BG12 = (GX_PIXEL_MONO | GX_PIXEL_16BIT | 0x0013)  # 0x1100013
    BAYER_GR16 = (GX_PIXEL_MONO | GX_PIXEL_16BIT | 0x002E)  # 0x110002E
    BAYER_RG16 = (GX_PIXEL_MONO | GX_PIXEL_16BIT | 0x002F)  # 0x110002F
    BAYER_GB16 = (GX_PIXEL_MONO | GX_PIXEL_16BIT | 0x0030)  # 0x1100030
    BAYER_BG16 = (GX_PIXEL_MONO | GX_PIXEL_16BIT | 0x0031)  # 0x1100031
    RGB8_PLANAR = (GX_PIXEL_COLOR | GX_PIXEL_24BIT | 0x0021)  # 0x2180021
    RGB10_PLANAR = (GX_PIXEL_COLOR | GX_PIXEL_48BIT | 0x0022)  # 0x2300022
    RGB12_PLANAR = (GX_PIXEL_COLOR | GX_PIXEL_48BIT | 0x0023)  # 0x2300023
    RGB16_PLANAR = (GX_PIXEL_COLOR | GX_PIXEL_48BIT | 0x0024)  # 0x2300024

    def __init__(self):
        pass


class GxAcquisitionModeEntry:
    SINGLE_FRAME = 0
    MULITI_FRAME = 1
    CONTINUOUS = 2

    def __init__(self):
        pass


class GxTriggerSourceEntry:
    SOFTWARE = 0
    LINE0 = 1
    LINE1 = 2
    LINE2 = 3
    LINE3 = 4


    def __init__(self):
        pass


class GxTriggerActivationEntry:
    FALLING_EDGE = 0
    RISING_EDGE = 1

    def __init__(self):
        pass


class GxExposureModeEntry:
    TIMED = 1
    TRIGGER_WIDTH = 2

    def __init__(self):
        pass


class GxUserOutputSelectorEntry:
    OUTPUT0 = 1
    OUTPUT1 = 2
    OUTPUT2 = 4

    def __init__(self):
        pass


class GxUserOutputModeEntry:
    STROBE = 0
    USER_DEFINED = 1

    def __init__(self):
        pass


class GxGainSelectorEntry:
    ALL = 0
    RED = 1
    GREEN = 2
    BLUE = 3

    def __init__(self):
        pass


class GxBlackLevelSelectEntry:
    ALL = 0
    RED = 1
    GREEN = 2
    BLUE = 3

    def __init__(self):
        pass


class GxBalanceRatioSelectorEntry:
    RED = 0
    GREEN = 1
    BLUE = 2

    def __init__(self):
        pass


class GxAALightEnvironmentEntry:
    NATURE_LIGHT = 0
    AC50HZ = 1
    AC60HZ = 2

    def __init__(self):
        pass


class GxUserSetEntry:
    DEFAULT = 0
    USER_SET0 = 1

    def __init__(self):
        pass


class GxAWBLampHouseEntry:
    ADAPTIVE = 0
    D65 = 1
    FLUORESCENCE = 2
    INCANDESCENT = 3
    D75 = 4
    D50 = 5
    U30 = 6

    def __init__(self):
        pass


class GxTestPatternEntry:
    OFF = 0
    GRAY_FRAME_RAMP_MOVING = 1
    SLANT_LINE_MOVING = 2
    VERTICAL_LINE_MOVING = 3
    SLANT_LINE = 6

    def __init__(self):
        pass


class GxTriggerSelectorEntry:
    FRAME_START = 1
    FRAME_BURST_START = 2

    def __init__(self):
        pass


class GxLineSelectorEntry:
    LINE0 = 0
    LINE1 = 1
    LINE2 = 2
    LINE3 = 3

    def __init__(self):
        pass


class GxLineModeEntry:
    INPUT = 0
    OUTPUT = 1

    def __init__(self):
        pass


class GxLineSourceEntry:
    OFF = 0
    STROBE = 1
    USER_OUTPUT0 = 2
    USER_OUTPUT1 = 3
    USER_OUTPUT2 = 4
    EXPOSURE_ACTIVE = 5
    FRAME_TRIGGER_WAIT = 6
    ACQUISITION_TRIGGER_WAIT = 7
    TIMER1_ACTIVE = 8

    def __init__(self):
        pass


class GxEventSelectorEntry:
    EXPOSURE_END = 0x0004
    BLOCK_DISCARD = 0x9000
    EVENT_OVERRUN = 0x9001
    FRAME_START_OVER_TRIGGER = 0x9002
    BLOCK_NOT_EMPTY = 0x9003
    INTERNAL_ERROR = 0x9004

    def __init__(self):
        pass


class GxLutSelectorEntry:
    LUMINANCE = 0

    def __init__(self):
        pass


class GxTransferControlModeEntry:
    BASIC = 0
    USER_CONTROLED = 1

    def __init__(self):
        pass


class GxTransferOperationModeEntry:
    MULTI_BLOCK = 0

    def __init__(self):
        pass


class GxTestPatternGeneratorSelectorEntry:
    SENSOR = 0          # Sensor test pattern
    REGION0 = 1         # FPGA test pattern

    def __init__(self):
        pass


class GxChunkSelectorEntry:
    FRAME_ID = 1
    TIME_STAMP = 2
    COUNTER_VALUE = 3

    def __init__(self):
        pass

class GxTimerSelectorEntry:
    TIMER1 = 1         

    def __init__(self):
        pass

class GxTimerTriggerSourceEntry:
    EXPOSURE_START = 1

    def __init__(self):
        pass

class GxCounterSelectorEntry:
    COUNTER1 = 1

    def __init__(self):
        pass

class GxCounterEventSourceEntry:
    FRAME_START = 1

    def __init__(self):
        pass

class GxCounterResetSourceEntry:
    OFF = 0
    SOFTWARE = 1
    LINE0 = 2
    LINE1 = 3
    LINE2 = 4
    LINE3 = 5

    def __init__(self):
        pass

class GxCounterResetActivationEntry:
    RISING_EDGE = 1

    def __init__(self):
        pass               

class GxBinningHorizontalModeEntry:
    SUM = 0
    AVERAGE = 1

    def __init__(self):
        pass


class GxBinningVerticalModeEntry:
    SUM = 0
    AVERAGE = 1

    def __init__(self):
        pass


class GxAcquisitionStatusSelectorEntry:
    ACQUISITION_TRIGGER_WAIT = 0
    FRAME_TRIGGER_WAIT = 1

    def __init__(self):
        pass


class GxGammaModeEntry:
    SRGB = 0
    USER = 1

    def __init__(self):
        pass


class GxColorTransformationModeEntry:
    RGB_TO_RGB = 0
    USER = 1

    def __init__(self):
        pass


class GxColorTransformationValueSelectorEntry:
    GAIN00 = 0
    GAIN01 = 1
    GAIN02 = 2
    GAIN10 = 3
    GAIN11 = 4
    GAIN12 = 5
    GAIN20 = 6
    GAIN21 = 7
    GAIN22 = 8

    def __init__(self):
        pass


class GxAutoEntry:
    OFF = 0
    CONTINUOUS = 1
    ONCE = 2

    def __init__(self):
        pass


class GxSwitchEntry:
    OFF = 0
    ON = 1

    def __init__(self):
        pass


class GxRegionSendModeEntry:
    SINGLE_ROI = 0
    MULTI_ROI = 1

    def __init__(self):
        pass


class GxRegionSelectorEntry:
    REGION0 = 0
    REGION1 = 1
    REGION2 = 2
    REGION3 = 3
    REGION4 = 4
    REGION5 = 5
    REGION6 = 6
    REGION7 = 7

    def __init__(self):
        pass


# image interpolation method
class DxBayerConvertType:
    NEIGHBOUR = 0                           # Neighborhood average interpolation algorithm
    ADAPTIVE = 1                            # Edge adaptive interpolation algorithm
    NEIGHBOUR3 = 2                          # The neighborhood average interpolation algorithm for a larger region

    def __init__(self):
        pass


# image valid bit
class DxValidBit:
    BIT0_7 = 0              # bit 0~7
    BIT1_8 = 1              # bit 1~8
    BIT2_9 = 2              # bit 2~9
    BIT3_10 = 3             # bit 3~10
    BIT4_11 = 4             # bit 4~11

    def __init__(self):
        pass


# image mirror method
class DxImageMirrorMode:
    HORIZONTAL_MIRROR = 0                               # Horizontal mirror
    VERTICAL_MIRROR = 1                                 # Vertical mirror

    def __init__(self):
        pass
