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

__all__ = ["APTDevice_Motor", "APTDevice_Motor_Trigger", "APTDevice_BayUnit"]

from .. import protocol as apt
from .aptdevice import APTDevice
from ..enums import EndPoint

class APTDevice_Motor(APTDevice):
    """
    Initialise and open serial device for a ThorLabs APT controller based on a DC motor drive,
    such as a linear translation stage.

    :param serial_port: Serial port device the device is connected to.
    :param vid: Numerical USB vendor ID to match.
    :param pid: Numerical USB product ID to match.
    :param manufacturer: Regular expression to match to a device manufacturer string.
    :param product: Regular expression to match to a device product string.
    :param serial_number: Regular expression to match to a device serial number.
    :param location: Regular expression to match to a device bus location.
    :param home: Perform a homing operation on initialisation.
    :param invert_direction_logic: Invert the meaning of "forward" and "reverse".
    :param swap_limit_switches: Swap "forward" and "reverse" limit switch values.
    :param status_updates: Set to ``"auto"``, ``"polled"`` or ``"none"``.
    :param controller: The destination :class:`EndPoint <thorlabs_apt_device.enums.EndPoint>` for the controller.
    :param bays: Tuple of :class:`EndPoint <thorlabs_apt_device.enums.EndPoint>`\\ (s) for the populated controller bays.
    :param channels: Tuple of indices (1-based) for the controller bay's channels.
    """

    def __init__(self, serial_port=None, vid=None, pid=None, manufacturer=None, product=None, serial_number=None, location=None, home=True, invert_direction_logic=False, swap_limit_switches=False, status_updates="none", controller=EndPoint.RACK, bays=(EndPoint.BAY0,), channels=(1,)):

        super().__init__(serial_port=serial_port, vid=vid, pid=pid, manufacturer=manufacturer, product=product, serial_number=serial_number, location=location, controller=controller, bays=bays, channels=channels, status_updates=status_updates)

        self.invert_direction_logic = invert_direction_logic
        """
        On some devices, "forward" velocity moves towards negative encoder counts.
        If that seems opposite to what is expected, this flag allows inversion of that logic.
        This will also swap the meaning of the ``"moving_forward"`` and ``"moving_reverse"`` 
        fields in the :data:`status_` flags.
        """

        self.swap_limit_switches = swap_limit_switches
        """
        On some devices, the "forward" limit switch triggers when hitting the limit in the negative
        encoder count direction, and the "reverse" limit switch triggers towards positive encoder 
        counts.
        If that seems opposite to what is expected, this flag swaps the values of the
        ``"forward_limit_switch"`` and ``"reverse_limit_switch"`` fields in the :data:`status`
        flags.

        Note that this is independent of :data:`invert_direction_logic`.
        A stage may report it is "moving forward" (towards either positive or negative encoder
        counts), and then trigger the "reverse" limit switch.
        """

        self.status_ = [[{
            "position" : 0,
            "enc_count" : 0,
            "velocity": 0.0,
            "forward_limit_switch" : False,
            "reverse_limit_switch" : False,
            "moving_forward" : False,
            "moving_reverse" : False,
            "jogging_forward" : False,
            "jogging_reverse" : False,
            "motor_connected" : False,
            "homing" : False,
            "homed" : False,
            "tracking" : False,
            "interlock" : False,
            "settled" : False,
            "motion_error" : False,
            "motor_current_limit_reached" : False,
            "channel_enabled" : False,
            # Update message fields
            "msg" : "",
            "msgid" : 0,
            "source" : 0,
            "dest" : 0,
            "chan_ident" : 0,
        } for _ in self.channels] for _ in self.bays]
        """
        Array of dictionaries of status information for the bays and channels of the device.

        As a device may have multiple card bays, each with multiple channels, this data structure
        is an array of array of dicts. The first axis of the array indexes the bay, the second
        indexes the channel.
        For example, stage.status_[0][1] will return the status dictionary for the first bay, second
        channel.

        Keys for the dictionary are ``"position"``, ``"velocity"``, ``"forward_limit_switch"``,
        ``"reverse_limit_switch"``, ``"moving_forward"``, ``"moving_reverse"``,
        ``"jogging_forward"``, ``"jogging_reverse"``, ``"motor_connected"``, ``"homing"``,
        ``"homed"``, ``"tracking"``, ``"interlock"``, ``"settled"``, ``"motion_error"``,
        ``"motor_current_limit_reached"``, and ``"channel_enabled"``.
        Note that not all keys are relevant to every device.
        
        The documentation states that position is measured in encoder counts, but velocity is
        returned in real units of mm/second.

        Additionally, information about the most recent status message which updated the
        dictionary are also available as ``"msgid"``, ``"source"``, ``"dest"``, and
        ``"chan_ident"``.
        """
        # Status updates are received automatically (configured by APTDevice super class)
        
        self.velparams_ = [[{
            "min_velocity" : 0,
            "max_velocity" : 0,
            "acceleration" : 0,
            # Update message fields
            "msg" : "",
            "msgid" : 0,
            "source" : 0,
            "dest" : 0,
            "chan_ident" : 0,
        } for _ in self.channels] for _ in self.bays]
        """
        Array of dictionaries of velocity parameters.

        As a device may have multiple card bays, each with multiple channels, this data structure
        is an array of array of dicts. The first axis of the array indexes the bay, the second
        indexes the channel.

        Keys are ``"min_velocity"``, ``"max_velocity"``, and ``"acceleration"``.
        Units are encoder counts/second for velocities and counts/second/second for acceleration.
        """
        # Request current velocity parameters
        for bay in self.bays:
            for channel in self.channels:
                self._loop.call_soon_threadsafe(self._write, apt.mot_req_velparams(source=EndPoint.HOST, dest=bay, chan_ident=channel))
        

        self.genmoveparams_ = [[{
            "backlash_distance" : 0,
            # Update message fields
            "msg" : "",
            "msgid" : 0,
            "source" : 0,
            "dest" : 0,
            "chan_ident" : 0,
        } for _ in self.channels] for _ in self.bays]
        """
        Array of dictionaries of general move parameters.

        As a device may have multiple card bays, each with multiple channels, this data structure
        is an array of array of dicts. The first axis of the array indexes the bay, the second
        indexes the channel.

        The only documented parameter is the backlash compensation move distance,
        ``"backlash_distance"``, measured in encoder counts.
        """
        # Request current general move parameters
        for bay in self.bays:
            for channel in self.channels:
                self._loop.call_soon_threadsafe(self._write, apt.mot_req_genmoveparams(source=EndPoint.HOST, dest=bay, chan_ident=channel))


        self.jogparams_ = [[{
            "jog_mode" : 0,
            "step_size" : 0,
            "min_velocity" : 0,
            "acceleration" : 0,
            "max_velocity" : 0,
            "stop_mode" : 0,
            # Update message fields
            "msg" : "",
            "msgid" : 0,
            "source" : 0,
            "dest" : 0,
            "chan_ident" : 0,
        } for _ in self.channels] for _ in self.bays]
        """
        Array of dictionaries of jog parameters.

        As a device may have multiple card bays, each with multiple channels, this data structure
        is an array of array of dicts. The first axis of the array indexes the bay, the second
        indexes the channel.

        Keys are ``"jog_mode"``, ``"step_size"``, ``"min_velocity"``, ``"acceleration"``,
        ``"max_velocity"``, and ``"stop_mode"``.
        """
        # Request current jog parameters
        for bay in self.bays:
            for channel in self.channels:
                self._loop.call_soon_threadsafe(self._write, apt.mot_req_jogparams(source=EndPoint.HOST, dest=bay, chan_ident=channel))

        self.homeparams_ = [[{
            "home_dir" : 0,
            "limit_switch" : 0,
            "home_velocity" : 0,
            "offset_distance" : 0
        } for _ in self.channels] for _ in self.bays]
        """
        Array of dictionaries of jog parameters.

        As a device may have multiple card bays, each with multiple channels, this data structure
        is an array of array of dicts. The first axis of the array indexes the bay, the second
        indexes the channel.

        Keys are ``"home_dir"``, ``"limit_switch"``, ``"home_velocity"``, and ``"offset_distance"``.
        """
        # Request current home parameters
        for bay in self.bays:
            for channel in self.channels:
                self._loop.call_soon_threadsafe(self._write, apt.mot_req_homeparams(source=EndPoint.HOST, dest=bay, chan_ident=channel))

        # Home each device if requested
        if home:
            for bay_i, _ in enumerate(self.bays):
                for channel_i, _ in enumerate(self.channels):
                    self.set_enabled(True, bay=bay_i, channel=channel_i)
                    # Sending enabled then home immediately on the TDC001 locks it up.
                    #self.home(bay=bay_i, channel=channel_i)
                    # Instead, initiate homing after some time delay
                    self._loop.call_later(1.0, self.home, bay_i, channel_i)
                    self.status_[bay_i][channel_i]["homing"] = True


    def close(self):
        """
        Stop the device and close the serial connection to the ThorLabs APT controller.
        """
        for bay_i, _ in enumerate(self.bays):
            for channel_i, _ in enumerate(self.channels):
                try:
                    self.stop(bay=bay_i, channel=channel_i)
                except: pass
        super().close()


    def _process_message(self, m):
        super()._process_message(m)
        
        # Decode bay and channel IDs and check if they match one of ours
        if m.msg in ("mot_get_statusupdate", "mot_get_dcstatusupdate", "mot_move_stopped", "mot_move_completed", 
                     "mot_get_velparams",
                     "mot_get_genmoveparams", "mot_genmoveparams",
                     "mot_get_jogparams",
                     "mot_get_homeparams",
                     "mot_get_avmodes"):
            if m.source == EndPoint.USB:
                # Map USB controller endpoint to first bay
                bay_i = 0
            else:
                # Check if source matches one of our bays
                try:
                    bay_i = self.bays.index(m.source)
                except ValueError:
                    # Ignore message from unknown bay id
                    if not m.source == 0:
                        # Some devices return zero as source of move_completed etc
                        self._log.warn(f"Message {m.msg} has unrecognised source={m.source}.")
                    bay_i = 0
                    #return
            # Check if channel matches one of our channels
            try:
                channel_i = self.channels.index(m.chan_ident)
            except ValueError:
                    # Ignore message from unknown channel id
                    self._log.warn(f"Message {m.msg} has unrecognised channel={m.chan_ident}.")
                    channel_i = 0
                    #return
        
        # Act on each message type
        if m.msg in ("mot_get_statusupdate", "mot_get_dcstatusupdate", "mot_move_stopped", "mot_move_completed"):
            # DC motor status update message    
            self.status_[bay_i][channel_i].update(m._asdict())
            # Scale velocity so it should be in mm/second
            # The explanation of scaling in the documentation doesn't make sense, but
            # dividing the returned value by 2.048 seems sensible (or by 2048 to give m/s)
            #self.status_[bay_i][channel_i]["velocity"] /= 2.048
            # Swap meaning of "moving forward" and "moving reverse" if requested
            if self.invert_direction_logic:
                tmp = self.status_[bay_i][channel_i]["moving_forward"]
                self.status_[bay_i][channel_i]["moving_forward"] = self.status_[bay_i][channel_i]["moving_reverse"]
                self.status_[bay_i][channel_i]["moving_reverse"] = tmp
            # Swap values of limit switches if requested
            if self.swap_limit_switches:
                tmp = self.status_[bay_i][channel_i]["forward_limit_switch"]
                self.status_[bay_i][channel_i]["forward_limit_switch"] = self.status_[bay_i][channel_i]["reverse_limit_switch"]
                self.status_[bay_i][channel_i]["reverse_limit_switch"] = tmp
        elif m.msg == "mot_get_velparams":
            # Velocity parameter update
            self.velparams_[bay_i][channel_i].update(m._asdict())
        elif m.msg in ("mot_get_genmoveparams", "mot_genmoveparams"):
            # General move parameter update
            self.genmoveparams_[bay_i][channel_i].update(m._asdict())
        elif m.msg == "mot_get_jogparams":
            # Jog move parameter update
            self.jogparams_[bay_i][channel_i].update(m._asdict())
        elif m.msg == "mot_get_homeparams":
            # Home parameter update
            self.homeparams_[bay_i][channel_i].update(m._asdict())
        else:
            #self._log.debug(f"Received message (unhandled): {m}")
            pass


    def home(self, bay=0, channel=0):
        """
        Home the device.

        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        self._log.debug(f"Homing [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.mot_move_home(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel]))


    def move_relative(self, distance=None, now=True, bay=0, channel=0):
        """
        Perform a relative move.

        :param distance: Movement amount in encoder steps.
        :param now: Perform movement immediately, or wait for subsequent trigger.
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        if now == True:
            self._log.debug(f"Relative move by {distance} steps [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
            self._loop.call_soon_threadsafe(self._write, apt.mot_move_relative(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], distance=distance))
        elif now == False and (not distance is None):
            self._log.debug(f"Preparing relative move by {distance} steps [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
            self._loop.call_soon_threadsafe(self._write, apt.mot_set_moverelparams(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], relative_distance=distance))
        else:
            # Don't move now, and no distance specified...
            self._log.warning("Requested a move_relative with now=False and distance=None: This does nothing!")


    def move_absolute(self, position=None, now=True, bay=0, channel=0):
        """
        Perform an absolute move.

        :param position: Movement destination in encoder steps.
        :param now: Perform movement immediately, or wait for subsequent trigger.
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        if now == True:
            self._log.debug(f"Absolute move to {position} steps [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
            self._loop.call_soon_threadsafe(self._write, apt.mot_move_absolute(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], position=position))
        elif now == False and (not position is None):
            self._log.debug(f"Preparing absolute move to {position} steps [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
            self._loop.call_soon_threadsafe(self._write, apt.mot_set_moveabsparams(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], absolute_position=position))
        else:
            # Don't move now, and no position specified...
            self._log.warning("Requested a move_absolute with now=False and position=None: This does nothing!")


    def stop(self, immediate=False, bay=0, channel=0):
        """
        Stop any current movement.

        :param immediate: Stop immediately, or using the profiled velocity curves.
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        # False == 2 == profiled, True == 1 == immediate
        stop_mode = (2, 1)[bool(immediate)]
        self._log.debug(f"Stopping {'immediately' if stop_mode == 1 else 'profiled'} [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.mot_move_stop(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], stop_mode=stop_mode))
    

    def move_velocity(self, direction="forward", bay=0, channel=0):
        """
        Start a movement at constant velocity in the specified direction.

        Direction can be specified as boolean, string or numerical:
        
            * ``False`` is reverse and ``True`` is forward.
            * ``reverse`` is reverse and any other string is forward.
            * ``0`` or ``2`` (or any even number) is reverse and ``1`` (or any odd number) is forward.

        :param direction: Direction to move (forward or reverse).
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        if type(direction) is bool:
            # False == 2 == reverse, True == 1 == forward
            direction = (2, 1)[direction]
        elif type(direction) is str:
            # forward unless specifically "reverse"
            direction = 2 if direction == "reverse" else 1
        elif type(direction) in (int, float):
            # forward = 1 (or odd numbers), reverse = 0 or 2 (even numbers)
            direction = 2 - int(direction)%2
        else:
            # Otherwise, default to forward
            self._log.warning("Requested a move_velocity with unknown direction \"{direction}\", defaulting to forward.")
            direction = 1
        self._log.debug(f"Velocity move {'forward' if direction == 1 else 'reverse'} [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        # Invert the forward=negative to forward=positive direction logic if requested
        direction = 2 - (direction + bool(self.invert_direction_logic))%2
        self._loop.call_soon_threadsafe(self._write, apt.mot_move_velocity(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], direction=direction))


    def set_velocity_params(self, acceleration, max_velocity, bay=0, channel=0):
        """
        Configure the parameters for movement velocity.

        :param acceleration: Acceleration in counts/second/second.
        :param max_velocity: Maximum velocity in counts/second.
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        self._log.debug(f"Setting velocity parameters to accel={acceleration}, max={max_velocity} [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.mot_set_velparams(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], min_velocity=0, acceleration=acceleration, max_velocity=max_velocity))
        # Update status with new velocity parameters
        self._loop.call_soon_threadsafe(self._write, apt.mot_req_velparams(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel]))


    def set_enabled(self, state=True, bay=0, channel=0):
        """
        Enable or disable a device.

        :param state: Set to ``True`` for enable, ``False`` for disabled.
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        state = (2, 1)[bool(state)]
        self._log.debug(f"Setting channel enabled={state == 1} [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.mod_set_chanenablestate(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], enable_state=state))


    def set_jog_params(self, size, acceleration, max_velocity, continuous=False, immediate_stop=False, bay=0, channel=0):
        """
        Configure the parameters for jogging movements.

        :param size: Size of movement in encoder counts.
        :param acceleration: Acceleration in counts/second/second.
        :param max_velocity: Maximum velocity in counts/second.
        :param continuous: Continuous movement, or single step.
        :param immediate_stop: Stop immediately, or using the profiled velocity curves.
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        # False == 2 == profiled, True == 1 == immediate
        stop_mode = (2, 1)[bool(immediate_stop)]
        # False == 2 == stepped, True == 1 == continuous
        jog_mode = (2, 1)[bool(continuous)]
        self._log.debug(f"Setting jog parameters to size={size}, accel={acceleration}, max={max_velocity}, cont={continuous}, imm={immediate_stop} [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.mot_set_jogparams(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], step_size=size, min_velocity=0, acceleration=acceleration, max_velocity=max_velocity, jog_mode=jog_mode, stop_mode=stop_mode))
        # Update status with new jog parameters
        self._loop.call_soon_threadsafe(self._write, apt.mot_req_jogparams(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel]))


    def move_jog(self, direction="forward", bay=0, channel=0):
        """
        Start a jog movement in the specified direction.

        Direction can be specified as boolean, string or numerical:
        
            * ``False`` is reverse and ``True`` is forward.
            * ``reverse`` is reverse and any other string is forward.
            * ``0`` or ``2`` (or any even number) is reverse and ``1`` (or any odd number) is forward.

        :param direction: Direction to move (forward or reverse).
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        if type(direction) is bool:
            # False == 2 == reverse, True == 1 == forward
            direction = (2, 1)[direction]
        elif type(direction) is str:
            # forward unless specifically "reverse"
            direction = 2 if direction == "reverse" else 1
        elif type(direction) in (int, float):
            # forward = 1 (or odd numbers), reverse = 0 or 2 (even numbers)
            direction = 2 - int(direction)%2
        else:
            # Otherwise, default to forward
            self._log.warning("Requested a move_jog with unknown direction \"{direction}\", defaulting to forward.")
            direction = 1
        self._log.debug(f"Jog move {'forward' if direction == 1 else 'reverse'} [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        # Invert the forward=negative to forward=positive direction logic if requested
        direction = 2 - (direction + bool(self.invert_direction_logic))%2
        self._loop.call_soon_threadsafe(self._write, apt.mot_move_jog(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], direction=direction))


    def set_move_params(self, backlash_distance, bay=0, channel=0):
        """
        Set parameters for generic move commands, currently only the backlash compensation distance.

        :param backlash_distance: Backlash compensation distance in encoder counts.
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        self._log.debug(f"Setting move parameters to backlash={backlash_distance} steps [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.mot_set_genmoveparams(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], backlash_distance=backlash_distance))
        # Update status with new general move parameters
        self._loop.call_soon_threadsafe(self._write, apt.mot_req_genmoveparams(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel]))


    def set_home_params(self, velocity, offset_distance, direction="reverse", bay=0, channel=0):
        """
        Set parameters for homing commands.

        :param velocity: Velocity for homing operations.
        :param offset_distance: Distance of home position from the home limit switch.
        :param direction: Direction for homing movement. Set to ``"forward"`` or ``"reverse"``.
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        if direction == "forward":
            direction = 1
            limit_switch = 4
        else:
            direction = 2
            limit_switch = 1
        self._log.debug(f"Setting home parameters to velocity={velocity}, offset_distance={offset_distance}, direction={direction}, limit_switch={limit_switch} [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.mot_set_homeparams(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], home_dir=direction, limit_switch=limit_switch, home_velocity=velocity, offset_distance=offset_distance))
        # Update status with new home parameters
        self._loop.call_soon_threadsafe(self._write, apt.mot_req_homeparams(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel]))


class APTDevice_Motor_Trigger(APTDevice_Motor):
    """
    A class for the ThorLabs APT device motor-driven families BSC, BBD, TBD and KBD.

    It is based off :class:`APTDevice_Motor`, but adds the trigger control capabilities.

    :param serial_port: Serial port device the device is connected to.
    :param vid: Numerical USB vendor ID to match.
    :param pid: Numerical USB product ID to match.
    :param manufacturer: Regular expression to match to a device manufacturer string.
    :param product: Regular expression to match to a device product string.
    :param serial_number: Regular expression to match to a device serial number.
    :param home: Perform a homing operation on initialisation.
    :param invert_direction_logic: Invert the meaning of "forward" and "reverse" directions.
    :param swap_limit_switches: Swap "forward" and "reverse" limit switch values.
    :param status_updates: Set to ``"auto"``, ``"polled"`` or ``"none"``.
    """
    def __init__(self, serial_port=None, vid=None, pid=None, manufacturer=None, product=None, serial_number=None, location=None, home=True, invert_direction_logic=False, swap_limit_switches=False, status_updates="none", controller=EndPoint.RACK, bays=(EndPoint.BAY0,), channels=(1,)):

        super().__init__(serial_port=serial_port, vid=vid, pid=pid, manufacturer=manufacturer, product=product, serial_number=serial_number, location=location, home=home, invert_direction_logic=invert_direction_logic, swap_limit_switches=swap_limit_switches, status_updates=status_updates, controller=EndPoint.RACK, bays=bays, channels=(1,))
        
        self.trigger_ = [[{
            # Actual integer code returned by device
            "mode" : 0,
            # Unpacked meaning of mode bits
            "input_edge" : "",
            "input_mode" : "",
            "output_logic" : "",
            "output_mode" : "",
            # Update message fields
            "msg" : "",
            "msgid" : 0,
            "source" : 0,
            "dest" : 0,
            "chan_ident" : 0,
        } for _ in self.channels] for _ in self.bays]
        """
        Input and output triggering configuration.

        Fields are ``"input_edge"``, ``"input_mode"``, ``"output_logic"``, and ``"output_mode"``.
        Additionally, ``"mode"`` stores the raw bit field data from the device as an integer.
        """
        # Request current trigger modes
        for bay in self.bays:
            for channel in self.channels:
                self._loop.call_soon_threadsafe(self._write, apt.mot_req_trigger(source=EndPoint.HOST, dest=bay, chan_ident=channel))


    def _process_message(self, m):
        super()._process_message(m)
       
        # Decode bay and channel IDs and check if they match one of ours
        if m.msg in ("mot_get_trigger",):
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
        
        if m.msg == "mot_get_trigger":
            # Trigger mode update message
            self.trigger_[bay_i][channel_i].update(m._asdict())
            # Decode the input bit fields
            self.trigger_[bay_i][channel_i]["input_edge"] = ("falling", "rising")[bool(m.mode & 0b00000001)]
            if m.mode & 0b00000010:
                self.trigger_[bay_i][channel_i]["input_mode"] = "move_relative"
            elif m.mode & 0b00000100:
                self.trigger_[bay_i][channel_i]["input_mode"] = "move_absolute"
            elif m.mode & 0b00001000:
                self.trigger_[bay_i][channel_i]["input_mode"] = "home"
            else:
                self.trigger_[bay_i][channel_i]["input_mode"] = "disabled"
            # Decode the output bit fields
            self.trigger_[bay_i][channel_i]["output_logic"] = ("low", "high")[bool(m.mode & 0b00010000)]
            if m.mode & 0b00100000:
                self.trigger_[bay_i][channel_i]["output_mode"] = "in_motion"
            elif m.mode & 0b01000000:
                self.trigger_[bay_i][channel_i]["output_mode"] = "motion_complete"
            elif m.mode & 0b10000000:
                self.trigger_[bay_i][channel_i]["output_mode"] = "max_velocity"
            else:
                self.trigger_[bay_i][channel_i]["output_mode"] = "disabled"


    def set_trigger(self, input_edge=None, input_mode=None, output_logic=None, output_mode=None, bay=0, channel=0):
        """
        Configure the external input and/or output triggering modes for the device.
        
        The input triggering logic is selected with ``input_edge``:
        
            * ``"rising"`` : Trigger on rising edge (low to high transition).
            * ``"falling"`` : Trigger on falling edge (high to low transition).
    
        On detection of the input trigger, either a relative, absolute, or homing move can be 
        started.
        For the moves, the movement parameters should have been pre-configured using the relevant
        :meth:`move_relative()` or :meth:`move_absolute()` methods, passing the ``now=False``
        parameter to indicate the move should be delayed until a subsequent trigger.
        The movement type once triggered is selected with ``input_mode``:

            * ``"move_relative"`` : Perform a relative move.
            * ``"move_absolute"`` : Perform an absolute move.
            * ``"home"`` : Perform a homing operation.
            * ``"disabled"`` : Do nothing.
        
        The output triggering logic is selected with ``output_logic``:

            * ``"high"`` : Output is high during the event.
            * ``"low"`` : Output is low during the event.

        The event for which the output trigger signal is sent is selected by ``output_mode``:

            * ``"in_motion"`` : Trigger activated during motion.
            * ``"motion_complete"`` : Trigger activated when motion is completed.
            * ``"max_velocity"`` : Trigger activated when movement reaches full speed.
            * ``"disabled"`` : Don't activate trigger.
        
        :param input_edge: Signal edge for input triggering.
        :param input_mode: Action to take on input trigger.
        :param output_logic: Output trigger logic level.
        :param output_mode: Event for which output trigger is activated.
        """
        # Note that all of the "mode" field is treated as a bit mask, which implies/allows for
        # multiple triggering actions. I'm assuming that is not actually possible, so the way
        # this is coded allows for only a single action on trigger.
        
        # TODO, actually use the current mode once that's implemented
        mode = 0

        # Set or clear the TRIGIN_HIGH bit
        # The documentation for this bit is horrible! We'll guess what it's supposed to mean...
        if input_edge == "rising":
            mode |= 0b00000001
        elif input_edge == "falling":
            mode &= 0b11111110
        elif input_edge is None:
            # Leave as is
            pass
        else:
            self._log.warn(f"Unrecognised trigger input_edge '{input_edge}'', should be 'rising' or 'falling'.")
        
        # Set one (only) of the TRIGIN_RELMOVE, TRIGIN_ABSMOVE or TRIGIN_HOMEMOVE bits
        if input_mode == "move_relative":
            mode &= 0b11110001
            mode |= 0b00000010
        elif input_mode == "move_absolute":
            mode &= 0b11110001
            mode |= 0b00000100
        elif input_mode == "home":
            mode &= 0b11110001
            mode |= 0b00001000
        elif input_mode == "disabled":
            mode &= 0b11110001
        elif input_mode is None:
            # Leave as is
            pass
        else:
            self._log.warn(f"Unrecognised trigger input_mode '{input_mode}', should be 'move_relative', 'move_absolute' or 'home'.")
        
        # Set or clear the TIGOUT_HIGH bit
        if output_logic == "high":
            mode |= 0b00010000
        elif output_logic == "low":
            mode &= 0b11101111
        elif output_logic is None:
            # Leave as is
            pass
        else:
            self._log.warn(f"Unrecognised trigger output_logic '{output_logic}', should be 'high' or 'low'")
        
        # Set one (only) of TRIGOUT_INMOTION, TRIGOUT_MOTIONCOMPLETE or TRIGOUT_MAXVELOCITY bits
        if output_mode == "in_motion":
            mode &= 0b00011111
            mode |= 0b00100000
        elif output_mode == "motion_complete":
            mode &= 0b00011111
            mode |= 0b01000000
        elif output_mode == "max_velocity":
            mode &= 0b00011111
            mode |= 0b10000000
        elif output_mode == "disabled":
            mode &= 0b00011111
        elif output_mode is None:
            # Leave as is
            pass
        else:
            self._log.warn(f"Unrecognised trigger output_mode '{output_mode}', should be 'in_motion', 'motion_complete' or 'max_velocity'.")
        
        self._log.debug(f"Setting trigger mode={mode} [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.mot_set_trigger(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], mode=mode))
        # Update status with new trigger parameters
        self._loop.call_soon_threadsafe(self._write, apt.mot_req_trigger(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel]))


class APTDevice_BayUnit(APTDevice_Motor_Trigger):
    """
    A class for ThorLabs APT bay-type device models BBD10x, BBD20x, BSC10x, BSC20x, where x is the number of channels (1, 2 or 3).

    It is based off :class:`APTDevice_Motor_Trigger` with some customisation for the specifics of the device.

    Note that the bay-type devices such as BBD and BSCs are referred to as a x-channel controllers,
    but the actual device layout is that the controller is a "rack" system with three bays,
    where x number of single-channel controller cards may be installed.
    In other words, the BBD203 "3 channel" controller actually has 3 populated bays (``bays=(EndPoint.BAY0, EndPoint.BAY1, EndPoint.BAY2)``),
    each of which only controls a single channel (``channels=(1,)``).

    The parameter ``x`` configures the number of channels.
    If ``x=1`` it is a single bay/channel controller, and aliases of ``status = status_[0][0]``
    etc are created for convenience.

    :param x: Number of channels the device controls.
    :param serial_port: Serial port device the device is connected to.
    :param vid: Numerical USB vendor ID to match.
    :param pid: Numerical USB product ID to match.
    :param manufacturer: Regular expression to match to a device manufacturer string.
    :param product: Regular expression to match to a device product string.
    :param serial_number: Regular expression to match to a device serial number.
    :param home: Perform a homing operation on initialisation.
    :param invert_direction_logic: Invert the meaning of "forward" and "reverse" directions.
    :param swap_limit_switches: Swap "forward" and "reverse" limit switch values.
    :param status_updates: Set to ``"auto"``, ``"polled"`` or ``"none"`` (default).
    """
    def __init__(self, serial_port=None, vid=None, pid=None, manufacturer=None, product=None, serial_number=None, location=None, x=1, home=True, invert_direction_logic=False, swap_limit_switches=True, status_updates="none"):
        
        # Configure number of bays
        if x == 3:
            bays = (EndPoint.BAY0, EndPoint.BAY1, EndPoint.BAY2)
        elif x == 2:
            bays = (EndPoint.BAY0, EndPoint.BAY1)
        else:
            bays = (EndPoint.BAY0,)

        super().__init__(serial_port=serial_port, vid=vid, pid=pid, manufacturer=manufacturer, product=product, serial_number=serial_number, location=location, home=home, invert_direction_logic=invert_direction_logic, swap_limit_switches=swap_limit_switches, status_updates=status_updates, controller=EndPoint.RACK, bays=bays, channels=(1,))

        if x == 1:
            self.status = self.status_[0][0]
            """Alias to first bay/channel of :data:`~thorlabs_apt_device.devices.aptdevice_motor.APTDevice_Motor.status_`."""
            
            self.velparams = self.velparams_[0][0]
            """Alias to first bay/channel of :data:`~thorlabs_apt_device.devices.aptdevice_motor.APTDevice_Motor.velparams_`"""
            
            self.genmoveparams = self.genmoveparams_[0][0]
            """Alias to first bay/channel of :data:`~thorlabs_apt_device.devices.aptdevice_motor.APTDevice_Motor.genmoveparams_`"""
            
            self.jogparams = self.jogparams_[0][0]
            """Alias to first bay/channel of :data:`~thorlabs_apt_device.devices.aptdevice_motor.APTDevice_Motor.jogparams_`"""
            
            self.homeparams = self.homeparams_[0][0]
            """Alias to first bay/channel of :data:`~thorlabs_apt_device.devices.aptdevice_motor.APTDevice_Motor.homeparams_`"""

            self.trigger = self.trigger_[0][0]
            """Alias to first bay/channel of :data:`~thorlabs_apt_device.devices.aptdevice_motor.APTDevice_Motor_Trigger.trigger_`"""

