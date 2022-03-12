#!/usr/bin/python
# -*- coding:utf-8 -*-
# -*-mode:python ; tab-width:4 -*- ex:set tabstop=4 shiftwidth=4 expandtab: -*-

import numpy
from .gxwrapper import *
from .dxwrapper import *
from .gxidef import *

ERROR_SIZE = 1024
PIXEL_BIT_MASK = 0x00ff0000

if sys.version_info.major > 2:
    INT_TYPE = int
else:
    INT_TYPE = (int, long)


class DeviceManager(object):
    __instance_num = 0

    def __new__(cls, *args, **kw):
        cls.__instance_num += 1
        status = gx_init_lib()
        StatusProcessor.process(status, 'DeviceManager', 'init_lib')
        return object.__new__(cls, *args)
    
    def __init__(self):
        self.__device_num = 0
        self.__device_info_list = []

        

    def __del__(self):
        self.__class__.__instance_num -= 1
        if self.__class__.__instance_num <= 0:
            status = gx_close_lib()
            StatusProcessor.process(status, 'DeviceManager', 'close_lib')

    def __get_device_info_list(self, base_info, ip_info, num):
        """
        :brief      Convert GxDeviceBaseInfo and GxDeviceIPInfo to device info list
        :param      base_info:  device base info list[GxDeviceBaseInfo]
        :param      ip_info:    device ip info list[GxDeviceIPInfo]
        :param      num:        device number
        :return:    device info list
        """
        device_info_list = []
        for i in range(num):
            device_info_list.append({
                'index': i+1,
                'vendor_name': string_decoding(base_info[i].vendor_name),
                'model_name': string_decoding(base_info[i].model_name),
                'sn': string_decoding(base_info[i].serial_number),
                'display_name': string_decoding(base_info[i].display_name),
                'device_id': string_decoding(base_info[i].device_id),
                'user_id': string_decoding(base_info[i].user_id),
                'access_status': base_info[i].access_status,
                'device_class': base_info[i].device_class,
                'mac': string_decoding(ip_info[i].mac),
                'ip': string_decoding(ip_info[i].ip),
                'subnet_mask': string_decoding(ip_info[i].subnet_mask),
                'gateway': string_decoding(ip_info[i].gateway),
                'nic_mac': string_decoding(ip_info[i].nic_mac),
                'nic_ip': string_decoding(ip_info[i].nic_ip),
                'nic_subnet_mask': string_decoding(ip_info[i].nic_subnet_mask),
                'nic_gateWay': string_decoding(ip_info[i].nic_gateWay),
                'nic_description': string_decoding(ip_info[i].nic_description)
            })

        return device_info_list

    def __get_ip_info(self, base_info_list, dev_mum):
        """
        :brief      Get the network information
        """

        ip_info_list = []
        for i in range(dev_mum):
            if base_info_list[i].device_class == GxDeviceClassList.GEV:
                status, ip_info = gx_get_device_ip_info(i+1)
                StatusProcessor.process(status, 'DeviceManager', '__get_ip_info')
                ip_info_list.append(ip_info)
            else:
                ip_info_list.append(GxDeviceIPInfo())

        return ip_info_list

    def update_device_list(self, timeout=200):
        """
        :brief      enumerate the same network segment devices
        :param      timeout:    Enumeration timeout, range:[0, 0xFFFFFFFF]
        :return:    dev_num:    device number
                    device_info_list: all device info list
        """
        if not isinstance(timeout, INT_TYPE):
            raise ParameterTypeError("DeviceManager.update_device_list: "
                                     "Expected timeout type is int, not %s" % type(timeout))

        if (timeout < 0) or (timeout > UNSIGNED_INT_MAX):
            print("DeviceManager.update_device_list: "
                  "timeout out of bounds, timeout: minimum=0, maximum=%s" % hex(UNSIGNED_INT_MAX).__str__())
            return 0, None

        status, dev_num = gx_update_device_list(timeout)
        StatusProcessor.process(status, 'DeviceManager', 'update_device_list')

        status, base_info_list = gx_get_all_device_base_info(dev_num)
        StatusProcessor.process(status, 'DeviceManager', 'update_device_list')

        ip_info_list = self.__get_ip_info(base_info_list, dev_num)
        self.__device_num = dev_num
        self.__device_info_list = self.__get_device_info_list(base_info_list, ip_info_list, dev_num)

        return self.__device_num, self.__device_info_list

    def update_all_device_list(self, timeout=200):
        """
        :brief      Enumerate devices on different network segments
        :param      timeout:    Enumeration timeout, range:[0, 0xFFFFFFFF]
        :return:    dev_num:    device number
                    device_info_list:   all device info list
        """
        if not isinstance(timeout, INT_TYPE):
            raise ParameterTypeError("DeviceManager.update_all_device_list: "
                                     "Expected timeout type is int, not %s" % type(timeout))

        if (timeout < 0) or (timeout > UNSIGNED_INT_MAX):
            print("DeviceManager.update_all_device_list: "
                  "timeout out of bounds, timeout: minimum=0, maximum=%s" % hex(UNSIGNED_INT_MAX).__str__())
            return 0, None

        status, dev_num = gx_update_all_device_list(timeout)
        StatusProcessor.process(status, 'DeviceManager', 'update_all_device_list')

        status, base_info_list = gx_get_all_device_base_info(dev_num)
        StatusProcessor.process(status, 'DeviceManager', 'update_all_device_list')

        ip_info_list = self.__get_ip_info(base_info_list, dev_num)
        self.__device_num = dev_num
        self.__device_info_list = self.__get_device_info_list(base_info_list, ip_info_list, dev_num)

        return self.__device_num, self.__device_info_list

    def get_device_number(self):
        """
        :brief      Get device number
        :return:    device number
        """
        return self.__device_num

    def get_device_info(self):
        """
        :brief      Get all device info
        :return:    info_dict:      device info list
        """
        return self.__device_info_list

    def open_device_by_index(self, index, access_mode=GxAccessMode.CONTROL):
        """
        :brief      open device by index
                    USB3 device return U3VDevice object
                    USB2 device return U2Device object
                    GEV  device return GEVDevice object
        :param      index:          device index must start from 1
        :param      access_mode:    the access of open device
        :return:    Device object
        """
        if not isinstance(index, INT_TYPE):
            raise ParameterTypeError("DeviceManager.open_device_by_index: "
                                     "Expected index type is int, not %s" % type(index))

        if not isinstance(access_mode, INT_TYPE):
            raise ParameterTypeError("DeviceManager.open_device_by_index: "
                                     "Expected access_mode type is int, not %s" % type(access_mode))

        if index < 1:
            print("DeviceManager.open_device_by_index: index must start from 1")
            return None
        elif index > UNSIGNED_INT_MAX:
            print("DeviceManager.open_device_by_index: index maximum: %s" % hex(UNSIGNED_INT_MAX).__str__())
            return None

        access_mode_dict = dict((name, getattr(GxAccessMode, name)) for name in dir(GxAccessMode) if not name.startswith('__'))
        if access_mode not in access_mode_dict.values():
            print("DeviceManager.open_device_by_index: "
                  "access_mode out of bounds, %s" % access_mode_dict.__str__())
            return None

        if self.__device_num < index:
            # Re-update the device
            self.update_all_device_list()
            if self.__device_num < index:
                raise NotFoundDevice("DeviceManager.open_device_by_index: invalid index")

        # open devices by index
        open_param = GxOpenParam()
        open_param.content = string_encoding(str(index))
        open_param.open_mode = GxOpenMode.INDEX
        open_param.access_mode = access_mode
        status, handle = gx_open_device(open_param)
        StatusProcessor.process(status, 'DeviceManager', 'open_device_by_index')

        # get device class
        device_class = self.__device_info_list[index-1]["device_class"]

        if device_class == GxDeviceClassList.U3V:
            return U3VDevice(handle)
        elif device_class == GxDeviceClassList.USB2:
            return U2Device(handle)
        elif device_class == GxDeviceClassList.GEV:
            return GEVDevice(handle)
        else:
            raise NotFoundDevice("DeviceManager.open_device_by_index: Does not support this device type.")

    def __get_device_class_by_sn(self, sn):
        """
        :brief:     1.find device by sn in self.__device_info_list
                    2.return different objects according to device class
        :param      sn:      device serial number
        :return:    device class
        """
        for index in range(self.__device_num):
            if self.__device_info_list[index]["sn"] == sn:
                return self.__device_info_list[index]["device_class"]

        # don't find this id in device base info list
        return -1

    def open_device_by_sn(self, sn, access_mode=GxAccessMode.CONTROL):
        """
        :brief      open device by serial number(SN)
                    USB3 device return U3VDevice object
                    USB2 device return U2Device object
                    GEV device return GEVDevice object
        :param      sn:             device serial number, type: str
        :param      access_mode:    the mode of open device[GxAccessMode]
        :return:    Device object
        """
        if not isinstance(sn, str):
            raise ParameterTypeError("DeviceManager.open_device_by_sn: "
                                     "Expected sn type is str, not %s" % type(sn))

        if not isinstance(access_mode, INT_TYPE):
            raise ParameterTypeError("DeviceManager.open_device_by_sn: "
                                     "Expected access_mode type is int, not %s" % type(access_mode))

        access_mode_dict = dict((name, getattr(GxAccessMode, name)) for name in dir(GxAccessMode) if not name.startswith('__'))
        if access_mode not in access_mode_dict.values():
            print("DeviceManager.open_device_by_sn: "
                  "access_mode out of bounds, %s" % access_mode_dict.__str__())
            return None

        # get device class from self.__device_info_list
        device_class = self.__get_device_class_by_sn(sn)
        if device_class == -1:
            # Re-update the device
            self.update_all_device_list()
            device_class = self.__get_device_class_by_sn(sn)
            if device_class == -1:
                # don't find this sn
                raise NotFoundDevice("DeviceManager.open_device_by_sn: Not found device")

        # open devices by sn
        open_param = GxOpenParam()
        open_param.content = string_encoding(sn)
        open_param.open_mode = GxOpenMode.SN
        open_param.access_mode = access_mode
        status, handle = gx_open_device(open_param)
        StatusProcessor.process(status, 'DeviceManager', 'open_device_by_sn')

        if device_class == GxDeviceClassList.U3V:
            return U3VDevice(handle)
        elif device_class == GxDeviceClassList.USB2:
            return U2Device(handle)
        elif device_class == GxDeviceClassList.GEV:
            return GEVDevice(handle)
        else:
            raise NotFoundDevice("DeviceManager.open_device_by_sn: Does not support this device type.")

    def __get_device_class_by_user_id(self, user_id):
        """
        :brief:     1.find device according to sn in self.__device_info_list
                    2.return different objects according to device class
        :param      user_id:        user ID
        :return:    device class
        """
        for index in range(self.__device_num):
            if self.__device_info_list[index]["user_id"] == user_id:
                return self.__device_info_list[index]["device_class"]

        # don't find this id in device base info list
        return -1

    def open_device_by_user_id(self, user_id, access_mode=GxAccessMode.CONTROL):
        """
        :brief      open device by user defined name
                    USB3 device return U3VDevice object
                    GEV  device return GEVDevice object
        :param      user_id:        user defined name, type:str
        :param      access_mode:    the mode of open device[GxAccessMode]
        :return:    Device object
        """
        if not isinstance(user_id, str):
            raise ParameterTypeError("DeviceManager.open_device_by_user_id: "
                                     "Expected user_id type is str, not %s" % type(user_id))
        elif user_id.__len__() == 0:
            raise InvalidParameter("DeviceManager.open_device_by_user_id: Don't support user_id's length is 0")

        if not isinstance(access_mode, INT_TYPE):
            raise ParameterTypeError("DeviceManager.open_device_by_user_id: "
                                     "Expected access_mode type is int, not %s" % type(access_mode))

        access_mode_dict = dict((name, getattr(GxAccessMode, name)) for name in dir(GxAccessMode) if not name.startswith('__'))
        if access_mode not in access_mode_dict.values():
            print("DeviceManager.open_device_by_user_id: access_mode out of bounds, %s" % access_mode_dict.__str__())
            return None

        # get device class from self.__device_info_list
        device_class = self.__get_device_class_by_user_id(user_id)
        if device_class == -1:
            # Re-update the device
            self.update_all_device_list()
            device_class = self.__get_device_class_by_user_id(user_id)
            if device_class == -1:
                # don't find this user_id
                raise NotFoundDevice("DeviceManager.open_device_by_user_id: Not found device")

        # open device by user_id
        open_param = GxOpenParam()
        open_param.content = string_encoding(user_id)
        open_param.open_mode = GxOpenMode.USER_ID
        open_param.access_mode = access_mode
        status, handle = gx_open_device(open_param)
        StatusProcessor.process(status, 'DeviceManager', 'open_device_by_user_id')

        if device_class == GxDeviceClassList.U3V:
            return U3VDevice(handle)
        elif device_class == GxDeviceClassList.GEV:
            return GEVDevice(handle)
        else:
            raise NotFoundDevice("DeviceManager.open_device_by_user_id: Does not support this device type.")

    def open_device_by_ip(self, ip, access_mode=GxAccessMode.CONTROL):
        """
        :brief      open device by device ip address
        :param      ip:             device ip address, type:str
        :param      access_mode:    the mode of open device[GxAccessMode]
        :return:    GEVDevice object
        """
        if not isinstance(ip, str):
            raise ParameterTypeError("DeviceManager.open_device_by_ip: "
                                     "Expected ip type is str, not %s" % type(ip))

        if not isinstance(access_mode, INT_TYPE):
            raise ParameterTypeError("DeviceManager.open_device_by_ip: "
                                     "Expected access_mode type is int, not %s" % type(access_mode))

        access_mode_dict = dict((name, getattr(GxAccessMode, name)) for name in dir(GxAccessMode) if not name.startswith('__'))
        if access_mode not in access_mode_dict.values():
            print("DeviceManager.open_device_by_ip: access_mode out of bounds, %s" % access_mode_dict.__str__())
            return None

        # open device by ip
        open_param = GxOpenParam()
        open_param.content = string_encoding(ip)
        open_param.open_mode = GxOpenMode.IP
        open_param.access_mode = access_mode
        status, handle = gx_open_device(open_param)
        StatusProcessor.process(status, 'DeviceManager', 'open_device_by_ip')

        return GEVDevice(handle)

    def open_device_by_mac(self, mac, access_mode=GxAccessMode.CONTROL):
        """
        :brief      open device by device mac address
        :param      mac:            device mac address, type:str
        :param      access_mode:    the mode of open device[GxAccessMode]
        :return:    GEVDevice object
        """
        if not isinstance(mac, str):
            raise ParameterTypeError("DeviceManager.open_device_by_mac: "
                                     "Expected mac type is str, not %s" % type(mac))

        if not isinstance(access_mode, INT_TYPE):
            raise ParameterTypeError("DeviceManager.open_device_by_mac: "
                                     "Expected access_mode type is int, not %s" % type(access_mode))

        access_mode_dict = dict((name, getattr(GxAccessMode, name)) for name in dir(GxAccessMode) if not name.startswith('__'))
        if access_mode not in access_mode_dict.values():
            print("DeviceManager.open_device_by_mac: access_mode out of bounds, %s" % access_mode_dict.__str__())
            return None

        # open device by ip
        open_param = GxOpenParam()
        open_param.content = string_encoding(mac)
        open_param.open_mode = GxOpenMode.MAC
        open_param.access_mode = access_mode
        status, handle = gx_open_device(open_param)
        StatusProcessor.process(status, 'DeviceManager', 'open_device_by_mac')

        return GEVDevice(handle)


