#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Collection of interfaces to PI controllers."""

# Wildcard import fastaligntools pylint: disable=W0401
from .fastaligntools import *

try:
    # Wildcard import pipython.gcs2.gcs2fastaligntools pylint: disable=W0401
    from pipython.pidevice.gcs2.gcs2fastaligntools import *
except ImportError:
    pass

try:
    # Wildcard import pipython.gcs21.gcs21fastaligntools pylint: disable=W0401
    from pipython.pidevice.gcs21.gcs21fastaligntools import *
except ImportError:
    pass

__signature__ = 0xa82491ba335cf068d2420d7d896aa388
