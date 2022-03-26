#!/usr/bin/python
# -*-mode:python ; tab-width:4 -*- ex:set tabstop=4 shiftwidth=4 expandtab: -*-
# -*- coding:utf-8 -*-

from ctypes import *
import sys


if sys.platform == 'linux2' or sys.platform == 'linux':
    try:
        dll = CDLL('/usr/lib/libgxiapi.so')
    except OSError:
        print("Cannot find libgxiapi.so.")
else:
    try:
        dll = WinDLL('GxIAPI.dll')
    except OSError:
        print('Cannot find GxIAPI.dll.')


# Error code
class GxStatusList:
    SUCCESS = 0	                # Success
    ERROR = -1                  # There is a unspecified internal error that is not expected to occur
    NOT_FOUND_TL = -2           # The TL library cannot be found
    NOT_FOUND_DEVICE = -3       # The device is not found
    OFFLINE = -4                # The current device is in a offline state
    INVALID_PARAMETER = -5      # Invalid parameter, Generally the pointer is NULL or the input IP and
                                # Other parameter formats are invalid
    INVALID_HANDLE = -6         # Invalid handle
    INVALID_CALL = -7           # The interface is invalid, which refers to software interface logic error
    INVALID_ACCESS = -8         # The function is currently inaccessible or the device access mode is incorrect
    NEED_MORE_BUFFER = -9       # The user request buffer is insufficient: the user input buffersize during
                                # the read operation is less than the actual need
    ERROR_TYPE = -10            # The type of FeatureID used by the user is incorrect,
                                # such as an integer interface using a floating-point function code
    OUT_OF_RANGE = -11          # The value written by the user is crossed
    NOT_IMPLEMENTED = -12       # This function is not currently supported
    NOT_INIT_API = -13          # There is no call to initialize the interface
    TIMEOUT = -14               # Timeout error
    REPEAT_OPENED = -1004       # The device has been opened

    def __init__(self):
        pass


class GxOpenMode:
    SN = 0	                   # Opens the device via a serial number
    IP = 1                     # Opens the device via an IP address
    MAC = 2                    # Opens the device via a MAC address
    INDEX = 3                  # Opens the device via a serial number(Start from 1)
    USER_ID = 4                # Opens the device via user defined ID

    def __init__(self):
        pass


class GxFrameMask:
    TYPE_MASK = 0xF0000000
    LEVEL_MASK = 0x0F000000
    
    def __init__(self):
        pass
    

class GxFeatureType:
    INT = 0x10000000            # Integer type
    FLOAT = 0X20000000          # Floating point type
    ENUM = 0x30000000           # Enum type
    BOOL = 0x40000000           # Boolean type
    STRING = 0x50000000         # String type
    BUFFER = 0x60000000         # Block data type
    COMMAND = 0x70000000        # Command type

    def __init__(self):
        pass


class GxFeatureLevel:
    REMOTE_DEV = 0x00000000     # RemoteDevice Layer
    TL = 0x01000000             # TL Layer
    IF = 0x02000000             # Interface Layer
    DEV = 0x03000000            # Device Layer
    DS = 0x04000000             # DataStream Layer

    def __init__(self):
        pass


