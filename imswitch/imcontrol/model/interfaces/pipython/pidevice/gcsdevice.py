#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Provide a device, connected via the PI GCS DLL."""

# Cyclic import (pipython -> pipython.gcsdevice) pylint: disable=R0401
from . import GCS2Device
from . import GCS21Device
from . import GCS21Error
from . import isgcs21

from .common.gcsbasedevice import GCSBaseDevice

__signature__ = 0x92cac9e12931ad5e1ed4284e196390ec


# Method 'GetError' is abstract in class 'GCSBaseDevice' but is not overridden pylint: disable=W0223
# Method 'close' is abstract in class 'GCSBaseDevice' but is not overridden pylint: disable=W0223
# Method 'devname' is abstract in class 'GCSBaseCommands' but is not overridden pylint: disable=W0223
# Method 'funcs' is abstract in class 'GCSBaseCommands' but is not overridden pylint: disable=W0223
# Method 'isavailable' is abstract in class 'GCSBaseDevice' but is not overridden pylint: disable=W0223
# Method 'paramconv' is abstract in class 'GCSBaseCommands' but is not overridden pylint: disable=W0223
# Method 'unload' is abstract in class 'GCSBaseDevice' but is not overridden pylint: disable=W0223
# Class inherits from object, can be safely removed from bases in python3 pylint: disable=R0205
class GCSDevice(GCSBaseDevice):
    """Provide a device connected via the PI GCS DLL or antoher gateway, can be used as context manager."""

    def __init__(self, devname='', gcsdll='', gateway=None):
        """Provide a device, connected via the PI GCS DLL or another 'gateway'.
        @param devname : Name of device, chooses according DLL which defaults to PI_GCS2_DLL.
        @param gcsdll : Name or path to GCS DLL to use, overwrites 'devname'.
        @type gateway : pipython.pidevice.interfaces.pigateway.PIGateway
        """
        GCSBaseDevice.__init__(self, devname=devname, gcsdll=gcsdll, gateway=gateway)

        if gateway and gateway.connected:
            self._set_gcsdevice_type()

    def _set_gcsdevice_type(self):
        if isgcs21(self._msgs):
            if GCS21Device is not None:
                GCSDevice.__bases__ = (GCS21Device,)
            if GCS21Error is not None:
                self._msgs.gcs_error_class = GCS21Error
        else:
            if GCS2Device is not None:
                GCSDevice.__bases__ = (GCS2Device,)

    def InterfaceSetupDlg(self, key=''):
        """Open dialog to select the interface.
        @param key: Optional key name as string to store the settings in the Windows registry.
        """
        super(GCSDevice, self).InterfaceSetupDlg(key=key)
        self._set_gcsdevice_type()

    def ConnectRS232(self, comport, baudrate):
        """Open an RS-232 connection to the device.
        @param comport: Port to use as integer (1 means "COM1") or device name ("dev/ttys0") as str.
        @param baudrate: Baudrate to use as integer.
        """
        super(GCSDevice, self).ConnectRS232(comport=comport, baudrate=baudrate)
        self._set_gcsdevice_type()

    def ConnectTCPIP(self, ipaddress, ipport=50000):
        """Open a TCP/IP connection to the device.
        @param ipaddress: IP address to connect to as string.
        @param ipport: Port to use as integer, defaults to 50000.
        """
        super(GCSDevice, self).ConnectTCPIP(ipaddress=ipaddress, ipport=ipport)
        self._set_gcsdevice_type()

    def ConnectTCPIPByDescription(self, description):
        """Open a TCP/IP connection to the device using the device 'description'.
        @param description: One of the identification strings listed by EnumerateTCPIPDevices().
        """
        super(GCSDevice, self).ConnectTCPIPByDescription(description=description)
        self._set_gcsdevice_type()

    def ConnectUSB(self, serialnum):
        """Open an USB connection to a device.
        @param serialnum: Serial number of device or one of the
        identification strings listed by EnumerateUSB().
        """
        super(GCSDevice, self).ConnectUSB(serialnum=serialnum)
        self._set_gcsdevice_type()

    def ConnectNIgpib(self, board, device):
        """Open a connection from a NI IEEE 488 board to the device.
        @param board: GPIB board ID as integer.
        @param device: The GPIB device ID of the device as integer.
        """
        super(GCSDevice, self).ConnectNIgpib(board=board, device=device)
        self._set_gcsdevice_type()

    def ConnectPciBoard(self, board):
        """Open a PCI board connection.
        @param board : PCI board number as integer.
        """
        super(GCSDevice, self).ConnectPciBoard(board=board)
        self._set_gcsdevice_type()

    def OpenRS232DaisyChain(self, comport, baudrate):
        """Open an RS-232 daisy chain connection.
        To get access to a daisy chain device you have to call ConnectDaisyChainDevice().
        @param comport: Port to use as integer (1 means "COM1").
        @param baudrate: Baudrate to use as integer.
        @return: Found devices as list of strings.
        """

        # To check if the controller is a GCS2 or GCS21 controller and select the right class therefore
        # it is necessary to communicate with the master of the daisy chain directly.
        super(GCSDevice, self).ConnectRS232(comport=comport, baudrate=baudrate)
        self._set_gcsdevice_type()
        super(GCSDevice, self).CloseConnection()

        devlist = super(GCSDevice, self).OpenRS232DaisyChain(comport=comport, baudrate=baudrate)
        return devlist

    def OpenUSBDaisyChain(self, description):
        """Open a USB daisy chain connection.
        To get access to a daisy chain device you have to call ConnectDaisyChainDevice().
        @param description: Description of the device returned by EnumerateUSB().
        @return: Found devices as list of strings.
        """

        # To check if the controller is a GCS2 or GCS21 controller and select the right class therefore
        # it is necessary to communicate with the master of the daisy chain directly.
        super(GCSDevice, self).ConnectUSB(serialnum=description)
        self._set_gcsdevice_type()
        super(GCSDevice, self).CloseConnection()

        devlist = super(GCSDevice, self).OpenUSBDaisyChain(description=description)
        return devlist

    def OpenTCPIPDaisyChain(self, ipaddress, ipport=50000):
        """Open a TCPIP daisy chain connection.
        To get access to a daisy chain device you have to call ConnectDaisyChainDevice().
        @param ipaddress: IP address to connect to as string.
        @param ipport: Port to use as integer, defaults to 50000.
        @return: Found devices as list of strings.
        """

        # To check if the controller is a GCS2 or GCS21 controller and select the right class therefore
        # it is necessary to communicate with the master of the daisy chain directly.
        super(GCSDevice, self).ConnectTCPIP(ipaddress=ipaddress, ipport=ipport)
        self._set_gcsdevice_type()
        super(GCSDevice, self).CloseConnection()

        devlist = super(GCSDevice, self).OpenTCPIPDaisyChain(ipaddress=ipaddress, ipport=ipport)
        return devlist
