import time
from typing import Dict
import numpy as np
import logging
logging.basicConfig(level=logging.DEBUG)
from .PositionerManager import PositionerManager
from ..detectors.DetectorManager import DetectorNumberParameter

try:
    from imswitch.imcontrol.model.interfaces.SmarACT import *
except ImportError:
    print('Could not import smaract interface!')
    raise


import ctypes as ct
MU2NM = 1e3 # micrometer to nanometer


class StageStatusException(BaseException):
    """Custom exception"""
    pass


class SmarACTPositionerManager(PositionerManager):
    """ SmarACT Positioner manager.

    This manager should function with old-style MCS1 stages but may not be compatible with the newer versions.

    It is based on the unofficial wrapper of the MCS2 stages. Newer stages may need more things.

    Known issues:
        - The stage will not gracefully exit when resetOnClose is set to True.

    Example json file configuration:
        "positioners": {
      "SmarACT": {
          "managerName": "SmarACTPositionerManager",
          "managerProperties": {
            "holdTime": 60000,
            "axis_lookup_table": {"X":0, "Y":2, "Z":1}
          },
          "axes": ["X", "Y", "Z"],
          "forScanning": false,
          "forPositioning": true,
          "resetOnClose": false
      }



    Manager properties:

    None
    """

    holdTime_ms = 60_000
    axis_lookup_table = dict(X=0, Y=2, Z=1)
    def __init__(self, positionerInfo, name, **lowLevelManagers):


        if 'holdTime' in positionerInfo.managerProperties:
            self.holdTime_ms = positionerInfo.managerProperties['holdTime']
        if 'axis_lookup_table' in positionerInfo.managerProperties:
            self.axis_lookup_table = positionerInfo.managerProperties['axis_lookup_table']
        # generate the inverse looup table for later use
        self.reverse_axis_lookup_table = {}
        for key, value in self.axis_lookup_table.items():
            self.reverse_axis_lookup_table[value] = key

        super().__init__(positionerInfo, name, initialPosition={'X': 0, 'Y':0, 'Z':0})

        self.__logger__ = logging.getLogger(name)
        self.__logger__.setLevel(logging.DEBUG)
        self.__logger__.debug('Connecting to stage')
        self.__setup_connection_and_buffers()
        self.__logger__.debug('Connected to stage')



        self._position = self.position

    def ExitIfError(self, status):
        # init error_msg variable
        error_msg = ct.c_char_p()
        if status != SA_OK:
            SA_GetStatusInfo(status, error_msg)
            error_message = (
                f"MCS error: {error_msg.value[:].decode('utf-8')} \n Err code {status}"
            )
            self.__logger__.error(error_message)
            raise StageStatusException(error_message)
        return status

    def __setup_connection_and_buffers(self):
        """ Internal use only. Connect to the device and set up a buffer to receive replies.
        """
        self.mcsHandle = ct.c_ulong()
        self.outBuffer = ct.create_string_buffer(17)
        self.ioBufferSize = ct.c_ulong(18)
        self.ExitIfError(
            SA_FindSystems("", self.outBuffer, self.ioBufferSize)
        )
        self.ExitIfError(
            SA_OpenSystem(self.mcsHandle, self.outBuffer, bytes("sync", "utf-8"))
        )
        self.__logger__.info(
            "MCS address: {}".format(self.outBuffer[:18].decode("utf-8")))  # connect to first system of list

    def finalize(self):
        """ Disconnect the device.

        """
        self.__logger__.info('Closing system')
        self.ExitIfError(SA_CloseSystem(self.mcsHandle))


    def move(self, dist, axis):
        """
        Move axis axis by a distance.

        Params:
            dist: distance in microns
            axis: axis to move. Should be in ['X', 'Y', 'Z']
        """

        current_position = self.getPosition(axis=axis)
        self.__logger__.info(f'Moving axis {axis} by {dist}. Current position {current_position}')
        new_position = current_position + dist
        self.setPosition(new_position, axis)

    def getPosition(self, axis):
        return self._get_position_channel(self.axis_lookup_table[axis])

    def setPosition(self, position: float, axis: str, wait_for_it=True):
        self.__logger__.info(f'Moving axis {axis} to {position}')
        axis_num = self.axis_lookup_table[axis]
        t = position * MU2NM
        self.ExitIfError(
            SA_GotoPositionAbsolute_S(
                self.mcsHandle,
                channelIndex=axis_num,
                position=ct.c_int(int(t)),
                holdTime=ct.c_ulong(self.holdTime_ms),
            )
        )
        if wait_for_it:
            self.wait_for_status()


    def set_closed_loop_max_speed(self, new_value, channel=None):
        """Set closed loop max speed, in mm per second"""
        new_value, channel = self._prepare_fancy_broadcasting(
            new_value, channel, MU2NM
        )
        for c, v in zip(channel, new_value):
            self.ExitIfError(
                SA_SetClosedLoopMoveSpeed_S(self.mcsHandle, c, ct.c_uint32(v))
            )
            # get it and check that it works
            set_val = self.get_closed_loop_move_speed(c)
            assert (
                set_val == v
            ), f"Could not set closed loop move speed. Requested {new_value}, got {set_val}"

    def _prepare_fancy_broadcasting(
        self, new_value, channel=None, conversion_factor=MU2NM
    ):
        """
        Internal use only. Do a numpy-like broadcasting for axes and scalars.

        This is to make it easy to change the speed per axis.
        """
        new_value = np.array(new_value)
        new_value = np.array(new_value * MU2NM, dtype=np.uint32)
        if len(new_value.ravel()) == 1:
            new_value = [
                new_value,
            ] * 3
        if channel is None:
            channel = range(3)
        if np.isscalar(channel):
            channel = [channel]
        return new_value, channel

    def set_closed_loop_move_acceleration(self, new_value, channel=None):
        """Set acceleration in mm/s^2"""
        new_value, channel = self._prepare_fancy_broadcasting(
            new_value, channel, MU2NM
        )

        for c, v in zip(channel, new_value):
            self.ExitIfError(
                SA_SetClosedLoopMoveAcceleration_S(self.mcsHandle, c, ct.c_uint32(v))
            )
            # get it and check that it works
            set_val = self.get_closed_loop_move_acelleration(c)
            assert (
                set_val == v
            ), f"Could not set closed loop move acelleration. Requested {new_value}, got {set_val}"

    def get_closed_loop_move_acelleration(self, channel):
        accel = ct.c_uint32(0)
        self.ExitIfError(
            SA_GetClosedLoopMoveAcceleration_S(self.mcsHandle, channel, accel)
        )
        return accel.value

    def get_closed_loop_move_speed(self, channel):
        speed = ct.c_uint32(0)
        self.ExitIfError(SA_GetClosedLoopMoveSpeed_S(self.mcsHandle, channel, speed))
        return speed.value

    def set_low_vibration_mode(self, channels=None):
        if channels is None:
            channels = range(3)
        for channel in channels:
            self.ExitIfError(
                SA_SetChannelProperty_S(
                    self.mcsHandle,
                    channel,
                    SA_EPK(SA_GENERAL, SA_LOW_VIBRATION, SA_OPERATION_MODE),
                    SA_ENABLED,
                )
            )

    @property
    def position(self) -> Dict[str, float]:
        self.axis_lookup_table.items()
        pos = np.array([self.getPosition(a) for a in 'XYZ'])
        positions = {}
        for ax, p in zip(self.axes, pos):
            positions[ax] = p
        self._position = positions
        return positions

    def _get_position_channel(self, channel):
        """Get position for channel channel. """
        x_cor = ct.c_ulong()
        self.ExitIfError(SA_GetPosition_S(self.mcsHandle, ct.c_ulong(channel), x_cor))
        return self.c_convert(x_cor.value) / MU2NM

    def wait_for_status(self, target_statuses=(SA_STOPPED_STATUS, SA_HOLDING_STATUS)):
        """Wait for the stage to reach status X.
        X can be an array or a single state."""
        if type(target_statuses) is int:
            target_statuses = np.array([target_statuses])
        else:
            target_statuses = np.array(target_statuses)

        while True:
            states = self.get_status()
            # check that all the axes are in the right state. First we check that the state
            # corresponds to any state we accept for all axes, and then we check that all axes match
            if np.all(np.any(states == target_statuses[:, None], axis=0)):
                break
            time.sleep(0.1)

    def get_status(self):
        """Get status for all three channels."""
        status = ct.c_ulong()
        states = np.zeros(3, int)
        for channel in range(3):
            self.ExitIfError(SA_GetStatus_S(self.mcsHandle, channel, status))
            states[channel] = int(status.value)
        return states

    def _start_moving(self, position):
        """Start moving to a position. This command will not wait for the movement to complete."""

        for i, t in enumerate(position * MU2NM):

            self.ExitIfError(
                SA_GotoPositionAbsolute_S(
                    self.mcsHandle,
                    ct.c_ulong(i),
                    ct.c_int(int(t)),
                    ct.c_ulong(self.holdTime_ms),
                )
            )

    def ExitIfError(self, status):
        # init error_msg variable
        error_msg = ct.c_char_p()
        if status != SA_OK:
            SA_GetStatusInfo(status, error_msg)
            error_message = (
                f"MCS error: {error_msg.value[:].decode('utf-8')} \n Err code {status}"
            )
            self.__logger__.error(error_message)
            raise StageStatusException(error_message)
        return status

    def c_convert(self, xx):
        "converts the ctype minus int values into python int value"
        if xx >> 31 > 0:
            mask = 0xFFFFFFFF
            xx = -xx ^ mask
        return xx



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
