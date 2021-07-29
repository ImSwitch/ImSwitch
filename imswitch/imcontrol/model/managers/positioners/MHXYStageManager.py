from .PositionerManager import PositionerManager


class MHXYStageManager(PositionerManager):
    """ PositionerManager for control of a Marzhauser XY-stage through RS232
    communication.

    Manager properties:

    - ``rs232device`` -- name of the defined rs232 communication channel
      through which the communication should take place
    """

    def __init__(self, positionerInfo, name, *args, **lowLevelManagers):
        if (len(positionerInfo.axes) != 2
                or 'X' not in positionerInfo.axes or 'Y' not in positionerInfo.axes):
            raise RuntimeError(f'{self.__class__.__name__} requires two axes named X and Y'
                               f' respectively, {positionerInfo.axes} provided.')

        super().__init__(positionerInfo, name, initialPosition={
            axis: 0 for axis in positionerInfo.axes
        })
        self._rs232Manager = lowLevelManagers['rs232sManager'][
            positionerInfo.managerProperties['rs232device']
        ]
        print(str(self._rs232Manager.send('?readsn')))  # print serial no of stage

    def move(self, value, axis):
        if axis == 'X':
            cmd = 'mor x ' + str(float(value))
        elif axis == 'Y':
            cmd = 'mor y ' + str(float(value))
        else:
            print('Wrong axis, has to be "X" or "Y".')
            return
        self._rs232Manager.send(cmd)
        self._position[axis] = self._position[axis] + value

    def setPosition(self, value, axis):
        if axis == 'X':
            cmd = 'moa x ' + str(float(value))
        elif axis == 'Y':
            cmd = 'moa y ' + str(float(value))
        else:
            print('Wrong axis, has to be "X" or "Y".')
            return
        self._rs232Manager.send(cmd)
        self._position[axis] = value


# Copyright (C) 2020, 2021 TestaLab
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