class Feature:
    def __init__(self, handle, feature):
        """
        :param  handle:      The handle of the device
        :param  feature:     The feature code ID
        """
        self.__handle = handle
        self.__feature = feature
        self.feature_name = self.__get_name()

    def __get_name(self):
        """
        brief:  Getting Feature Name
        return: Success:    feature name
                Failed:     convert feature ID to string
        """
        status, name = gx_get_feature_name(self.__handle, self.__feature)
        if status != GxStatusList.SUCCESS:
            name = (hex(self.__feature)).__str__()

        return name

    def is_implemented(self):
        """
        brief:  Determining whether the feature is implemented
        return: is_implemented
        """
        status, is_implemented = gx_is_implemented(self.__handle, self.__feature)
        if status == GxStatusList.SUCCESS:
            return is_implemented
        elif status == GxStatusList.INVALID_PARAMETER:
            return False
        else:
            StatusProcessor.process(status, 'Feature', 'is_implemented')

    def is_readable(self):
        """
        brief:  Determining whether the feature is readable
        return: is_readable
        """
        implemented = self.is_implemented()
        if not implemented:
            return False

        status, is_readable = gx_is_readable(self.__handle, self.__feature)
        StatusProcessor.process(status, 'Feature', 'is_readable')
        return is_readable

    def is_writable(self):
        """
        brief:  Determining whether the feature is writable
        return: is_writable
        """
        implemented = self.is_implemented()
        if not implemented:
            return False

        status, is_writable = gx_is_writable(self.__handle, self.__feature)
        StatusProcessor.process(status, 'Feature', 'is_writable')
        return is_writable


class IntFeature(Feature):
    def __init__(self, handle, feature):
        """
        :param  handle:      The handle of the device
        :param  feature:     The feature code ID
        """
        Feature.__init__(self, handle, feature)
        self.__handle = handle
        self.__feature = feature

    def __range_dict(self, int_range):
        """
        :brief      Convert GxIntRange to dictionary
        :param      int_range:  GxIntRange
        :return:    range_dicts
        """
        range_dicts = {
            "min": int_range.min,
            "max": int_range.max,
            "inc": int_range.inc
        }
        return range_dicts

    def get_range(self):
        """
        :brief      Getting integer range
        :return:    integer range dictionary
        """
        implemented = self.is_implemented()
        if not implemented:
            print("%s.get_range is not support" % self.feature_name)
            return None

        status, int_range = gx_get_int_range(self.__handle, self.__feature)
        StatusProcessor.process(status, 'IntFeature', 'get_range')
        return self.__range_dict(int_range)

    def get(self):
        """
        :brief      Getting integer value
        :return:    integer value
        """
        readable = self.is_readable()
        if not readable:
            print("%s.get is not readable" % self.feature_name)
            return None

        status, int_value = gx_get_int(self.__handle, self.__feature)
        StatusProcessor.process(status, 'IntFeature', 'get')
        return int_value

    def set(self, int_value):
        """
        :brief      Setting integer value
        :param      int_value
        :return:    None
        """
        if not isinstance(int_value, INT_TYPE):
            raise ParameterTypeError("IntFeature.set: "
                                     "Expected int_value type is int, not %s" % type(int_value))

        writeable = self.is_writable()
        if not writeable:
            print("%s.set: is not writeable" % self.feature_name)
            return

        int_range = self.get_range()
        check_ret = range_check(int_value, int_range["min"], int_range["max"], int_range["inc"])
        if not check_ret:
            print("IntFeature.set: "
                  "int_value out of bounds, %s.range=[%d, %d, %d]" %
                  (self.feature_name, int_range["min"], int_range["max"], int_range["inc"]))
            return

        status = gx_set_int(self.__handle, self.__feature, int_value)
        StatusProcessor.process(status, 'IntFeature', 'set')


class FloatFeature(Feature):
    def __init__(self, handle, feature):
        """
        :param      handle:      The handle of the device
        :param      feature:     The feature code ID
        """
        Feature.__init__(self, handle, feature)
        self.__handle = handle
        self.__feature = feature

    def __range_dict(self, float_range):
        """
        :brief      Convert GxFloatRange to dictionary
        :param      float_range:  GxFloatRange
        :return:    range_dicts
        """
        range_dicts = {
            "min": float_range.min,
            "max": float_range.max,
            "inc": float_range.inc,
            "unit": string_decoding(float_range.unit),
            "inc_is_valid": float_range.inc_is_valid
        }
        return range_dicts

    def get_range(self):
        """
        :brief      Getting float range
        :return:    float range dictionary
        """
        implemented = self.is_implemented()
        if not implemented:
            print("%s.get_range is not support" % self.feature_name)
            return None

        status, float_range = gx_get_float_range(self.__handle, self.__feature)
        StatusProcessor.process(status, 'FloatFeature', 'get_range')
        return self.__range_dict(float_range)

    def get(self):
        """
        :brief      Getting float value
        :return:    float value
        """
        readable = self.is_readable()
        if not readable:
            print("%s.get: is not readable" % self.feature_name)
            return None

        status, float_value = gx_get_float(self.__handle, self.__feature)
        StatusProcessor.process(status, 'FloatFeature', 'get')
        return float_value

    def set(self, float_value):
        """
        :brief      Setting float value
        :param      float_value
        :return:    None
        """
        if not isinstance(float_value, (INT_TYPE, float)):
            raise ParameterTypeError("FloatFeature.set: "
                                     "Expected float_value type is float, not %s" % type(float_value))

        writeable = self.is_writable()
        if not writeable:
            print("%s.set: is not writeable" % self.feature_name)
            return

        float_range = self.get_range()
        check_ret = range_check(float_value, float_range["min"], float_range["max"])
        if not check_ret:
            print("FloatFeature.set: float_value out of bounds, %s.range=[%f, %f]" %
                  (self.feature_name, float_range["min"], float_range["max"]))
            return

        status = gx_set_float(self.__handle, self.__feature, float_value)
        StatusProcessor.process(status, 'FloatFeature', 'set')


