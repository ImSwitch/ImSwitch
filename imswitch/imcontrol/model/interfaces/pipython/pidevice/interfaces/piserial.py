#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Provide access to the serial port. Requires the "pyserial" package (pip install pyserial)."""

from logging import debug
import serial

from ..interfaces.pigateway import PIGateway

__signature__ = 0x6cf969e1fd8746f703870b5cc9395205


class PISerial(PIGateway):
    """Provide access to the serial port, can be used as context manager."""

    def __init__(self, port, baudrate):
        """Provide access to the serial port.
        @param port : Name of the serial port to use as string, e.g. "COM1" or "/dev/ttyS0".
        @param baudrate : Baud rate as integer.
        """
        debug('create an instance of PISerial(port=%s, baudrate=%s)', port, baudrate)
        self._timeout = 7000  # milliseconds
        self._ser = serial.Serial(port=port, baudrate=baudrate, timeout=self._timeout / 1000.)
        self._connected = True
        self.flush()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __str__(self):
        return 'PISerial(port=%s, baudrate=%s)' % (self._ser.port, self._ser.baudrate)

    @property
    def timeout(self):
        """Return timeout in milliseconds."""
        return self._timeout

    def settimeout(self, value):
        """Set timeout to 'value' in milliseconds."""
        self._timeout = value
        self._ser.timeout = value / 1000.

    @property
    def connected(self):
        """Return True if a device is connected."""
        return self._connected

    @property
    def connectionid(self):
        """Return 0 as ID of current connection."""
        return 0

    def send(self, msg):
        """Send 'msg' to the serial port.
        @param msg : String to send.
        """
        debug('PISerial.send: %r', msg)
        self._ser.write(msg)

    def read(self):
        """Return the answer to a GCS query command.
        @return : Answer as string.
        """
        received = self._ser.read_all()
        debug('PISerial.read: %r', received)
        return received

    def flush(self):
        """Flush input buffer."""
        debug('PISerial.flush()')
        self._ser.read_all()

    def close(self):
        """Close serial port if connected."""
        if not self.connected:
            return
        debug('PISerial.close: close connection to port %r', self._ser.port)
        self._connected = False
        self._ser.close()
