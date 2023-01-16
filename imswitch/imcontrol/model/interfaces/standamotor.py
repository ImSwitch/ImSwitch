import platform
import numpy as np
import os
import sys
import platform
import tempfile
import re
import importlib
from ctypes import *

if sys.version_info >= (3,0):
    import urllib.parse

from imswitch.imcommon.model import initLogger


class StandaMotor():
    def __init__(self, device_id, lib_loc, steps_per_turn, microsteps_per_step):
        self.__logger = initLogger(self)
        # Initiate ximc library
        self.__initiate_library(lib_loc)
        self._device_id = device_id
        self._steps_per_turn = steps_per_turn
        self._microsteps_per_step = microsteps_per_step
        if self._imported:
            # This is device search and enumeration with probing. It gives more information about devices.
            probe_flags = pyximc.EnumerateFlags.ENUMERATE_PROBE
            enum_hints = b"addr="
            devenum = pyximc.lib.enumerate_devices(probe_flags, enum_hints)
            dev_count = pyximc.lib.get_device_count(devenum)
            if dev_count > 0:
                open_name = pyximc.lib.get_device_name(devenum, self._device_id)
            elif sys.version_info >= (3,0):
                # use URI for virtual device when there is new urllib python3 API
                tempdir = tempfile.gettempdir() + "/testdevice.bin"
                if os.altsep:
                    tempdir = tempdir.replace(os.sep, os.altsep)
                # urlparse build wrong path if scheme is not file
                uri = urllib.parse.urlunparse(urllib.parse.ParseResult(scheme="file", \
                        netloc=None, path=tempdir, params=None, query=None, fragment=None))
                open_name = re.sub(r'^file', 'xi-emu', uri).encode()
                self.__logger.debug("Controller not found, mock controller opened.")

            if type(open_name) is str:
                open_name = open_name.encode()

            self.__logger.info(f"Open device {repr(open_name)}")
            self._device_id = pyximc.lib.open_device(open_name)
            self.set_def_sync_in_settings()
            self.set_def_sync_out_settings()

    def close(self):
        if self._imported:
            pyximc.lib.close_device(byref(cast(self._device_id, POINTER(c_int))))

    def set_def_sync_in_settings(self):
        x_sync_in_settings = pyximc.sync_in_settings_t()
        x_sync_in_settings.Position = int(20*self._steps_per_turn/360)
        x_sync_in_settings.Speed = 1000
        x_sync_in_settings.SyncInFlags = 1  # (0x01 (enabled) + 0x02 (trigger on falling edge) + 0x04 (go to position, not relative shift))
        _ = pyximc.lib.set_sync_in_settings(self._device_id, x_sync_in_settings)

    def set_sync_in_settings(self, abs_pos_deg):
        pos_steps, pos_usteps = self.dist_translate(abs_pos_deg)
        x_sync_in_settings = pyximc.sync_in_settings_t()
        x_sync_in_settings.Position = pos_steps
        x_sync_in_settings.uPosition = pos_usteps
        x_sync_in_settings.Speed = 1000
        x_sync_in_settings.ClutterTime = 1
        x_sync_in_settings.SyncInFlags = 5  # (0x01 (enabled) + 0x04 (go to position, not relative shift))
        _ = pyximc.lib.set_sync_in_settings(self._device_id, x_sync_in_settings)

    def set_def_sync_out_settings(self):
        x_sync_out_settings = pyximc.sync_out_settings_t()
        x_sync_out_settings.SyncOutPulseSteps = 100  # (0x01 (enabled))
        x_sync_out_settings.SyncOutFlags = 17  # (0x01 (enabled) + 0x10 (on motion start) (+ 0x20 (on motion stop)))
        _ = pyximc.lib.set_sync_out_settings(self._device_id, x_sync_out_settings)

    #def set_sync_out_settings(self):
    #    x_sync_out_settings = pyximc.sync_out_settings_t()
    #    x_sync_out_settings.SyncOutPulseSteps = 1000  # (0x01 (enabled))
    #    x_sync_out_settings.SyncOutFlags = 17  # (0x01 (enabled) + 0x10 (on motion start))
    #    _ = pyximc.lib.set_sync_out_settings(self._device_id, x_sync_out_settings)

    def get_pos(self):
        self.wait_for_stop(interval=10)
        x_pos = pyximc.get_position_t()
        _ = pyximc.lib.get_position(self._device_id, byref(x_pos))
        pos_deg = self.dist_translate_inv(x_pos.Position, x_pos.uPosition)
        return pos_deg

    def moverel(self, d_move_deg):
        d_move, d_move_u = self.dist_translate(d_move_deg)
        #self.__logger.debug(f'Move relative {d_move_deg} deg / {d_move} st, {d_move_u} ust')
        pyximc.lib.command_movr(self._device_id, d_move, d_move_u)

    def moveabs(self, pos_move):
        d_move, d_move_u = self.dist_translate(pos_move)
        #self.__logger.debug(f'Position absolute {pos_move} deg / {d_move} st, {d_move_u} ust')
        pyximc.lib.command_move(self._device_id, d_move, d_move_u)

    def wait_for_stop(self, interval=100):
        pyximc.lib.command_wait_for_stop(self._device_id, interval)

    def set_zero_pos(self):
        pyximc.lib.command_zero(self._device_id)

    def dist_translate(self, d_deg):
        d = d_deg/360 * self._steps_per_turn
        if d > 0:
            d = np.floor(d)
            d_u = round(((d_deg/360 * self._steps_per_turn) % 1) * self._microsteps_per_step)
        elif d < 0:
            d = np.ceil(d)
            d_u = round(-(-(d_deg/360 * self._steps_per_turn) % 1) * self._microsteps_per_step)
        else:
            d_u = 0
        return int(d), int(d_u)

    def dist_translate_inv(self, steps, usteps):
        d_deg = steps/self._steps_per_turn*360 + usteps/self._microsteps_per_step*360/self._steps_per_turn
        return d_deg

    def test_info(self):
        info = {}
        if self._imported:
            x_device_information = pyximc.device_information_t()
            result = pyximc.lib.get_device_information(self._device_id, byref(x_device_information))
            if result == pyximc.Result.Ok:
                info['Manufacturer'] = repr(string_at(x_device_information.Manufacturer).decode())
                info['ManufacturerId'] = repr(string_at(x_device_information.ManufacturerId).decode())
                info['ProductDescription'] = repr(string_at(x_device_information.ProductDescription).decode())
                info['Major'] = repr(x_device_information.Major)
                info['Minor'] = repr(x_device_information.Minor)
                info['Release'] = repr(x_device_information.Release)
        return info

    def set_rot_speed(self, speed):
        """ Speed currently input in milli rpm, change this to be deg/s later with a transformation below. """
        #speed_mrpm = transf * speed_deg
        x_move_settings = pyximc.move_settings_t()
        _ = pyximc.lib.get_move_settings(self._device_id, byref(x_move_settings))
        x_move_settings.Speed = int(speed)
        pyximc.lib.set_move_settings(self._device_id, x_move_settings)
    
    def start_cont_rot(self):
        pyximc.lib.command_right(self._device_id)

    def stop_cont_rot(self):
        pyximc.lib.command_sstp(self._device_id)

    def __initiate_library(self, lib_loc):
        """ Initiate ximc library, necessary for communicating with motor controller. 
        Import library locally only if standamotor is instantiated, otherwise avoid it. """
        # For correct usage of the library libximc, you need to add the file pyximc.py wrapper with the structures of the library to the python path.
        ximc_dir = os.path.join(lib_loc) # Formation of the directory name with all dependencies. The dependencies for the examples are located in the ximc directory.
        ximc_package_dir = os.path.join(ximc_dir, "crossplatform", "wrappers", "python") # Formation of the directory name with python dependencies.
        sys.path.append(ximc_package_dir)  # add pyximc.py wrapper to python path

        # Determining the directory with dependencies for windows depending on the bit depth.
        arch_dir = "win64" if "64" in platform.architecture()[0] else "win32"
        libdir = os.path.join(ximc_dir, arch_dir)
        if sys.version_info >= (3,8):
            os.chdir(libdir)
            os.add_dll_directory(libdir)
        try:
            global pyximc
            pyximc = importlib.__import__("pyximc", globals=globals(), locals=locals(), fromlist=[], level=0)
            self._imported = True
        except ImportError as err:
            self._imported = False
            self.__logger.warning('pyximc library import failed, check lib location in setup json file.')
        except OSError as err:
            self._imported = False
            self.__logger.error(err.errno, err.filename, err.strerror, err.winerror) # Allows you to display detailed information by mistake.


class MockStandaMotor():
    def __init__(self, *args):
        pass

    def close(self):
        pass

    def get_pos(self):
        return 0

    def moverel(self, d_move_deg):
        pass

    def moveabs(self, pos_move):
        pass

    def test_info(self):
        return {}

    def startmove(self):
        pass

    def stopmove(self):
        pass
