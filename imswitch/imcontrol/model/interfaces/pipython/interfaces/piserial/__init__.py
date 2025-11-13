#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Collection of libraries to use PI controllers and process GCS data."""

import warnings
# Wildcard import pipython.pidevice.interfaces.piserial pylint: disable=W0401
from pipython.pidevice.interfaces.piserial import *

warnings.warn("Please use 'pipython.pidevice.interfaces.piserial' instead", DeprecationWarning)

__all__ = ['PISerial']

__signature__ = 0xfe1208deaa1f62021f2d00f9a45892cc
