from qdarkstyle import DarkPalette
from qtpy import QtCore, QtWidgets

from .AboutDialog import AboutDialog
from .CheckUpdatesDialog import CheckUpdatesDialog
from .PickModulesDialog import PickModulesDialog


class MultiModuleWindow(QtWidgets.QMainWindow):
    sigPickModules = QtCore.Signal()
    sigOpenUserDir = QtCore.Signal()
    sigShowDocs = QtCore.Signal()
    sigCheckUpdates = QtCore.Signal()
    sigShowAbout = QtCore.Signal()

    sigModuleAdded = QtCore.Signal(str, str)  # (moduleId, moduleName)

    def __init__(self, title, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.moduleWidgets = {}

        self.setWindowTitle(title)

        self.pickModulesDialog = PickModulesDialog(self)
        self.checkUpdatesDialog = CheckUpdatesDialog(self)
        self.aboutDialog = AboutDialog(self)

        # Add tabs
        self.moduleTabs = QtWidgets.QTabWidget()
        self.moduleTabs.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)

        # RAM usage bar
        self.memBarLabel = QtWidgets.QLabel('Current RAM usage:')
        self.memBarLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.memBar = QtWidgets.QProgressBar()
        self.memBar.setMaximum(100)  # Percentage
        self.memBar.setStyleSheet(
            f'min-width: 320px;'
            f'border: 1px solid {DarkPalette.COLOR_BACKGROUND_5};'
            f'background-color: {DarkPalette.COLOR_BACKGROUND_1};'
        )

        self.memBarContainer = QtWidgets.QWidget()
        self.memBarContainer.setStyleSheet('background-color: transparent;')
        self.memBarContainerLayout = QtWidgets.QHBoxLayout()
        self.memBarContainerLayout.setContentsMargins(0, 2, 6, 4)
        self.memBarContainerLayout.addWidget(self.memBarLabel, 1)
        self.memBarContainerLayout.addWidget(self.memBar)
        self.memBarContainer.setLayout(self.memBarContainerLayout)

        self.statusBar().addPermanentWidget(self.memBarContainer)

        # Display loading screen until show(showLoadingScreen=False) is called
        loadingLabel = QtWidgets.QLabel('<h1>Starting ImSwitch…</h1>')
        loadingLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.loadingProgressBar = QtWidgets.QProgressBar()
        self.loadingProgressBar.setMaximumWidth(480)
        self.loadingProgressBar.setValue(0)
        self.loadingProgressBar.setTextVisible(False)

        loadingLayout = QtWidgets.QVBoxLayout()
        loadingLayout.setAlignment(QtCore.Qt.AlignCenter)
        loadingLayout.setSpacing(32)
        loadingLayout.addWidget(loadingLabel)
        loadingLayout.addWidget(self.loadingProgressBar)

        loadingContainer = QtWidgets.QWidget()
        loadingContainer.setLayout(loadingLayout)
        self.setCentralWidget(loadingContainer)

    def addModule(self, moduleId, moduleName, moduleWidget):
        self.moduleWidgets[moduleName] = moduleWidget
        self.moduleTabs.addTab(moduleWidget, moduleName)

        if hasattr(moduleWidget, 'menuBar') and callable(moduleWidget.menuBar):
            # Module widget has menu bar; add common items and hide fallback menu bar
            moduleWidget.menuBar().setNativeMenuBar(False)
            self.addItemsToMenuBar(moduleWidget.menuBar())
            self.menuBar().hide()

        self.sigModuleAdded.emit(moduleId, moduleName)

    def setSelectedModule(self, moduleName):
        """ Sets the currently displayed module to the module with the
        specified display name. """
        for i in range(self.moduleTabs.count()):
            if self.moduleTabs.tabText(i) == moduleName:
                self.moduleTabs.setCurrentIndex(i)
                return

    def updateLoadingProgress(self, progressFraction):
        self.loadingProgressBar.setValue(int(progressFraction * 100))

    def updateRAMUsage(self, usageFraction):
        self.memBar.setValue(round(usageFraction * 100))

    def showPickModulesDialogBlocking(self):
        result = self.pickModulesDialog.exec_()
        return result == QtWidgets.QDialog.Accepted

    def showCheckUpdatesDialogBlocking(self):
        result = self.checkUpdatesDialog.exec_()
        return result == QtWidgets.QDialog.Accepted

    def showAboutDialogBlocking(self):
        result = self.aboutDialog.exec_()
        return result == QtWidgets.QDialog.Accepted

    def addItemsToMenuBar(self, menuBar):
        menuChildren = menuBar.findChildren(QtWidgets.QMenu, None, QtCore.Qt.FindDirectChildrenOnly)

        toolsMenu = None
        helpMenu = None
        for menuChild in menuChildren:
            if menuChild.title() == '&Tools':
                toolsMenu = menuChild
            if menuChild.title() == '&Help':
                helpMenu = menuChild

        if toolsMenu is None:
            toolsMenu = menuBar.addMenu('&Tools')
        if helpMenu is None:
            helpMenu = menuBar.addMenu('&Help')

        if not toolsMenu.isEmpty():
            toolsMenu.addSeparator()
        if not helpMenu.isEmpty():
            helpMenu.addSeparator()

        pickModulesAction = QtWidgets.QAction('Set active modules…', self)
        pickModulesAction.triggered.connect(self.sigPickModules)
        toolsMenu.addAction(pickModulesAction)

        openUserDirAction = QtWidgets.QAction('Open user files folder', self)
        openUserDirAction.triggered.connect(self.sigOpenUserDir)
        toolsMenu.addAction(openUserDirAction)

        showDocsAction = QtWidgets.QAction('Documentation', self)
        showDocsAction.triggered.connect(self.sigShowDocs)
        helpMenu.addAction(showDocsAction)

        checkUpdatesAction = QtWidgets.QAction('Check for updates…', self)
        checkUpdatesAction.triggered.connect(self.sigCheckUpdates)
        helpMenu.addAction(checkUpdatesAction)

        aboutAction = QtWidgets.QAction('About', self)
        aboutAction.triggered.connect(self.sigShowAbout)
        helpMenu.addAction(aboutAction)

    def show(self, showLoadingScreen=False):
        if not showLoadingScreen:
            # Create fallback menu bar
            self.addItemsToMenuBar(self.menuBar())

            # Show tabs
            self.setCentralWidget(self.moduleTabs)

        self.showMaximized()
        super().show()

    def closeEvent(self, event):
        QtWidgets.QApplication.instance().quit()
        event.accept()


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
