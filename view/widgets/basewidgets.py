# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 17:08:54 2020

@author: _Xavi
"""
from pyqtgraph.Qt import QtGui

class Widget(QtGui.QWidget):
    """ Superclass for all Widgets.
            All Widgets are subclasses of QWidget and should have a registerListener function. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def registerListener(self):
        """ Manage interactions with the WidgetController linked to the Widget. """
        raise NotImplementedError
