from dataclasses import dataclass
from qtpy import QtCore, QtWidgets

from imswitch.imcommon.model import initLogger
from arkitekt.qt.magic_bar import MagicBar


class MikroMainView(QtWidgets.QMainWindow):
    sigLoadParamsFromHDF5 = QtCore.Signal()
    sigPickSetup = QtCore.Signal()
    sigClosing = QtCore.Signal()

    def __init__(self, app, *args, **kwargs):
        self.__logger = initLogger(self)
        self.__logger.debug("Initializing")

        super().__init__(*args, **kwargs)

        self.app = app

        self.magic_bar = MagicBar(self.app, dark_mode=True)

        # Menu Bar
        menuBar = self.menuBar()
        file = menuBar.addMenu("&File")
        tools = menuBar.addMenu("&Tools")
        self.shortcuts = menuBar.addMenu("&Shortcuts")

        self.loadParamsAction = QtWidgets.QAction(
            "Load parameters from saved HDF5 file…", self
        )
        self.loadParamsAction.setShortcut("Ctrl+P")
        self.loadParamsAction.triggered.connect(self.sigLoadParamsFromHDF5)
        file.addAction(self.loadParamsAction)

        self.pickSetupAction = QtWidgets.QAction("Pick hardware setup…", self)
        self.pickSetupAction.triggered.connect(self.sigPickSetup)
        tools.addAction(self.pickSetupAction)

        # Window
        self.setWindowTitle("ImArkitekt")

        self.cwidget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        self.cwidget.setLayout(layout)
        self.setCentralWidget(self.cwidget)

        layout.addWidget(self.magic_bar)
        layout.addStretch()

        # Maximize window
        # self.showMaximized()
        self.hide()  # Minimize time the window is displayed while loading multi module window


@dataclass
class _DockInfo:
    name: str
    yPosition: int


# Copyright (C) 2020-2021 ImSwitch developers
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
