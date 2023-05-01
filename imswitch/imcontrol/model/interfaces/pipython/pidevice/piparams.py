#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Collection of helpers for handling PI device parameters."""

from . import GCSError, gcserror

__signature__ = 0x1bc3317c79e207983e9c8ebf5487f03c


def applyconfig(pidevice, axis, config, andsave=False):
    """Try to apply 'config' for 'axis' by applyconfig() or CST() function.
    @type pidevice : pipython.gcscommands.GCSDevice
    @param axis: Single axis as string convertible.
    @param config: Name of a configuration existing in PIStages database as string.
    @param andsave: saves the configuration to non volatile memory on the controller.
    @return : Warning as string or empty string on success.
    """
    try:
        pidevice.dll.applyconfig(items='axis %s' % axis, config=config, andsave=andsave)
    except AttributeError:  # function not found in DLL
        if not pidevice.HasCST():
            return 'CST command is not supported'
        pidevice.CST(axis, config)
    except GCSError as exc:
        if exc == gcserror.E_10013_PI_PARAMETER_DB_AND_HPA_MISMATCH_LOOSE:
            del pidevice.axes
            return '%s\n%s' % (exc, pidevice.dll.warning.rstrip())
        raise
    del pidevice.axes
    return ''


def readconfig(pidevice):
    """Try to read available stages by readconfig() or qVST() function.
    @type pidevice : pipython.gcscommands.GCSDevice
    @return : Answer as list of string.
    """
    try:
        answer = pidevice.dll.getconfigs()
    except AttributeError:  # function not found in DLL
        if not pidevice.HasqVST():
            return 'qVST command is not supported'
        answer = pidevice.qVST()
    return answer.split()
