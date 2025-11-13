#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Collection of libraries to use PI controllers and process GCS data."""

import warnings
# Wildcard import pipython.pidevice.gcserror pylint: disable=W0401
from pipython.pidevice.gcserror import *

warnings.warn("Please use 'pipython.pidevice.gcserror' instead", DeprecationWarning)

__all__ = ['GCSError']

__signature__ = 0xd0ac5fff7ef5b0e006e959b7755d01c3