class EnumFeature(Feature):
    def __init__(self, handle, feature):
        """
        :param handle:      The handle of the device
        :param feature:     The feature code ID
        """
        Feature.__init__(self, handle, feature)
        self.__handle = handle
        self.__feature = feature

    def get_range(self):
        """
        :brief      Getting range of Enum feature
        :return:    enum_dict:    enum range dictionary
        """
        implemented = self.is_implemented()
        if not implemented:
            print("%s.get_range: is not support" % self.feature_name)
            return None

        status, enum_num = gx_get_enum_entry_nums(self.__handle, self.__feature)
        StatusProcessor.process(status, 'EnumFeature', 'get_range')

        status, enum_list = gx_get_enum_description(self.__handle, self.__feature, enum_num)
        StatusProcessor.process(status, 'EnumFeature', 'get_range')

        enum_dict = {}
        for i in range(enum_num):
            enum_dict[string_decoding(enum_list[i].symbolic)] = enum_list[i].value

        return enum_dict

    def get(self):
        """
        :brief      Getting value of Enum feature
        :return:    enum_value:     enum value
                    enum_str:       string for enum description
        """
        readable = self.is_readable()
        if not readable:
            print("%s.get: is not readable" % self.feature_name)
            return None, None

        status, enum_value = gx_get_enum(self.__handle, self.__feature)
        StatusProcessor.process(status, 'EnumFeature', 'get')

        range_dict = self.get_range()
        new_dicts = {v: k for k, v in range_dict.items()}
        return enum_value, new_dicts[enum_value]

    def set(self, enum_value):
        """
        :brief      Setting enum value
        :param      enum_value
        :return:    None
        """
        if not isinstance(enum_value, INT_TYPE):
            raise ParameterTypeError("EnumFeature.set: "
                                     "Expected enum_value type is int, not %s" % type(enum_value))

        writeable = self.is_writable()
        if not writeable:
            print("%s.set: is not writeable" % self.feature_name)
            return

        range_dict = self.get_range()
        enum_value_list = range_dict.values()
        if enum_value not in enum_value_list:
            print("EnumFeature.set: enum_value out of bounds, %s.range:%s" %
                  (self.feature_name, range_dict.__str__()))
            return

        status = gx_set_enum(self.__handle, self.__feature, enum_value)
        StatusProcessor.process(status, 'EnumFeature', 'set')


class BoolFeature(Feature):
    def __init__(self, handle, feature):
        """
        :param handle:      The handle of the device
        :param feature:     The feature code ID
        """
        Feature.__init__(self, handle, feature)
        self.__handle = handle
        self.__feature = feature

    def get(self):
        """
        :brief      Getting bool value
        :return:    bool value[bool]
        """
        readable = self.is_readable()
        if not readable:
            print("%s.get is not readable" % self.feature_name)
            return None

        status, bool_value = gx_get_bool(self.__handle, self.__feature)
        StatusProcessor.process(status, 'BoolFeature', 'get')
        return bool_value

    def set(self, bool_value):
        """
        :brief      Setting bool value
        :param      bool_value[bool]
        :return:    None
        """
        if not isinstance(bool_value, bool):
            raise ParameterTypeError("BoolFeature.set: "
                                     "Expected bool_value type is bool, not %s" % type(bool_value))

        writeable = self.is_writable()
        if not writeable:
            print("%s.set: is not writeable" % self.feature_name)
            return

        status = gx_set_bool(self.__handle, self.__feature, bool_value)
        StatusProcessor.process(status, 'BoolFeature', 'set')


class StringFeature(Feature):
    def __init__(self, handle, feature):
        """
        :param      handle:      The handle of the device
        :param      feature:     The feature code ID
        """
        Feature.__init__(self, handle, feature)
        self.__handle = handle
        self.__feature = feature

    def get_string_max_length(self):
        """
        :brief      Getting the maximum length that string can set
        :return:    length:     the maximum length that string can set
        """
        implemented = self.is_implemented()
        if not implemented:
            print("%s.get_string_max_length is not support" % self.feature_name)
            return None

        status, length = gx_get_string_max_length(self.__handle, self.__feature)
        StatusProcessor.process(status, 'StringFeature', 'get_string_max_length')
        return length

    def get(self):
        """
        :brief      Getting string value
        :return:    strings
        """
        readable = self.is_readable()
        if not readable:
            print("%s.get is not readable" % self.feature_name)
            return None

        status, strings = gx_get_string(self.__handle, self.__feature)
        StatusProcessor.process(status, 'StringFeature', 'get')
        return strings

    def set(self, input_string):
        """
        :brief      Setting string value
        :param      input_string[string]
        :return:    None
        """
        if not isinstance(input_string, str):
            raise ParameterTypeError("StringFeature.set: "
                                     "Expected input_string type is str, not %s" % type(input_string))

        writeable = self.is_writable()
        if not writeable:
            print("%s.set: is not writeable" % self.feature_name)
            return

        max_length = self.get_string_max_length()
        if input_string.__len__() > max_length:
            print("StringFeature.set: "
                  "input_string length out of bounds, %s.length_max:%s"
                  % (self.feature_name, max_length))
            return

        status = gx_set_string(self.__handle, self.__feature, input_string)
        StatusProcessor.process(status, 'StringFeature', 'set')


class BufferFeature(Feature):
    def __init__(self, handle, feature):
        """
        :param      handle:      The handle of the device
        :param      feature:     The feature code ID
        """
        Feature.__init__(self, handle, feature)
        self.__handle = handle
        self.__feature = feature

    def get_buffer_length(self):
        """
        :brief      Getting buffer length
        :return:    length:     buffer length
        """
        implemented = self.is_implemented()
        if not implemented:
            print("%s.get_buffer_length is not support" % self.feature_name)
            return None

        status, length = gx_get_buffer_length(self.__handle, self.__feature)
        StatusProcessor.process(status, 'BuffFeature', 'get_buffer_length')
        return length

    def get_buffer(self):
        """
        :brief      Getting buffer data
        :return:    Buffer object

        """
        readable = self.is_readable()
        if not readable:
            print("%s.get_buffer is not readable" % self.feature_name)
            return None

        status, buf = gx_get_buffer(self.__handle, self.__feature)
        StatusProcessor.process(status, 'BuffFeature', 'get_buffer')
        return Buffer(buf)

    def set_buffer(self, buf):
        """
        :brief      Setting buffer data
        :param      buf:    Buffer object
        :return:    None
        """
        if not isinstance(buf, Buffer):
            raise ParameterTypeError("BuffFeature.set_buffer: "
                                     "Expected buff type is Buffer, not %s" % type(buf))

        writeable = self.is_writable()
        if not writeable:
            print("%s.set_buffer is not writeable" % self.feature_name)
            return

        max_length = self.get_buffer_length()
        if buf.get_length() > max_length:
            print("BuffFeature.set_buffer: "
                  "buff length out of bounds, %s.length_max:%s" % (self.feature_name, max_length))
            return

        status = gx_set_buffer(self.__handle, self.__feature,
                               buf.get_ctype_array(), buf.get_length())
        StatusProcessor.process(status, 'BuffFeature', 'set_buffer')


class CommandFeature(Feature):
    def __init__(self, handle, feature):
        """
        :param      handle:      The handle of the device
        :param      feature:     The feature code ID
        """
        Feature.__init__(self, handle, feature)
        self.__handle = handle
        self.__feature = feature

    def send_command(self):
        """
        :brief      Sending command
        :return:    None
        """
        implemented = self.is_implemented()
        if not implemented:
            print("%s.send_command is not support" % self.feature_name)
            return

        status = gx_send_command(self.__handle, self.__feature)
        StatusProcessor.process(status, 'CommandFeature', 'send_command')


class Buffer:
    def __init__(self, data_array):
        try:
            addressof(data_array)
        except TypeError:
            error_msg = "Buffer.__init__: param is error type."
            raise ParameterTypeError(error_msg)

        self.data_array = data_array

    @staticmethod
    def from_file(file_name):
        file_object = open(file_name, "rb")
        file_string = file_object.read()
        data_array = create_string_buffer(file_string)
        file_object.close()
        return Buffer(data_array)

    @staticmethod
    def from_string(string_data):
        data_array = create_string_buffer(string_data)
        return Buffer(data_array)

    def get_data(self):
        buff_p = c_void_p()
        buff_p.value = addressof(self.data_array)
        print(buff_p.value)
        string_data = string_at(buff_p, len(self.data_array))
        return string_data

    def get_ctype_array(self):
        return self.data_array

    def get_numpy_array(self):
        numpy_array = numpy.array(self.data_array)
        return numpy_array

    def get_length(self):
        return len(self.data_array)


