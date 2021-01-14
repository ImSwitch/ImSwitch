# -*- coding: utf-8 -*-
"""
Created on Wed Jan 13 11:57:00 2021

@author: jonatanalvelid
"""

from .PositionerManager import PositionerManager


class PiezoconceptZManager(PositionerManager):
    def __init__(self, positionerInfo, name, *args, **kwargs):
        super().__init__(name=name, initialPosition=0)
        self._rs232Manager = kwargs['rs232sManager']._subManagers[positionerInfo.managerProperties['rs232device']]
        print('ZPiezo fake reply')

    def move(self, value, *args):
        if value == 0:
            return self._position
        elif float(value) < 0:
            cmd = 'MOVRX +' + str(round(float(value), 3))[1:7] + 'u'
        elif float(value) > 0:
            cmd = 'MOVRX -' + str(round(float(value), 3))[0:6] + 'u'
        self._rs232Manager.send(cmd)

        self._position = self._position + value
        return self._position

    def setPosition(self, value, *args):
        cmd = 'MOVEX ' + str(round(float(value), 3)) + 'u'
        self._rs232Manager.send(cmd)

        self._position = value
        return self._position

    def position(self, *args):
        return self._position

    def get_abs(self):
        cmd = 'GET_X'
        reply = self._rs232Manager.send(cmd)
        if reply is None:
            reply = self._position
        return reply

