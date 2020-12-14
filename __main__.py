# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:17:46 2020

@author: _Xavi
"""

import os
import sys

from pyqtgraph.Qt import QtGui
import imcommon.view.stylesheet

import configfileutils
from controller.MainController import MainController
from model.MainModel import MainModel
from view.MainView import MainView
from view.guitools import ViewSetupInfo

os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5'  # force Qt to use PyQt5

model = MainModel(configfileutils.loadSetupInfo(ViewSetupInfo))
app = QtGui.QApplication([])
app.setStyleSheet(imcommon.view.stylesheet.getBaseStyleSheet())
view = MainView(model.setupInfo)
controller = MainController(model, view)
view.show()
sys.exit(app.exec_())
