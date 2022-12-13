# Load DLL library
from ctypes import *
import time
import os
import sys
import platform
import tempfile
import re
import collections
import struct
import ctypes
## Load XIMC DLL library

if sys.version_info >= (3, 0):
    import urllib.parse

# Dependences

# For correct usage of the library libximc,
# you need to add the file pyximc.py wrapper with the structures of the library to python path.
cur_dir = os.path.abspath(os.path.dirname(__file__))  # Specifies the current directory.
XIMC_DIR = os.path.join(cur_dir,"ximc")  # Formation of the directory name with all dependencies. The dependencies for the examples are located in the ximc directory.
ximc_package_dir = os.path.join(XIMC_DIR, "crossplatform", "wrappers",
                                "python")  # Formation of the directory name with python dependencies.
sys.path.append(ximc_package_dir)  # add pyximc.py wrapper to python path
print(f"XIMC Library at: {ximc_package_dir}")
# Depending on your version of Windows, add the path to the required DLLs to the environment variable
# bindy.dll
# libximc.dll
# xiwrapper.dll
if platform.system() == "Windows":
    # Determining the directory with dependencies for windows depending on the bit depth.
    arch_dir = "win64" if "64" in platform.architecture()[0] else "win32"  #
    libdir = os.path.join(XIMC_DIR, arch_dir)
    if sys.version_info >= (3, 8):
        os.add_dll_directory(libdir)
    else:
        os.environ["Path"] = libdir + ";" + os.environ["Path"]  # add dll path into an environment variable
elif sys.platform == 'linux2' or sys.platform == 'linux':
    # For correct usage of the library libximc,
    # you need to add the file pyximc.py wrapper with the structures of the library to python path.
    # Formation of the directory name with all dependencies. The dependencies for the examples are located in the ximc directory.
    XIMC_DIR = "/home/mstingl/Documents/locai-hw/Standa/ximc-2.13.5/ximc"  # Formation of the directory name with all dependencies. The dependencies for the examples are located in the ximc directory.
    ximc_package_dir = os.path.join(XIMC_DIR, "crossplatform", "wrappers",
                                    "python")  # Formation of the directory name with python dependencies.
    sys.path.append(ximc_package_dir)  # add pyximc.py wrapper to python path
    print(f"XIMC Library at: {ximc_package_dir}")
    arch_dir = "debian-amd64"  #
    libdir = os.path.join(XIMC_DIR, arch_dir)
    sys.path.append(libdir)  # add pyximc.py wrapper to python path
    # os.environ["Path"] = libdir + ";" + os.environ["Path"]  # add dll path into an environment variable
    # os.add_dll_directory(libdir)

try:
    from pyximc import *
except ImportError as err:
    print(
        "Can't import pyximc module. The most probable reason is that you changed the relative location of the test_Python.py and pyximc.py files. See developers' documentation for details.")
    exit()
except OSError as err:
    # print(err.errno, err.filename, err.strerror, err.winerror) # Allows you to display detailed information by mistake.
    if platform.system() == "Windows":
        if err.winerror == 193:  # The bit depth of one of the libraries bindy.dll, libximc.dll, xiwrapper.dll does not correspond to the operating system bit.
            print(
                "Err: The bit depth of one of the libraries bindy.dll, libximc.dll, xiwrapper.dll does not correspond to the operating system bit.")
            # print(err)
        elif err.winerror == 126:  # One of the library bindy.dll, libximc.dll, xiwrapper.dll files is missing.
            print("Err: One of the library bindy.dll, libximc.dll, xiwrapper.dll is missing.")
            print(
                "It is also possible that one of the system libraries is missing. This problem is solved by installing the vcredist package from the ximc\\winXX folder.")
            # print(err)
        else:  # Other errors the value of which can be viewed in the code.
            print(err)
        print(
            "Warning: If you are using the example as the basis for your module, make sure that the dependencies installed in the dependencies section of the example match your directory structure.")
        print("For correct work with the library you need: pyximc.py, bindy.dll, libximc.dll, xiwrapper.dll")
    else:
        print(err)
        print(
            "Can't load libximc library. Please add all shared libraries to the appropriate places. It is decribed in detail in developers' documentation. On Linux make sure you installed libximc-dev package.\nmake sure that the architecture of the system and the interpreter is the same")
    exit()

