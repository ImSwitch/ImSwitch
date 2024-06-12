# Copyright 2021 Patrick C. Tapping
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Python interface to ThorLabs devices which use the APT protocol.

Note that everything important from the submodules is imported directly here to the main package.
This means you may use code like ``from thorlabs_apt_device import APTDevice`` (instead of
using the full ``from thorlabs_apt_device.devices.aptdevice import APTDevice`` or similar).
"""

__version__ = "0.3.8"

from .devices import *
from .enums import *
from .utils import *
