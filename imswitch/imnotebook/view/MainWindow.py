from imswitch import IS_HEADLESS
from pyqtgraph.dockarea import Dock, DockArea
from qtpy import QtCore, QtWidgets

from PyQt5.QtCore import pyqtSlot, QSettings, QTimer, QUrl, Qt
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QDockWidget, QPlainTextEdit, QTabWidget
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView as QWebView, QWebEnginePage as QWebPage
    from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
    from PyQt5.QtWebEngineWidgets import QWebEngineProfile
    IS_QTWEBENGINE = True
except:
    IS_QTWEBENGINE = False
from PyQt5.QtCore import QSettings, QDir, QObject, pyqtSignal, QUrl
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QApplication

from .logger import log, setup_logging, set_logger
from .CustomWebView import CustomWebView
from .notebook_process import testnotebook, startnotebook, stopnotebook
import os
import sys
from .logger import log

SETTING_GEOMETRY = "io.github.openuc2/JupyterQt/geometry"



class LoggerDock(QDockWidget):

    def __init__(self, *args):
        super(LoggerDock, self).__init__(*args)
        self.textView = QPlainTextEdit(self)
        self.textView.setReadOnly(True)
        self.setWidget(self.textView)

    @pyqtSlot(str)
    def log(self, message):
        self.textView.appendPlainText(message)


class MainWindow(QMainWindow):

    def __init__(self, parent=None, homepage=None):
        if not IS_QTWEBENGINE: return
        super(MainWindow, self).__init__(parent)
        self.homepage = homepage
        self.windows = []

        self.loggerdock = LoggerDock("Log Message", self)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.loggerdock)

        settings = QSettings()
        val = settings.value(SETTING_GEOMETRY, None)
        if val is not None:
            self.restoreGeometry(val)

        self.basewebview = CustomWebView(self, log=log, main=True)
        self.windows.append(self.basewebview)
        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.destroyBrowserTab)
        self.basewebview.tabIndex = self.tabs.addTab(self.basewebview, "File Browser")

        self.setCentralWidget(self.tabs)

    def loadmain(self, homepage):
        self.homepage = homepage
        QTimer.singleShot(0, self.initialload)

    def createBrowserTab(self, windowtype, js=True):
        v = CustomWebView(self)
        self.windows.append(v)
        log("Window count: %s" % (len(self.windows)+1))
        v.tabIndex = self.tabs.addTab(v, "Window %s" % (len(self.windows)+1))
        self.tabs.setCurrentIndex(v.tabIndex)
        return v

    @pyqtSlot(int)
    def destroyBrowserTab(self, which):
        closeevent = QCloseEvent()
        win = self.tabs.widget(which)
        if win.main:
            self.close()
        else:
            win.closeEvent(closeevent)
            if closeevent.isAccepted():
                self.tabs.removeTab(which)

    @pyqtSlot()
    def initialload(self):
        if self.homepage:
            self.basewebview.load(QUrl(self.homepage))
        self.show()

    def savefile(self, url):
        pass

    def closeEvent(self, event):
        if len(self.windows) > 1:
            if QMessageBox.Ok == QMessageBox.information(self, "Really Close?",
                                                         "Really close %s tabs?" % (len(self.windows)),
                                                         QMessageBox.Cancel | QMessageBox.Ok):
                for i in reversed(range(len(self.windows))):
                    w = self.windows.pop(i)
                    w.close()
                event.accept()
            else:
                event.ignore()
                return
        else:
            event.accept()

        # save geometry
        settings = QSettings()
        settings.setValue(SETTING_GEOMETRY, self.saveGeometry())


    def closeEvent(self, event):
        self.sigClosing.emit()
        event.accept()
        