# variable 'lib' points to the loaded library
# note that ximc uses stdcall on win
print("Library loaded")

MICROSTEP_MODE = [0,
                  MicrostepMode.MICROSTEP_MODE_FULL,
                  MicrostepMode.MICROSTEP_MODE_FRAC_2,
                  MicrostepMode.MICROSTEP_MODE_FRAC_4,
                  MicrostepMode.MICROSTEP_MODE_FRAC_8,
                  MicrostepMode.MICROSTEP_MODE_FRAC_16,
                  MicrostepMode.MICROSTEP_MODE_FRAC_32,
                  MicrostepMode.MICROSTEP_MODE_FRAC_64,
                  MicrostepMode.MICROSTEP_MODE_FRAC_128,
                  MicrostepMode.MICROSTEP_MODE_FRAC_256]
MICROSTEP_MODE_STR = ["", "MICROSTEP_MODE_FULL", "MICROSTEP_MODE_FRAC_2", "MICROSTEP_MODE_FRAC_4",
                      "MICROSTEP_MODE_FRAC_8", "MICROSTEP_MODE_FRAC_16", "MICROSTEP_MODE_FRAC_32",
                    "MICROSTEP_MODE_FRAC_64", "MICROSTEP_MODE_FRAC_128", "MICROSTEP_MODE_FRAC_256"]

