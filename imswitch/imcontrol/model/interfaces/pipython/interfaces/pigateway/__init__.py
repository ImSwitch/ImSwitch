#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Collection of libraries to use PI controllers and process GCS data."""

import warnings
# Wildcard import pipython.pidevice.interfaces.pigateway pylint: disable=W0401
from pipython.pidevice.interfaces.pigateway import *

warnings.warn("Please use 'pipython.pidevice.interfaces.pigateway' instead", DeprecationWarning)

__all__ = ['PIGateway']

__signature__ = 0xcca0e8699c57b617e35b0767f3136290