class GxFeatureID:
    # ---------------Device Information Section---------------------------
    STRING_DEVICE_VENDOR_NAME = 0x50000000                 # The name of the device's vendor
    STRING_DEVICE_MODEL_NAME = 0x50000001                  # The model name of the device
    STRING_DEVICE_FIRMWARE_VERSION = 0x50000002            # The version of the device's firmware and software
    STRING_DEVICE_VERSION = 0x50000003                     # The version of the device
    STRING_DEVICE_SERIAL_NUMBER = 0x50000004               # A serial number for device
    STRING_FACTORY_SETTING_VERSION = 0x50000006            # The version of the device's Factory Setting
    STRING_DEVICE_USER_ID = 0x50000007                     # A user programmable string
    INT_DEVICE_LINK_SELECTOR = 0x10000008                  # Selects which Link of the device to control
    ENUM_DEVICE_LINK_THROUGHPUT_LIMIT_MODE = 0x30000009    # DeviceLinkThroughputLimit switch
    INT_DEVICE_LINK_THROUGHPUT_LIMIT = 0x1000000a          # Limits the maximum bandwidth of the data
    INT_DEVICE_LINK_CURRENT_THROUGHPUT = 0x1000000b        # Current bandwidth of the data
    COMMAND_DEVICE_RESET = 0x7000000c                      # Device reset
    INT_TIMESTAMP_TICK_FREQUENCY = 0x1000000d              # Timestamp tick frequency
    COMMAND_TIMESTAMP_LATCH = 0x7000000e                   # Timestamp latch
    COMMAND_TIMESTAMP_RESET = 0x7000000f                   # Timestamp reset
    COMMAND_TIMESTAMP_LATCH_RESET = 0x70000010             # Timestamp latch reset
    INT_TIMESTAMP_LATCH_VALUE = 0x10000011                 # The value of timestamp latch

    # ---------------ImageFormat Section----------------------------------
    INT_SENSOR_WIDTH = 0x100003e8                           # The actual width of the camera's sensor in pixels
    INT_SENSOR_HEIGHT = 0x100003e9                          # The actual height of the camera's sensor in pixels
    INT_WIDTH_MAX = 0x100003ea                              # Width max[read_only]
    INT_HEIGHT_MAX = 0x100003eb                             # Height max[read_only]
    INT_OFFSET_X = 0x100003ec                               # The X offset for the area of interest
    INT_OFFSET_Y = 0x100003ed                               # The Y offset for the area of interest
    INT_WIDTH = 0x100003ee                                  # the width of the area of interest in pixels
    INT_HEIGHT = 0x100003ef                                 # the height of the area of interest in pixels
    INT_BINNING_HORIZONTAL = 0x100003f0                     # Horizontal pixel Binning
    INT_BINNING_VERTICAL = 0x100003f1                       # Vertical pixel Binning
    INT_DECIMATION_HORIZONTAL = 0x100003f2                  # Horizontal pixel sampling
    INT_DECIMATION_VERTICAL = 0x100003f3                    # Vertical pixel sampling
    ENUM_PIXEL_SIZE = 0x300003f4                            # Pixel depth, Reference GxPixelSizeEntry
    ENUM_PIXEL_COLOR_FILTER = 0x300003f5                    # Bayer format, Reference GxPixelColorFilterEntry
    ENUM_PIXEL_FORMAT = 0x300003f6                          # Pixel format, Reference GxPixelFormatEntry
    BOOL_REVERSE_X = 0x400003f7                             # Horizontal flipping
    BOOL_REVERSE_Y = 0x400003f8                             # Vertical flipping
    ENUM_TEST_PATTERN = 0x300003f9                          # Test pattern, Reference GxTestPatternEntry
    ENUM_TEST_PATTERN_GENERATOR_SELECTOR = 0x300003fa       # The source of test pattern, reference GxTestPatternGeneratorSelectorEntry
    ENUM_REGION_SEND_MODE = 0x300003fb                      # ROI region output mode, reference GxRegionSendModeEntry
    ENUM_REGION_MODE = 0x300003fc                           # ROI region output switch
    ENUM_REGION_SELECTOR = 0x300003fd                       # ROI region select, reference GxRegionSelectorEntry
    INT_CENTER_WIDTH = 0x100003fe                           # Window width
    INT_CENTER_HEIGHT = 0x100003ff                          # Window height
    ENUM_BINNING_HORIZONTAL_MODE = 0x30000400               # Binning horizontal mode
    ENUM_BINNING_VERTICAL_MODE = 0x30000401                 # Binning vertical mode

    # ---------------TransportLayer Section-------------------------------
    INT_PAYLOAD_SIZE = 0x100007d0                           # Size of images in byte
    BOOL_GEV_CURRENT_IP_CONFIGURATION_LLA = 0x400007d1      # IP configuration by LLA.
    BOOL_GEV_CURRENT_IP_CONFIGURATION_DHCP = 0x400007d2     # IP configuration by DHCP
    BOOL_GEV_CURRENT_IP_CONFIGURATION_PERSISTENT_IP = 0x400007d3   # IP configuration by PersistentIP
    INT_ESTIMATED_BANDWIDTH = 0x100007d4                    # Estimated Bandwidth in Bps
    INT_GEV_HEARTBEAT_TIMEOUT = 0x100007d5                  # The heartbeat timeout in milliseconds
    INT_GEV_PACKET_SIZE = 0x100007d6                        # The packet size in bytes for each packet
    INT_GEV_PACKET_DELAY = 0x100007d7                       # A delay between the transmission of each packet
    INT_GEV_LINK_SPEED = 0x100007d8                         # The connection speed in Mbps

    # ---------------AcquisitionTrigger Section---------------------------
    ENUM_ACQUISITION_MODE = 0x30000bb8                      # The mode of acquisition, Reference: GxAcquisitionModeEntry
    COMMAND_ACQUISITION_START = 0x70000bb9                  # The command for starts the acquisition of images
    COMMAND_ACQUISITION_STOP = 0x70000bba                   # The command for stop the acquisition of images
    INT_ACQUISITION_SPEED_LEVEL = 0x10000bbb                # The level for acquisition speed
    INT_ACQUISITION_FRAME_COUNT = 0x10000bbc
    ENUM_TRIGGER_MODE = 0x30000bbd                          # Trigger mode, Reference:GxTriggerModeEntry
    COMMAND_TRIGGER_SOFTWARE = 0x70000bbe                   # The command for generates a software trigger signal
    ENUM_TRIGGER_ACTIVATION = 0x30000bbf                    # Trigger polarity, Reference GxTriggerActivationEntry
    ENUM_TRIGGER_SWITCH = 0x30000bc0                        # The switch of External trigger
    FLOAT_EXPOSURE_TIME = 0x20000bc1                        # Exposure time
    ENUM_EXPOSURE_AUTO = 0x30000bc2                         # Exposure auto
    FLOAT_TRIGGER_FILTER_RAISING = 0x20000bc3               # The Value of rising edge triggered filter
    FLOAT_TRIGGER_FILTER_FALLING = 0x20000bc4               # The Value of falling edge triggered filter
    ENUM_TRIGGER_SOURCE = 0x30000bc5                        # Trigger source, Reference GxTriggerSourceEntry
    ENUM_EXPOSURE_MODE = 0x30000bc6                         # Exposure mode, Reference GxExposureModeEntry
    ENUM_TRIGGER_SELECTOR = 0x30000bc7                      # Trigger type, Reference GxTriggerSelectorEntry
    FLOAT_TRIGGER_DELAY = 0x20000bc8                        # The trigger delay in microsecond
    ENUM_TRANSFER_CONTROL_MODE = 0x30000bc9                 # The control method for the transfers, Reference GxTransferControlModeEntry
    ENUM_TRANSFER_OPERATION_MODE = 0x30000bca               # The operation method for the transfers, Reference GxTransferOperationModeEntry
    COMMAND_TRANSFER_START = 0x70000bcb                     # Starts the streaming of data blocks out of the device
    INT_TRANSFER_BLOCK_COUNT = 0x10000bcc                   # The number of data Blocks that the device should stream before stopping
    BOOL_FRAME_STORE_COVER_ACTIVE = 0x40000bcd              # The switch for frame cover
    ENUM_ACQUISITION_FRAME_RATE_MODE = 0x30000bce           # The switch for Control frame rate
    FLOAT_ACQUISITION_FRAME_RATE = 0x20000bcf               # The value for Control frame rate
    FLOAT_CURRENT_ACQUISITION_FRAME_RATE = 0x20000bd0       # The maximum allowed frame acquisition rate
    ENUM_FIXED_PATTERN_NOISE_CORRECT_MODE = 0x30000bd1      # The switch of fixed pattern noise correct
    INT_ACQUISITION_BURST_FRAME_COUNT = 0x10000bd6          # The acquisition burst frame count
    ENUM_ACQUISITION_STATUS_SELECTOR = 0x30000bd7           # The selector of acquisition status
    BOOL_ACQUISITION_STATUS = 0x40000bd8                    # The acquisition status
    FLOAT_EXPOSURE_DELAY = 0x2000765c                       # The exposure delay

    # ----------------DigitalIO Section-----------------------------------
    ENUM_USER_OUTPUT_SELECTOR = 0x30000fa0                  # selects user settable output signal, Reference GxUserOutputSelectorEntry
    BOOL_USER_OUTPUT_VALUE = 0x40000fa1                     # The state of the output signal
    ENUM_USER_OUTPUT_MODE = 0x30000fa2                      # UserIO output mode, Reference GxUserOutputModeEntry
    ENUM_STROBE_SWITCH = 0x30000fa3                         # Strobe switch
    ENUM_LINE_SELECTOR = 0x30000fa4                         # Line selector, Reference GxLineSelectorEntry
    ENUM_LINE_MODE = 0x30000fa5                             # Line mode, Reference GxLineModeEntry
    BOOL_LINE_INVERTER = 0x40000fa6                         # Pin level reversal
    ENUM_LINE_SOURCE = 0x30000fa7                           # line source, Reference GxLineSourceEntry
    BOOL_LINE_STATUS = 0x40000fa8                           # line status
    INT_LINE_STATUS_ALL = 0x10000fa9                        # all line status
    FLOAT_PULSE_WIDTH = 0x20000faa                          #

    # ----------------AnalogControls Section------------------------------
    ENUM_GAIN_AUTO = 0x30001388                             # gain auto, Reference GxGainAutoEntry
    ENUM_GAIN_SELECTOR = 0x30001389                         # selects gain channel, Reference GxGainSelectorEntry
    ENUM_BLACK_LEVEL_AUTO = 0x3000138b                      # Black level auto, Reference GxBlackLevelAutoEntry
    ENUM_BLACK_LEVEL_SELECTOR = 0x3000138c                  # Black level channel, Reference GxBlackLevelSelectEntry
    ENUM_BALANCE_WHITE_AUTO = 0x3000138e                    # Balance white auto, Reference GxBalanceWhiteAutoEntry
    ENUM_BALANCE_RATIO_SELECTOR = 0x3000138f                # selects Balance white channel, Reference GxBalanceRatioSelectorEntry
    FLOAT_BALANCE_RATIO = 0x20001390                        # Balance white channel ratio
    ENUM_COLOR_CORRECT = 0x30001391                         # Color correct, Reference GxColorCorrectEntry
    ENUM_DEAD_PIXEL_CORRECT = 0x30001392                    # Pixel correct, Reference GxDeadPixelCorrectEntry
    FLOAT_GAIN = 0x20001393                                 # gain
    FLOAT_BLACK_LEVEL = 0x20001394                          # Black level
    BOOL_GAMMA_ENABLE = 0x40001395                          # Gamma enable bit
    ENUM_GAMMA_MODE = 0x30001396                            # Gamma mode
    FLOAT_GAMMA = 0x20001397                                # The value of Gamma
    INT_DIGITAL_SHIFT = 0x10001398                          #

    # ---------------CustomFeature Section--------------------------------
    INT_ADC_LEVEL = 0x10001770                              # AD conversion level
    INT_H_BLANKING = 0x10001771                             # Horizontal blanking
    INT_V_BLANKING = 0x10001772                             # Vertical blanking
    STRING_USER_PASSWORD = 0x50001773                       # User encrypted zone cipher
    STRING_VERIFY_PASSWORD = 0x50001774                     # User encrypted zone check cipher
    BUFFER_USER_DATA = 0x60001775                           # User encrypted area content
    INT_GRAY_VALUE = 0x10001776                             # Expected gray value
    ENUM_AA_LIGHT_ENVIRONMENT = 0x30001777                  # Gain auto, Exposure auto, Light environment type,
                                                            # Reference GxAALightEnvironmentEntry
    INT_AAROI_OFFSETX = 0x10001778                          # The X offset for the rect of interest in pixels for 2A
    INT_AAROI_OFFSETY = 0x10001779                          # The Y offset for the rect of interest in pixels for 2A
    INT_AAROI_WIDTH = 0x1000177a                            # The width offset for the rect of interest in pixels for 2A
    INT_AAROI_HEIGHT = 0x1000177b                           # The height offset for the rect of interest in pixels for 2A
    FLOAT_AUTO_GAIN_MIN = 0x2000177c                        # Automatic gain minimum
    FLOAT_AUTO_GAIN_MAX = 0x2000177d                        # Automatic gain maximum
    FLOAT_AUTO_EXPOSURE_TIME_MIN = 0x2000177e               # Automatic exposure minimum
    FLOAT_AUTO_EXPOSURE_TIME_MAX = 0x2000177f               # Automatic exposure maximum
    BUFFER_FRAME_INFORMATION = 0x60001780                   # Image frame information
    INT_CONTRAST_PARAM = 0x10001781                         # Contrast parameter
    FLOAT_GAMMA_PARAM = 0x20001782                          # Gamma parameter
    INT_COLOR_CORRECTION_PARAM = 0x10001783                 # Color correction param
    ENUM_IMAGE_GRAY_RAISE_SWITCH = 0x30001784               # Image gray raise, Reference GxImageGrayRaiseSwitchEntry
    ENUM_AWB_LAMP_HOUSE = 0x30001785                        # Automatic white balance light source
                                                            # Reference GxAWBLampHouseEntry
    INT_AWBROI_OFFSETX = 0x10001786                         # Offset_X of automatic white balance region
    INT_AWBROI_OFFSETY = 0x10001787                         # Offset_Y of automatic white balance region
    INT_AWBROI_WIDTH = 0x10001788                           # Width of automatic white balance region
    INT_AWBROI_HEIGHT = 0x10001789                          # Height of automatic white balance region
    ENUM_SHARPNESS_MODE = 0x3000178a                        # Sharpness mode, Reference GxSharpnessModeEntry
    FLOAT_SHARPNESS = 0x2000178b                            # Sharpness

    # ---------------UserSetControl Section-------------------------------
    ENUM_USER_SET_SELECTOR = 0x30001b58                     # Parameter group selection, Reference GxUserSetSelectorEntry
    COMMAND_USER_SET_LOAD = 0x70001b59                      # Load parameter group
    COMMAND_USER_SET_SAVE = 0x70001b5a                      # Save parameter group
    ENUM_USER_SET_DEFAULT = 0x30001b5b                      # Startup parameter group, Reference GxUserSetDefaultEntry

    # ---------------Event Section----------------------------------------
    ENUM_EVENT_SELECTOR = 0x30001f40                        # Event source select, Reference GxEventSelectorEntry
    ENUM_EVENT_NOTIFICATION = 0x30001f41                    # Event enabled, Reference GxEventNotificationEntry
    INT_EVENT_EXPOSURE_END = 0x10001f42                     # Exposure end event
    INT_EVENT_EXPOSURE_END_TIMESTAMP = 0x10001f43           # The timestamp of Exposure end event
    INT_EVENT_EXPOSURE_END_FRAME_ID = 0x10001f44            # The frame id of Exposure end event
    INT_EVENT_BLOCK_DISCARD = 0x10001f45                    # Block discard event
    INT_EVENT_BLOCK_DISCARD_TIMESTAMP = 0x10001f46          # The timestamp of Block discard event
    INT_EVENT_OVERRUN = 0x10001f47                          # Event queue overflow event
    INT_EVENT_OVERRUN_TIMESTAMP = 0x10001f48                # The timestamp of event queue overflow event
    INT_EVENT_FRAME_START_OVER_TRIGGER = 0x10001f49         # Trigger signal shield event
    INT_EVENT_FRAME_START_OVER_TRIGGER_TIMESTAMP = 0x10001f4a   # The timestamp of trigger signal shield event
    INT_EVENT_BLOCK_NOT_EMPTY = 0x10001f4b                  # Frame memory not empty event
    INT_EVENT_BLOCK_NOT_EMPTY_TIMESTAMP = 0x10001f4c        # The timestamp of frame memory not empty event
    INT_EVENT_INTERNAL_ERROR = 0x10001f4d                   # Internal erroneous event
    INT_EVENT_INTERNAL_ERROR_TIMESTAMP = 0x10001f4e         # The timestamp of internal erroneous event

    # ---------------LUT Section------------------------------------------
    ENUM_LUT_SELECTOR = 0x30002328                          # Select lut, Reference GxLutSelectorEntry
    BUFFER_LUT_VALUE_ALL = 0x60002329                       # Lut data
    BOOL_LUT_ENABLE = 0x4000232a                            # Lut enable bit
    INT_LUT_INDEX = 0x1000232b                              # Lut index
    INT_LUT_VALUE = 0x1000232c                              # Lut value

    # ---------------Color Transformation Control-------------------------
    ENUM_COLOR_TRANSFORMATION_MODE = 0x30002af8             # Color transformation mode
    BOOL_COLOR_TRANSFORMATION_ENABLE = 0x40002af9           # Color transformation enable bit
    ENUM_COLOR_TRANSFORMATION_VALUE_SELECTOR = 0x30002afa   # The selector of color transformation value
    FLOAT_COLOR_TRANSFORMATION_VALUE = 0x20002afb           # The value of color transformation

    # ---------------ChunkData Section------------------------------------
    BOOL_CHUNK_MODE_ACTIVE = 0x40002711                     # Enable frame information
    ENUM_CHUNK_SELECTOR = 0x30002712                        # Select frame information channel, Reference GxChunkSelectorEntry
    BOOL_CHUNK_ENABLE = 0x40002713                          # Enable single frame information channel

    # ---------------Device Feature---------------------------------------
    INT_COMMAND_TIMEOUT = 0x13000000                        # The time of command timeout
    INT_COMMAND_RETRY_COUNT = 0x13000001                    # Command retry times

    # ---------------DataStream Feature-----------------------------------
    INT_ANNOUNCED_BUFFER_COUNT = 0x14000000                 # The number of Buffer declarations
    INT_DELIVERED_FRAME_COUNT = 0x14000001                  # Number of received frames (including remnant frames)
    INT_LOST_FRAME_COUNT = 0x14000002                       # Number of lost frames caused by buffer deficiency
    INT_INCOMPLETE_FRAME_COUNT = 0x14000003                 # Number of residual frames received
    INT_DELIVERED_PACKET_COUNT = 0x14000004                 # The number of packets received
    INT_RESEND_PACKET_COUNT = 0x14000005                    # Number of retransmission packages
    INT_RESCUED_PACKED_COUNT = 0x14000006                   # Retransmission success package number
    INT_RESEND_COMMAND_COUNT = 0x14000007                   # Retransmission command times
    INT_UNEXPECTED_PACKED_COUNT = 0x14000008                # Exception packet number
    INT_MAX_PACKET_COUNT_IN_ONE_BLOCK = 0x14000009          # Data block maximum retransmission number
    INT_MAX_PACKET_COUNT_IN_ONE_COMMAND = 0x1400000a        # The maximum number of packets contained in one command
    INT_RESEND_TIMEOUT = 0x1400000b                         # Retransmission timeout time
    INT_MAX_WAIT_PACKET_COUNT = 0x1400000c                  # Maximum waiting packet number
    ENUM_RESEND_MODE = 0x3400000d                           # Retransmission mode, Reference GxDSResendModeEntry
    INT_MISSING_BLOCK_ID_COUNT = 0x1400000e                 # BlockID lost number
    INT_BLOCK_TIMEOUT = 0x1400000f                          # Data block timeout time
    INT_STREAM_TRANSFER_SIZE = 0x14000010                   # Data block size
    INT_STREAM_TRANSFER_NUMBER_URB = 0x14000011             # Number of data blocks
    INT_MAX_NUM_QUEUE_BUFFER = 0x14000012                   # The maximum Buffer number of the collection queue
    INT_PACKET_TIMEOUT = 0x14000013                         # Packet timeout time

    def __init__(self):
        pass


