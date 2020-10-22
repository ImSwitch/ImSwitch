# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:35:31 2020

@author:_Xavi
"""

import sys

from pyqtgraph.Qt import QtGui

app = QtGui.QApplication([])
win = QtGui.QMainWindow()
sys.exit(app.exec_())
win.show()
