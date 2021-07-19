import weakref
from qtpy import QtWidgets


class WidgetFactory:
    """ Factory class for creating widgets. """

    def __init__(self, options):
        self._options = options
        self._createdWidgets = []

    def createWidget(self, widgetClass, *args, **kwargs):
        if issubclass(widgetClass, Widget):
            widget = widgetClass(self._options, *args, **kwargs)
        else:
            widget = widgetClass(*args, **kwargs)

        self._createdWidgets.append(weakref.ref(widget))
        return widget


class Widget(QtWidgets.QWidget):
    """ Superclass for all Widgets. All Widgets are subclasses of QWidget. """

    def __init__(self, options, *args, **kwargs):
        self._options = options
        super().__init__(*args, **kwargs)

    def replaceWithError(self, errorText):
        errorLabel = QtWidgets.QLabel(errorText)

        grid = QtWidgets.QGridLayout()
        QtWidgets.QWidget().setLayout(self.layout())  # unset layout
        self.setLayout(grid)
        grid.addWidget(errorLabel)


# Copyright (C) 2020, 2021TestaLab
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
