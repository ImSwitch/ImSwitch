# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:35:31 2020

@author:_Xavi
"""

from pyqtgraph.Qt import QtGui
import sys

app = QtGui.QApplication([])
win = QtGui.QMainWindow()
sys.exit(app.exec_())
win.show()