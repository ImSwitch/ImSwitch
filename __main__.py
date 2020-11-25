# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:17:46 2020

@author: _Xavi
"""

import os
import sys

from pyqtgraph.Qt import QtGui
import qdarkstyle

from controller.MainController import MainController
from model.MainModel import MainModel
from view.MainView import MainView

model = MainModel()
app = QtGui.QApplication([])
app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api=os.environ.get('PYQTGRAPH_QT_LIB')))
view = MainView(model.setupInfo.availableWidgets)
controller = MainController(model, view)
view.show()
sys.exit(app.exec_())
