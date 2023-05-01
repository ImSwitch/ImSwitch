#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Collection of interfaces to PI controllers."""

# Wildcard import datarectools pylint: disable=W0401
from .datarectools import *

try:
    # Wildcard import pipython.gcs2.gcs2datarectools pylint: disable=W0401
    from pipython.pidevice.gcs2.gcs2datarectools import *
except ImportError:
    pass

try:
    # Wildcard import pipython.gcs21.gcs21datarectools pylint: disable=W0401
    from pipython.pidevice.gcs21.gcs21datarectools import *
except ImportError:
    pass

__signature__ = 0xbc2dc24b47964c8b4739257578e691c4