class Device:
    """
    The Camera class mainly encapsulates some common operations and function attributes,
    which are the operations and properties usually found in the camera.
    In addition, this class also encapsulates the common operations of  some functions in the C interface,
    such as SetInt, SetFloat, etc. Can not open to the user, so that when the subsequent addition of features,
    Python interface does not upgrade, or only the definition of the control code can support new features
    """
    def __init__(self, handle):
        self.__dev_handle = handle
        self.data_stream = []

        self.__OfflineCallBack = None
        self.__py_offline_callback = None
        self.__offline_callback_handle = None
        self.__py_capture_callback = None
        self.__CaptureCallBack = None
        self.__user_param = None

        # ---------------Device Information Section--------------------------
        self.DeviceVendorName = StringFeature(self.__dev_handle, GxFeatureID.STRING_DEVICE_VENDOR_NAME)
        self.DeviceModelName = StringFeature(self.__dev_handle, GxFeatureID.STRING_DEVICE_MODEL_NAME)
        self.DeviceFirmwareVersion = StringFeature(self.__dev_handle, GxFeatureID.STRING_DEVICE_FIRMWARE_VERSION)
        self.DeviceVersion = StringFeature(self.__dev_handle, GxFeatureID.STRING_DEVICE_VERSION)
        self.DeviceSerialNumber = StringFeature(self.__dev_handle, GxFeatureID.STRING_DEVICE_SERIAL_NUMBER)
        self.FactorySettingVersion = StringFeature(self.__dev_handle, GxFeatureID.STRING_FACTORY_SETTING_VERSION)
        self.DeviceUserID = StringFeature(self.__dev_handle, GxFeatureID.STRING_DEVICE_USER_ID)
        self.DeviceLinkSelector = IntFeature(self.__dev_handle, GxFeatureID.INT_DEVICE_LINK_SELECTOR)
        self.DeviceLinkThroughputLimitMode = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_DEVICE_LINK_THROUGHPUT_LIMIT_MODE)
        self.DeviceLinkThroughputLimit = IntFeature(self.__dev_handle, GxFeatureID.INT_DEVICE_LINK_THROUGHPUT_LIMIT)
        self.DeviceLinkCurrentThroughput = IntFeature(self.__dev_handle, GxFeatureID.INT_DEVICE_LINK_CURRENT_THROUGHPUT)
        self.DeviceReset = CommandFeature(self.__dev_handle, GxFeatureID.COMMAND_DEVICE_RESET)
        self.TimestampTickFrequency = IntFeature(self.__dev_handle, GxFeatureID.INT_TIMESTAMP_TICK_FREQUENCY)
        self.TimestampLatch = CommandFeature(self.__dev_handle, GxFeatureID.COMMAND_TIMESTAMP_LATCH)
        self.TimestampReset = CommandFeature(self.__dev_handle, GxFeatureID.COMMAND_TIMESTAMP_RESET)
        self.TimestampLatchReset = CommandFeature(self.__dev_handle, GxFeatureID.COMMAND_TIMESTAMP_LATCH_RESET)
        self.TimestampLatchValue = IntFeature(self.__dev_handle, GxFeatureID.INT_TIMESTAMP_LATCH_VALUE)

        # ---------------ImageFormat Section--------------------------------
        self.SensorWidth = IntFeature(self.__dev_handle, GxFeatureID.INT_SENSOR_WIDTH)
        self.SensorHeight = IntFeature(self.__dev_handle, GxFeatureID.INT_SENSOR_HEIGHT)
        self.WidthMax = IntFeature(self.__dev_handle, GxFeatureID.INT_WIDTH_MAX)
        self.HeightMax = IntFeature(self.__dev_handle, GxFeatureID.INT_HEIGHT_MAX)
        self.OffsetX = IntFeature(self.__dev_handle, GxFeatureID.INT_OFFSET_X)
        self.OffsetY = IntFeature(self.__dev_handle, GxFeatureID.INT_OFFSET_Y)
        self.Width = IntFeature(self.__dev_handle, GxFeatureID.INT_WIDTH)
        self.Height = IntFeature(self.__dev_handle, GxFeatureID.INT_HEIGHT)
        self.BinningHorizontal = IntFeature(self.__dev_handle, GxFeatureID.INT_BINNING_HORIZONTAL)
        self.BinningVertical = IntFeature(self.__dev_handle, GxFeatureID.INT_BINNING_VERTICAL)
        self.DecimationHorizontal = IntFeature(self.__dev_handle, GxFeatureID.INT_DECIMATION_HORIZONTAL)
        self.DecimationVertical = IntFeature(self.__dev_handle, GxFeatureID.INT_DECIMATION_VERTICAL)
        self.PixelSize = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_PIXEL_SIZE)
        self.PixelColorFilter = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_PIXEL_COLOR_FILTER)
        self.PixelFormat = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_PIXEL_FORMAT)
        self.ReverseX = BoolFeature(self.__dev_handle, GxFeatureID.BOOL_REVERSE_X)
        self.ReverseY = BoolFeature(self.__dev_handle, GxFeatureID.BOOL_REVERSE_Y)
        self.TestPattern = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_TEST_PATTERN)
        self.TestPatternGeneratorSelector = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_TEST_PATTERN_GENERATOR_SELECTOR)
        self.RegionSendMode = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_REGION_SEND_MODE)
        self.RegionMode = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_REGION_MODE)
        self.RegionSelector = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_REGION_SELECTOR)
        self.CenterWidth = IntFeature(self.__dev_handle, GxFeatureID.INT_CENTER_WIDTH)
        self.CenterHeight = IntFeature(self.__dev_handle, GxFeatureID.INT_CENTER_HEIGHT)
        self.BinningHorizontalMode = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_BINNING_HORIZONTAL_MODE)
        self.BinningVerticalMode = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_BINNING_VERTICAL_MODE)

        # ---------------TransportLayer Section-------------------------------
        self.PayloadSize = IntFeature(self.__dev_handle, GxFeatureID.INT_PAYLOAD_SIZE)

        # ---------------AcquisitionTrigger Section---------------------------
        self.AcquisitionMode = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_ACQUISITION_MODE)
        self.AcquisitionStart = CommandFeature(self.__dev_handle, GxFeatureID.COMMAND_ACQUISITION_START)
        self.AcquisitionStop = CommandFeature(self.__dev_handle, GxFeatureID.COMMAND_ACQUISITION_STOP)
        self.TriggerMode = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_TRIGGER_MODE)
        self.TriggerSoftware = CommandFeature(self.__dev_handle, GxFeatureID.COMMAND_TRIGGER_SOFTWARE)
        self.TriggerActivation = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_TRIGGER_ACTIVATION)
        self.ExposureTime = FloatFeature(self.__dev_handle, GxFeatureID.FLOAT_EXPOSURE_TIME)
        self.ExposureAuto = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_EXPOSURE_AUTO)
        self.TriggerFilterRaisingEdge = FloatFeature(self.__dev_handle, GxFeatureID.FLOAT_TRIGGER_FILTER_RAISING)
        self.TriggerFilterFallingEdge = FloatFeature(self.__dev_handle, GxFeatureID.FLOAT_TRIGGER_FILTER_FALLING)
        self.TriggerSource = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_TRIGGER_SOURCE)
        self.ExposureMode = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_EXPOSURE_MODE)
        self.TriggerSelector = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_TRIGGER_SELECTOR)
        self.TriggerDelay = FloatFeature(self.__dev_handle, GxFeatureID.FLOAT_TRIGGER_DELAY)
        self.TransferControlMode = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_TRANSFER_CONTROL_MODE)
        self.TransferOperationMode = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_TRANSFER_OPERATION_MODE)
        self.TransferStart = CommandFeature(self.__dev_handle, GxFeatureID.COMMAND_TRANSFER_START)
        self.TransferBlockCount = IntFeature(self.__dev_handle, GxFeatureID.INT_TRANSFER_BLOCK_COUNT)
        self.FrameBufferOverwriteActive = BoolFeature(self.__dev_handle, GxFeatureID.BOOL_FRAME_STORE_COVER_ACTIVE)
        self.AcquisitionFrameRateMode = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_ACQUISITION_FRAME_RATE_MODE)
        self.AcquisitionFrameRate = FloatFeature(self.__dev_handle, GxFeatureID.FLOAT_ACQUISITION_FRAME_RATE)
        self.CurrentAcquisitionFrameRate = FloatFeature(self.__dev_handle, GxFeatureID.FLOAT_CURRENT_ACQUISITION_FRAME_RATE)
        self.FixedPatternNoiseCorrectMode = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_FIXED_PATTERN_NOISE_CORRECT_MODE)
        self.AcquisitionBurstFrameCount = IntFeature(self.__dev_handle, GxFeatureID.INT_ACQUISITION_BURST_FRAME_COUNT)
        self.AcquisitionStatusSelector = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_ACQUISITION_STATUS_SELECTOR)
        self.AcquisitionStatus = BoolFeature(self.__dev_handle, GxFeatureID.BOOL_ACQUISITION_STATUS)
        self.ExposureDelay = FloatFeature(self.__dev_handle, GxFeatureID.FLOAT_EXPOSURE_DELAY)

        # ----------------DigitalIO Section----------------------------------
        self.UserOutputSelector = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_USER_OUTPUT_SELECTOR)
        self.UserOutputValue = BoolFeature(self.__dev_handle, GxFeatureID.BOOL_USER_OUTPUT_VALUE)
        self.LineSelector = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_LINE_SELECTOR)
        self.LineMode = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_LINE_MODE)
        self.LineInverter = BoolFeature(self.__dev_handle, GxFeatureID.BOOL_LINE_INVERTER)
        self.LineSource = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_LINE_SOURCE)
        self.LineStatus = BoolFeature(self.__dev_handle, GxFeatureID.BOOL_LINE_STATUS)
        self.LineStatusAll = IntFeature(self.__dev_handle, GxFeatureID.INT_LINE_STATUS_ALL)

        # ----------------AnalogControls Section----------------------------
        self.GainAuto = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_GAIN_AUTO)
        self.GainSelector = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_GAIN_SELECTOR)
        self.BlackLevelAuto = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_BLACK_LEVEL_AUTO)
        self.BlackLevelSelector = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_BLACK_LEVEL_SELECTOR)
        self.BalanceWhiteAuto = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_BALANCE_WHITE_AUTO)
        self.BalanceRatioSelector = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_BALANCE_RATIO_SELECTOR)
        self.BalanceRatio = FloatFeature(self.__dev_handle, GxFeatureID.FLOAT_BALANCE_RATIO)
        self.DeadPixelCorrect = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_DEAD_PIXEL_CORRECT)
        self.Gain = FloatFeature(self.__dev_handle, GxFeatureID.FLOAT_GAIN)
        self.BlackLevel = FloatFeature(self.__dev_handle, GxFeatureID.FLOAT_BLACK_LEVEL)
        self.GammaEnable = BoolFeature(self.__dev_handle, GxFeatureID.BOOL_GAMMA_ENABLE)
        self.GammaMode = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_GAMMA_MODE)
        self.Gamma = FloatFeature(self.__dev_handle, GxFeatureID.FLOAT_GAMMA)
        self.DigitalShift = IntFeature(self.__dev_handle, GxFeatureID.INT_DIGITAL_SHIFT)

        # ---------------CustomFeature Section------------------------------
        self.ExpectedGrayValue = IntFeature(self.__dev_handle, GxFeatureID.INT_GRAY_VALUE)
        self.AAROIOffsetX = IntFeature(self.__dev_handle, GxFeatureID.INT_AAROI_OFFSETX)
        self.AAROIOffsetY = IntFeature(self.__dev_handle, GxFeatureID.INT_AAROI_OFFSETY)
        self.AAROIWidth = IntFeature(self.__dev_handle, GxFeatureID.INT_AAROI_WIDTH)
        self.AAROIHeight = IntFeature(self.__dev_handle, GxFeatureID.INT_AAROI_HEIGHT)
        self.AutoGainMin = FloatFeature(self.__dev_handle, GxFeatureID.FLOAT_AUTO_GAIN_MIN)
        self.AutoGainMax = FloatFeature(self.__dev_handle, GxFeatureID.FLOAT_AUTO_GAIN_MAX)
        self.AutoExposureTimeMin = FloatFeature(self.__dev_handle, GxFeatureID.FLOAT_AUTO_EXPOSURE_TIME_MIN)
        self.AutoExposureTimeMax = FloatFeature(self.__dev_handle, GxFeatureID.FLOAT_AUTO_EXPOSURE_TIME_MAX)
        self.ContrastParam = IntFeature(self.__dev_handle, GxFeatureID.INT_CONTRAST_PARAM)
        self.GammaParam = FloatFeature(self.__dev_handle, GxFeatureID.FLOAT_GAMMA_PARAM)
        self.ColorCorrectionParam = IntFeature(self.__dev_handle, GxFeatureID.INT_COLOR_CORRECTION_PARAM)
        self.AWBLampHouse = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_AWB_LAMP_HOUSE)
        self.AWBROIOffsetX = IntFeature(self.__dev_handle, GxFeatureID.INT_AWBROI_OFFSETX)
        self.AWBROIOffsetY = IntFeature(self.__dev_handle, GxFeatureID.INT_AWBROI_OFFSETY)
        self.AWBROIWidth = IntFeature(self.__dev_handle, GxFeatureID.INT_AWBROI_WIDTH)
        self.AWBROIHeight = IntFeature(self.__dev_handle, GxFeatureID.INT_AWBROI_HEIGHT)
        self.SharpnessMode = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_SHARPNESS_MODE)
        self.Sharpness = FloatFeature(self.__dev_handle, GxFeatureID.FLOAT_SHARPNESS)

        # ---------------UserSetControl Section-------------------------
        self.UserSetSelector = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_USER_SET_SELECTOR)
        self.UserSetLoad = CommandFeature(self.__dev_handle, GxFeatureID.COMMAND_USER_SET_LOAD)
        self.UserSetSave = CommandFeature(self.__dev_handle, GxFeatureID.COMMAND_USER_SET_SAVE)
        self.UserSetDefault = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_USER_SET_DEFAULT)

        # ---------------LUT Section-------------------------------
        self.LUTSelector = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_LUT_SELECTOR)
        self.LUTValueAll = BufferFeature(self.__dev_handle, GxFeatureID.BUFFER_LUT_VALUE_ALL)
        self.LUTEnable = BoolFeature(self.__dev_handle, GxFeatureID.BOOL_LUT_ENABLE)
        self.LUTIndex = IntFeature(self.__dev_handle, GxFeatureID.INT_LUT_INDEX)
        self.LUTValue = IntFeature(self.__dev_handle, GxFeatureID.INT_LUT_VALUE)

        # ---------------Color Transformation Control--------------
        self.ColorTransformationMode = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_COLOR_TRANSFORMATION_MODE)
        self.ColorTransformationEnable = BoolFeature(self.__dev_handle, GxFeatureID.BOOL_COLOR_TRANSFORMATION_ENABLE)
        self.ColorTransformationValueSelector = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_COLOR_TRANSFORMATION_VALUE_SELECTOR)
        self.ColorTransformationValue = FloatFeature(self.__dev_handle, GxFeatureID.FLOAT_COLOR_TRANSFORMATION_VALUE)

        # ---------------ChunkData Section-------------------------
        self.ChunkModeActive = BoolFeature(self.__dev_handle, GxFeatureID.BOOL_CHUNK_MODE_ACTIVE)
        self.ChunkSelector = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_CHUNK_SELECTOR)
        self.ChunkEnable = BoolFeature(self.__dev_handle, GxFeatureID.BOOL_CHUNK_ENABLE)


    def stream_on(self):
        """
        :brief      send start command, camera start transmission image data
        :return:    none
        """
        status = gx_send_command(self.__dev_handle, GxFeatureID.COMMAND_ACQUISITION_START)
        StatusProcessor.process(status, 'Device', 'stream_on')

        payload_size = self.PayloadSize.get()
        self.data_stream[0].set_payload_size(payload_size)
        self.data_stream[0].acquisition_flag = True

    def stream_off(self):
        """
        :brief      send stop command, camera stop transmission image data
        :return:    none
        """
        self.data_stream[0].acquisition_flag = False
        status = gx_send_command(self.__dev_handle, GxFeatureID.COMMAND_ACQUISITION_STOP)
        StatusProcessor.process(status, 'Device', 'stream_off')

    def export_config_file(self, file_path):
        """
        :brief      Export the current configuration file
        :param      file_path:      file path(type: str)
        :return:    none
        """
        if not isinstance(file_path, str):
            raise ParameterTypeError("Device.export_config_file: "
                                     "Expected file_path type is str, not %s" % type(file_path))

        status = gx_export_config_file(self.__dev_handle, file_path)
        StatusProcessor.process(status, 'Device', 'export_config_file')

    def import_config_file(self, file_path, verify=False):
        """
        :brief      Imported configuration file
        :param      file_path:  file path(type: str)
        :param      verify:     If this value is true, all the imported values will be read out
                                and checked for consistency(type: bool)
        :return:    none
        """
        if not isinstance(file_path, str):
            raise ParameterTypeError("Device.import_config_file: "
                                     "Expected file_path type is str, not %s" % type(file_path))

        if not isinstance(verify, bool):
            raise ParameterTypeError("Device.import_config_file: "
                                     "Expected verify type is bool, not %s" % type(verify))

        status = gx_import_config_file(self.__dev_handle, file_path, verify)
        StatusProcessor.process(status, 'Device', 'import_config_file')

    def close_device(self):
        """
        :brief      close device, close device handle
        :return:    None
        """
        status = gx_close_device(self.__dev_handle)
        StatusProcessor.process(status, 'Device', 'close_device')
        self.__dev_handle = None

    def get_stream_channel_num(self):
        """
        :brief      Get the number of stream channels supported by the current device.
        :return:    the number of stream channels
        """
        return len(self.data_stream)


    def register_device_offline_callback(self, call_back):
        """
        :brief      Register the device offline event callback function.
        :param      call_back:  callback function
        :return:    none
        """
        self.__py_offline_callback = call_back
        self.__OfflineCallBack = OFF_LINE_CALL(self.__on_device_offline_call_back)
        status, self.__offline_callback_handle = gx_register_device_offline_callback\
            (self.__dev_handle, self.__OfflineCallBack)
        StatusProcessor.process(status, 'Device', 'register_device_offline_callback')

    def unregister_device_offline_callback(self):
        """
        :brief      Unregister the device offline event callback function.
        :return:    none
        """
        status = gx_unregister_device_offline_callback(self.__dev_handle, self.__offline_callback_handle)
        self.__py_offline_callback = None
        self.__offline_callback_handle = None
        StatusProcessor.process(status, 'Device', 'unregister_device_offline_callback')

    def __on_device_offline_call_back(self, c_user_param):
        """
        :brief      Device offline event callback function with an unused c_void_p.
        :return:    none
        """
        self.__py_offline_callback()


    def register_capture_callback(self, user_param, cap_call):
        """
        :brief      Register the capture event callback function.
        :param      cap_call:  callback function
        :return:    none
        """
        self.__user_param = user_param
        self.__py_capture_callback = cap_call
        self.__CaptureCallBack = CAP_CALL(self.__on_capture_call_back)
        status = gx_register_capture_callback(self.__dev_handle, self.__CaptureCallBack)
        StatusProcessor.process(status, 'Device', 'register_capture_callback')

    def unregister_capture_callback(self):
        """
        :brief      Unregister the capture event callback function.
        :return:    none
        """
        status = gx_unregister_capture_callback(self.__dev_handle)
        self.__py_capture_callback = None
        self.__user_param = None
        StatusProcessor.process(status, 'Device', 'unregister_capture_callback')

    def __on_capture_call_back(self, capture_data):
        """
        :brief      Capture event callback function with capture date.
        :return:    none
        """
        frame_data = GxFrameData()
        frame_data.image_buf = capture_data.contents.image_buf
        frame_data.width = capture_data.contents.width
        frame_data.height = capture_data.contents.height
        frame_data.pixel_format = capture_data.contents.pixel_format
        frame_data.image_size = capture_data.contents.image_size
        frame_data.frame_id = capture_data.contents.frame_id
        frame_data.timestamp = capture_data.contents.timestamp
        frame_data.buf_id = capture_data.contents.frame_id
        image = RawImage(frame_data)
        self.__py_capture_callback(self.__user_param, image)