class GxDeviceIPInfo(Structure):
    _fields_ = [
        ('device_id', c_char * 68),         # The unique identifier of the device.
        ('mac', c_char * 32),               # MAC address
        ('ip', c_char * 32),                # IP address
        ('subnet_mask', c_char * 32),       # Subnet mask
        ('gateway', c_char * 32),           # Gateway
        ('nic_mac', c_char * 32),           # The MAC address of the corresponding NIC(Network Interface Card).
        ('nic_ip', c_char * 32),            # The IP of the corresponding NIC
        ('nic_subnet_mask', c_char * 32),   # The subnet mask of the corresponding NIC
        ('nic_gateWay', c_char * 32),       # The Gateway of the corresponding NIC
        ('nic_description', c_char * 132),  # The description of the corresponding NIC
        ('reserved', c_char * 512),         # Reserved 512 bytes
    ]

    def __str__(self):
        return "GxDeviceIPInfo\n%s" % "\n".join("%s:\t%s" % (n, getattr(self, n[0])) for n in self._fields_)


class GxDeviceBaseInfo(Structure):
    _fields_ = [
        ('vendor_name', c_char*32),         # Vendor name
        ('model_name', c_char*32),          # TModel name
        ('serial_number', c_char*32),       # Serial number
        ('display_name', c_char*132),       # Display name
        ('device_id', c_char*68),           # The unique identifier of the device.
        ('user_id', c_char*68),             # User's custom name
        ('access_status', c_int),           # Access status that is currently supported by the device
                                            # Refer to GxAccessStatus
        ('device_class', c_int),            # Device type. Such as USB2.0, GEV.
        ('reserved', c_char*300),           # Reserved 300 bytes
    ]

    def __str__(self):
        return "GxDeviceBaseInfo\n%s" % "\n".join("%s:\t%s" % (n, getattr(self, n[0])) for n in self._fields_)


