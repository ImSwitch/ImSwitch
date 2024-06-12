# MIT License

# Copyright (c) 2020 yaq

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Our new and improved APT protocol unpacker, which we'll include
# here until (if?) our merge request gets accepted.

__all__ = ["Unpacker"]

import asyncio
from collections import namedtuple
import io
import struct
import warnings

from .parsing import id_to_func


class Unpacker:
    """
    Create an Unpacker to decode a byte stream into Thorlabs APT protocol messages.

    The ``file_like`` parameter should be an object which data can be sourced from.
    It should support the ``read()`` method.

    The ``on_error`` parameter selects the action to take if invalid data is detected.
    If set to ``"continue"`` (the default), bytes will be discarded if the byte sequence
    does not appear to be a valid message.
    If set to ``"warn"``, the behaviour is identical, but a warning message will be emitted.
    To instead immediately abort the stream decoding and raise a ``RuntimeError``, set to
    ``"raise"``.

    :param file_like: A file-like object which data can be `read()` from.
    :param on_error: Action to take if invalid data is detected.
    """
    def __init__(self, file_like=None, on_error="continue"):
        if file_like is None:
            self._file = io.BytesIO()
        else:
            self._file = file_like
        self.buf = b""
        self.on_error = on_error

    def __iter__(self):
        return self

    def _decoding_error(self, message="Error decoding message from buffer."):
        """
        Take appropriate action if parsing of data stream fails.

        :param message: Warning or error message string.
        """
        if self.on_error == "raise":
            raise RuntimeError(message)
        if self.on_error == "warn":
            warnings.warn(message)
        # Discard first byte of buffer, it might decode better now...
        self.buf = self.buf[1:]

    def __next__(self):
        # Basic message packet is 6 bytes, try to fill buffer to at least that size
        if len(self.buf) < 6:
            self.buf += self._file.read(6 - len(self.buf))
        # Hopefully enough data in buffer now to try to decode a message
        while len(self.buf) >= 6:
            # Look at first two bytes and ensure they look like a message ID we recognise
            msgid, length = struct.unpack_from("<HH", self.buf)
            if not msgid in id_to_func:
                self._decoding_error(f"Invalid message with id={msgid:#x}")
                continue
            # Looks like a message, now check the source and destination locations
            long_form = self.buf[4] & 0x80  # Check MSB of byte 4 for "long form" flag
            dest = self.buf[4] & ~0x80      # Destination is remaining lower bits
            source = self.buf[5]
            # Destination should be the Host, source should be a recognised controller ID
            if not ((dest in (0x00, 0x01)) and (source in (0x00, 0x11, 0x21, 0x22, 0x23, 0x24, 0x25,
                                                           0x26, 0x27, 0x28, 0x29, 0x2A, 0x50))):
                self._decoding_error("Invalid source or destination for message with id="
                                    f"{msgid:#x}, src={source:#04x}, dest={dest:#04x}")
                continue
            # Message ID, source and dest seem legit, now check long form length
            if long_form:
                # A bad or malicious packet could make us try to read up to 65 kB...
                # Documentation says "currently no datapacket exceeds 255 bytes in length"
                if length > 255:
                    self._decoding_error(f"Invalid length={length} for message with id={msgid:#06x},"
                                         f" src={source:#04x}, dest={dest:#04x}")
                    continue
            else:
                # Length field is actually two parameters in short form messages
                length = 0
            # Either short form message, or long form message of reasonable size
            # Looks good! Break from loop and proceed
            break                    
        # If we got here, either the buffer was/shrank too small,
        # or we have the start of something that looks like a valid message
        if len(self.buf) < 6:
            # Not enough data to form a message packet
            raise StopIteration
        # Buffer contains enough for a short message, but maybe not a long form one
        if len(self.buf) < length + 6:
            # Not enough data in buffer to decode long form message, attempt to read some more data
            self.buf += self._file.read(length - len(self.buf) + 6)
            if len(self.buf) < length + 6:
                # Still didn't receive enough data to decode message
                raise StopIteration
        # Have enough data in buffer to decode the full message
        data = self.buf[:length + 6]
        # Can now remove the message data from the buffer
        self.buf = self.buf[length + 6:]
        # Decode the message contents
        dict_ = id_to_func[msgid](data)
        return namedtuple(dict_["msg"], dict_.keys())(**dict_)

    def __aiter__(self):
        return self

    async def __anext__(self):
        while True:
            try:
                return next(self)
            except StopIteration:
                await asyncio.sleep(0.001)

    def feed(self, data: bytes):
        """
        Add byte data to the input stream.

        The input stream must support random access, if it does not, must be fed externally
        (e.g. serial port data).

        :param data: Byte array containing data to add.
        """
        pos = self._file.tell()
        self._file.seek(0, 2)
        self._file.write(data)
        self._file.seek(pos)