class GEVDevice(Device):
    def __init__(self, handle):
        self.__dev_handle = handle
        Device.__init__(self, self.__dev_handle)
        self.GevCurrentIPConfigurationLLA = BoolFeature(self.__dev_handle, GxFeatureID.BOOL_GEV_CURRENT_IP_CONFIGURATION_LLA)
        self.GevCurrentIPConfigurationDHCP = BoolFeature(self.__dev_handle, GxFeatureID.BOOL_GEV_CURRENT_IP_CONFIGURATION_DHCP)
        self.GevCurrentIPConfigurationPersistentIP = BoolFeature(self.__dev_handle, GxFeatureID.BOOL_GEV_CURRENT_IP_CONFIGURATION_PERSISTENT_IP)
        self.EstimatedBandwidth = IntFeature(self.__dev_handle, GxFeatureID.INT_ESTIMATED_BANDWIDTH)
        self.GevHeartbeatTimeout = IntFeature(self.__dev_handle, GxFeatureID.INT_GEV_HEARTBEAT_TIMEOUT)
        self.GevSCPSPacketSize = IntFeature(self.__dev_handle, GxFeatureID.INT_GEV_PACKET_SIZE)
        self.GevSCPD = IntFeature(self.__dev_handle, GxFeatureID.INT_GEV_PACKET_DELAY)
        self.GevLinkSpeed = IntFeature(self.__dev_handle, GxFeatureID.INT_GEV_LINK_SPEED)
        self.DeviceCommandTimeout = IntFeature(self.__dev_handle, GxFeatureID.INT_COMMAND_TIMEOUT)
        self.DeviceCommandRetryCount = IntFeature(self.__dev_handle, GxFeatureID.INT_COMMAND_RETRY_COUNT)
        self.data_stream.append(GEVDataStream(self.__dev_handle))


