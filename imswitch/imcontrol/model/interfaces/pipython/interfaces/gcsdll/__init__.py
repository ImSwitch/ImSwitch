#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Collection of libraries to use PI controllers and process GCS data."""

import warnings
# Wildcard import pipython.pidevice.interfaces.gcsdll pylint: disable=W0401
from pipython.pidevice.interfaces.gcsdll import *

warnings.warn("Please use 'pipython.pidevice.interfaces.gcsdll' instead", DeprecationWarning)

__all__ = ['GCSDll']

__signature__ = 0xfe7a64230a066b15f72775cd1732d381
