from dataclasses import dataclass
from typing import Optional


@dataclass
class ScriptEntry:
    filePath: Optional[str]
    code: str = ''
    unsaved: bool = False

    def isSavedToFile(self):
        """ Returns whether this script entry has been saved to a file. """
        return self.filePath is not None

    def save(self):
        """ Saves this script entry to a file. If it has not been saved to a
        file previously, a RuntimeError will be raised. """
        if not self.isSavedToFile():
            raise RuntimeError('Cannot save, no file path set in entry')

        with open(self.filePath, 'w', newline='\n') as file:
            file.write(self.code)

        self.unsaved = False

    @classmethod
    def loadFromFile(cls, filePath):
        """ Creates a ScriptEntry from the file at the specified path. """
        with open(filePath) as file:
            code = file.read()

        return cls(filePath=filePath, code=code)


class ScriptStore:
    def __init__(self):
        self._entries = {}  # { ID: entry }

    def __getitem__(self, key):
        return self._entries[key]

    def __setitem__(self, key, entry):
        self._entries[key] = entry

    def __delitem__(self, key):
        del self._entries[key]

    def __contains__(self, key):
        return key in self._entries

    def __iter__(self):
        yield from self._entries.items()


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