class U3VDevice(Device):
    """
    The U3VDevice class inherits from the Device class. In addition to inheriting the properties of the Device,
    the U3V Device has special attributes such as bandwidth limitation, URBSetting, frame info, etc.
    """
    def __init__(self, handle):
        self.__dev_handle = handle
        Device.__init__(self, self.__dev_handle)
        self.data_stream.append(U3VDataStream(self.__dev_handle))


class U2Device(Device):
    """
    The U2Device class inherits from the Device class
    """
    def __init__(self, handle):
        self.__dev_handle = handle
        Device.__init__(self, self.__dev_handle)
        self.AcquisitionSpeedLevel = IntFeature(self.__dev_handle, GxFeatureID.INT_ACQUISITION_SPEED_LEVEL)
        self.AcquisitionFrameCount = IntFeature(self.__dev_handle, GxFeatureID.INT_ACQUISITION_FRAME_COUNT)
        self.TriggerSwitch = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_TRIGGER_SWITCH)
        self.UserOutputMode = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_USER_OUTPUT_MODE)
        self.StrobeSwitch = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_STROBE_SWITCH)
        self.ADCLevel = IntFeature(self.__dev_handle, GxFeatureID.INT_ADC_LEVEL)
        self.Hblanking = IntFeature(self.__dev_handle, GxFeatureID.INT_H_BLANKING)
        self.Vblanking = IntFeature(self.__dev_handle, GxFeatureID.INT_V_BLANKING)
        self.UserPassword = StringFeature(self.__dev_handle, GxFeatureID.STRING_USER_PASSWORD)
        self.VerifyPassword = StringFeature(self.__dev_handle, GxFeatureID.STRING_VERIFY_PASSWORD)
        self.UserData = BufferFeature(self.__dev_handle, GxFeatureID.BUFFER_USER_DATA)
        self.AALightEnvironment = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_AA_LIGHT_ENVIRONMENT)
        self.FrameInformation = BufferFeature(self.__dev_handle, GxFeatureID.BUFFER_FRAME_INFORMATION)
        self.ImageGrayRaiseSwitch = EnumFeature(self.__dev_handle, GxFeatureID.ENUM_IMAGE_GRAY_RAISE_SWITCH)
        self.data_stream.append(DataStream(self.__dev_handle))


class DataStream:
    def __init__(self, handle):
        self.__dev_handle = handle
        self.StreamAnnouncedBufferCount = IntFeature(self.__dev_handle, GxFeatureID.INT_ANNOUNCED_BUFFER_COUNT)
        self.StreamDeliveredFrameCount = IntFeature(self.__dev_handle, GxFeatureID.INT_DELIVERED_FRAME_COUNT)
        self.StreamLostFrameCount = IntFeature(self.__dev_handle, GxFeatureID.INT_LOST_FRAME_COUNT)
        self.StreamIncompleteFrameCount = IntFeature(self.__dev_handle, GxFeatureID.INT_INCOMPLETE_FRAME_COUNT)
        self.StreamDeliveredPacketCount = IntFeature(self.__dev_handle, GxFeatureID.INT_DELIVERED_PACKET_COUNT)
        self.payload_size = 0
        self.acquisition_flag = False

    def set_payload_size(self, payload_size):
        self.payload_size = payload_size

    def set_acquisition_buffer_number(self, buf_num):
        """
        :brief      set the number of acquisition buffer
        :param      buf_num:   the number of acquisition buffer, range:[1, 0xFFFFFFFF]
        """
        if not isinstance(buf_num, INT_TYPE):
            raise ParameterTypeError("DataStream.set_acquisition_buffer_number: "
                                     "Expected buf_num type is int, not %s" % type(buf_num))

        if (buf_num < 1) or (buf_num > UNSIGNED_LONG_LONG_MAX):
            print("DataStream.set_acquisition_buffer_number:"
                  "buf_num out of bounds, minimum=1, maximum=%s"
                  % hex(UNSIGNED_LONG_LONG_MAX).__str__())
            return

        status = gx_set_acquisition_buffer_number(self.__dev_handle, buf_num)
        StatusProcessor.process(status, 'DataStream', 'set_acquisition_buffer_number')

    def get_image(self, timeout=1000):
        """
        :brief          Get an image, get successfully create image class object
        :param          timeout:    Acquisition timeout, range:[0, 0xFFFFFFFF]
        :return:        image object
        """
        if not isinstance(timeout, INT_TYPE):
            raise ParameterTypeError("DataStream.get_image: "
                                     "Expected timeout type is int, not %s" % type(timeout))

        if (timeout < 0) or (timeout > UNSIGNED_INT_MAX):
            print("DataStream.get_image: "
                  "timeout out of bounds, minimum=0, maximum=%s"
                  % hex(UNSIGNED_INT_MAX).__str__())
            return None

        if self.acquisition_flag is False:
            print("DataStream.get_image: Current data steam don't  start acquisition")
            return None

        frame_data = GxFrameData()
        frame_data.image_size = self.payload_size
        frame_data.image_buf = None
        image = RawImage(frame_data)

        status = gx_get_image(self.__dev_handle, image.frame_data, timeout)
        if status == GxStatusList.SUCCESS:
            return image
        elif status == GxStatusList.TIMEOUT:
            return None
        else:
            StatusProcessor.process(status, 'DataStream', 'get_image')
            return None

    def flush_queue(self):
        status = gx_flush_queue(self.__dev_handle)
        StatusProcessor.process(status, 'DataStream', 'flush_queue')


class U3VDataStream(DataStream):
    def __init__(self, handle):
        self.__handle = handle
        DataStream.__init__(self, self.__handle)
        self.StreamTransferSize = IntFeature(self.__handle, GxFeatureID.INT_STREAM_TRANSFER_SIZE)
        self.StreamTransferNumberUrb = IntFeature(self.__handle, GxFeatureID.INT_STREAM_TRANSFER_NUMBER_URB)


class GEVDataStream(DataStream):
    def __init__(self, handle):
        self.__handle = handle
        DataStream.__init__(self, self.__handle)
        self.StreamResendPacketCount = IntFeature(self.__handle, GxFeatureID.INT_RESEND_PACKET_COUNT)
        self.StreamRescuedPacketCount = IntFeature(self.__handle, GxFeatureID.INT_RESCUED_PACKED_COUNT)
        self.StreamResendCommandCount = IntFeature(self.__handle, GxFeatureID.INT_RESEND_COMMAND_COUNT)
        self.StreamUnexpectedPacketCount = IntFeature(self.__handle, GxFeatureID.INT_UNEXPECTED_PACKED_COUNT)
        self.MaxPacketCountInOneBlock = IntFeature(self.__handle, GxFeatureID.INT_MAX_PACKET_COUNT_IN_ONE_BLOCK)
        self.MaxPacketCountInOneCommand = IntFeature(self.__handle, GxFeatureID.INT_MAX_PACKET_COUNT_IN_ONE_COMMAND)
        self.ResendTimeout = IntFeature(self.__handle, GxFeatureID.INT_RESEND_TIMEOUT)
        self.MaxWaitPacketCount = IntFeature(self.__handle, GxFeatureID.INT_MAX_WAIT_PACKET_COUNT)
        self.ResendMode = EnumFeature(self.__handle, GxFeatureID.ENUM_RESEND_MODE)
        self.StreamMissingBlockIDCount = IntFeature(self.__handle, GxFeatureID.INT_MISSING_BLOCK_ID_COUNT)
        self.BlockTimeout = IntFeature(self.__handle, GxFeatureID.INT_BLOCK_TIMEOUT)
        self.MaxNumQueueBuffer = IntFeature(self.__handle, GxFeatureID.INT_MAX_NUM_QUEUE_BUFFER)
        self.PacketTimeout = IntFeature(self.__handle, GxFeatureID.INT_PACKET_TIMEOUT)


class UnexpectedError(Exception):
    """
    brief:  Unexpected error exception
    param:  args            exception description
    return: none
    """
    def __init__(self, args):
        Exception.__init__(self, args)


class NotFoundTL(Exception):
    """
    brief:  not found TL exception
    param:  args             exception description
    return: none
    """
    def __init__(self, args):
        Exception.__init__(self, args)


class NotFoundDevice(Exception):
    """
    brief:  not found device exception
    param:  args              exception description
    return: none
    """
    def __init__(self, args):
        Exception.__init__(self, args)


class OffLine(Exception):
    """
    brief:  device offline exception
    param:  args            exception description
    return: none
    """
    def __init__(self, args):
        Exception.__init__(self, args)


class InvalidParameter(Exception):
    """
    brief:  input invalid parameter exception
    param:  args            exception description
    return: none
    """
    def __init__(self, args):
        Exception.__init__(self, args)


class InvalidHandle(Exception):
    """
    brief:  invalid handle exception
    param:  args            exception description
    return: none
    """
    def __init__(self, args):
        Exception.__init__(self, args)


class InvalidCall(Exception):
    """
    brief:  invalid callback exception
    param:  args            exception description
    return: none
    """
    def __init__(self, args):
        Exception.__init__(self, args)


class InvalidAccess(Exception):
    """
    brief:  invalid access exception
    param:  args            exception description
    return: none
    """
    def __init__(self, args):
        Exception.__init__(self, args)


class NeedMoreBuffer(Exception):
    """
    brief:  need more buffer exception
    param:  args            exception description
    return: none
    """
    def __init__(self, args):
        Exception.__init__(self, args)


class FeatureTypeError(Exception):
    """
    brief:  feature id error exception
    param:  args            exception description
    return: none
    """
    def __init__(self, args):
        Exception.__init__(self, args)


class OutOfRange(Exception):
    """
    brief:  param out of range exception
    param:  args            exception description
    return: none
    """
    def __init__(self, args):
        Exception.__init__(self, args)


class NotInitApi(Exception):
    """
    brief:  not init api exception
    param:  args            exception description
    return: none
    """
    def __init__(self, args):
        Exception.__init__(self, args)


class Timeout(Exception):
    """
    brief:  timeout exception
    param:  args            exception description
    return: none
    """
    def __init__(self, args):
        Exception.__init__(self, args)


class ParameterTypeError(Exception):
    """
    brief:  parameter type error exception
    param:  args            exception description
    return: none
    """
    def __init__(self, args):
        Exception.__init__(self, args)


