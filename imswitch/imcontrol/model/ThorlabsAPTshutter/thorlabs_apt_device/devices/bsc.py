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

__all__ = ["BSC", "BSC201", "BSC201_DRV250"]

from .. import protocol as apt
from .aptdevice_motor import APTDevice_BayUnit
from ..enums import EndPoint

class BSC(APTDevice_BayUnit):
    """
    A class for the BSC10x and BSC20x series of Thorlabs APT controllers.

    It is based off
    :class:`~thorlabs_apt_device.devices.aptdevice_motor.APTDevice_BayUnit` with the
    addition of the control loop parameters used for encoded stages.

    Note that it seems (at least some of) the BSC series will send automatic status updates, but
    they do not support the corresponding acknowledgement message, and so will stop responding after
    ~5 seconds due to the lack of acknowledgement from the host. As a workaround, the status of the
    device will be polled.

    Additionally, it seems that the initial movement and homing velocities can be effectively zero,
    making it seem like the device is not working, though it is actually just moving extremely
    slowly. It's a good idea to ensure sensible values are set for
    :meth:`~thorlabs_apt_device.devices.aptdevice_motor.APTDevice_Motor.set_velocity_params`,
    :meth:`~thorlabs_apt_device.devices.aptdevice_motor.APTDevice_Motor.set_jog_params` and
    :meth:`~thorlabs_apt_device.devices.aptdevice_motor.APTDevice_Motor.set_home_params` during
    initialisation. What values qualify as "sensible" will depend on the particular stepper and
    stage being controlled. For example, the DRV250 actuator has 409600 microsteps/mm, 21987328
    microsteps/mm/s, and 4506 microsteps/mm/s/s. Thus, using ``acceleration=4506`` and
    ``max_velocity=21987328`` in
    :meth:`~thorlabs_apt_device.devices.aptdevice_motor.APTDevice_Motor.set_velocity_params` would
    result in a movement speed of 1 mm/s and an acceleration of 1 mm/s/s. Consult the `APT
    Communications Protocol
    <https://www.thorlabs.com/Software/Motion%20Control/APT_Communications_Protocol.pdf>`__ PDF
    document on the Thorlabs website for parameters for a specific stage.

    :param serial_port: Serial port device the device is connected to.
    :param vid: Numerical USB vendor ID to match.
    :param pid: Numerical USB product ID to match.
    :param manufacturer: Regular expression to match to a device manufacturer string.
    :param product: Regular expression to match to a device product string.
    :param serial_number: Regular expression matching the serial number of device to search for.
    :param location: Regular expression to match to a device bus location.
    :param x: Number of channels the device controls (the x in BSC20x).
    :param home: Perform a homing operation on initialisation.
    :param invert_direction_logic: Invert the meaning of "forward" and "reverse" directions.
    :param swap_limit_switches: Swap "forward" and "reverse" limit switch values.
    """
    def __init__(self, serial_port=None, vid=None, pid=None, manufacturer=None, product=None, serial_number=None, location=None, home=True, x=1, invert_direction_logic=False, swap_limit_switches=True):

        super().__init__(serial_port=serial_port, vid=vid, pid=pid, manufacturer=manufacturer, product=product, serial_number=serial_number, location=location, home=home, x=x, invert_direction_logic=invert_direction_logic, swap_limit_switches=swap_limit_switches, status_updates="polled")

        self.loopparams_ = [[{
            "loop_mode": 0,
            "prop": 0,
            "int": 0,
            "diff": 0,
            "pid_clip": 0,
            "pid_tol": 0,
            "encoder_const": 0,
            # Update message fields
            "msg" : "",
            "msgid" : 0,
            "source" : 0,
            "dest" : 0,
            "chan_ident" : 0,
        } for _ in self.channels] for _ in self.bays]
        """
        Parameters for the closed-loop position control for encoded stages.

        Fields are ``"loop_mode"``, ``"prop"``, ``"int"``, ``"diff"``, ``"pid_clip"``, ``"pid_tol"``, and ``"encoder_const"``.
        """
        # Request current control loop parameters
        for bay in self.bays:
            for channel in self.channels:
                self._loop.call_soon_threadsafe(self._write, apt.mot_req_kcubekstloopparams(source=EndPoint.HOST, dest=bay, chan_ident=channel))

        self.powerparams_ = [[{
            "rest_factor": 0,
            "move_factor": 0,
            # Update message fields
            "msg" : "",
            "msgid" : 0,
            "source" : 0,
            "dest" : 0,
            "chan_ident" : 0,
        } for _ in self.channels] for _ in self.bays]
        """
        Parameters for the motor power parameters.

        Fields are ``"rest_factor"`` and ``"move_factor"``.
        """
        # Request current motor power parameters
        for bay in self.bays:
            for channel in self.channels:
                self._loop.call_soon_threadsafe(self._write, apt.mot_req_powerparams(source=EndPoint.HOST, dest=bay, chan_ident=channel))

        if x == 1:
            self.loopparams = self.loopparams_[0][0]
            """Alias to first bay/channel of :data:`loopparams_`."""
            self.powerparams = self.powerparams_[0][0]
            """Alias to first bay/channel of :data:`powerparams`."""

    def _process_message(self, m):
        super()._process_message(m)

        # Decode bay and channel IDs and check if they match one of ours
        if m.msg in ("mot_get_kcubekstloopparams", "mot_get_powerparams"):
            # Check if source matches one of our bays
            try:
                bay_i = self.bays.index(m.source)
            except ValueError:
                # Ignore message from unknown bay id
                self._log.warn(f"Message {m.msg} has unrecognised source={m.source}.")
                bay_i = 0
            # Check if channel matches one of our channels
            try:
                channel_i = self.channels.index(m.chan_ident)
            except ValueError:
                # Ignore message from unknown channel id
                self._log.warn(f"Message {m.msg} has unrecognised channel={m.chan_ident}.")
                channel_i = 0
        
        if m.msg == "mot_get_kcubekstloopparams":
            # Control loop update message
            self.loopparams_[bay_i][channel_i].update(m._asdict())
        elif m.msg == "mot_get_powerparams":
            # Motor power update message
            self.powerparams_[bay_i][channel_i].update(m._asdict())


    def set_loop_params(self, loop_mode=None, prop=None, integral=None, diff=None, pid_clip=None, pid_tol=None, encoder_const=None, bay=0, channel=0):
        """
        Configure the closed-loop positioning parameters used by encoded stages.

        The closed-loop control algorithm is a PID style. Note that the keyword parameter to modify
        the "int" value is named "integral" so as not to confuse it with the python int keyword.

        :param loop_mode: Set to 1 if open-loop, 2 for closed-loop mode.
        :param prop: Coefficient of the proportional gain term.
        :param integral: Coefficient of the integral gain term.
        :param diff: Coefficient of the differential gain term.
        :param pid_clip: Maximum value of the PID algorithm output.
        :param pid_tol: Minimum allowed (non-zero) value of the PID algorithm output.
        :encoder_const: Coefficient to map encoder counts to motor steps.
        """
        if loop_mode is None:
            loop_mode = self.loopparams_[bay][channel]["loop_mode"]
        if prop is None:
            prop = self.loopparams_[bay][channel]["prop"]
        if integral is None:
            integral = self.loopparams_[bay][channel]["int"]
        if diff is None:
            diff = self.loopparams_[bay][channel]["diff"]
        if pid_clip is None:
            pid_clip = self.loopparams_[bay][channel]["pid_clip"]
        if pid_tol is None:
            pid_tol = self.loopparams_[bay][channel]["pid_tol"]
        if encoder_const is None:
            encoder_const = self.loopparams_[bay][channel]["encoder_const"]

        self._log.debug(f"Setting control loop parameters for [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.mot_set_kcubekstloopparams(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], loop_mode=loop_mode, prop=prop, int=integral, diff=diff, pid_clip=pid_clip, pid_tol=pid_tol, encoder_const=encoder_const))
        # Update status with new loop parameters
        self._loop.call_soon_threadsafe(self._write, apt.mot_req_kcubekstloopparams(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel]))


    def set_power_params(self, rest_factor=None, move_factor=None, bay=0, channel=0):
        """
        Configure the motor power parameters used during movement and rest.

        Values are expressed as a percentage between ``0`` and ``100``. Typically move power should
        be set to ``100``, and the rest power reduced to prevent excessive heating of the motor.


        :param rest_factor: Percentage power used when at rest.
        :param move_factor: Percentage power used when moving.
        """
        if rest_factor is None:
            rest_factor = self.loopparams_[bay][channel]["rest_factor"]
        if move_factor is None:
            move_factor = self.loopparams_[bay][channel]["move_factor"]
        
        self._log.debug(f"Setting motor power parameters for [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.mot_set_powerparams(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], rest_factor=rest_factor, move_factor=move_factor))
        # Update status with new power parameters
        self._loop.call_soon_threadsafe(self._write, apt.mot_req_powerparams(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel]))


