# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:17:46 2020

@author: _Xavi
"""

from controller.TempestaController import TempestaController
from view.TempestaView import TempestaView
from model.TempestaModel import TempestaModel
from pyqtgraph.Qt import QtGui
import sys

model = TempestaModel()
app = QtGui.QApplication([])
view = TempestaView()
controller = TempestaController(model, view)
view.registerController(controller)
view.show()
sys.exit(app.exec_())
