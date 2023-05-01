#!/usr/bin python
# -*- coding: utf-8 -*-
"""Provide GCSError defines and GCSError exception class."""
# too many lines in module pylint: disable=C0302
# line too long pylint: disable=C0301


__signature__ = 0x59d4981f571d3e5b1eba375f320e2ebb



class PIErrorBase(Exception):
    """GCSError exception."""

    PI_NO_ERROR = 0

    def __init__(self, value, message=''):
        """GCSError exception.
        @param value : Error value as integer.
        @param message : Optional message to show in exceptions string representation.
        """
        Exception.__init__(self)
        if isinstance(value, PIErrorBase):
            self.val = value.val
            self.msg = value.msg
        else:
            self.val = value
            self.msg = self.translate_error(value)
        if message:
            self.msg += ': %r' % message

    def __str__(self):
        return self.msg

    def __repr__(self):
        return self.msg

    def __eq__(self, other):
        return self.val == other

    def __hash__(self):
        return hash(self.val)

    def __ne__(self, other):
        return self.val != other

    @staticmethod
    def translate_error(value):
        """Return a readable error message of 'value'.
        @param value : Error value as integer.
        @return : Error message as string if 'value' was an integer else 'value' itself.
        """
        return str(value)