class BSC201(BSC):
    """
    A class for ThorLabs APT device model BSC201.

    It is based off :class:`BSC`, but looking for a serial number starting with ``"40"`` and setting ``x = 1``.

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
    def __init__(self, serial_port=None, vid=None, pid=None, manufacturer=None, product=None, serial_number="40", location=None, home=True, invert_direction_logic=False, swap_limit_switches=True):

        super().__init__(serial_port=serial_port, vid=vid, pid=pid, manufacturer=manufacturer, product=product, serial_number=serial_number, location=location, x=1, home=home, invert_direction_logic=invert_direction_logic, swap_limit_switches=swap_limit_switches)


class BSC201_DRV250(BSC201):
    """
    A class for ThorLabs APT device model BSC201 with DRV250 stepper-motor-driven actuator, sold as
    a package as the `LNR502 and LNR502E <https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=2297&pn=LNR502E/M>`__.

    It is based off :class:`BSC201`, but with sensible default movement parameters configured for the actuator.

    For the DRV250, there are 409600 microsteps/mm, 21987328 microsteps/mm/s, and 4506 microsteps/mm/s/s.

    For the models with the optical encoder (LNR502E, LNR502E/M), use the parameter
    ``closed_loop=True`` to enable closed-loop positioning. This will configure the controller
    parameters to use feedback from the encoder during positioning. For non-encoded stages, or to
    use open-loop control, this should be set to ``closed_loop=False``.

    :param closed_loop: Boolean to indicate the use of an encoded stage (the "E" in LNR502E) in closed-loop mode, default is False.
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
    def __init__(self, serial_port=None, vid=None, pid=None, manufacturer=None, product=None, serial_number="40", location=None, home=True, invert_direction_logic=False, swap_limit_switches=True, closed_loop=False):

        super().__init__(serial_port=serial_port, vid=vid, pid=pid, manufacturer=manufacturer, product=product, serial_number=serial_number, location=location, home=home, invert_direction_logic=invert_direction_logic, swap_limit_switches=swap_limit_switches)

        # Initial velocity parameters are effectively zero on startup, set something more sensible
        # Homing is initiated 1.0s after init, so hopefully these will take effect before then...
        for bay_i, _ in enumerate(self.bays):
            for channel_i, _ in enumerate(self.channels):
                self.set_velocity_params(acceleration=4506, max_velocity=21987328, bay=bay_i, channel=channel_i)
                self.set_jog_params(size=409600, acceleration=4506, max_velocity=21987328, bay=bay_i, channel=channel_i)
                self.set_home_params(velocity=21987328, offset_distance=20480, bay=bay_i, channel=channel_i)
    
        if closed_loop:
            # Configure some default parameters for the closed-loop positioning routine
            for bay_i, _ in enumerate(self.bays):
                for channel_i, _ in enumerate(self.channels):
                    self.set_loop_params(loop_mode=2, prop=50000, integral=5000, diff=100, pid_clip=16000000, pid_tol=80, encoder_const=4292282941, bay=0, channel=0)
        else:
            # Use open-loop positioning (only using stepper counts)
            for bay_i, _ in enumerate(self.bays):
                for channel_i, _ in enumerate(self.channels):
                    self.set_loop_params(loop_mode=1, prop=0, integral=0, diff=0, pid_clip=0, pid_tol=0, encoder_const=0, bay=0, channel=0)

