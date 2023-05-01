#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Provide a device, connected via the PI GCS DLL."""

from logging import debug
from ..gcsmessages import GCSMessages
from ..common.gcsbasedevice import GCSBaseDevice
from .gcs2commands import GCS2Commands

__signature__ = 0xdd997bcecd414b93036ccca72704bdd2


# Invalid method name pylint: disable=C0103
# Too many public methods pylint: disable=R0904
class GCS2Device(GCSBaseDevice, GCS2Commands):
    """Provide a device connected via the PI GCS DLL or antoher gateway, can be used as context manager."""

    def __init__(self, devname='', gcsdll='', gateway=None):
        """Provide a device, connected via the PI GCS DLL or another 'gateway'.
        @param devname : Name of device, chooses according DLL which defaults to PI_GCS2_DLL.
        @param gcsdll : Name or path to GCS DLL to use, overwrites 'devname'.
        @type gateway : pipython.pidevice.interfaces.pigateway.PIGateway
        """
        GCSBaseDevice.__init__(self, devname, gcsdll, gateway)
        messages = GCSMessages(self.dll)
        GCS2Commands.__init__(self, messages)

    def close(self):
        """Close connection to device and daisy chain."""
        debug('GCS2Device.close()')
        del self.funcs
        del self.devname
        del self.axes
        self._settings = {'paramconv': {}}
        self.dll.close()

    def GetError(self):
        """Get current controller error.
        @return : Current error code as integer.
        """
        return self.qERR()

    def CloseConnection(self):
        """Reset axes property and close connection to the device."""
        del self.axes
        GCSBaseDevice.CloseConnection(self)

    def hasref(self, axis):
        """Return True if 'axis' has a reference switch.
        @param axis : Axis to check as string convertible.
        @return : True if 'axis' has a reference switch
        """
        debug('GCS2Device.hasref(axis=%s)', axis)
        if self.HasqTRS():
            return self.qTRS(axis)[axis]
        if self.HasqREF():
            return self.qREF(axis)[axis]
        if self.getparam(0x14, axis) is not None:  # has reference
            return bool(self.getparam(0x14, axis))
        return False

    def haslim(self, axis):
        """Return True if 'axis' has a limit switch.
        @param axis : Axis to check as string convertible.
        @return : True if 'axis' has a limit switch
        """
        debug('GCS2Device.haslim(axis=%s)', axis)
        if self.getparam(0x32, axis) is not None:  # has no limit switch
            return not bool(self.getparam(0x32, axis))
        return False

    def canfrf(self, axis):
        """Return True if 'axis' can be referenced with the "FRF" command.
        @param axis : Axis to check as string convertible.
        @return : True if 'axis' can be referenced with the "FRF" command
        """
        debug('GCS2Device.canfrf(axis=%s)', axis)
        if not self.HasFRF():
            return False
        if self.getparam(0x70, axis) is not None:  # reference signal type
            return self.getparam(0x70, axis) != 4  # no reference signal
        return self.hasref(axis)

    def canfnl(self, axis):
        """Return True if 'axis' can be referenced with the "FNL" command.
        @param axis : Axis to check as string convertible.
        @return : True if 'axis' can be referenced with the "FNL" command
        """
        debug('GCS2Device.canfnl(axis=%s)', axis)
        return self.HasFNL() and self.haslim(axis)

    def canfpl(self, axis):
        """Return True if 'axis' can be referenced with the "FPL" command.
        @param axis : Axis to check as string convertible.
        @return : True if 'axis' can be referenced with the "FPL" command
        """
        debug('GCS2Device.canfpl(axis=%s)', axis)
        return self.HasFPL() and self.haslim(axis)
