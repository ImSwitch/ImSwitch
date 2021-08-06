import os
import weakref
from abc import ABCMeta, abstractmethod

from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools


class _QObjectABCMeta(type(QtCore.QObject), ABCMeta):
    pass


class WidgetFactory:
    """ Factory class for creating widgets. """

    def __init__(self, options):
        self._options = options
        self._baseKwargs = {}
        self._createdWidgets = []

    def createWidget(self, widgetClass, *args, **extraKwargs):
        kwargs = self._baseKwargs.copy()
        kwargs.update(extraKwargs)

        if issubclass(widgetClass, Widget):
            widget = widgetClass(self._options, *args, **kwargs)
        else:
            widget = widgetClass(*args, **kwargs)

        self._createdWidgets.append(weakref.ref(widget))
        return widget

    def setArgument(self, name, value):
        self._baseKwargs[name] = value


class Widget(QtWidgets.QWidget, metaclass=_QObjectABCMeta):
    """ Superclass for all Widgets. All Widgets are subclasses of QWidget. """

    @abstractmethod
    def __init__(self, options, *_args, **_kwargs):
        self._options = options
        QtWidgets.QWidget.__init__(self)

    def replaceWithError(self, errorText):
        errorLabel = QtWidgets.QLabel(errorText)

        grid = QtWidgets.QGridLayout()
        if self.layout() is not None:
            QtWidgets.QWidget().setLayout(self.layout())  # unset layout
        self.setLayout(grid)
        grid.addWidget(errorLabel)


class NapariHybridWidget(Widget, guitools.NapariBaseWidget, metaclass=_QObjectABCMeta):
    """ Superclass for widgets that can use the functionality of
    NapariBaseWidget. Derived classes should not implement __init__; instead,
    they should implement __post_init__. """

    def __init__(self, options, *, napariViewer=None):
        Widget.__init__(self, options)

        if napariViewer is None:
            if 'IMSWITCH_FULL_APP' not in os.environ or os.environ['IMSWITCH_FULL_APP'] != '1':
                # ImSwitch components running as napari plugins - raise error
                raise ValueError('napariViewer must be specified')

            self.replaceWithError('Could not load widget; napariViewer not specified. This error is'
                                  ' most likely happening because this widget requires the image'
                                  ' display widget to also be enabled, but it is not enabled in'
                                  ' your currently active hardware configuration.')
            return

        guitools.NapariBaseWidget.__init__(self, napariViewer)
        self.__post_init__()

    @abstractmethod
    def __post_init__(self):
        pass


# Copyright (C) 2020, 2021 TestaLab
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
