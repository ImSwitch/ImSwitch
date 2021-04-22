"""
Created on Wed Jan 13 11:57:00 2021

@author: jonatanalvelid
"""


class LeicaDMIManager:
    def __init__(self, name, *args, **kwargs):
        pass
        #super().__init__(name=name, initialPosition=[0])
        # TODO: the following does not work now, as there is no controller trying to load this manager as of now. 
        #self._rs232Manager = kwargs['rs232sManager'][positionerInfo.managerProperties['rs232device']]
        #cmd = '71002'
        #print(self._rs232Manager.send(cmd))  # print serial no of dmi stand

    def move(self, value, *args):
        if not int(value) == 0:
            cmd = '71024 ' + str(int(value))
            if int(value) > 132:
                print('Warning: Step bigger than 500nm.')
            self._rs232Manager.send(cmd)

        self._position = self._position + value
        return self._position

    def setPosition(self, value, *args):
        cmd = '71022 ' + str(int(value))
        self._rs232Manager.send(cmd)

        self._position = value
        return self._position

    def position(self, *args):
        cmd = '71023'
        return self.returnMod(self._rs232Manager.send(cmd))

    def returnMod(self, reply):
        return reply[6:]

    def motCorrPos(self, value):
        """ Absolute mot_corr position movement. """
        movetopos = int(round(value*93.83))
        cmd = '47022 -1 ' + str(movetopos)
        self._rs232Manager.send(cmd)


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
