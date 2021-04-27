"""
Created on Wed Jan 13 11:57:00 2021

@author: jonatanalvelid
"""

from .PositionerManager import PositionerManager


class PiezoconceptZManager(PositionerManager):
    def __init__(self, positionerInfo, name, *args, **kwargs):
        if len(positionerInfo.axes) != 1:
            raise RuntimeError(f'{self.__class__.__name__} only supports one axis,'
                               f' {len(positionerInfo.axes)} provided.')

        super().__init__(positionerInfo, name, initialPosition={
            axis: 0 for axis in positionerInfo.axes
        })
        self._rs232Manager = kwargs['rs232sManager'][positionerInfo.managerProperties['rs232device']]
        #print('ZPiezo fake reply')

    def move(self, value, axis):
        if value == 0:
            return
        elif float(value) > 0:
            cmd = 'MOVRX +' + str(round(float(value), 3))[0:6] + 'u'
        elif float(value) < 0:
            cmd = 'MOVRX -' + str(round(float(value), 3))[1:7] + 'u'
        self._rs232Manager.send(cmd)

        self._position[self.axes[0]] = self._position[self.axes[0]] + value

    def setPosition(self, value, axis):
        cmd = 'MOVEX ' + str(round(float(value), 3)) + 'u'
        self._rs232Manager.send(cmd)

        self._position[self.axes[0]] = value

    def get_abs(self):
        cmd = 'GET_X'
        reply = self._rs232Manager.send(cmd)
        if reply is None:
            reply = self._position[self.axes[0]]
        else:
            reply = float(reply.split(' ')[0])
        return reply


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
