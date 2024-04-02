import json
import h5py

from imswitch.imcommon.framework import Signal, SignalInterface


class SharedAttributes(SignalInterface):
    sigAttributeSet = Signal(object, object)  # (key, value)

    def __init__(self):
        super().__init__()
        self._data = {}

    def getHDF5Attributes(self):
        """ Returns a dictionary of HDF5 attributes representing this object.
        """
        attrs = {}
        for key, value in self._data.items():
            if not h5py.check_dtype_serializable(type(value)):
                print(value, type(value))
                continue
            attrs[':'.join(key)] = value

        return attrs

    def getJSON(self):
        """ Returns a JSON representation of this instance. """
        attrs = {}
        for key, value in self._data.items():
            if not self.is_jsonable(value):
                continue
            parent = attrs
            for i in range(len(key) - 1):
                if key[i] not in parent:
                    parent[key[i]] = {}
                parent = parent[key[i]]

            parent[key[-1]] = value

        return json.dumps(attrs)

    def is_jsonable(self, x):
        try:
            json.dumps(x)
            return True
        except (TypeError, OverflowError):
            print(x, type(x))
            return False

    def update(self, data):
        """ Updates this object with the data in the given dictionary or
        SharedAttributes object. """
        if isinstance(data, SharedAttributes):
            data = data._data

        for key, value in data.items():
            self[key] = value

    def __getitem__(self, key):
        self._validateKey(key)
        return self._data[key]

    def __setitem__(self, key, value):
        self._validateKey(key)
        self._data[key] = value
        self.sigAttributeSet.emit(key, value)

    def __iter__(self):
        yield from self._data.items()

    @classmethod
    def fromHDF5File(cls, file, dataset):
        """ Loads the attributes from a HDF5 file into a SharedAttributes
        object. """
        attrs = cls()
        for key, value in file[dataset].attrs.items():
            keyTuple = tuple(key.split(':'))
            attrs[keyTuple] = value
        return attrs

    @staticmethod
    def _validateKey(key):
        if type(key) is not tuple:
            raise TypeError('Key must be a tuple of strings')

        for keySegment in key:
            if not isinstance(keySegment, str):
                raise TypeError('Key must be a tuple of strings')

            if ':' in keySegment:
                raise KeyError('Key must not contain ":"')


# Copyright (C) 2020-2021 ImSwitch developers
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
