# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:17:46 2020

@author: _Xavi
"""

from TempestaController import TempestaController
from view.TempestaView import TempestaView
from model.TempestaModel import TempestaModel

model = TempestaModel()
view = TempestaView(model)
controller = TempestaController(model, view)
view.setController(controller)
view.startView()
