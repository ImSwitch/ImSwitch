from qtpy import QtCore, QtWidgets, QtGui

from imswitch.imcontrol.view import guitools
from .basewidgets import Widget
import os


class TilingWidget(Widget):
    """ Widget that watch for new script files (.py) in a specific folder, for running them sequentially."""

    sigSaveFocus = QtCore.Signal(bool)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.skipTileButton = guitools.BetterPushButton("Skip tile")
        self.registerFocusButton = guitools.BetterPushButton("Register focus")
        self.tileNumberEdit = QtWidgets.QLabel("Tile Number: 0/0")

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        layout.addWidget(self.tileNumberEdit, 0, 0)
        layout.addWidget(self.registerFocusButton, 0, 1)
        layout.addWidget(self.skipTileButton, 0, 2)

        self.registerFocusButton.clicked.connect(lambda: self.sigSaveFocus.emit(True))
        self.skipTileButton.clicked.connect(lambda: self.sigSaveFocus.emit(False))

    def setLabel(self, label):
        self.tileNumberEdit.setText(label)

# Copyright (C) 2020-2023 ImSwitch developers
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
