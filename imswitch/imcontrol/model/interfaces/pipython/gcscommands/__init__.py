#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Collection of libraries to use PI controllers and process GCS data."""

import warnings
# Wildcard import pipython.pidevice.common.gcscommands_helpers pylint: disable=W0401
from pipython.pidevice.gcscommands import *
# Redefining built-in 'unicode' pylint: disable=W0622
# Redefining built-in 'basestring' pylint: disable=W0622
from pipython.pidevice.common.gcscommands_helpers import *

warnings.warn("Please use 'pipython.pidevice.gcscommands' instead", DeprecationWarning)

__all__ = ['GCSCommands']

__signature__ = 0x1355c2889da4f7f7e9ec8308ed3a815f
