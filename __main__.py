# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:17:46 2020

@author: _Xavi
"""

import sys

from pyqtgraph.Qt import QtGui

from controller.TempestaController import TempestaController
from model.TempestaModel import TempestaModel
from view.TempestaView import TempestaView

model = TempestaModel()
app = QtGui.QApplication([])
view = TempestaView()
controller = TempestaController(model, view)
view.show()
sys.exit(app.exec_())
