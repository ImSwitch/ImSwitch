# -*- coding: utf-8 -*-
"""
Created on Thu Jan 07 15:14:00 2021

@author: jonatanalvelid
"""

from .PositionerManager import PositionerManager


class PiezoconceptZManager(PositionerManager):
    def __init__(self, *args, **kwargs):
        super().__init__('name', 0)
        self._piezoz = getPCZObj()

    def move(self, value, *args):
        self._piezoz.move_relZ(value)
        self._position = self._position + value
        return self._position

    def setPosition(self, value, *args):
        self._piezoz.move_absZ(value)
        self._position = value
        return self._position

    def position(self, *args):
        return self._position

    def get_abs(self):
        return self._piezoz.absZ


def getPCZObj():
    try:
        from model.interfaces.piezoPiezoconceptZ import PCZPiezo
        print('Trying to import z-piezo')
        piezoz = PCZPiezo()
        piezoz.initialize()
    except:
        print('Initializing mock z-piezo')
        from model.interfaces.mockers import MockPCZPiezo
        piezoz = MockPCZPiezo()
    return piezoz
