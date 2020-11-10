# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 19:11:50 2020

@author: andreas.boden
"""


class ValidChildFactory:
    def __new__(cls, main, className, *args, **kwargs):
        product = globals()[main.className](*args)
        if product.isValidChild(*args, **kwargs):
            return product
