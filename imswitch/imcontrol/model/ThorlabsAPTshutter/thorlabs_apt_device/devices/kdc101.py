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

__all__ = ["KDC101"]

from .. import protocol as apt
from .aptdevice_motor import APTDevice_Motor
from ..enums import EndPoint


class KDC101(APTDevice_Motor):
    """
    A class specific to the ThorLabs KDC101 motion controller.

    It can be considered an updated version of the
    :mod:`TDC001 <thorlabs_apt_device.devices.tdc001>`, with the addition of some features like
    external triggering modes.

    Note that the triggering configuration is not yet implemented (see https://gitlab.com/ptapping/thorlabs-apt-device/-/issues/6).

    As it is a single bay/channel controller, aliases of ``status = status_[0][0]``
    etc are created for convenience.

    :param serial_port: Serial port device the device is connected to.
    :param vid: Numerical USB vendor ID to match.
    :param pid: Numerical USB product ID to match.
    :param manufacturer: Regular expression to match to a device manufacturer string.
    :param product: Regular expression to match to a device product string.
    :param serial_number: Regular expression matching the serial number of device to search for.
    :param location: Regular expression to match to a device bus location.
    :param home: Perform a homing operation on initialisation.
    :param invert_direction_logic: Invert the meaning of "forward" and "reverse".
    :param swap_limit_switches: Swap the "forward" and "reverse" limit switch signals.
    """

    def __init__(self, serial_port=None, vid=None, pid=None, manufacturer=None, product=None, serial_number="27",
                 location=None, home=True, invert_direction_logic=True, swap_limit_switches=True):
        super().__init__(serial_port=serial_port, vid=vid, pid=pid, manufacturer=manufacturer, product=product,
                         serial_number=serial_number, location=location, home=home,
                         invert_direction_logic=invert_direction_logic, swap_limit_switches=swap_limit_switches,
                         status_updates="polled", controller=None, bays=(EndPoint.USB,), channels=(1,))

        # Needs DC motor update message (also known as mot_req_ustatusupdate)
        # We'll run polled status update mode as auto updates don't seem to work (on some devices?)
        self.update_message = apt.mot_req_dcstatusupdate

        self.status = self.status_[0][0]
        """Alias to first bay/channel of :data:`~thorlabs_apt_device.devices.aptdevice_motor.APTDevice_Motor.status_`."""

        self.velparams = self.velparams_[0][0]
        """Alias to first bay/channel of :data:`~thorlabs_apt_device.devices.aptdevice_motor.APTDevice_Motor.velparams_`"""

        self.homeparams = self.homeparams_[0][0]
        """Alias to first bay/channel of :data:`~thorlabs_apt_device.devices.aptdevice_motor.APTDevice_Motor.homeparams_`"""

        self.genmoveparams = self.genmoveparams_[0][0]
        """Alias to first bay/channel of :data:`~thorlabs_apt_device.devices.aptdevice_motor.APTDevice_Motor.genmoveparams_`"""

        self.jogparams = self.jogparams_[0][0]
        """Alias to first bay/channel of :data:`~thorlabs_apt_device.devices.aptdevice_motor.APTDevice_Motor.jogparams_`"""


    def _process_message(self, m):
        super()._process_message(m)
        # Future KDC specific message handling here...

    
    def identify(self, channel=None):
        """
        Flash the device's front panel LED to identify the unit.

        Note that for the KDC101 the correct channel is always used and the value of the passed parameter is ignored.

        :param channel: Parameter has no function on the KDC101.
        """
        self._log.debug("Identifying [channel=None].")
        self._loop.call_soon_threadsafe(self._write, apt.mod_identify(source=EndPoint.HOST, dest=EndPoint.USB, chan_ident=0))
        