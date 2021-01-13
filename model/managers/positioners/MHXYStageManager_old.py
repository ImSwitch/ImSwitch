# -*- coding: utf-8 -*-
"""
Created on Tue Jan 12 09:58:00 2021

@author: jonatanalvelid
"""

from .PositionerManager import PositionerManager


class MHXYStageManager(PositionerManager):
    def __init__(self, *args, **kwargs):
        super().__init__('name', initialPosition=[0,0])

    def move(self, value, axis):
        if axis == 0:
            self._mhxystage.move_relX(value)
        elif axis == 1:
            self._mhxystage.move_relY(value)
        else:
            print('Wrong axis, has to be 0 or 1.')
        self._position[axis] = self._position[axis] + value
        return self._position[axis]

    def setPosition(self, value, axis):
        if axis == 0:
            self._mhxystage.move_absX(value)
        elif axis == 1:
            self._mhxystage.move_absY(value)
        else:
            print('Wrong axis, has to be 0 or 1.')
        self._position[axis] = value
        return self._position[axis]

    def position(self, axis):
        if axis == 0 or axis == 1:
            return self._position[axis]
        else:
            print('Wrong axis, has to be 0 or 1.')


def getMHXYObj():
    try:
        from model.interfaces.stageMHXY import MHXYStage
        print('Trying to import MH xy-stage')
        mhxystage = MHXYStage()
        mhxystage.initialize()
        print('Initialized MH XY-stage Object, serial no: ', mhxystage.idn)
        return mhxystage
    except:
        print('Initializing Mock MH xy-stage')
        from model.interfaces.mockers import MockMHXYStage
        return MockMHXYStage()
