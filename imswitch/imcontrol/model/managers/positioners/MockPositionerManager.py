from .PositionerManager import PositionerManager


class MockPositionerManager(PositionerManager):
    """ PositionerManager for mock positioner used for repeating measurements
    and/or timelapses.

    Manager properties:

    None
    """

    def __init__(self, positionerInfo, name, **lowLevelManagers):

        if len(positionerInfo.axes) != 1:
            raise RuntimeError(f'{self.__class__.__name__} only supports one axis,'
                               f' {len(positionerInfo.axes)} provided.')
                               
        super().__init__(positionerInfo, name, initialPosition={
            axis: 0 for axis in positionerInfo.axes
        })

    def move(self, dist, axis):
        self.setPosition(self._position[self.axes[0]] + dist, axis)

    def setPosition(self, position, axis):
        self._position[self.axes[0]] = position


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
