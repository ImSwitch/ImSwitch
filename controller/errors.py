# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 19:10:01 2020

@author: andreas.boden
"""


class InvalidChildClassError(Exception):
    """Exception raised when trying to inialize an invalid child"""

    def __init__(self, message):
        self.message = message


class IncompatibilityError(Exception):
    """Exception raised when initialized object is not compatibile with 
    other module/s"""

    def __init__(self, message):
        self.message = message


class NidaqHelperError(Exception):
    """ Exception raised when error occurs in NidaqHelper """

    def __init__(self, message):
        self.message = message
