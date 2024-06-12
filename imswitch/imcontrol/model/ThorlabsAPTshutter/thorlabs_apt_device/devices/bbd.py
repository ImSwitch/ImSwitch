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

__all__ = ["BBD201", "BBD202", "BBD203"]

from .. import protocol as apt
from .aptdevice_motor import APTDevice_BayUnit
from ..enums import EndPoint


class BBD201(APTDevice_BayUnit):
    """
    A class for ThorLabs APT device model BBD201.

    It is based off :class:`APTDevice_BayUnit` configured with a single channel and the the BBD serial number
    preset in the initialisation method.

    :param serial_port: Serial port device the device is connected to.
    :param vid: Numerical USB vendor ID to match.
    :param pid: Numerical USB product ID to match.
    :param manufacturer: Regular expression to match to a device manufacturer string.
    :param product: Regular expression to match to a device product string.
    :param serial_number: Regular expression matching the serial number of device to search for.
    :param location: Regular expression to match to a device bus location.
    :param home: Perform a homing operation on initialisation.
    :param invert_direction_logic: Invert the meaning of "forward" and "reverse" directions.
    :param swap_limit_switches: Swap "forward" and "reverse" limit switch values.
    """
    def __init__(self, serial_port=None, vid=None, pid=None, manufacturer=None, product=None, serial_number="73", location=None, home=True, invert_direction_logic=False, swap_limit_switches=True):

        super().__init__(serial_port=serial_port, vid=vid, pid=pid, manufacturer=manufacturer, product=product, serial_number=serial_number, location=location, x=1, home=home, invert_direction_logic=invert_direction_logic, swap_limit_switches=swap_limit_switches, status_updates="auto")


class BBD202(APTDevice_BayUnit):
    """
    A class for ThorLabs APT device model BBD202.

    It is based off :class:`BBD_BSC` configured with two channels and the the BBD serial number
    preset in the initialisation method.

    :param serial_port: Serial port device the device is connected to.
    :param vid: Numerical USB vendor ID to match.
    :param pid: Numerical USB product ID to match.
    :param manufacturer: Regular expression to match to a device manufacturer string.
    :param product: Regular expression to match to a device product string.
    :param serial_number: Regular expression to match to a device serial number.
    :param home: Perform a homing operation on initialisation.
    :param invert_direction_logic: Invert the meaning of "forward" and "reverse" directions.
    :param swap_limit_switches: Swap "forward" and "reverse" limit switch values.
    """
    def __init__(self, serial_port=None, vid=None, pid=None, manufacturer=None, product=None, serial_number="73", location=None, home=True, invert_direction_logic=False, swap_limit_switches=True):

        super().__init__(serial_port=serial_port, vid=vid, pid=pid, manufacturer=manufacturer, product=product, serial_number=serial_number, location=location, x=2, home=home, invert_direction_logic=invert_direction_logic, swap_limit_switches=swap_limit_switches, status_updates="auto")


class BBD203(APTDevice_BayUnit):
    """
    A class for ThorLabs APT device model BBD203.

    It is based off :class:`BBD_BSC` configured with three channels and the the BBD serial number
    preset in the initialisation method.

    :param serial_port: Serial port device the device is connected to.
    :param vid: Numerical USB vendor ID to match.
    :param pid: Numerical USB product ID to match.
    :param manufacturer: Regular expression to match to a device manufacturer string.
    :param product: Regular expression to match to a device product string.
    :param serial_number: Regular expression to match to a device serial number.
    :param home: Perform a homing operation on initialisation.
    :param invert_direction_logic: Invert the meaning of "forward" and "reverse" directions.
    :param swap_limit_switches: Swap "forward" and "reverse" limit switch values.
    """
    def __init__(self, serial_port=None, vid=None, pid=None, manufacturer=None, product=None, serial_number="73", location=None, home=True, invert_direction_logic=False, swap_limit_switches=True):

        super().__init__(serial_port=serial_port, vid=vid, pid=pid, manufacturer=manufacturer, product=product, serial_number=serial_number, location=location, x=3, home=home, invert_direction_logic=invert_direction_logic, swap_limit_switches=swap_limit_switches, status_updates="auto")

