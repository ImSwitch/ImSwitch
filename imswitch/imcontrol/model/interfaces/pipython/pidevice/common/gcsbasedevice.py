#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Provide a device, connected via the PI GCS DLL."""

from logging import debug
from abc import abstractmethod
from ..interfaces.gcsdll import GCSDll
from .. import gcserror
from .gcsbasecommands import GCSBaseCommands
from ..gcsmessages import GCSMessages
from .. import GCSError

__signature__ = 0x1dcb748570b30bb29fdbdc7e4531a570


# Invalid method name pylint: disable=C0103
# Too many public methods pylint: disable=R0904
class GCSBaseDevice(GCSBaseCommands):
    """Provide a device connected via the PI GCS DLL or antoher gateway, can be used as context manager."""

    def __init__(self, devname='', gcsdll='', gateway=None):
        """Provide a device, connected via the PI GCS DLL or another 'gateway'.
        @param devname : Name of device, chooses according DLL which defaults to PI_GCS2_DLL.
        @param gcsdll : Name or path to GCS DLL to use, overwrites 'devname'.
        @type gateway : pipython.pidevice.interfaces.pigateway.PIGateway
        """
        self.dll = gateway or GCSDll(devname, gcsdll)
        messages = GCSMessages(self.dll)
        GCSBaseCommands.__init__(self, messages)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def dcid(self):
        """Get ID of current daisy chain connection as integer."""
        return self.dll.dcid

    @property
    def dllpath(self):
        """Get full path to GCS DLL."""
        return self.dll.dllpath

    @property
    def isavailable(self):
        """Return True if controller is available, i.e. connected and responding to qIDN command."""
        timeout = self.timeout
        self.timeout = 200
        try:
            _ = self.qIDN()
        except GCSError:
            return False
        finally:
            self.timeout = timeout
        return True

    def unload(self):
        """Close connection to device and daisy chain and unload GCS DLL."""
        debug('GCSBaseDevice.unload()')
        del self.funcs
        del self.devname
        del self.axes
        self._settings = {'paramconv': {}}
        self.dll.unload()

    @abstractmethod
    def close(self):
        """Close connection to device and daisy chain."""

    @abstractmethod
    def GetError(self):
        """Get current controller error.
        @return : Current error code as integer.
        """

    @staticmethod
    def TranslateError(errval):
        """Translate GCS error number into readable error message.
        @param errval: GCSError value as integer.
        @return: GCSError message as string.
        """
        return gcserror.translate_error(errval)

    def GetAsyncBuffer(self, firstline=1, lastline=0, numtables=1):
        """Query all available data points, return list with 'numtables' columns.
        DEPRECATED: Use GCSMessages.bufdata instead.
        Buffer is used by qDRR(), qDDL(), qGWD(), qTWS(), qJLT() and qHIT().
        @param firstline : Optional, but must be >= 1 and smaller than 'lastline'.
        @param lastline : Optional, defaults to query all available data points.
        @param numtables : Arrange data into 'numtables' columns, defaults to "1".
        @return: List of data points as float with 'numtables' columns.
        """
        return self.dll.GetAsyncBuffer(firstline, lastline, numtables)

    def GetAsyncBufferIndex(self):
        """Get current index used for the internal buffer.
        DEPRECATED: Use GCSMessages.bufindex instead.
        @return: Buffer index as integer.
        """
        return self.dll.GetAsyncBufferIndex()

    def IsConnected(self):
        """Return True if a device is connected."""
        return self.dll.connected

    @property
    def connected(self):
        """Return True if a device is connected."""
        return self.dll.connected

    def GetInterfaceDescription(self):
        """Get textual description of actual interface connection."""
        return self.dll.GetInterfaceDescription()

    def InterfaceSetupDlg(self, key=''):
        """Open dialog to select the interface.
        @param key: Optional key name as string to store the settings in the Windows registry.
        """
        self.dll.InterfaceSetupDlg(key)

    def ConnectRS232(self, comport, baudrate):
        """Open an RS-232 connection to the device.
        @param comport: Port to use as integer (1 means "COM1") or device name ("dev/ttys0") as str.
        @param baudrate: Baudrate to use as integer.
        """
        self.dll.ConnectRS232(comport, baudrate)

    def ConnectTCPIP(self, ipaddress, ipport=50000):
        """Open a TCP/IP connection to the device.
        @param ipaddress: IP address to connect to as string.
        @param ipport: Port to use as integer, defaults to 50000.
        """
        self.dll.ConnectTCPIP(ipaddress, ipport)

    def ConnectTCPIPByDescription(self, description):
        """Open a TCP/IP connection to the device using the device 'description'.
        @param description: One of the identification strings listed by EnumerateTCPIPDevices().
        """
        self.dll.ConnectTCPIPByDescription(description)

    def ConnectUSB(self, serialnum):
        """Open an USB connection to a device.
        @param serialnum: Serial number of device or one of the
        identification strings listed by EnumerateUSB().
        """
        self.dll.ConnectUSB(serialnum)

    def ConnectNIgpib(self, board, device):
        """Open a connection from a NI IEEE 488 board to the device.
        @param board: GPIB board ID as integer.
        @param device: The GPIB device ID of the device as integer.
        """
        self.dll.ConnectNIgpib(board, device)

    def ConnectPciBoard(self, board):
        """Open a PCI board connection.
        @param board : PCI board number as integer.
        """
        self.dll.ConnectPciBoard(board)

    def EnumerateUSB(self, mask=''):
        """Get identification strings of all USB connected devices.
        @param mask: String to filter the results for certain text.
        @return: Found devices as list of strings.
        """
        return self.dll.EnumerateUSB(mask)

    def EnumerateTCPIPDevices(self, mask=''):
        """Get identification strings of all TCP connected devices.
        @param mask: String to filter the results for certain text.
        @return: Found devices as list of strings.
        """
        return self.dll.EnumerateTCPIPDevices(mask)

    def OpenRS232DaisyChain(self, comport, baudrate):
        """Open an RS-232 daisy chain connection.
        To get access to a daisy chain device you have to call ConnectDaisyChainDevice().
        @param comport: Port to use as integer (1 means "COM1").
        @param baudrate: Baudrate to use as integer.
        @return: Found devices as list of strings.
        """
        return self.dll.OpenRS232DaisyChain(comport, baudrate)

    def OpenUSBDaisyChain(self, description):
        """Open a USB daisy chain connection.
        To get access to a daisy chain device you have to call ConnectDaisyChainDevice().
        @param description: Description of the device returned by EnumerateUSB().
        @return: Found devices as list of strings.
        """
        return self.dll.OpenUSBDaisyChain(description)

    def OpenTCPIPDaisyChain(self, ipaddress, ipport=50000):
        """Open a TCPIP daisy chain connection.
        To get access to a daisy chain device you have to call ConnectDaisyChainDevice().
        @param ipaddress: IP address to connect to as string.
        @param ipport: Port to use as integer, defaults to 50000.
        @return: Found devices as list of strings.
        """
        return self.dll.OpenTCPIPDaisyChain(ipaddress, ipport)

    def ConnectDaisyChainDevice(self, deviceid, daisychainid=None):
        """Connect device with 'deviceid' on the daisy chain 'daisychainid'.
        Daisy chain has to be connected before, see Open<interface>DaisyChain() functions.
        @param daisychainid : Daisy chain ID as int from the daisy chain master instance or None.
        @param deviceid : Device ID on the daisy chain as integer.
        """
        self.dll.ConnectDaisyChainDevice(deviceid, daisychainid)

    def EnableBaudRateScan(self, enable_bautrate_scan):
        """Enables the baud rate scan for RS232 and FTDI_USB. If the baud rate scan is enabled the DLL automatically
        tries to swithc the controller to the buau rate gifen by the connect function. If 'False' there is no baud rate
        scan and the connect function fails if the buad rate of the connect function does not match the baud rate
        of the controller
        @param enable_bautrate_scan : If 'True' the baud rate scan is enabled, else it is not enabled
        """
        self.dll.EnableBaudRateScan(enable_bautrate_scan)

    def SetConnectTimeout(self, timeout):
        """Sets the connection time out
        @param timeout : The timeout in ms
        """
        self.dll.SetConnectTimeout(timeout)

    def CloseConnection(self):
        """Reset axes property and close connection to the device."""
        del self.axes
        self.dll.CloseConnection()

    def CloseDaisyChain(self):
        """Close all connections on daisy chain and daisy chain connection itself."""
        self.dll.CloseDaisyChain()
