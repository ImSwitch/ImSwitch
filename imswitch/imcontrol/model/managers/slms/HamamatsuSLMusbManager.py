import os
import glob
import enum
import numpy as np
from PIL import Image
import math
from scipy import signal as sg
from pathlib import Path
import matplotlib.pyplot as plt

import ctypes
from ctypes import c_int32, c_uint8, c_char_p, byref, create_string_buffer

from imswitch.imcommon.framework import Signal, SignalInterface
from imswitch.imcommon.model import initLogger

_dllpath = r"C:\Users\guillaume.minet\Documents\GitHub\ImSwitch\imswitch\imcontrol\model\interfaces\hpkSLMdaLV_cdecl_64bit\hpkSLMdaLV.dll"

class HamamatsuSLMusbManager(SignalInterface):
    """Manager for communication with Hamamatsu SLM with USB connection"""

    def __init__(self,slmInfo,slmName,*args,**kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        self.serial_number = slmInfo.serial_number
        if self.serial_number is None:
            raise ValueError(f"SLM serial number not provided for {slmName}, needed for USB connection!")
        
        self.slmName = slmName
        self.slmInfo = slmInfo
        self.width = slmInfo.width
        self.height = slmInfo.height
        self.pixel_size = slmInfo.pixelSize

        if slmInfo.managerProperties is not None:
            self.mockermode = slmInfo.managerProperties.get("mockermode", False)
        
        if self.mockermode:
            self.__logger.info(f"SLM Manager {self.slmName} running in MOCKER MODE. No actual connection to SLM will be made.")
            self.dll = None
        else:
            try:
                self.dll = ctypes.CDLL(_dllpath)
            except Exception as e:
                self.__logger.error(f"Could not load Hamamatsu SLM DLL from {_dllpath}: {e}")
                self.dll = None
                self.bID = None
                self.num_devices = 0
                self.connected = False
                if self.dll is not None:
                    self.define_dll_prototypes()

    def finalize(self):
        """Finalize the manager by closing any open connections."""
        if not self.mockermode:
            self.close_device()


    def connect_to_device(self):
        """
        Connect to the Hamamatsu SLM device that matches self.serial_number.
        """
        if self.mockermode:
            return True, "Mocker mode - no actual device connection."
        
        if self.dll is None:
            self.__logger.warning("DLL not loaded, cannot connect to device.")
            return False, None
        max_devices = 8
        self.bIDList = (c_uint8 * max_devices)()
        self.num_devices = self.dll.Open_Dev(self.bIDList, max_devices)

        if self.num_devices <= 0:
            self.__logger.warning("No SLM devices detected via USB.")
            self.connected = False
            return False, None

        self.__logger.debug(f"{self.slmName} connection: detected {self.num_devices} SLM device(s)."
                           f"Searching for serial: {self.serial_number}")

        found = False
        serial_buf = create_string_buffer(11)

        # Loop through all connected device IDs
        for i in range(self.num_devices):
            bID = self.bIDList[i]
            success = self.dll.Check_HeadSerial(bID, serial_buf, 11)
            if not success:
                self.__logger.warning(f"Could not read serial for device index {i} (bID={bID}).")
                continue

            serial = serial_buf.value.decode(errors="ignore").strip()
            self.__logger.debug(f"Device index {i}: serial '{serial}'")

            if serial == self.serial_number:
                self.__logger.debug(f"Matched target device with serial {serial}")
                self.bID = bID
                found = True
                break

        if found:
            self.connected = True
            self.__logger.info(f"{self.slmName}: successfully connected to target SLM device.")
            return True, serial
        else:
            self.__logger.warning(f"{self.slmName}: no connected SLM matched serial '{self.serial_number}'."
                                  f"Change serial number in config file or check USB connection.")
            # Cleanly close all connections opened by Open_Dev
            self.dll.Close_Dev(self.bIDList, self.num_devices)
            self.connected = False
            return False, None


    def upload_pattern(self, pattern, slot_no=0, add_correction_pattern=False, apply_max_value=True):
        """ Upload pattern to SLM """

        if self.mockermode:
            self.__logger.info("Mocker mode - not uploading pattern to device.")
            return

        if self.bID is None:
            raise RuntimeError("No device connected. Cannot upload pattern.")

        if add_correction_pattern:
            if self.correction_pattern is None:
                raise ValueError("Correction pattern not set.")
            pattern = pattern + self.correction_pattern
            pattern = pattern % 256
        
        if apply_max_value:
            pattern = pattern.astype(np.float16) * self.max_value / 255
            pattern = pattern.astype(np.uint8)

        # Flatten to 1D
        array_1d = pattern.flatten()

        # Convert to ctypes
        c_array = (c_uint8 * array_1d.size)(*array_1d)

        # Upload to slot_no
        success = self.dll.Write_FMemArray(
            self.bID,
            c_array,
            array_1d.size,
            1272,
            1024,
            slot_no
        )

        if success:
            self.__logger.debug("Array uploaded successfully to slot_no", slot_no)
            self.dll.Change_DispSlot(self.bID, slot_no)
            self.currently_displayed = pattern
        else:
            print("Failed to upload array")

    def close_device(self):
        """Close USB connection with SLM """

        if self.mockermode:
            return True, "Mocker mode - no device to close."

        if self.bID is not None:
            # NOTE: Close_Dev(uint8_t bIDList[], int32_t bIDSize) disconnects communication with 
            # the target device(s) specified in bIDList.To disconnect only one, we prepare a list 
            # containing only this device ID

            if self.dll is None:
                self.__logger.warning("DLL not loaded, cannot close device.")
                return False, "DLL not loaded"

            single_bID_list = (c_uint8 * 1)(self.bID)
            result = self.dll.Close_Dev(single_bID_list, 1)

            if result: 
                self.bID = None
                self.num_devices = 0
                self.connected = False
                self.__logger.info(f"{self.slmName} connection closed.")
                success = True
                msg = "Sucessfully disconnection"
            else:
                self.__logger.warning(f"{self.slmName}: closing connection failed.")
                success = False
                msg = "Error when closing device"
        else:
            self.__logger.info("Found no device to close.")
            success = True
            msg = "Found no device to close"
        return success,msg

    def define_dll_prototypes(self):
        self.dll.Open_Dev.argtypes = [ctypes.POINTER(c_uint8), c_int32]
        self.dll.Open_Dev.restype = c_int32

        self.dll.Close_Dev.argtypes = [ctypes.POINTER(c_uint8), c_int32]
        self.dll.Close_Dev.restype = c_int32

        self.dll.Check_HeadSerial.argtypes = [c_uint8, ctypes.c_char_p, c_int32]
        self.dll.Check_HeadSerial.restype = c_int32

        self.dll.Write_FMemBMPPath.argtypes = [c_uint8, c_char_p, c_int32]
        self.dll.Write_FMemBMPPath.restype = c_int32

        self.dll.Change_DispSlot.argtypes = [c_uint8, c_int32]
        self.dll.Change_DispSlot.restype = c_int32

        # Define prototype
        self.dll.Write_FMemArray.argtypes = [
            c_uint8,                      # bID
            ctypes.POINTER(c_uint8),      # ArrayIn
            c_int32,                      # ArraySize
            c_int32,                     # XPixel
            c_int32,                     # YPixel
            c_int32                      # SlotNo
        ]
        self.dll.Write_FMemArray.restype = c_int32