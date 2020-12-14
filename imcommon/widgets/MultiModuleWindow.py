from pyqtgraph.Qt import QtCore, QtGui


class MultiModuleWindow(QtGui.QMainWindow):
    closing = QtCore.pyqtSignal()

    def __init__(self, modules, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('ImSwitch')

        # Add tabs
        self.moduleTabs = QtGui.QTabWidget()
        self.moduleTabs.setTabPosition(QtGui.QTabWidget.TabPosition.West)

        for moduleName, moduleWidget in modules:
            self.moduleTabs.addTab(moduleWidget, moduleName)

        self.setCentralWidget(self.moduleTabs)

        # Maximize window
        self.showMaximized()
