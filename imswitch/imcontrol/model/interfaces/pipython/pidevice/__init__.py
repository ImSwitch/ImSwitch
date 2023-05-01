#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Collection of libraries to use PI controllers and process GCS data."""

from . import gcserror
from .gcserror import GCSError

try:
    from .gcs2.gcs2commands import GCS2Commands
except ImportError:
    GCS2Commands = None

try:
    from .gcs2.gcs2device import GCS2Device
except ImportError:
    GCS2Device = None

try:
    from .gcs21.gcs21commands import GCS21Commands
except ImportError:
    GCS21Commands = None

try:
    from .gcs21.gcs21device import GCS21Device
except ImportError:
    GCS21Device = None

try:
    from .gcs21.gcs21commands_helpers import isgcs21
except ImportError:
    def isgcs21(_gcsmessages):
        """
        dummy function
        """
        return False
try:
    from pipython.pidevice.gcs21.umf_framework.umfcommands.umfcommands_gcs21 import UMFCommandsGCS21
except ImportError:
    UMFCommandsGCS21 = None

try:
    from .gcs21.gcs21error import GCS21Error
except ImportError:
    GCS21Error = None

from .gcsdevice import GCSDevice

__all__ = ['GCSDevice', 'GCS2Device', 'GCS21Device', 'GCS2Commands', 'GCS21Commands', 'UMFCommandsGCS21', 'isgcs21']

__signature__ = 0xa472f4b9a033ddb6615052f0067c7954
