#!/usr/bin/env python
# -*- coding: utf-8 -*-


class IC_Exception(Exception):
    """
    An exception for the IC imaging control software. It contains a message
    property which is a string indicating what went wrong.
    
    error code -3 has multiple possible interpretations, sometimes from the same function!
    
    :param errorCode: Error code to be used to look up error message.
    """

    @property
    def message(self):
        return self._error_codes[self.error_code]
            
    @property
    def error_code(self):
        return self._error_code
        
    _error_codes = {
        # IC errors
        1: 'IC SUCCESS',
        0: 'IC ERROR',
        -1: 'IC NO HANDLE',
        -2: 'IC NO DEVICE',
        -3: 'IC NOT AVAILABLE / IC NO PROPERTYSET / IC DEFAULT WINDOW SIZE SET / IC NOT IN LIVEMODE',
        -4: 'IC PROPERTY ITEM NOT AVAILABLE',
        -5: 'IC PROPERTY ELEMENT NOT AVAILABLE',
        -6: 'IC PROPERTY ELEMENT WRONG INTERFACE',

        # other errors
        -100: 'UNKNOWN ERROR',
        -101: 'UNKNOWN DEVICE FEATURE',
        -102: 'VIDEO NORM INDEX OUT OF RANGE',
        -103: 'VIDEO FORMAT INDEX OUT OF RANGE',
        -104: 'VIDEO NORM RETURNED NULL TYPE',
        -105: 'VIDEO FORMAT RETURNED NULL TYPE',
        -106: 'DEVICE NAME NOT FOUND'
    }
    
    def __init__(self, error_code):
        # if error code does not match expected codes then assign invalid code
        if error_code in self._error_codes:
            self._error_code = error_code
        else:
            self._error_code = -100


# MIT License
#
# Copyright (c) 2017 morefigs
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