class GxOpenParam(Structure):
    _fields_ = [
        ('content',             c_char_p),
        ('open_mode',           c_uint),
        ('access_mode',         c_uint),
    ]

    def __str__(self):
        return "GxOpenParam\n%s" % "\n".join( "%s:\t%s" % (n, getattr(self, n[0])) for n in self._fields_)


class GxFrameCallbackParam(Structure):
    _fields_ = [
        ('user_param_index',    c_void_p),      # User private data
        ('status',              c_int),         # The return state of the image
        ('image_buf',           c_void_p),      # Image buff address
        ('image_size',          c_int),         # Image data size, Including frame information
        ('width',               c_int),         # Image width
        ('height',              c_int),         # Image height
        ('pixel_format',        c_int),         # Image PixFormat
        ('frame_id',            c_ulonglong),   # The frame id of the image
        ('timestamp',           c_ulonglong),   # Time stamp of image
        ('reserved',            c_int),         # Reserved
    ]

    def __str__(self):
        return "GxFrameCallbackParam\n%s" % "\n".join("%s:\t%s" % (n, getattr(self, n[0])) for n in self._fields_)


class GxFrameData(Structure):
    _fields_ = [
        ('status', c_int),                      # The return state of the image
        ('image_buf', c_void_p),                # Image buff address
        ('width', c_int),                       # Image width
        ('height', c_int),                      # Image height
        ('pixel_format', c_int),                # Image PixFormat
        ('image_size', c_int),                  # Image data size, Including frame information
        ('frame_id', c_ulonglong),              # The frame id of the image
        ('timestamp', c_ulonglong),             # Time stamp of image
        ('buf_id', c_ulonglong),                # Image buff ID
        ('reserved',  c_int),                   # Reserved
    ]

    def __str__(self):
        return "GxFrameData\n%s" % "\n".join("%s:\t%s" % (n, getattr(self, n[0])) for n in self._fields_)


class GxIntRange(Structure):
    _fields_ = [
        ('min',                 c_ulonglong),
        ('max',                 c_ulonglong),
        ('inc',                 c_ulonglong),
        ('reserved',            c_int * 8),
    ]

    def __str__(self):
        return "GxIntRange\n%s" % "\n".join("%s:\t%s" % (n, getattr(self, n[0])) for n in self._fields_)


class GxFloatRange(Structure):
    _fields_ = [
        ('min',                 c_double),
        ('max',                 c_double),
        ('inc',                 c_double),
        ('unit',                c_char * 8),
        ('inc_is_valid',        c_bool),
        ('reserved',            c_char * 31),
    ]

    def __str__(self):
        return "GxFloatRange\n%s" % "\n".join("%s:\t%s" % (n, getattr(self, n[0])) for n in self._fields_)


class GxEnumDescription(Structure):
    _fields_ = [
        ('value',               c_longlong),    # Enum value
        ('symbolic',            c_char * 64),   # Character description
        ('reserved',            c_int * 8),
    ]

    def __str__(self):
        return "GxEnumDescription\n%s" % "\n".join("%s:\t%s" % (n, getattr(self, n[0])) for n in self._fields_)


if hasattr(dll, 'GXInitLib'):
    def gx_init_lib():
        """
        :brief      Initialize the device library for some resource application operations
        :return:    None
        """
        return dll.GXInitLib()


if hasattr(dll, 'GXCloseLib'):
    def gx_close_lib():
        """
        :brief      Close the device library to release resources.
        :return:    None
        """
        return dll.GXCloseLib()


if hasattr(dll, 'GXGetLastError'):
    def gx_get_last_error(size=1024):
        """
        :brief      To get the latest error descriptions information of the program
        :param      size:           string buff length(size=1024)
                                    Type: Int, Minnum: 0
        :return:    status:         State return value, See detail in GxStatusList
                    err_code:       Return the last error code
                    err_content:    the latest error descriptions information of the program
        """
        err_code = c_int()
        err_content_buff = create_string_buffer(size)

        content_size = c_size_t()
        content_size.value = size

        status = dll.GXGetLastError(byref(err_code), byref(err_content_buff), byref(content_size))
        err_content = string_at(err_content_buff, content_size.value-1)

        return status, err_code.value, string_decoding(err_content)


if hasattr(dll, 'GXUpdateDeviceList'):
    def gx_update_device_list(time_out=200):
        """
        :brief      Enumerating currently all available devices in subnet and gets the number of devices.
        :param      time_out:           The timeout time of enumeration (unit: ms).
                                        Type: Int, Minimum:0
        :return:    status:             State return value, See detail in GxStatusList
                    device_num:         The number of devices
        """
        time_out_c = c_uint()
        time_out_c.value = time_out

        device_num = c_uint()
        status = dll.GXUpdateDeviceList(byref(device_num), time_out_c)
        return status, device_num.value


if hasattr(dll, 'GXUpdateAllDeviceList'):
    def gx_update_all_device_list(time_out=200):
        """
        :brief      Enumerating currently all available devices in entire network and gets the number of devices
        :param      time_out:           The timeout time of enumeration (unit: ms).
                                        Type: Int, Minimum: 0
        :return:    status:             State return value, See detail in GxStatusList
                    device_num:         The number of devices
        """
        time_out_c = c_uint()
        time_out_c.value = time_out

        device_num = c_uint()
        status = dll.GXUpdateAllDeviceList(byref(device_num), time_out_c)
        return status, device_num.value


if hasattr(dll, 'GXGetAllDeviceBaseInfo'):
    def gx_get_all_device_base_info(devices_num):
        """
        :brief      To get the basic information of all the devices
        :param      devices_num:        The number of devices
                                        Type: Int, Minimum: 0
        :return:    status:             State return value, See detail in GxStatusList
                    device_ip_info:     The structure pointer of the device information(GxDeviceIPInfo)
        """
        devices_info = (GxDeviceBaseInfo * devices_num)()

        buf_size_c = c_size_t()
        buf_size_c.value = sizeof(GxDeviceBaseInfo) * devices_num

        status = dll.GXGetAllDeviceBaseInfo(byref(devices_info), byref(buf_size_c))
        return status, devices_info
        

if hasattr(dll, 'GXGetDeviceIPInfo'):
    def gx_get_device_ip_info(index):
        """
        :brief      To get the network information of the device.
        :param      index:              Device index
                                        Type: Int, Minimum: 1
        :return:    status:             State return value, See detail in GxStatusList
                    device_ip_info:     The structure pointer of the device information(GxDeviceIPInfo)
        """
        index_c = c_uint()
        index_c.value = index

        device_ip_info = GxDeviceIPInfo()
        status = dll.GXGetDeviceIPInfo(index_c, byref(device_ip_info))

        return status, device_ip_info


