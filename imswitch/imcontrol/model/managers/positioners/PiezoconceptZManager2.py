import time

from .PositionerManager import PositionerManager


class PiezoconceptZManager2(PositionerManager):
    """Improved PositionerManager for control of a Piezoconcept Z-piezo through RS232
    communication. Adapted to new Firmware as of 2026.

    Manager properties:

    - ``rs232device`` -- name of the defined rs232 communication channel
      through which the communication should take place
    """

    def __init__(self, positionerInfo, name, *args, **lowLevelManagers):
        if len(positionerInfo.axes) != 1:
            raise RuntimeError(f'{self.__class__.__name__} only supports one axis,'
                               f' {len(positionerInfo.axes)} provided.')

        super().__init__(positionerInfo, name, initialPosition={
            axis: 0 for axis in positionerInfo.axes
        })
        self._rs232Manager = lowLevelManagers['rs232sManager'][
            positionerInfo.managerProperties['rs232device']
        ]
        # Try to retrieve range and move to center!
        try:
            self._range = positionerInfo.managerProperties['range_um']
            self.setPosition(self._range//2, None)
        except Exception as e:(
            print(f"PiezoconceptZManager2 init error: {e}"))



    def move(self, value, _):
        if float(value) > 0:
            cmd = 'MOVRZ +' + str(round(float(value), 3))[0:6] + 'u'
        elif float(value) < 0:
            cmd = 'MOVRZ -' + str(round(float(value), 3))[1:7] + 'u'
        else:
            return
        _ = self._rs232Manager.query(cmd)

        self._position[self.axes[0]] = self._position[self.axes[0]] + value

    def setPosition(self, value, _):
        cmd = 'MOVEZ ' + str(round(float(value), 3)) + 'u'
        _ = self._rs232Manager.query(cmd)

        self._position[self.axes[0]] = value

    @property
    def position(self):
        _ = self.get_abs()
        return self._position

    def get_abs(self):
        cmd = 'GET_Z'
        reply = self._rs232Manager.query(cmd)
        if reply is None:
            reply = self._position[self.axes[0]]
        else:
            try:
                reply = float(reply.split(' ')[0])
            except Exception as e:
                print(f"PiezoZManager get abs error: {e}")
                return  self._position[self.axes[0]]
        self._position[self.axes[0]] = reply
        return reply


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
