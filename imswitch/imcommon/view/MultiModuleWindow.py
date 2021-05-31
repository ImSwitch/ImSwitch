from pyqtgraph.Qt import QtCore, QtGui, QtWidgets

from imswitch.imcommon.model import APIExport


class MultiModuleWindow(QtWidgets.QMainWindow):
    sigPickModules = QtCore.Signal()

    def __init__(self, title, iconPath=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._moduleIdNameMap = {}

        self.setWindowTitle(title)
        if iconPath:
            self.setWindowIcon(QtGui.QIcon(iconPath))

        # Create fallback menu bar
        self._addItemsToMenuBar(self.menuBar())

        # Add tabs
        self.moduleTabs = QtWidgets.QTabWidget()
        self.moduleTabs.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)

        self.setCentralWidget(self.moduleTabs)

    def addModule(self, moduleId, moduleName, moduleWidget):
        self._moduleIdNameMap[moduleId] = moduleName
        self.moduleTabs.addTab(moduleWidget, moduleName)

        if hasattr(moduleWidget, 'menuBar') and callable(moduleWidget.menuBar):
            # Module widget has menu bar; add common items and hide fallback menu bar
            self._addItemsToMenuBar(moduleWidget.menuBar())
            self.menuBar().hide()

    def _addItemsToMenuBar(self, menuBar):
        menuChildren = menuBar.findChildren(QtWidgets.QMenu, None, QtCore.Qt.FindDirectChildrenOnly)
        toolsMenu = None
        for menuChild in menuChildren:
            if menuChild.title() == '&Tools':
                toolsMenu = menuChild
                break

        if toolsMenu is None:
            toolsMenu = menuBar.addMenu('&Tools')

        if not toolsMenu.isEmpty():
            toolsMenu.addSeparator()

        pickModulesAction = QtWidgets.QAction('Set active modules…', self)
        pickModulesAction.triggered.connect(self.sigPickModules)
        toolsMenu.addAction(pickModulesAction)

    @APIExport
    def setCurrentModule(self, moduleId):
        """ Sets the currently displayed module to the module with the
        specified ID (e.g. "imcontrol"). """
        moduleName = self._moduleIdNameMap[moduleId]
        for i in range(self.moduleTabs.count()):
            if self.moduleTabs.tabText(i) == moduleName:
                self.moduleTabs.setCurrentIndex(i)
                return

    def show(self):
        super().show()
        self.showMaximized()


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