if hasattr(dll, 'GXOpenDeviceByIndex'):
    def gx_open_device_by_index(index):
        """
        :brief      Open the device by a specific Index(1, 2, 3, ...)
        :param      index:          Device index
                                    Type: Int, Minimum: 1
        :return:    status:         State return value, See detail in GxStatusList
                    handle:         The device handle returned by the interface
        """
        index_c = c_uint()
        index_c.value = index

        handle_c = c_void_p()
        status = dll.GXOpenDeviceByIndex(index_c, byref(handle_c))
        return status, handle_c.value


if hasattr(dll, 'GXOpenDevice'):
    def gx_open_device(open_param):
        """
        :brief      Open the device by a specific unique identification, such as: SN, IP, MAC, Index etc.
        :param      open_param:     The open device parameter which is configurated by the user.
                                    Type: GxOpenParam
        :return:    status:         State return value, See detail in GxStatusList
                    handle:         The device handle returned by the interface
        """
        handle = c_void_p()
        status = dll.GXOpenDevice(byref(open_param), byref(handle))
        return status, handle.value


if hasattr(dll, 'GXCloseDevice'):
    def gx_close_device(handle):
        """
        :brief      Specify the device handle to close the device
        :param      handle:     The device handle that the user specified to close.
                                Type: Long, Greater than 0
        :return:    status:     State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        status = dll.GXCloseDevice(handle_c)
        return status

'''
if hasattr(dll, 'GXGetDevicePersistentIpAddress'):
    def gx_get_device_persistent_ip_address(handle, ip_length=16, subnet_mask_length=16, default_gateway_length=16):
        """
        :brief      Get the persistent IP information of the device
        :param      handle:                 The handle of the device
        :param      ip_length:              The character string length of the device persistent IP address.
        :param      subnet_mask_length:     The character string length of the device persistent subnet mask.
        :param      default_gateway_length: The character string length of the device persistent gateway
        :return:    status:                 State return value, See detail in GxStatusList
                    ip:                     The device persistent IP address(str)
                    subnet_mask:            The device persistent subnet mask(str)
                    default_gateway:        The device persistent gateway
        """
        handle_c = c_void_p()
        handle_c.value = handle

        ip_length_c = c_uint()
        ip_length_c.value = ip_length
        ip_c = create_string_buffer(ip_length)

        subnet_mask_length_c = c_uint()
        subnet_mask_length_c.value = subnet_mask_length
        subnet_mask_c = create_string_buffer(subnet_mask_length)

        default_gateway_length_c = c_uint()
        default_gateway_length_c.value = default_gateway_length
        default_gateway_c = create_string_buffer(default_gateway_length)

        status = dll.GXGetDevicePersistentIpAddress(handle_c, byref(ip_c), byref(ip_length_c),
                                                    byref(subnet_mask_c), byref(subnet_mask_length_c),
                                                    byref(default_gateway_c), byref(default_gateway_length_c))

        ip = string_at(ip_c, ip_length_c.value-1)
        subnet_mask = string_at(subnet_mask_c, subnet_mask_length_c.value-1)
        default_gateway = string_at(default_gateway_c, default_gateway_length_c.value-1)

        return status, string_decoding(ip), string_decoding(subnet_mask), string_decoding(default_gateway)

if hasattr(dll, 'GXSetDevicePersistentIpAddress'):
    def gx_set_device_persistent_ip_address(handle, ip, subnet_mask, default_gate_way):
        """
        :brief      Set the persistent IP information of the device
        :param      handle:             The handle of the device
        :param      ip:                 The persistent IP character string of the device(str)
        :param      subnet_mask:        The persistent subnet mask character string of the device(str)
        :param      default_gate_way:   The persistent gateway character string of the device(str)
        :return:    status:             State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        ip_c = create_string_buffer(string_encoding(ip))
        subnet_mask_c = create_string_buffer(string_encoding(subnet_mask))
        default_gate_way_c = create_string_buffer(string_encoding(default_gate_way))

        status = dll.GXSetDevicePersistentIpAddress(handle_c, byref(ip_c), byref(subnet_mask_c),
                                                    byref(default_gate_way_c))
        return status
