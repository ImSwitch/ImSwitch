from pyqtgraph.Qt import QtGui


class BetterPushButton(QtGui.QPushButton):
    """BetterPushButton is a QPushButton that does not become too small when
    styled."""

    def __init__(self, text=None, minMinWidth=20, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self._minMinWidth = minMinWidth
        self.updateMinWidth(text)

    def setText(self, text, *args, **kwargs):
        super().setText(text, *args, **kwargs)
        self.updateMinWidth(text)

    def updateMinWidth(self, text=None):
        if text is None:
            text = self.text()

        fontMetrics = QtGui.QFontMetrics(self.font())
        textWidth = fontMetrics.width(text)
        minWidth = max(self._minMinWidth, textWidth + 8)
        self.setStyleSheet(f'min-width: {minWidth}px')

# Copyright (C) 2020, 2021 Staffan Al-Kadhimi, Xavier Casas, Andreas Boden
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