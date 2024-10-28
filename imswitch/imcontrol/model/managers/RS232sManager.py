from .MultiManager import MultiManager


class RS232sManager(MultiManager):
    """ RS232sManager is an interface for dealing with RS232 devices. It is a
    MultiManager for RS232 devices.

    RS232Manager instances for individual RS232 devices can be accessed by
    ``rs232sManager['your_rs232_device_name']``. """

    def __init__(self, rs232deviceInfos, **lowLevelManagers):
        super().__init__(rs232deviceInfos, 'rs232', **lowLevelManagers)


# Copyright (C) 2020-2023 ImSwitch developers
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
