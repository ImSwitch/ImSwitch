# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:17:46 2020

@author: _Xavi
"""

import os
import sys

from pyqtgraph.Qt import QtGui
import qdarkstyle

import configfileutils
from controller.MainController import MainController
from view.MainView import MainView
from view.guitools import ViewSetupInfo

os.environ['NAPARI_ASYNC'] = '1'
os.environ['NAPARI_OCTREE'] = '0'

setupInfo = configfileutils.loadSetupInfo(ViewSetupInfo)
app = QtGui.QApplication([])
app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api=os.environ.get('PYQTGRAPH_QT_LIB')))
view = MainView(setupInfo)
controller = MainController(setupInfo, view)
view.show()
sys.exit(app.exec_())
