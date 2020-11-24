# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:17:46 2020

@author: _Xavi
"""

import sys

from pyqtgraph.Qt import QtGui

from controller.MainController import MainController
from model.MainModel import MainModel
from view.MainView import MainView

model = MainModel()
app = QtGui.QApplication([])
view = MainView(model.setupInfo.availableWidgets)
controller = MainController(model, view)
view.show()
sys.exit(app.exec_())
