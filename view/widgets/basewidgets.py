# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 17:08:54 2020

@author: _Xavi
"""
from pyqtgraph.Qt import QtGui


class WidgetFactory:
    """Factory class for creating a WidgetController object. Factory checks
    that the new object is a valid WidgetController."""

    def __init__(self, defaultPreset):
        self._defaultPreset = defaultPreset

    def createWidget(self, widgetClass, *args, **kwargs):
        if issubclass(widgetClass, Widget):
            return widgetClass(self._defaultPreset, *args, **kwargs)
        else:
            return widgetClass(*args, **kwargs)


class Widget(QtGui.QWidget):
    """ Superclass for all Widgets. All Widgets are subclasses of QWidget. """

    def __init__(self, defaultPreset, *args, **kwargs):
        self._defaultPreset = defaultPreset
        super().__init__(*args, **kwargs)
