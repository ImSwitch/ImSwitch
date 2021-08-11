import re
import sys
import traceback

from imswitch.imcommon.model import initLogger


def joinModulePath(segment1, segment2):
    """ Joins two module path segments, e.g. "imswitch.imcommon.model" and
    "pythontools" into "imswitch.imcommon.model.pythontools", with security
    checks. """

    if not isinstance(segment1, str) or not isinstance(segment2, str):
        raise TypeError('Module path segments must be strings')

    if not segment1.endswith('.'):
        segment1 += '.'

    joinedPath = segment1 + segment2
    if ('..' in joinedPath or not joinedPath.startswith(segment1)
            or bool(re.search('[^A-z0-9.]', joinedPath))):
        raise ValueError('Module path segments include ".." or invalid characters')

    return joinedPath


def installExceptHook():
    if not (hasattr(sys.excepthook, 'implements')
            and sys.excepthook.implements('ExceptionHandler')):
        sys.excepthook = ExceptionHandler()


class ExceptionHandler:
    """ This class is based on PyQtGraph's ExceptionHandler and will override
    it in practice. """

    def __init__(self):
        self.__logger = initLogger(self)

    def __call__(self, *args):
        recursionLimit = sys.getrecursionlimit()
        try:
            sys.setrecursionlimit(recursionLimit + 100)
            self.__logger.error(''.join(traceback.format_exception(*args)))
        finally:
            sys.setrecursionlimit(recursionLimit)

    def implements(self, interface=None):
        if interface is None:
            return ['ExceptionHandler']
        else:
            return interface == 'ExceptionHandler'


# Copyright (C) 2020, 2021 TestaLab
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
