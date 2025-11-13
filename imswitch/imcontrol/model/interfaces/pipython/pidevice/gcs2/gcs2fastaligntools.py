#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tools for using the fast alignment routines of a PI device."""

from __future__ import print_function
from time import sleep, time
from ...pitools import waitonready, isdeviceavailable
from ... import GCS2Commands

__signature__ = 0x7ddd91ffdf166556ff8118bcb68ad853

# Too many arguments (6/5) pylint: disable=R0913
def waitonalign(pidevice, routines=None, timeout=60, predelay=0, postdelay=0, polldelay=0.1):
    """Wait until all fast align 'routines' are finished, i.e. do not run or are paused.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param routines : Name of the routines as int, string or list, or None to wait for all routines.
    @param timeout : Timeout in seconds as float, defaults to 60 seconds.
    @param predelay : Time in seconds as float until querying any state from controller.
    @param postdelay : Additional delay time in seconds as float after reaching desired state.
    @param polldelay : Delay time between polls in seconds as float.
    """
    if not isdeviceavailable([GCS2Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    waitonready(pidevice, timeout, predelay)
    maxtime = time() + timeout
    while 2 in list(pidevice.qFRP(routines).values()):
        if time() > maxtime:
            raise SystemError('waitonalign() timed out after %.1f seconds' % timeout)
        sleep(polldelay)
    sleep(postdelay)
