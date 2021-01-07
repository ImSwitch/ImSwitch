# -*- coding: utf-8 -*-
"""
Created on Thu Jan 07 15:14:00 2021

@author: jonatanalvelid
"""


class PiezoconceptZHelper:
    def __init__(self, piezoz, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__piezoz = piezoz

    def move(self, value):
        if value < 10:
            self.move_rel(value)
        else:
            self.move_abs(value)

    def move_rel(self, value):
        self.__piezoz.move_relZ(value)

    def move_abs(self, value):
        self.__piezoz.move_absZ(value)

    def get_abs(self):
        return self.__piezoz.absZ
