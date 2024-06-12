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

__all__ = ["TDC001"]

from .. import protocol as apt
from .aptdevice_motor import APTDevice_Motor
from ..enums import EndPoint, LEDMode


class TDC001(APTDevice_Motor):
    """
    A class specific to the ThorLabs TDC001 motion controller.

    It is based off :class:`APTDevice_Motor` with some customisation for the specifics of the device.
    For example, the controller is single bay/channel, has inverted direction logic, and has a
    few extra device-specific commands.

    Additionally, as it is a single bay/channel controller, aliases of ``status = status_[0][0]``
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
    def __init__(self, serial_port=None, vid=None, pid=None, manufacturer=None, product=None, serial_number="83", location=None, home=True, invert_direction_logic=True, swap_limit_switches=True):
        super().__init__(serial_port=serial_port, vid=vid, pid=pid, manufacturer=manufacturer, product=product, serial_number=serial_number, location=location, home=home, invert_direction_logic=invert_direction_logic, swap_limit_switches=swap_limit_switches, status_updates="polled", controller=EndPoint.RACK, bays=(EndPoint.BAY0,), channels=(1,))
        
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
        
        self.pidparams = {
            "proportional" : 0,
            "integral" : 0,
            "differential" : 0,
            "integral_limits" : 0,
            "filter_control" : 0,
            # Update message fields
            "msg" : "",
            "msgid" : 0,
            "source" : 0,
            "dest" : 0,
            "chan_ident" : 0,
        }
        """
        Dictionary of PID algorithm parameters.
        
        Keys are ``"proportional"``, ``"integral"``, ``"differential"``, ``"integral_limits"``, and
        ``"filter_control"``.
        """
        # Request current PID parameters
        self._loop.call_soon_threadsafe(self._write, apt.mot_req_dcpidparams(source=EndPoint.HOST, dest=self.bays[0], chan_ident=self.channels[0]))

        self.ledmode = {
            LEDMode.IDENT : False,
            LEDMode.LIMITSWITCH : False,
            LEDMode.MOVING : False,
        }
        """
        Dictionary describing the LED activity mode.
        
        See :class:`LEDMode <thorlabs_apt_device.enums.LEDMode>` for details on the different modes.
        """
        # Request current LED modes
        self._loop.call_soon_threadsafe(self._write, apt.mot_req_avmodes(source=EndPoint.HOST, dest=self.bays[0], chan_ident=self.channels[0]))


    def _process_message(self, m):
        super()._process_message(m)
        if m.msg == "mot_get_dcpidparams":
            self.pidparams.update(m._asdict())
        elif m.msg == "mot_get_avmodes":
            # LED mode parameter update
            self.ledmode.update({
                LEDMode.IDENT : bool(m.mode_bits & LEDMode.IDENT),
                LEDMode.LIMITSWITCH : bool(m.mode_bits & LEDMode.LIMITSWITCH),
                LEDMode.MOVING : bool(m.mode_bits & LEDMode.MOVING),
            })


    def set_led_mode(self, mode_bits, bay=0, channel=0):
        """
        Configure the behaviour of the controller's status LEDs.

        The ``mode_bits`` can be generated by composing values from the :class:`LEDMode <thorlabs_apt_device.enums.LEDMode>` enum.
        For example, ``LEDMode.IDENT | LEDMode.MOVING`` would set the LED to flash when the identify message is sent, and also when the motor is moving.

        :param mode_bits: Integer containing the relevant mode bits.
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        self._log.debug(f"Setting LED mode to mode_bits={mode_bits} [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.mot_set_avmodes(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], mode_bits=mode_bits))
        # Update status with new LED parameters
        self._loop.call_soon_threadsafe(self._write, apt.mot_req_avmodes(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel]))
