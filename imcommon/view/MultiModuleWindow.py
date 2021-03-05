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