def exception_deal(status, args):
    """
    brief:  deal with different exception
    param:  status         function return value
    param:  args            exception description
    return: none
    """
    if status == GxStatusList.ERROR:
        raise UnexpectedError(args)
    elif status == GxStatusList.NOT_FOUND_TL:
        raise NotFoundTL(args)
    elif status == GxStatusList.NOT_FOUND_DEVICE:
        raise NotFoundDevice(args)
    elif status == GxStatusList.OFFLINE:
        raise OffLine(args)
    elif status == GxStatusList.INVALID_PARAMETER:
        raise InvalidParameter(args)
    elif status == GxStatusList.INVALID_HANDLE:
        raise InvalidHandle(args)
    elif status == GxStatusList.INVALID_CALL:
        raise InvalidCall(args)
    elif status == GxStatusList.INVALID_ACCESS:
        raise InvalidAccess(args)
    elif status == GxStatusList.NEED_MORE_BUFFER:
        raise NeedMoreBuffer(args)
    elif status == GxStatusList.ERROR_TYPE:
        raise FeatureTypeError(args)
    elif status == GxStatusList.OUT_OF_RANGE:
        raise OutOfRange(args)
    elif status == GxStatusList.NOT_INIT_API:
        raise NotInitApi(args)
    elif status == GxStatusList.TIMEOUT:
        raise Timeout(args)
    elif status == GxStatusList.REPEAT_OPENED:
        raise InvalidAccess(args)
    else:
        raise Exception(args)


class StatusProcessor:
    def __init__(self):
        pass

    @staticmethod
    def process(status, class_name, function_name):
        """
        :brief      1.Error code processing
                    2.combine the class name and function name of the transmitted function into a string
                    3.Throw an exception
        :param      status:   function return value
        :param      class_name:  class name
        :param      function_name: function name
        :return:    none
        """
        if status != GxStatusList.SUCCESS:
            ret, err_code, string = gx_get_last_error(ERROR_SIZE)
            error_message = "%s.%s:%s" % (class_name, function_name, string)
            exception_deal(status, error_message)

    @staticmethod
    def printing(status, class_name, function_name):
        """
        :brief      1.Error code processing
                    2.combine the class name and function name of the transmitted function into a string and print it out
        :param      status:   function return value
        :param      class_name:  class name
        :param      function_name: function name
        :return:    none
        """
        if status != GxStatusList.SUCCESS:
            ret, err_code, string = gx_get_last_error(ERROR_SIZE)
            error_message = "%s.%s:%s" % (class_name, function_name, string)
            print(error_message)


class RGBImage:
    def __init__(self, frame_data):
        self.frame_data = frame_data

        if self.frame_data.image_buf is not None:
            self.__image_array = string_at(self.frame_data.image_buf, self.frame_data.image_size)
        else:
            self.__image_array = (c_ubyte * self.frame_data.image_size)()
            self.frame_data.image_buf = addressof(self.__image_array)

    def image_improvement(self, color_correction_param=0, contrast_lut=None, gamma_lut=None):
        """
        :brief:     Improve image quality of the object itself
        :param      color_correction_param:     color correction param address
                                                (get from Device.ColorCorrectionParam.get_int())
        :param      contrast_lut:               contrast lut
        :param      gamma_lut:                  gamma lut
        :return:    None
        """
        if (color_correction_param == 0) and (contrast_lut is None) and (gamma_lut is None):
            return

        if contrast_lut is None:
            contrast_parameter = None
        elif isinstance(contrast_lut, Buffer):
            contrast_parameter = contrast_lut.get_ctype_array()
        else:
            raise ParameterTypeError("RGBImage.image_improvement: "
                                     "Expected contrast_lut type is Buffer, not %s" % type(contrast_lut))

        if gamma_lut is None:
            gamma_parameter = None
        elif isinstance(gamma_lut, Buffer):
            gamma_parameter = gamma_lut.get_ctype_array()
        else:
            raise ParameterTypeError("RGBImage.image_improvement: "
                                     "Expected gamma_lut type is Buffer, not %s" % type(gamma_lut))

        if not isinstance(color_correction_param, INT_TYPE):
            raise ParameterTypeError("RGBImage.image_improvement: "
                                     "Expected color_correction_param type is int, not %s" % type(color_correction_param))

        status = dx_image_improvement(self.frame_data.image_buf, self.frame_data.image_buf,
                                      self.frame_data.width, self.frame_data.height,
                                      color_correction_param, contrast_parameter, gamma_parameter)

        if status != DxStatus.OK:
            raise UnexpectedError("RGBImage.image_improvement: failed, error code:%s" % hex(status).__str__())

    def get_numpy_array(self):
        """
        :brief:     Return data as a numpy.Array type with dimension Image.height * Image.width * 3
        :return:    numpy.Array objects
        """
        image_np = numpy.frombuffer(self.__image_array, dtype=numpy.ubyte).reshape(self.frame_data.height, self.frame_data.width, 3)
        return image_np

    def get_image_size(self):
        """
        :brief      Get RGB data size
        :return:    size
        """
        return self.frame_data.image_size


