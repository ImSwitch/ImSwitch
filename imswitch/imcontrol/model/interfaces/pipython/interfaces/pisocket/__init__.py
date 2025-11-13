#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Collection of libraries to use PI controllers and process GCS data."""

import warnings
# Wildcard import pipython.pidevice.interfaces.pisocket pylint: disable=W0401
from pipython.pidevice.interfaces.pisocket import *

warnings.warn("Please use 'pipython.pidevice.interfaces.pisocket' instead", DeprecationWarning)

__all__ = ['PISocket']

__signature__ = 0x874d9b1e6a272641b5525a18e30cd747