'''

if hasattr(dll, 'GXGetFeatureName'):
    def gx_get_feature_name(handle, feature_id):
        """
        :brief      Get the string description for the feature code
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      feature_id:     The feature code ID
                                    Type: Int, Greater than 0
        :return:    status:         State return value, See detail in GxStatusList
                    name:           The string description for the feature code
        """
        handle_c = c_void_p()
        handle_c.value = handle
        feature_id_c = c_int()
        feature_id_c.value = feature_id

        size_c = c_size_t()
        status = dll.GXGetFeatureName(handle_c, feature_id_c, None, byref(size_c))

        name_buff = create_string_buffer(size_c.value)
        status = dll.GXGetFeatureName(handle_c, feature_id_c, byref(name_buff), byref(size_c))

        name = string_at(name_buff, size_c.value-1)
        return status, string_decoding(name)


if hasattr(dll, 'GXIsImplemented'):
    def gx_is_implemented(handle, feature_id):
        """
        :brief      Inquire the current camera whether support a special feature.
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      feature_id:     The feature code ID
                                    Type: int, Greater than 0
        :return:    status:         State return value, See detail in GxStatusList
                    is_implemented: To return the result whether is support this feature
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        is_implemented = c_bool()
        status = dll.GXIsImplemented(handle_c, feature_id_c, byref(is_implemented))
        return status, is_implemented.value


if hasattr(dll, 'GXIsReadable'):
    def gx_is_readable(handle, feature_id):
        """
        :brief      Inquire if a feature code is currently readable
        :param      handle:             The handle of the device
                                        Type: Long, Greater than 0
        :param      feature_id:         The feature code ID
                                        Type: int, Greater than 0
        :return:    status:             State return value, See detail in GxStatusList
                    is_readable:        To return the result whether the feature code ID is readable
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        is_readable = c_bool()
        status = dll.GXIsReadable(handle_c, feature_id_c, byref(is_readable))
        return status, is_readable.value


if hasattr(dll, 'GXIsWritable'):
    def gx_is_writable(handle, feature_id):
        """
        :brief      Inquire if a feature code is currently writable
        :param      handle:             The handle of the device.
                                        Type: Long, Greater than 0
        :param      feature_id:         The feature code ID
                                        Type: int, Greater than 0
        :return:    status:             State return value, See detail in GxStatusList
                    is_writeable:       To return the result whether the feature code ID is writable(Bool)
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        is_writeable = c_bool()
        status = dll.GXIsWritable(handle_c, feature_id_c, byref(is_writeable))
        return status, is_writeable.value


if hasattr(dll, 'GXGetIntRange'):
    def gx_get_int_range(handle, feature_id):
        """
        :brief      To get the minimum value, maximum value and steps of the int type
        :param      handle:         The handle of the device.
                                    Type: Long, Greater than 0
        :param      feature_id:     The feature code ID
                                    Type: int, Greater than 0
        :return:    status:         State return value, See detail in GxStatusList
                    int_range:      The structure of range description(GxIntRange)
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        int_range = GxIntRange()
        status = dll.GXGetIntRange(handle_c, feature_id_c, byref(int_range))
        return status, int_range


if hasattr(dll, 'GXGetInt'):
    def gx_get_int(handle, feature_id):
        """
        :brief      Get the current value of the int type.
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      feature_id:     The feature code ID
                                    Type: int, Greater than 0
        :return:    status:         State return value, See detail in GxStatusList
                    int_value:      Get the current value of the int type
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        int_value = c_int64()
        status = dll.GXGetInt(handle_c, feature_id_c, byref(int_value))
        return status, int_value.value


if hasattr(dll, 'GXSetInt'):
    def gx_set_int(handle, feature_id, int_value):
        """
        :brief      Set the value of int type
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      feature_id:     The feature code ID.
                                    Type: int, Greater than 0
        :param      int_value:      The value that the user will set
                                    Type: long, minnum:0
        :return:    status:         State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        value_c = c_int64()
        value_c.value = int_value

        status = dll.GXSetInt(handle_c, feature_id_c, value_c)
        return status


if hasattr(dll, 'GXGetFloatRange'):
    def gx_get_float_range(handle, feature_id):
        """
        :brief      To get the minimum value, maximum value, stepsand unit of the float type
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      feature_id:     The feature code ID
                                    Type: int, Greater than 0
        :return:    status:         State return value, See detail in GxStatusList
                    float_range:    The description structure(GxFloatRange)
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        float_range = GxFloatRange()
        status = dll.GXGetFloatRange(handle_c, feature_id_c, byref(float_range))
        return status, float_range


if hasattr(dll, 'GXSetFloat'):
    def gx_set_float(handle, feature_id, float_value):
        """
        :brief      Set the value of float type
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      feature_id:     The feature code ID
                                    Type: int, Greater than 0
        :param      float_value:    The float value that the user will set
                                    Type: double
        :return:    status:         State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        value_c = c_double()
        value_c.value = float_value

        status = dll.GXSetFloat(handle_c, feature_id_c, value_c)
        return status


if hasattr(dll, 'GXGetFloat'):
    def gx_get_float(handle, feature_id):
        """
        :brief      Get the value of float type
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      feature_id:     The feature code ID
                                    Type: int, Greater than 0
        :return:    status:         State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        float_value = c_double()
        status = dll.GXGetFloat(handle_c, feature_id_c, byref(float_value))

        return status, float_value.value


if hasattr(dll, 'GXGetEnumEntryNums'):
    def gx_get_enum_entry_nums(handle, feature_id):
        """
        :brief      Get the number of the options for the enumeration item
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      feature_id:     The feature code ID
                                    Type: int, Greater than 0
        :return:    status:         State return value, See detail in GxStatusList
                    enum_num:       The number of the options for the enumeration item
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        enum_nums = c_uint()
        status = dll.GXGetEnumEntryNums(handle_c, feature_id_c, byref(enum_nums))
        return status, enum_nums.value


if hasattr(dll, 'GXGetEnumDescription'):
    def gx_get_enum_description(handle, feature_id, enum_num):
        """
        :brief      To get the description information of the enumerated type values
                    the number of enumerated items and the value and descriptions of each item
                    please reference GxEnumDescription.
        :param      handle:             The handle of the device
                                        Type: Long, Greater than 0
        :param      feature_id:         The feature code ID
                                        Type: int, Greater than 0
        :param      enum_num:           The number of enumerated information
                                        Type: int, Greater than 0
        :return:    status:             State return value, See detail in GxStatusList
                    enum_description:   Enumerated information array(GxEnumDescription)
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        buf_size_c = c_size_t()
        buf_size_c.value = sizeof(GxEnumDescription) * enum_num

        enum_description = (GxEnumDescription * enum_num)()
        status = dll.GXGetEnumDescription(handle_c, feature_id_c, byref(enum_description), byref(buf_size_c))
        return status, enum_description


if hasattr(dll, 'GXGetEnum'):
    def gx_get_enum(handle, feature_id):
        """
        :brief      To get the current enumeration value
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      feature_id:     The feature code ID
                                    Type: int, Greater than 0
        :return:    status:         State return value, See detail in GxStatusList
                    enum_value:     Get the current enumeration value
        """
        handle_c = c_void_p()
        handle_c.value = handle
        feature_id_c = c_int()
        feature_id_c.value = feature_id

        enum_value = c_int64()
        status = dll.GXGetEnum(handle_c, feature_id_c, byref(enum_value))

        return status, enum_value.value


if hasattr(dll, 'GXSetEnum'):
    def gx_set_enum(handle, feature_id, enum_value):
        """
        :brief      Set the enumeration value
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      feature_id:     The feature code ID
                                    Type: int, Greater than 0
        :param      enum_value:     Set the enumeration value
                                    Type: int
        :return:    status:         State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        value_c = c_int64()
        value_c.value = enum_value

        status = dll.GXSetEnum(handle_c, feature_id_c, value_c)
        return status


if hasattr(dll, 'GXGetBool'):
    def gx_get_bool(handle, feature_id):
        """
        :brief      Get the value of bool type
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      feature_id:     The feature code ID
                                    Type: int, Greater than 0
        :return:    status:         State return value, See detail in GxStatusList
                    boot_value:     the value of bool type
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        boot_value = c_bool()
        status = dll.GXGetBool(handle_c, feature_id_c, byref(boot_value))
        return status, boot_value.value


if hasattr(dll, 'GXSetBool'):
    def gx_set_bool(handle, feature_id, bool_value):
        """
        :brief      Set the value of bool type
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      feature_id:     The feature code ID
                                    Type: int, Greater than 0
        :param      bool_value:     The bool value that the user will set
                                    Type: Bool
        :return:    status:         State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        value_c = c_bool()
        value_c.value = bool_value

        status = dll.GXSetBool(handle_c, feature_id_c, value_c)
        return status


if hasattr(dll, 'GXGetStringLength'):
    def gx_get_string_length(handle, feature_id):
        """
        :brief      Get the current value length of the character string type. Unit: byte
        :param      handle:             The handle of the device
                                        Type: Long, Greater than 0
        :param      feature_id:         The feature code ID
                                        Type: int, Greater than 0
        :return:    status:             State return value, See detail in GxStatusList
                    string_length:      the current value length of the character string type
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        string_length = c_size_t()
        status = dll.GXGetStringLength(handle_c, feature_id_c, byref(string_length))

        return status, string_length.value - 1


if hasattr(dll, 'GXGetStringMaxLength'):
    def gx_get_string_max_length(handle, feature_id):
        """
        :brief      Get the maximum length of the string type value,  Unit: byte
        :param      handle:             The handle of the device
                                        Type: Long, Greater than 0
        :param      feature_id:         The feature code ID
                                        Type: int, Greater than 0
        :return:    status:             State return value, See detail in GxStatusList
                    string_max_length:  the maximum length of the string type value
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        string_max_length = c_size_t()
        status = dll.GXGetStringMaxLength(handle_c, feature_id, byref(string_max_length))

        return status, string_max_length.value - 1


if hasattr(dll, 'GXGetString'):
    def gx_get_string(handle, feature_id):
        """
        :brief      Get the content of the string type value
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      feature_id:     The feature code ID
                                    Type: int, Greater than 0
        :return:    status:         State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        size_c = c_size_t()
        status = dll.GXGetString(handle_c, feature_id_c, None, byref(size_c))

        content_c = create_string_buffer(size_c.value)
        status = dll.GXGetString(handle_c, feature_id_c, byref(content_c), byref(size_c))

        content = string_at(content_c, size_c.value-1)
        return status, string_decoding(content)


if hasattr(dll, 'GXSetString'):
    def gx_set_string(handle, feature_id, content):
        """
        :brief      Set the content of the string value
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      feature_id:     The feature code ID
                                    Type: int, Greater than 0
        :param      content:        The string will be setting(str)
                                    Type: str
        :return:    status:         State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        content_c = create_string_buffer(string_encoding(content))

        status = dll.GXSetString(handle_c, feature_id_c, byref(content_c))
        return status


if hasattr(dll, 'GXGetBufferLength'):
    def gx_get_buffer_length(handle, feature_id):
        """
        :brief      Get the length of the chunk data and the unit is byte,
                    the user can apply the buffer based on the length obtained,
                    and then call the gx_get_buffer to get the chunk data.
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      feature_id:     The feature code ID
                                    Type: int, Greater than 0
        :return:    status:         State return value, See detail in GxStatusList
                    buff_length:    Buff length, Unit: byte
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        buff_length = c_size_t()
        status = dll.GXGetBufferLength(handle_c, feature_id_c, byref(buff_length))
        return status, buff_length.value


if hasattr(dll, 'GXGetBuffer'):
    def gx_get_buffer(handle, feature_id):
        """
        :brief      Get the chunk data
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      feature_id:     The feature code ID
                                    Type: int, Greater than 0
        :return:    status:         State return value, See detail in GxStatusList
                    buff:           chunk data
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        buff_length_c = c_size_t()
        status = dll.GXGetBuffer(handle_c, feature_id_c, None, byref(buff_length_c))

        buff_c = (c_ubyte * buff_length_c.value)()
        status = dll.GXGetBuffer(handle_c, feature_id_c, byref(buff_c), byref(buff_length_c))
        return status, buff_c


if hasattr(dll, 'GXSetBuffer'):
    def gx_set_buffer(handle, feature_id, buff, buff_size):
        """
        :brief      Set the chunk data
        :param      handle:         The handle of the device
        :param      feature_id:     The feature code ID
                                    Type: long, Greater than 0
        :param      buff:           chunk data buff
                                    Type: Ctype array
        :param      buff_size:      chunk data buff size
                                    Type: int, Greater than 0
        :return:    status:         State return value, See detail in GxStatusList
        """

        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        buff_size_c = c_size_t()
        buff_size_c.value = buff_size

        status = dll.GXSetBuffer(handle_c, feature_id_c, buff, buff_size_c)
        return status


if hasattr(dll, 'GXSendCommand'):
    def gx_send_command(handle, feature_id):
        """
        :brief      Send the command
        :param      handle:         The handle of the device
                                    Type: long, Greater than 0
        :param      feature_id:     The feature code ID.
                                    Type: int, Greater than 0
        :return:    status:         State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        status = dll.GXSendCommand(handle_c, feature_id_c)
        return status


CAP_CALL = CFUNCTYPE(None, POINTER(GxFrameCallbackParam))
if hasattr(dll, 'GXRegisterCaptureCallback'):
    def gx_register_capture_callback(handle, cap_call):
        """
        :brief      Register the capture callback function
        :param      handle:         The handle of the device
        :param      cap_call:       The callback function that the user will register(@ CAP_CALL)
        :return:    status:         State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        status = dll.GXRegisterCaptureCallback(handle_c, None, cap_call)
        return status


if hasattr(dll, 'GXUnregisterCaptureCallback'):
    def gx_unregister_capture_callback(handle):
        """
        :brief      Unregister the capture callback function
        :param      handle:         The handle of the device
        :return:    status:         State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        status = dll.GXUnregisterCaptureCallback(handle_c)
        return status


if hasattr(dll, 'GXGetImage'):
    def gx_get_image(handle, frame_data, time_out=200):
        """
        :brief      After starting acquisition, you can call this function to get images directly.
                    Noting that the interface can not be mixed with the callback capture mode.
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      frame_data:     [out]User introduced to receive the image data
                                    Type: GxFrameData
        :param      time_out:       The timeout time of capture image.(unit: ms)
                                    Type: int, minnum: 0
        :return:    status:         State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        time_out_c = c_uint()
        time_out_c.value = time_out

        status = dll.GXGetImage(handle_c, byref(frame_data), time_out_c)
        return status


if hasattr(dll, 'GXFlushQueue'):
    def gx_flush_queue(handle):
        """
        :brief      Empty the cache image in the image output queue.
        :param      handle:     The handle of the device
                                Type: Long, Greater than 0
        :return:    status:     State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        status = dll.GXFlushQueue(handle_c)
        return status



OFF_LINE_CALL = CFUNCTYPE(None, c_void_p)
if hasattr(dll, 'GXRegisterDeviceOfflineCallback'):
    def gx_register_device_offline_callback(handle, call_back):
        """
        :brief      At present, the mercury GIGE camera provides the device offline notification event mechanism,
                    the user can call this interface to register the event handle callback function
        :param      handle:             The handle of the device
        :param      call_back:          The user event handle callback function(@ OFF_LINE_CALL)
        :return:    status:             State return value, See detail in GxStatusList
                    call_back_handle:   The handle of offline callback function
                                        the handle is used for unregistering the callback function
        """
        handle_c = c_void_p()
        handle_c.value = handle

        call_back_handle = c_void_p()
        status = dll.GXRegisterDeviceOfflineCallback(handle_c, None, call_back, byref(call_back_handle))
        return status, call_back_handle.value


if hasattr(dll, 'GXUnregisterDeviceOfflineCallback'):
    def gx_unregister_device_offline_callback(handle, call_back_handle):
        """
        :brief      Unregister event handle callback function
        :param      handle:             The handle of the device
        :param      call_back_handle:   The handle of device offline callback function
        :return:    status:             State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        call_back_handle_c = c_void_p()
        call_back_handle_c.value = call_back_handle

        status = dll.GXUnregisterDeviceOfflineCallback(handle_c, call_back_handle_c)
        return status

'''
if hasattr(dll, 'GXFlushEvent'):
    def gx_flush_event(handle):
        """
        :brief      Empty the device event, such as the frame exposure to end the event data queue
        :param      handle:    The handle of the device
        :return:    status:     State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        status = dll.GXFlushEvent(handle_c)
        return status


if hasattr(dll, 'GXGetEventNumInQueue'):
    def gx_get_event_num_in_queue(handle):
        """
        :brief      Get the number of the events in the current remote device event queue cache.
        :param      handle:     The handle of the device
        :return:    status:     State return value, See detail in GxStatusList
                    event_num:  event number.
        """
        handle_c = c_void_p()
        handle_c.value = handle

        event_num = c_uint()

        status = dll.GXGetEventNumInQueue(handle_c, byref(event_num))
        return status, event_num.value


FEATURE_CALL = CFUNCTYPE(None, c_uint, c_void_p)
if hasattr(dll, 'GXRegisterFeatureCallback'):
    def gx_register_feature_callback(handle, call_back, feature_id):
        """
        :brief      Register device attribute update callback function.
                    When the current value of the device property has updated, or the accessible property is changed,
                    call this callback function.
        :param      handle:             The handle of the device
        :param      call_back:          The user event handle callback function(@ FEATURE_CALL)
        :param      feature_id:         The feature code ID
        :return:    status:             State return value, See detail in GxStatusList
                    call_back_handle:   The handle of property update callback function,
                                        to unregister the callback function.
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        call_back_handle = c_void_p()
        status = dll.GXRegisterFeatureCallback(handle_c, None, call_back, feature_id_c, byref(call_back_handle))

        return status, call_back_handle.value