class RawImage:
    def __init__(self, frame_data):
        self.frame_data = frame_data

        if self.frame_data.image_buf is not None:
            self.__image_array = string_at(self.frame_data.image_buf, self.frame_data.image_size)
        else:
            self.__image_array = (c_ubyte * self.frame_data.image_size)()
            self.frame_data.image_buf = addressof(self.__image_array)

    def __get_bit_depth(self, pixel_format):
        """
        :brief      Calculate pixel depth based on pixel format
        :param      pixel_format
        :return:    pixel depth
        """
        bpp10_tup = (GxPixelFormatEntry.MONO10, GxPixelFormatEntry.BAYER_GR10, GxPixelFormatEntry.BAYER_RG10,
                     GxPixelFormatEntry.BAYER_GB10, GxPixelFormatEntry.BAYER_BG10)

        bpp12_tup = (GxPixelFormatEntry.MONO12, GxPixelFormatEntry.BAYER_GR12, GxPixelFormatEntry.BAYER_RG12,
                     GxPixelFormatEntry.BAYER_GB12, GxPixelFormatEntry.BAYER_BG12)

        bpp16_tup = (GxPixelFormatEntry.MONO16, GxPixelFormatEntry.BAYER_GR16, GxPixelFormatEntry.BAYER_RG16,
                     GxPixelFormatEntry.BAYER_GB16, GxPixelFormatEntry.BAYER_BG16)

        if (pixel_format & PIXEL_BIT_MASK) == GX_PIXEL_8BIT:
            return GxPixelSizeEntry.BPP8
        elif pixel_format in bpp10_tup:
            return GxPixelSizeEntry.BPP10
        elif pixel_format in bpp12_tup:
            return GxPixelSizeEntry.BPP12
        elif pixel_format == GxPixelFormatEntry.MONO14:
            return GxPixelSizeEntry.BPP14
        elif pixel_format in bpp16_tup:
            return GxPixelSizeEntry.BPP16
        elif (pixel_format & PIXEL_BIT_MASK) == GX_PIXEL_24BIT:
            return GxPixelSizeEntry.BPP24
        elif (pixel_format & PIXEL_BIT_MASK) == GX_PIXEL_48BIT:
            return GxPixelSizeEntry.BPP48
        else:
            return -1

    def __get_pixel_color_filter(self, pixel_format):
        """
        :brief      Calculate pixel color filter based on pixel format
        :param      pixel_format
        :return:    pixel color filter
        """
        gr_tup = (GxPixelFormatEntry.BAYER_GR8, GxPixelFormatEntry.BAYER_GR10,
                  GxPixelFormatEntry.BAYER_GR12, GxPixelFormatEntry.BAYER_GR16)
        rg_tup = (GxPixelFormatEntry.BAYER_RG8, GxPixelFormatEntry.BAYER_RG10,
                  GxPixelFormatEntry.BAYER_RG12, GxPixelFormatEntry.BAYER_RG16)
        gb_tup = (GxPixelFormatEntry.BAYER_GB8, GxPixelFormatEntry.BAYER_GB10,
                  GxPixelFormatEntry.BAYER_GB12, GxPixelFormatEntry.BAYER_GB16)
        bg_tup = (GxPixelFormatEntry.BAYER_BG8, GxPixelFormatEntry.BAYER_BG10,
                  GxPixelFormatEntry.BAYER_BG12, GxPixelFormatEntry.BAYER_BG16)
        mono_tup = (GxPixelFormatEntry.MONO8, GxPixelFormatEntry.MONO8_SIGNED,
                    GxPixelFormatEntry.MONO10, GxPixelFormatEntry.MONO12,
                    GxPixelFormatEntry.MONO14, GxPixelFormatEntry.MONO16)

        if pixel_format in gr_tup:
            return DxPixelColorFilter.GR
        elif pixel_format in rg_tup:
            return DxPixelColorFilter.RG
        elif pixel_format in gb_tup:
            return DxPixelColorFilter.GB
        elif pixel_format in bg_tup:
            return DxPixelColorFilter.BG
        elif pixel_format in mono_tup:
            return DxPixelColorFilter.NONE
        else:
            return -1

    def __pixel_format_raw16_to_raw8(self, pixel_format):
        """
        :brief      convert raw16 to raw8, the pixel format need convert to 8bit bayer format
        :param      pixel_format(10bit, 12bit, 16bit)
        :return:    pixel_format(8bit)
        """
        gr16_tup = (GxPixelFormatEntry.BAYER_GR10, GxPixelFormatEntry.BAYER_GR12, GxPixelFormatEntry.BAYER_GR16)
        rg16_tup = (GxPixelFormatEntry.BAYER_RG10, GxPixelFormatEntry.BAYER_RG12, GxPixelFormatEntry.BAYER_RG16)
        gb16_tup = (GxPixelFormatEntry.BAYER_GB10, GxPixelFormatEntry.BAYER_GB12, GxPixelFormatEntry.BAYER_GB16)
        bg16_tup = (GxPixelFormatEntry.BAYER_BG10, GxPixelFormatEntry.BAYER_BG12, GxPixelFormatEntry.BAYER_BG16)
        mono16_tup = (GxPixelFormatEntry.MONO10, GxPixelFormatEntry.MONO12,
                      GxPixelFormatEntry.MONO14, GxPixelFormatEntry.MONO16)

        if pixel_format in gr16_tup:
            return GxPixelFormatEntry.BAYER_GR8
        elif pixel_format in rg16_tup:
            return GxPixelFormatEntry.BAYER_RG8
        elif pixel_format in gb16_tup:
            return GxPixelFormatEntry.BAYER_GB8
        elif pixel_format in bg16_tup:
            return GxPixelFormatEntry.BAYER_BG8
        elif pixel_format in mono16_tup:
            return GxPixelFormatEntry.MONO8
        else:
            return -1

    def __raw16_to_raw8(self, pixel_bit_depth, valid_bits):
        """
        :brief      convert raw16 to raw8
        :param      pixel_bit_depth     pixel bit depth
        :param      valid_bits:         data valid digit[DxValidBit]
        :return:    RAWImage object
        """
        if pixel_bit_depth == GxPixelSizeEntry.BPP10:
            valid_bits = min(valid_bits, DxValidBit.BIT2_9)
        elif pixel_bit_depth == GxPixelSizeEntry.BPP12:
            valid_bits = min(valid_bits, DxValidBit.BIT4_11)
        else:
            print("RawImage.__dx_raw16_to_raw8: Only support 10bit and 12bit")
            return None

        frame_data = GxFrameData()
        frame_data.status = self.frame_data.status
        frame_data.width = self.frame_data.width
        frame_data.height = self.frame_data.height
        frame_data.pixel_format = self.__pixel_format_raw16_to_raw8(self.frame_data.pixel_format)
        frame_data.image_size = self.frame_data.width * self.frame_data.height
        frame_data.frame_id = self.frame_data.frame_id
        frame_data.timestamp = self.frame_data.timestamp
        # frame_data.buf_id = self.frame_data.buf_id
        frame_data.image_buf = None
        image_raw8 = RawImage(frame_data)

        status = dx_raw16_to_raw8(self.frame_data.image_buf, image_raw8.frame_data.image_buf,
                                  self.frame_data.width, self.frame_data.height, valid_bits)

        if status != DxStatus.OK:
            raise UnexpectedError("RawImage.convert: raw16 convert to raw8 failed, Error core: %s"
                                  % hex(status).__str__())
        else:
            return image_raw8

    def __raw8_to_rgb(self, raw8_image, convert_type, pixel_color_filter, flip):
        """
        :brief      convert raw8 to RGB
        :param      raw8_image          RAWImage object, bit depth is 8bit
        :param      convert_type:       Bayer convert type, See detail in DxBayerConvertType
        :param      pixel_color_filter: pixel color filter, See detail in DxPixelColorFilter
        :param      flip:               Output image flip flag
                                        True: turn the image upside down
                                        False: do not flip
        :return:    RAWImage object
        """
        frame_data = GxFrameData()
        frame_data.status = raw8_image.frame_data.status
        frame_data.width = raw8_image.frame_data.width
        frame_data.height = raw8_image.frame_data.height
        frame_data.pixel_format = GxPixelFormatEntry.RGB8_PLANAR
        frame_data.image_size = raw8_image.frame_data.width * raw8_image.frame_data.height * 3
        frame_data.frame_id = raw8_image.frame_data.frame_id
        frame_data.timestamp = raw8_image.frame_data.timestamp
        # frame_data.buf_id = self.frame_data.buf_id
        frame_data.image_buf = None
        image_rgb = RGBImage(frame_data)

        status = dx_raw8_to_rgb24(raw8_image.frame_data.image_buf, image_rgb.frame_data.image_buf,
                                  raw8_image.frame_data.width, raw8_image.frame_data.height,
                                  convert_type, pixel_color_filter, flip)

        if status != DxStatus.OK:
            raise UnexpectedError("RawImage.convert: failed, error code:%s" % hex(status).__str__())

        return image_rgb

    def convert(self, mode, flip=False, valid_bits=DxValidBit.BIT4_11,
                convert_type=DxBayerConvertType.NEIGHBOUR):
        """
        :brief      Image format convert
        :param      mode:           "RAW8":     convert raw16 RAWImage object to raw8 RAWImage object
                                    "RGB":   convert raw8 RAWImage object to RGBImage object
        :param      flip:           Output image flip flag
                                    True: turn the image upside down
                                    False: do not flip
        :param      valid_bits:     Data valid digit, See detail in DxValidBit, raw8 don't this param
        :param      convert_type:   Bayer convert type, See detail in DxBayerConvertType
        :return:    return image object according to mode parameter
        """
        if self.frame_data.status != GxFrameStatusList.SUCCESS:
            print("RawImage.convert: This is a incomplete image")
            return None

        if not isinstance(flip, bool):
            raise ParameterTypeError("RawImage.convert: "
                                     "Expected flip type is bool, not %s" % type(flip))

        if not isinstance(convert_type, INT_TYPE):
            raise ParameterTypeError("RawImage.convert: "
                                     "Expected convert_type type is int, not %s" % type(convert_type))

        if not isinstance(valid_bits, INT_TYPE):
            raise ParameterTypeError("RawImage.convert: "
                                     "Expected valid_bits type is int, not %s" % type(valid_bits))

        if not isinstance(mode, str):
            raise ParameterTypeError("RawImage.convert: "
                                     "Expected mode type is str, not %s" % type(mode))

        convert_type_dict = dict((name, getattr(DxBayerConvertType, name))
                                 for name in dir(DxBayerConvertType) if not name.startswith('__'))
        if convert_type not in convert_type_dict.values():
            print("RawImage.convert: convert_type out of bounds, %s" % convert_type_dict.__str__())
            return None

        valid_bits_dict = dict((name, getattr(DxValidBit, name))
                               for name in dir(DxValidBit) if not name.startswith('__'))
        if valid_bits not in valid_bits_dict.values():
            print("RawImage.convert: valid_bits out of bounds, %s" % valid_bits_dict.__str__())
            return None

        pixel_bit_depth = self.__get_bit_depth(self.frame_data.pixel_format)
        pixel_color_filter = self.__get_pixel_color_filter(self.frame_data.pixel_format)

        if pixel_bit_depth < GxPixelSizeEntry.BPP8 or \
           pixel_bit_depth > GxPixelSizeEntry.BPP12:
            print("RawImage.convert: This pixel format is not support")
            return None

        if mode == "RAW8":
            if flip is True:
                print('''RawImage.convert: mode="RAW8" don't support flip=True''')
                return None

            if pixel_bit_depth in (GxPixelSizeEntry.BPP10, GxPixelSizeEntry.BPP12):
                image_raw8 = self.__raw16_to_raw8(pixel_bit_depth, valid_bits)
                return image_raw8
            else:
                print('RawImage.convert: mode="RAW8" only support 10bit and 12bit')
        elif mode == "RGB":
            if pixel_bit_depth in (GxPixelSizeEntry.BPP10, GxPixelSizeEntry.BPP12):
                image_raw8 = self.__raw16_to_raw8(pixel_bit_depth, valid_bits)
            else:
                image_raw8 = self

            return self.__raw8_to_rgb(image_raw8, convert_type, pixel_color_filter, flip)
        else:
            print('''RawImage.convert: mode="%s", isn't support''' % mode)
            return None

    def get_numpy_array(self):
        """
        :brief      Return data as a numpy.Array type with dimension Image.height * Image.width
        :return:    numpy.Array objects
        """
        if self.frame_data.status != GxFrameStatusList.SUCCESS:
            print("RawImage.get_numpy_array: This is a incomplete image")
            return None

        image_size = self.frame_data.width * self.frame_data.height

        if self.frame_data.pixel_format & PIXEL_BIT_MASK == GX_PIXEL_8BIT:
            image_np = numpy.frombuffer(self.__image_array, dtype=numpy.ubyte, count=image_size).\
                reshape(self.frame_data.height, self.frame_data.width)
        elif self.frame_data.pixel_format & PIXEL_BIT_MASK == GX_PIXEL_16BIT:
            image_np = numpy.frombuffer(self.__image_array, dtype=numpy.uint16, count=image_size).\
                reshape(self.frame_data.height, self.frame_data.width)
        else:
            image_np = None

        return image_np

    def get_data(self):
        """
        :brief      get Raw data
        :return:    raw data[string]
        """
        image_str = string_at(self.__image_array, self.frame_data.image_size)
        return image_str

    def save_raw(self, file_path):
        """
        :brief      save raw data
        :param      file_path:      file path
        :return:    None
        """
        if not isinstance(file_path, str):
            raise ParameterTypeError("RawImage.save_raw: "
                                     "Expected file_path type is str, not %s" % type(file_path))

        try:
            fp = open(file_path, "wb")
            fp.write(self.__image_array)
            fp.close()
        except Exception as error:
            raise UnexpectedError("RawImage.save_raw:%s" % error)

    def get_status(self):
        """
        :brief      get raw data status
        :return:    status
        """
        return self.frame_data.status

    def get_width(self):
        """
        :brief      get width of raw data
        :return:    width
        """
        return self.frame_data.width

    def get_height(self):
        """
        :brief     get height of raw data
        :return:
        """
        return self.frame_data.height

    def get_pixel_format(self):
        """
        :brief      Get image pixel format
        :return:    pixel format
        """
        return self.frame_data.pixel_format

    def get_image_size(self):
        """
        :brief      Get raw data size
        :return:    size
        """
        return self.frame_data.image_size

    def get_frame_id(self):
        """
        :brief      Get  frame id of raw data
        :return:    frame id
        """
        return self.frame_data.frame_id

    def get_timestamp(self):
        """
        :brief      Get timestamp of raw data
        :return:    timestamp
        """
        return self.frame_data.timestamp



class Utility:
    def __init__(self):
        pass

    @staticmethod
    def get_gamma_lut(gamma=1):
        if not (isinstance(gamma, (INT_TYPE, float))):
            raise ParameterTypeError("Utility.get_gamma_lut: "
                                     "Expected gamma type is float, not %s" % type(gamma))

        if (gamma < GAMMA_MIN) or (gamma > GAMMA_MAX):
            print("Utility.get_gamma_lut: gamma out of bounds, range:[0.1, 10.0]")
            return None

        status, gamma_lut, gamma_lut_len = dx_get_gamma_lut(gamma)
        if status != DxStatus.OK:
            print("Utility.get_gamma_lut: get gamma lut failure, Error code:%s" % hex(status).__str__())
            return None

        return Buffer(gamma_lut)

    @staticmethod
    def get_contrast_lut(contrast=0):
        if not (isinstance(contrast, INT_TYPE)):
            raise ParameterTypeError("Utility.get_contrast_lut: "
                                     "Expected contrast type is int, not %s" % type(contrast))

        if (contrast < CONTRAST_MIN) or (contrast > CONTRAST_MAX):
            print("Utility.get_contrast_lut: contrast out of bounds, range:[-50, 100]")
            return None

        status, contrast_lut, contrast_lut_len = dx_get_contrast_lut(contrast)
        if status != DxStatus.OK:
            print("Utility.get_contrast_lut: get contrast lut failure, Error code:%s" % hex(status).__str__())
            return None

        return Buffer(contrast_lut)



