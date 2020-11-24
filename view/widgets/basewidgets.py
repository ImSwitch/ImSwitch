# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 17:08:54 2020

@author: _Xavi
"""
import weakref
from pyqtgraph.Qt import QtGui
import view.guitools as guitools


class WidgetFactory:
    """Factory class for creating widgets. It also has a method for loading a
    preset for all the created widgets."""

    def __init__(self, defaultPreset):
        self._defaultPreset = defaultPreset
        self._createdWidgets = []

    def createWidget(self, widgetClass, *args, **kwargs):
        if issubclass(widgetClass, Widget):
            widget = widgetClass(self._defaultPreset, *args, **kwargs)
        else:
            widget = widgetClass(*args, **kwargs)

        self._createdWidgets.append(weakref.ref(widget))
        return widget


class Widget(QtGui.QWidget):
    """ Superclass for all Widgets. All Widgets are subclasses of QWidget. """

    def __init__(self, defaultPreset, *args, **kwargs):
        self._defaultPreset = defaultPreset
        super().__init__(*args, **kwargs)