if hasattr(dll, 'GXUnregisterFeatureCallback'):
    """
    """
    def gx_unregister_feature_cEallback(handle, feature_id, call_back_handle):
        """
        :brief      Unregister device attribute update callback function
        :param      handle:             The handle of the device
        :param      feature_id:         The feature code ID
        :param      call_back_handle:   Handle of property update callback function
        :return:    status:             State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        feature_id_c = c_int()
        feature_id_c.value = feature_id

        call_back_handle_c = c_void_p()
        call_back_handle_c.value = call_back_handle

        status = dll.GXUnregisterFeatureCallback(handle_c, feature_id_c, call_back_handle_c)
        return status
'''

if hasattr(dll, 'GXExportConfigFile'):
    def gx_export_config_file(handle, file_path):
        """
        :brief      Export the current parameter of the camera to the configuration file.
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      file_path:      The path of the configuration file that to be generated
                                    Type: str
        :return:    status:         State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        file_path_c = create_string_buffer(string_encoding(file_path))
        status = dll.GXExportConfigFile(handle_c, byref(file_path_c))

        return status


if hasattr(dll, 'GXImportConfigFile'):
    def gx_import_config_file(handle, file_path, verify):
        """
        :brief      Import the configuration file for the camera
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      file_path:      The path of the configuration file(str)
                                    Type: str
        :param      verify:         If this value is true, all imported values will be read out
                                    to check whether they are consistent.
        :return:    status:         State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        verify_c = c_bool()
        verify_c.value = verify

        file_path_c = create_string_buffer(string_encoding(file_path))
        status = dll.GXImportConfigFile(handle_c, byref(file_path_c), verify_c)
        return status

'''
if hasattr(dll, 'GXReadRemoteDevicePort'):
    def gx_read_remote_device_port(handle, address, buff, size):
        """
        :brief      Read data for user specified register.
        :param      handle:     The handle of the device
        :param      address:    Register address
        :param      buff:       Output data buff
        :param      size:       Buff size
        :return:    status:     State return value, See detail in GxStatusList
                    size:       Returns the length of the actual read register
        """
        handle_c = c_void_p()
        handle_c.value = handle

        address_c = c_ulonglong()
        address_c.value = address

        size_c = c_uint()
        size_c.value = size

        status = dll.GXReadRemoteDevicePort(handle_c, address_c, byref(buff), byref(size_c))
        return status, size_c.value


if hasattr(dll, 'GXWriteRemoteDevicePort'):
    def gx_write_remote_device_port(handle, address, buff, size):
        """
        :brief      Writes user specified data to a user specified register.
        :param      handle:     The handle of the device
        :param      address:    Register address
        :param      buff:       User data
        :param      size:       User data size
        :return:    status:     State return value, See detail in GxStatusList
                    size:       Returns the length of the actual write register
        """
        handle_c = c_void_p()
        handle_c.value = handle

        address_c = c_ulonglong()
        address_c.value = address

        size_c = c_uint()
        size_c.value = size

        status = dll.GXWriteRemoteDevicePort(handle_c, address_c, byref(buff), byref(size_c))
        return status, size_c.value


if hasattr(dll, 'GXGigEIpConfiguration'):
    def gx_gige_ip_configuration(mac_address, ipconfig_flag, ip_address, subnet_mask, default_gateway, user_id):
        """
        "brief      Configure the static IP address of the camera
        :param      mac_address:        The MAC address of the device(str)
        :param      ipconfig_flag:      IP Configuration mode(GxIPConfigureModeList)
        :param      ip_address:         The IP address to be set(str)
        :param      subnet_mask:        The subnet mask to be set(str)
        :param      default_gateway:    The default gateway to be set(str)
        :param      user_id:            The user-defined name to be set(str)
        :return:    status:             State return value, See detail in GxStatusList
        """
        mac_address_c = create_string_buffer(string_encoding(mac_address))
        ip_address_c = create_string_buffer(string_encoding(ip_address))
        subnet_mask_c = create_string_buffer(string_encoding(subnet_mask))
        default_gateway_c = create_string_buffer(string_encoding(default_gateway))
        user_id_c = create_string_buffer(string_encoding(user_id))

        status = dll.GXGigEIpConfiguration(mac_address_c, ipconfig_flag,
                                           ip_address_c, subnet_mask_c,
                                           default_gateway_c, user_id_c)
        return status


if hasattr(dll, 'GXGigEForceIp'):
    def gx_gige_force_ip(mac_address, ip_address, subnet_mask, default_gate_way):
        """
        :brief      Execute the Force IP
        :param      mac_address:        The MAC address of the device(str)
        :param      ip_address:         The IP address to be set(str)
        :param      subnet_mask:        The subnet mask to be set(str)
        :param      default_gate_way:   The default gateway to be set(str)
        :return:    status:             State return value, See detail in GxStatusList
        """
        mac_address_c = create_string_buffer(string_encoding(mac_address))
        ip_address_c = create_string_buffer(string_encoding(ip_address))
        subnet_mask_c = create_string_buffer(string_encoding(subnet_mask))
        default_gate_way_c = create_string_buffer(string_encoding(default_gate_way))

        status = dll.GXGigEForceIp(mac_address_c, ip_address_c, subnet_mask_c, default_gate_way_c)
        return status
'''

if hasattr(dll, 'GXSetAcqusitionBufferNumber'):
    def gx_set_acquisition_buffer_number(handle, buffer_num):
        """
        :brief      Users Set Acquisition buffer Number
        :param      handle:         The handle of the device
                                    Type: Long, Greater than 0
        :param      buffer_num:     Acquisition buffer Number
                                    Type: int, Greater than 0
        :return:    status:         State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        buffer_num_c = c_uint64()
        buffer_num_c.value = buffer_num

        status = dll.GXSetAcqusitionBufferNumber(handle_c, buffer_num_c)
        return status

