from dataclasses import dataclass
from io import IOBase
from typing import Union

import h5py

from imswitch.imcommon.framework import Signal, SignalInterface


@dataclass
class VFileItem:
    data: Union[IOBase, h5py.File]
    filePath: str
    savedToDisk: bool


class VFileCollection(SignalInterface):
    """ VFileCollection is a collection of virtual file-like objects. In
    addition to holding the data, it also handles saving it to the disk. """

    sigDataSet = Signal(str, VFileItem)  # (name, vFileItem)
    sigDataSavedToDisk = Signal(str, str)  # (name, filePath)
    sigDataWillRemove = Signal(str)  # (name)
    sigDataRemoved = Signal(str)  # (name)

    def __init__(self):
        super().__init__()
        self._data = {}

    def getSavePath(self, name):
        """ Returns the path to which the file associated with the given name
        is saved. """
        return self._data[name].filePath

    def saveToDisk(self, name):
        """ Saves the data with the given name to disk. """
        filePath = self.getSavePath(name)

        if isinstance(self._data[name].data, IOBase):
            with open(filePath, 'wb') as file:
                file.write(self._data[name].data.getbuffer())
        elif isinstance(self._data[name].data, h5py.File):
            with open(filePath, 'wb') as file:
                file.write(self._data[name].data.id.get_file_image())
        else:
            raise TypeError(f'Data has unsupported type "{type(self._data[name].data).__name__}"')

        self.sigDataSavedToDisk.emit(name, filePath)

    def __getitem__(self, name):
        return self._data[name]

    def __setitem__(self, name, value):
        if not isinstance(value, VFileItem):
            raise TypeError('Value must be a VFileItem')

        if name in self._data and self._data[name] != value:
            del self._data[name]

        self._data[name] = value
        self.sigDataSet.emit(name, value)

    def __delitem__(self, name):
        self.sigDataWillRemove.emit(name)
        self._data[name].data.close()
        del self._data[name]
        self.sigDataRemoved.emit(name)

    def __contains__(self, name):
        return name in self._data

    def __iter__(self):
        yield from self._data.items()


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
