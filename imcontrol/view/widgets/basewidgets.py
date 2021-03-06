import weakref
from pyqtgraph.Qt import QtWidgets


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


class Widget(QtWidgets.QWidget):
    """ Superclass for all Widgets. All Widgets are subclasses of QWidget. """

    def __init__(self, defaultPreset, *args, **kwargs):
        self._defaultPreset = defaultPreset
        super().__init__(*args, **kwargs)

# Copyright (C) 2020, 2021Staffan Al-Kadhimi, Xavier Casas, Andreas Boden
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License