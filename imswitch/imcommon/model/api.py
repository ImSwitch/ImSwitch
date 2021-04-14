from dotmap import DotMap


def APIExport(func):
    """ Decorator for methods that should be exported to API. """
    func._APIExport = True
    return func


def generateAPI(objs):
    """ Generates an API from APIExport-decorated methods in the objects in the
    passed array objs. """

    exportedFuncs = {}
    for obj in objs:
        for subObjName in dir(obj):
            subObj = getattr(obj, subObjName)
            if not callable(getattr(obj, subObjName)):
                continue

            if not hasattr(subObj, '_APIExport') or not subObj._APIExport:
                continue

            if subObjName in exportedFuncs:
                raise NameError(f'API method name "{subObjName}" is already in use')

            exportedFuncs[subObjName] = subObj

    return DotMap(exportedFuncs)


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
