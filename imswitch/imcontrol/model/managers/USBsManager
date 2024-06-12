from .MultiManager import MultiManager


class USBManager(MultiManager):
    """ USBManager is an interface for dealing with USB devices. It is a
    MultiManager for USB devices.

    USBManager instances for individual USB devices can be accessed by
    ``usbManager['your_usb_device_name']``. """

    def __init__(self, usbdeviceInfos, **lowLevelManagers):
        super().__init__(usbdeviceInfos, 'usb', **lowLevelManagers)


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