'''
if hasattr(dll, 'GXStreamOn'):
    def gx_stream_on(handle):
        """
        :brief      Start acquisition
        :param      handle:     The handle of the device
        :return:    status:     State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        status = dll.GXStreamOn(handle_c)
        return status


if hasattr(dll, 'GXDQBuf'):
    def gx_dequeue_buf(handle, time_out):
        """
        :brief      Get a image
                    After the image processing is completed, the gx_queue_buf interface needs to be called
                    otherwise the collection will not be able to continue.
        :param      handle:             The handle of the device
        :param      time_out:           The timeout time of capture image.(unit: ms)
        :return:    status:             State return value, See detail in GxStatusList
                    frame_data:         Image data
                    frame_data_p:       Image buff address
        """
        handle_c = c_void_p()
        handle_c.value = handle

        time_out_c = c_uint()
        time_out_c.value = time_out

        frame_data_p = c_void_p()
        status = dll.GXDQBuf(handle_c, byref(frame_data_p), time_out_c)

        frame_data = GxFrameData()
        memmove(addressof(frame_data), frame_data_p.value, sizeof(frame_data))
        return status, frame_data, frame_data_p.value


if hasattr(dll, 'GXQBuf'):
    def gx_queue_buf(handle, frame_data_p):
        """
        :brief      Put an image Buff back to the GxIAPI library and continue to be used for collection.
        :param      handle:         The handle of the device
        :param      frame_data_p:   Image buff address
        :return:    status:         State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        frame_data_p_p = c_void_p()
        frame_data_p_p.value = frame_data_p

        status = dll.GXQBuf(handle_c, frame_data_p_p)
        return status
        

if hasattr(dll, 'GXDQAllBufs'):
    def gx_dequeue_all_bufs(handle, buff_num, time_out):
        """
        :brief      Get images
                    After the image processing is completed, the gx_queue_all_bufs interface needs to be called
                    otherwise the collection will not be able to continue.
        :param      handle:         The handle of the device
        :param      buff_num:       The number of images expected to be obtained
        :param      time_out:       The timeout time of capture image.(unit: ms)
        :return:    status:         State return value, See detail in GxStatusList
                    frame_data:     Image data arrays
                    frame_count:    The number of images that are actually returned
        """
        handle_c = c_void_p()
        handle_c.value = handle

        time_out_c = c_uint()
        time_out_c.value = time_out

        frame_data_p = (c_void_p * buff_num)()
        frame_count_c = c_uint()

        status = dll.GXDQAllBufs(handle_c, frame_data_p, buff_num, byref(frame_count_c), time_out_c)
        frame_data = (GxFrameData * buff_num)()

        for i in range(buff_num):
            memmove(addressof(frame_data[i]), frame_data_p[i], sizeof(GxFrameData))

        return status, frame_data, frame_count_c.value


if hasattr(dll, 'GXQAllBufs'):
    def gx_queue_all_bufs(handle):
        """
        :brief      The image data Buf is returned to the GxIAPI library and used for collection.
        :param      handle:     The handle of the device
        :return:    status:     State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        status = dll.GXQAllBufs(handle_c)
        return status


if hasattr(dll, 'GXStreamOff'):
    def gx_stream_off(handle):
        """
        :brief      Stop acquisition
        :param      handle:     The handle of the device
        :return:    status:     State return value, See detail in GxStatusList
        """
        handle_c = c_void_p()
        handle_c.value = handle

        status = dll.GXStreamOff(handle_c)
        return status
'''


def string_encoding(string):
    """
    :breif      Python3.X: String encoded as bytes
    :param      string
    :return:
    """
    if sys.version_info.major == 3:
        string = string.encode()
    return string


def string_decoding(string):
    """
    :brief      Python3.X: bytes decoded as string
    :param      string
    :return:
    """
    if sys.version_info.major == 3:
        string = string.decode()
    return string


def range_check(value, min_value, max_value, inc_value=0):
    """
    :brief      Determine if the input parameter is within range
    :param      value:       input value
    :param      min_value:   max value
    :param      max_value:   min value
    :param      inc_value:   step size, default=0
    :return:    True/False
    """
    if value < min_value:
        return False
    elif value > max_value:
        return False
    elif (inc_value != 0) and (value != int(value / inc_value) * inc_value):
        return False
    return True
