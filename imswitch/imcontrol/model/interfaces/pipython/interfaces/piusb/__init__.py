#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Collection of libraries to use PI controllers and process GCS data."""

import warnings
# Wildcard import pipython.pidevice.interfaces.piusb pylint: disable=W0401
from pipython.pidevice.interfaces.piusb import *

warnings.warn("Please use 'pipython.pidevice.interfaces.piusb' instead", DeprecationWarning)

__all__ = ['PIUSB']

__signature__ = 0x9af11ca53559f63ad5ac5d5ad8b85fe8
