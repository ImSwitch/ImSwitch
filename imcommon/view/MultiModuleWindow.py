from pyqtgraph.Qt import QtWidgets


class MultiModuleWindow(QtWidgets.QMainWindow):
    def __init__(self, title, modules=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle(title)

        # Add tabs
        self.moduleTabs = QtWidgets.QTabWidget()
        self.moduleTabs.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)

        self.modules = {}
        if modules is not None:
            for moduleName, moduleWidget in modules.items():
                self.addModule(moduleName, moduleWidget)

        self.setCentralWidget(self.moduleTabs)

    def addModule(self, moduleName, moduleWidget):
        self.moduleTabs.addTab(moduleWidget, moduleName)
        self.modules[moduleName] = moduleWidget

    def show(self):
        super().show()
        self.showMaximized()

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