class XimcLibraryWrapper():
    def __init__(self, ximc_dir = XIMC_DIR, verbose = 0):
        self.ximc_dir = ximc_dir
        self.set_bindy_key()
        self.verbose = verbose
        self.opened_devices = self.open_available_devices()
        self.microstep_mode_str = MICROSTEP_MODE_STR

    def print_header(self, device_ind):
        if self.verbose:
            print(f'{self.opened_devices[device_ind]["positioner_name"]}/{self.opened_devices[device_ind]["friendly_name"]}', end=": ")

    @property
    def verbose(self):
        return self._verbose
    @verbose.setter
    def verbose(self, v):
        self._verbose = v

    @property
    def version(self):
        sbuf = create_string_buffer(64)
        lib.ximc_version(sbuf)
        ver = sbuf.raw.decode().rstrip("\0")
        if self.verbose:
            print("Library version: " + ver)
        return ver

    def set_bindy_key(self):
        # Set bindy (network) keyfile. Must be called before any call to "enumerate_devices" or "open_device" if you
        # wish to use network-attached controllers. Accepts both absolute and relative paths, relative paths are resolved
        # relative to the process working directory. If you do not need network devices then "set_bindy_key" is optional.
        # In Python make sure to pass byte-array object to this function (b"string literal").
        result = lib.set_bindy_key(os.path.join(self.ximc_dir, "win32", "keyfile.sqlite").encode("utf-8"))
        if result != Result.Ok:
            lib.set_bindy_key("keyfile.sqlite".encode("utf-8"))  # Search for the key file in the current directory.

    def get_positioner_from_controller_name(self, ctrl_name: str):
        """
        :param ctrl_name: Friendly name assigned to the positioner {'b\'Axis n\'', with n=int}
        :return: Positioner name: names according to x-,y-,z-axis
                 Positioner index: orders devices (x,y,z)
        """
        if ctrl_name == 'b\'Axis 1\'':
            # TODO: str.decode() to avoid backlashes.
            return "X",0
        elif ctrl_name == 'b\'Axis 2\'':
            return "Y",1
        elif ctrl_name == 'b\'Axis 3\'':
            return "Z",2
        elif ctrl_name == 'b\'\'':
            print("Please name your positioner")
            raise ValueError
        else:
            print("Positioner's name not recognized")
            raise ValueError


    def get_user_calibration_from_controller_name(self, ctrl_name: str):
        """
               :param ctrl_name: Friendly name assigned to the positioner {'b\'Axis n\'', with n=int}
               :return: A: user units - calibration param A
                        ms: microstep mode
        """
        if ctrl_name == 'b\'Axis 1\'':
            # TODO: str.decode() to avoid backlashes.
            return 1/80, MicrostepMode.MICROSTEP_MODE_FRAC_256
        elif ctrl_name == 'b\'Axis 2\'':
            return 1/80, MicrostepMode.MICROSTEP_MODE_FRAC_256
        elif ctrl_name == 'b\'Axis 3\'':
            return 1/8000, MicrostepMode.MICROSTEP_MODE_FRAC_256
        elif ctrl_name == 'b\'\'':
            print("Please name your positioner")
            raise ValueError
        else:
            print("Positioner's name not recognized")
            raise ValueError

    def get_port_name_by_ind(self, device_ind):
        for device in self.opened_devices.values():
            if device["device_ind"] == device_ind:
                return device["port_name"]
        print(f"Device ind {device_ind} not found")
        raise ValueError

    def get_positioner_name_by_ind(self, device_ind):
        for device in self.opened_devices.values():
            if device["device_ind"] == device_ind:
                return device["positioner_name"]
        print(f"Device ind {device_ind} not found")
        raise ValueError

    def get_friendly_name_by_ind(self, device_ind):
        for device in self.opened_devices.values():
            if device["device_ind"] == device_ind:
                return device["friendly_name"]
        print(f"Device ind {device_ind} not found")
        raise ValueError

    def open_available_devices(self):
        # Returns dict with opened available stages.
        # This is device search and enumeration with probing. It gives more information about devices.
        probe_flags = EnumerateFlags.ENUMERATE_PROBE + EnumerateFlags.ENUMERATE_NETWORK
        enum_hints = b"addr="
        # enum_hints = b"addr=" # Use this hint string for broadcast enumerate
        devenum = lib.enumerate_devices(probe_flags, enum_hints)
        dev_count = lib.get_device_count(devenum)

        if self.verbose > 1:
            print("Device enum handle: " + repr(devenum))
            print("Device enum handle type: " + repr(type(devenum)))
            print("Device count: " + repr(dev_count))

        stages_dict = {}
        controller_name = controller_name_t()
        for dev_ind in range(dev_count):
            enum_name = lib.get_device_name(devenum, dev_ind)
            result = lib.get_enumerate_device_controller_name(devenum, dev_ind, byref(controller_name))
            if result == Result.Ok:
                if self.verbose > 1:
                    print("Enumerated device #{} name (port name): ".format(dev_ind) + repr(
                    enum_name) + ". Friendly name: " + repr(controller_name.ControllerName) + ".")

                dev_ind_enabled = self.open_device(enum_name)

                pos_name, pos_ind = self.get_positioner_from_controller_name(repr(controller_name.ControllerName))
                A, ms = self.get_user_calibration_from_controller_name(repr(controller_name.ControllerName))
                stages_dict[dev_ind_enabled] = {"port_name": enum_name, "device_ind": dev_ind_enabled,
                                                "friendly_name": repr(controller_name.ControllerName),
                                                "positioner_name": pos_name, "positioner_ind": pos_ind,
                                         "user_calibration": A, "microstep_mode": ms}
            else:
                print("Result: " + repr(result))
                print("Error when searching device")
                raise SystemError

        return stages_dict

    def cfg_from_devices(self):
        d = {}
        for dev in self.opened_devices.values():
            d[dev["positioner_name"]] = dev
        return d

    def open_device(self, port_name):
        device_ind = lib.open_device(port_name)
        if self.verbose:
            print("Opening device at " + repr(port_name))
            print("Device ind: " + repr(device_ind))
        return device_ind

    def close_device(self, device_ind):
        # port_name = self.get_port_name_by_ind(device_ind)
        # The device_t device parameter in this function is a C pointer, unlike most library functions that use this parameter
        result = lib.close_device(byref(cast(device_ind, POINTER(c_int))))
        if self.verbose > 1:
            # TODO: Check ind_to_port
            #  print(f"Closing device {device_ind} at port {repr(port_name)}")
            print(f"Closing device {device_ind} at port {repr(port_name)}")
        if result != Result.Ok:
            print("Result: " + repr(result))
            print("Error when closing device")
            raise SystemError

    def info(self, device_ind):
        x_device_information = device_information_t()
        result = lib.get_device_information(device_ind, byref(x_device_information))
        if result == Result.Ok:
            if self.verbose:
                self.print_header(device_ind)
                print("Device information:")
                print("  Manufacturer: " +
                      repr(string_at(x_device_information.Manufacturer).decode()))
                print("  ManufacturerId: " +
                      repr(string_at(x_device_information.ManufacturerId).decode()))
                print("  ProductDescription: " +
                      repr(string_at(x_device_information.ProductDescription).decode()))
                print("  Major: " + repr(x_device_information.Major))
                print("  Minor: " + repr(x_device_information.Minor))
                print("  Release: " + repr(x_device_information.Release))
            return {"Manufacturer": repr(string_at(x_device_information.Manufacturer).decode()),
                    "ManufacturerId": repr(string_at(x_device_information.ManufacturerId).decode()),
                    "ProductDescription": repr(string_at(x_device_information.ProductDescription).decode()),
                    "Major":repr(x_device_information.Major),
                    "Minor":repr(x_device_information.Minor),
                    "Release": repr(x_device_information.Release),
                    }
        else:
            print("Result: " + repr(result))
            print("Error when getting device info")
            raise ValueError

    def status(self, device_ind):
        x_status = status_t()
        result = lib.get_status(device_ind, byref(x_status))
        if result == Result.Ok:
            if self.verbose:
                self.print_header(device_ind)
                print("Status:")
                print("  Status.Ipwr: " + repr(x_status.Ipwr))
                print("  Status.Upwr: " + repr(x_status.Upwr))
                print("  Status.Iusb: " + repr(x_status.Iusb))
                print("  Status.Flags: " + repr(hex(x_status.Flags)))
            return {"Ipwr": repr(x_status.Ipwr),
                    "Upwr": repr(x_status.Upwr),
                    "Iusb": repr(x_status.Iusb),
                    "Flags": repr(x_status.Flags)}
        else:
            print("Result: " + repr(result))
            print("Error when getting device status")
            raise ValueError

    def get_position(self, device_ind, mode=1):
        """
        Obtaining information about the position of the positioner.

        This function allows you to get information about the current positioner coordinates,
        both in steps and in encoder counts, if it is set.
        Also, depending on the state of the mode parameter, information can be obtained in user units.

        :param device_ind: device ind.
        :param mode: mode in feedback counts or in user units. (Default value = 1)
        """
        if mode:
            x_pos = get_position_t()
            result = lib.get_position(device_ind, byref(x_pos))
            if result == Result.Ok:
                if self.verbose:
                    self.print_header(device_ind)
                    print(f"Position: {x_pos.Distance} steps, {x_pos.uPosition} microsteps")
            else:
                print("Result: " + repr(result))
                print("Error when getting device position")
                raise ValueError
            return x_pos.Distance, x_pos.uPosition
        else:
            user_unit = calibration_t()

            user_unit.A = self.opened_devices[device_ind]["user_calibration"]
            user_unit.MicrostepMode = self.opened_devices[device_ind]["microstep_mode"]

            x_pos = get_position_calb_t()
            result = lib.get_position_calb(device_ind, byref(x_pos), byref(user_unit))
            if result == Result.Ok:
                if self.verbose:
                    self.print_header(device_ind)
                    print(f"Position: {x_pos.Distance} mm")
            else:
                print("Result: " + repr(result))
                print("Error when getting device position")
                raise ValueError
            return x_pos.Distance

    def left(self, device_ind):
        """
        Move to the left.

        :param device_ind: device ind.
        """
        result = lib.command_left(device_ind)
        if result == Result.Ok:
            if self.verbose:
                self.print_header(device_ind)
                print("Moving left")
        else:
            print("Result: " + repr(result))
            print("Error when moving left")
            raise ValueError

    def right(self, device_ind):
        """
        Move to the right.

        :param device_ind: device ind.
        """
        result = lib.command_right(device_ind)
        if result == Result.Ok:
            if self.verbose:
                self.print_header(device_ind)
                print("Moving right")
        else:
            print("Result: " + repr(result))
            print("Error when moving left")
            raise ValueError

    def home(self, device_ind):
        result = lib.command_home(device_ind)
        if result == Result.Ok:
            if self.verbose:
                self.print_header(device_ind)
                print("Homing")
        else:
            print("Result: " + repr(result))
            print("Error when homing")
            raise ValueError

    def zero(self, device_ind):
        raise NotImplementedError

    def set_user_calibration(self, device_ind, A):
        user_unit = calibration_t()
        self.opened_devices[device_ind]["user_calibration"] = float(A)
        user_unit.A = float(A)
        user_unit.MicrostepMode = self.opened_devices[device_ind]["microstep_mode"]
        if self.verbose:
            self.print_header(device_ind)
            print(f"User units: A = {user_unit.A}. Microstep mode = {user_unit.MicrostepMode}.")
        return user_unit.A


    def get_user_calibration(self, device_ind):
        if self.verbose:
            self.print_header(device_ind)
            print(f"User units: A = {self.opened_devices[device_ind]['user_calibration']}.")
        return self.opened_devices[device_ind]['user_calibration']

    def move(self, device_ind, distance, udistance, mode=0):
        """
        Move to the specified coordinate.
        Depending on the mode parameter, you can set coordinates in steps or feedback counts, or in custom units.

        :param device_ind: device ind.
        :param distance: the position of the destination.
        :param udistance: destination position in micro steps if this mode is used.
        :param mode:  mode in feedback counts or in user units. (Default value = 1)
        """
        # TODO: Check why it is not saved on the positioner.
        if mode:
            result = lib.command_move(device_ind, distance, udistance)
            if result == Result.Ok:
                if self.verbose:
                    self.print_header(device_ind)
                    print(f"Going to {distance} steps, {udistance} microsteps")
            else:
                print("Result: " + repr(result))
                print("Error when moving")
                raise ValueError
        else:
            user_unit = calibration_t()

            user_unit.A = self.opened_devices[device_ind]["user_calibration"]
            user_unit.MicrostepMode = self.opened_devices[device_ind]["microstep_mode"]

            # udistance is not used for setting movement in custom units.
            result = lib.command_move_calb(device_ind, c_float(distance), byref(user_unit))
            if result == Result.Ok:
                if self.verbose:
                    self.print_header(device_ind)
                    print(f"Move to the position {distance} mm.")
            else:
                print("Result: " + repr(result))
                print("Error when moving (calb)")
                raise ValueError

    def shift(self, device_ind, distance, udistance, mode=0):
        """
        The shift by the specified offset coordinates.

        Depending on the mode parameter, you can set coordinates in steps or feedback counts, or in custom units.

        :param device_ind: device ind.
        :param distance: size of the offset in steps.
        :param udistance: Size of the offset in micro steps.
        :param mode:  (Default value = 1)
        """
        if mode:
            result = lib.command_movr(device_ind, distance, udistance)
            if result == Result.Ok:
                if self.verbose:
                    self.print_header(device_ind)
                    print(f"Shift on {distance} steps, {udistance} microsteps")
            else:
                print("Result: " + repr(result))
                print("Error when shifting")
                raise ValueError
        else:
            user_unit = calibration_t()
            user_unit.A = self.opened_devices[device_ind]["user_calibration"]
            user_unit.MicrostepMode = self.opened_devices[device_ind]["microstep_mode"]
            # udistance is not used for setting movement in custom units.
            result = lib.command_movr_calb(device_ind, c_float(distance), byref(user_unit))
            if result == Result.Ok:
                if self.verbose:
                    self.print_header(device_ind)
                    print(f"Shift on {distance} mm.")
            else:
                print("Result: " + repr(result))
                print("Error when shifting")
                raise ValueError

    def wait_for_stop(self, device_ind, interval=10):
        """
        Waiting for the movement to complete.

        :param device_ind: device ind.
        :param interval: step of the check time in milliseconds.
        """
        result = lib.command_wait_for_stop(device_ind, interval)
        if result == Result.Ok:
            return 0
        else:
            print("Result: " + repr(result))
            print("Error when waiting to stop")
            raise ValueError

    def serial(self, device_ind):
        """
        Reading the device's serial number.

        :param device_ind: device ind.
        """
        x_serial = c_uint()
        result = lib.get_serial_number(device_ind, byref(x_serial))
        if result == Result.Ok:
            if self.verbose:
                self.print_header(device_ind)
                print("Serial: " + repr(x_serial.value))
            return repr(x_serial.value)
        else:
            print("Result: " + repr(result))
            print("Error when reading serial number")
            raise ValueError

    def get_speed(self, device_ind, mode = 0):
        if mode:
            # Create move settings structure
            mvst = move_settings_t()
            # Get current move settings from controller
            result = lib.get_move_settings(device_ind, byref(mvst))
            if self.verbose:
                self.print_header(device_ind)
                print(f"Working speed {repr(mvst.Speed)} steps/s")
        else:
            user_unit = calibration_t()
            user_unit.A = self.opened_devices[device_ind]["user_calibration"]
            user_unit.MicrostepMode = self.opened_devices[device_ind]["microstep_mode"]
            mvst = move_settings_calb_t()
            result = lib.get_move_settings_calb(device_ind, byref(mvst), byref(user_unit))
            # Print command return status. It will be 0 if all is OK
            if self.verbose:
                self.print_header(device_ind)
                print(f"Working speed {repr(mvst.Speed)} mm/s")
        if result == Result.Ok:
            return mvst.Speed
        else:
            print("Result: " + repr(result))
            print("Error when getting speed")
            raise ValueError

    def get_engine_settings(self, device_ind):
        # Create move settings structure
        engst = engine_settings_t()
        # Get current move settings from controller
        result = lib.get_device_information(device_ind, byref(engst))
        if result == Result.Ok:
            if self.verbose:
                self.print_header(device_ind)
                print("Engine settings: "+repr(engst))
            # TODO: should be a dict
            return engst
        else:
            print("Result: " + repr(result))
            print("Error when getting engine settings")
            raise ValueError

    def get_stage_name(self, device_ind):
        # Create move settings structure
        stgnm = stage_name_t()
        # Get current move settings from controller
        result = lib.get_stage_name(device_ind, byref(stgnm))
        if result == Result.Ok:
            if self.verbose:
                self.print_header(device_ind)
                print(f"Stage name {stgnm.PositionerName} as in Stage/Positioner name")
            return stgnm.PositionerName
        else:
            print("Result: " + repr(result))
            print("Error when getting stage name")
            raise ValueError

    def get_device_information(self, device_ind):
        # Create move settings structure
        devinf = device_information_t()
        # Get current move settings from controller
        result = lib.get_device_information(device_ind, byref(devinf))
        # Print command return status. It will be 0 if all is OK
        if result == Result.Ok:
            if self.verbose:
                self.print_header(device_ind)
                print(f"Device information: {repr(devinf)}")
            return devinf
        else:
            print("Result: " + repr(result))
            print("Error when getting device information")
            raise ValueError

    def get_stage_information(self, device_ind):
        """
        Read information from the EEPROM of the progress bar if it is installed.

        :param device_ind: device ind.
        """
        x_stage_inf = stage_information_t()
        result = lib.get_stage_information(device_ind, byref(x_stage_inf))
        if result == Result.Ok:
            if self.verbose:
                self.print_header(device_ind)
                print(f"Stage information: {repr(x_stage_inf)}")
            return x_stage_inf
        else:
            print("Result: " + repr(result))
            print("Error when getting stage information")
            raise ValueError

    def get_stage_settings(self, device_ind):
        """
        Read information from the EEPROM of the progress bar if it is installed.

        :param device_ind: device ind.
        """
        x_stage_set = stage_settings_t()
        result = lib.get_stage_settings(device_ind, byref(x_stage_set))
        if result == Result.Ok:
            if self.verbose:
                self.print_header(device_ind)
                print(f"Stage settings: {repr(x_stage_set)}")
            return x_stage_set
        else:
            print("Result: " + repr(result))
            print("Error when getting stage settings")
            raise ValueError

    def get_move_settings(self, device_ind, mode=1):
        """
        Read the move settings.

        :param device_ind: device ind.
        :param mode: data mode in feedback counts or in user units. (Default value = 1)
        """
        if mode:
            # Create move settings structure
            mvst = move_settings_t()
            result = lib.get_move_settings(device_ind, byref(mvst))
        else:
            mvst = move_settings_calb_t()
            user_unit = calibration_t()
            user_unit.A = self.opened_devices[device_ind]["user_calibration"]
            user_unit.MicrostepMode = self.opened_devices[device_ind]["microstep_mode"]
            result = lib.get_move_settings_calb(device_ind, byref(mvst), byref(user_unit))
        if result == Result.Ok:
            if self.verbose:
                self.print_header(device_ind)
                print("Move settings:")
                print("  Current speed: " + repr(mvst.Speed))
                print("  Current acceleration: " + repr(mvst.Accel))
                print("  Current deceleration: " + repr(mvst.Decel))
            return {"Speed": repr(mvst.Speed),
                    "Accel": repr(mvst.Accel),
                    "Decel": repr(mvst.Decel)}
        else:
            print("Result: " + repr(result))
            print("Error when getting move settings")
            raise ValueError

    def get_max_speed(self, device_ind, mode = 0):
        if mode:
            # Create move settings structure
            mvst = motor_settings_t()
            # Get current move settings from controller
            result = lib.get_motor_settings(device_ind, byref(mvst))
            # Print command return status. It will be 0 if all is OK
            print("Read command result: " + repr(result))
            if result == Result.Ok:
                if self.verbose:
                    self.print_header(device_ind)
                    print(f"Maximum speed from Stage/Motor {mvst.MaxSpeed} [steps/s]")
            return mvst.MaxSpeed
        else:
            user_unit = calibration_t()
            user_unit.A = self.opened_devices[device_ind]["user_calibration"]
            user_unit.MicrostepMode = self.opened_devices[device_ind]["microstep_mode"]
            # Create move settings structure
            stg = stage_settings_t()
            # Get current move settings from controller
            result = lib.get_stage_settings(device_ind, byref(stg), byref(user_unit))
            # Print command return status. It will be 0 if all is OK
            if result == Result.Ok:
                if self.verbose:
                    self.print_header(device_ind)
                    print(f"Maximum speed from Stage/Motor {stg.MaxSpeed} [mm/s]")
                return stg.MaxSpeed
        print("Result: " + repr(result))
        print("Error when getting move settings")
        raise ValueError


    def get_motor_settings(self, device_ind):
        """
        Receiving the configuration of the motor.

        :param device_ind: device ind.
        """
        x_motor_settings = motor_settings_t()
        result = lib.get_motor_settings(device_ind, byref(x_motor_settings))
        if result == Result.Ok:
            if self.verbose:
                self.print_header(device_ind)
                print(f"Motor settings: {repr(x_motor_settings)}")
            return x_motor_settings
        else:
            print("Result: " + repr(result))
            print("Error when getting motor settings")
            raise ValueError

    def set_speed(self, device_ind, speed, mode = 0):
        if mode:
            mvst = move_settings_t()
            # Get current move settings from controller
            result_read = lib.get_move_settings(device_ind, byref(mvst))

            mvst.Speed = int(speed)
            # Write new move settings to controller
            result_write = lib.set_move_settings(device_ind, byref(mvst))
            # Print command return status. It will be 0 if all is OK
            if result_read == Result.Ok and result_write == Result.Ok:
                if self.verbose:
                    self.print_header(device_ind)
                    print(f"changed working speed {mvst.Speed} steps/s -> {speed} steps/s")
            else:
                print(f"Result (read): {repr(result_read)}. Result (write): {repr(result_write)}")
                print("Error when setting speed")
                raise ValueError
        else:
            user_unit = calibration_t()
            user_unit.A = self.opened_devices[device_ind]["user_calibration"]
            user_unit.MicrostepMode = self.opened_devices[device_ind]["microstep_mode"]
            mvst = move_settings_calb_t()
            result_read = lib.get_move_settings_calb(device_ind, byref(mvst), byref(user_unit))
            mvst.Speed = float(speed)
            result_write = lib.set_move_settings_calb(device_ind, byref(mvst), byref(user_unit))
            if result_read == Result.Ok and result_write == Result.Ok:
                if self.verbose:
                    self.print_header(device_ind)
                    print(f"changed working speed {mvst.Speed} mm/s -> {speed} mm/s")
            else:
                print(f"Result (read): {repr(result_read)}. Result (write): {repr(result_write)}")
                print("Error when setting speed (calb)")
                raise ValueError(f"{mvst.Speed}")

    def get_microstep_mode(self, device_ind):
        """
        Get microstep mode. Works only for stepper motors

        :param device_ind: device ind.
        """
        eng = engine_settings_t()
        # Get current engine settings from controller
        result = lib.get_engine_settings(device_ind, byref(eng))
        if result == Result.Ok:
            if self.verbose:
                self.print_header(device_ind)
                print("The Microstep mode is ", self.microstep_mode_str[eng.MicrostepMode])
            return eng.MicrostepMode
        else:
            print("Result: " + repr(result))
            print("Error when getting microstep mode")
            raise ValueError

    def set_microstep_mode(self, device_ind, microstep):
        # Create engine settings structure
        eng = engine_settings_t()
        # Get current engine settings from controller
        result_read = lib.get_engine_settings(device_ind, byref(eng))
        if microstep == "Full":
            eng.MicrostepMode = MicrostepMode.MICROSTEP_MODE_FULL
        elif microstep in MICROSTEP_MODE:
            eng.MicrostepMode = microstep
        else:
            print(f"Impossible to divide step by: Microstep {microstep}. The available microsteps are: ")
            [print(f"Value = {i} - Ustep = {s}") for i,s in enumerate(self.microstep_mode_str)]
            raise ValueError
        result_write = lib.set_engine_settings(device_ind, byref(eng))
        if result_read == Result.Ok and result_write == Result.Ok:
            if self.verbose:
                self.print_header(device_ind)
                print(f"Microstep set to {self.microstep_mode_str[microstep]}")
            return microstep
        else:
            print(f"Result (read): {repr(result_read)}. Result (write): {repr(result_write)}")
            print("Error when setting microstep mode")
            raise ValueError

    def test_eeprom(self, device_ind):
        """
        Checks for the presence of EEPROM. If it is present, it displays information.

        :param device_ind: device ind.
        """

        print("Test EEPROM")
        status = self.status(device_ind)
        if status != None:
            if int(repr(status["Flags"])) and StateFlags.STATE_EEPROM_CONNECTED:
                print("EEPROM CONNECTED")
                stage_information = self.get_stage_information(device_ind)
                print("PartNumber: " + repr(string_at(stage_information.PartNumber).decode()))
                motor_settings = self.get_motor_settings(device_ind)
                if int(repr(motor_settings.MotorType)) == MotorTypeFlags.MOTOR_TYPE_STEP:
                    print("Motor Type: STEP")
                elif int(repr(motor_settings.MotorType)) == MotorTypeFlags.MOTOR_TYPE_DC:
                    print("Motor Type: DC")
                elif int(repr(motor_settings.MotorType)) == MotorTypeFlags.MOTOR_TYPE_BLDC:
                    print("Motor Type: BLDC")
                else:
                    print("Motor Type: UNKNOWN")
            else:
                print("EEPROM NO CONNECTED")

    def flex_wait_for_stop(self, device_ind, msec, mode=0):
        """
        This function performs dynamic output coordinate in the process of moving.

        :param device_ind: device ind.
        :param msec: Pause between reading the coordinates.
        :param mode: data mode in feedback counts or in user units. (Default value = 0)
        """
        stat = status_t()
        stat.MvCmdSts |= 0x80
        while (stat.MvCmdSts & MvcmdStatus.MVCMD_RUNNING > 0):
            result = lib.get_status(device_ind, byref(stat))
            if result == Result.Ok:
                if self.verbose:
                    self.get_position(device_ind, mode)
                lib.msec_sleep(msec)
        return 0