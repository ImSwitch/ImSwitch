import imswitch
from pyqtgraph.dockarea import Dock, DockArea
from qtpy import QtCore, QtWidgets

from PyQt5.QtCore import pyqtSlot, QSettings, QTimer, QUrl, Qt
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QDockWidget, QPlainTextEdit, QTabWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView as QWebView, QWebEnginePage as QWebPage
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtWebEngineWidgets import QWebEngineProfile
from PyQt5.QtCore import QSettings, QDir, QObject, pyqtSignal, QUrl
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QApplication

from .logger import log, setup_logging, set_logger
from .CustomWebView import CustomWebView
from .MainWindow import MainWindow
from .notebook_process import testnotebook, startnotebook, stopnotebook
import os
import sys
from .logger import log

SETTING_BASEDIR = "io.github.openuc2/JupyterQt/basedir"
SETTING_EXECUTABLE = "io.github.openuc2/JupyterQt/executable"
DEBUG = True


class ImScrMainView(QtWidgets.QMainWindow):
    """ Main self.view of ImNotebook. """
    
    sigClosing = QtCore.Signal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Notebook')
        
        # Actions in menubar
        if imswitch.IS_HEADLESS:
            return 
        
        # setup application
        python_exec_path = os.path.dirname(sys.executable)
        execname = os.path.join(python_exec_path, 'jupyter-notebook')

        if not testnotebook(execname):
            while True:
                QMessageBox.information(None, "Error", "It appears that Jupyter Notebook isn't where it usually is. " +
                                        "Ensure you've installed Jupyter correctly and then press Ok to " +
                                        "find the executable 'jupyter-notebook'", QMessageBox.Ok)
                if testnotebook(execname):
                    break
                
        # setup logging
        # try to write to a log file, or redirect to stdout if debugging
        logfile = os.path.join(str(QDir.homePath()), ".JupyterQt", "JupyterQt.log")
            
        setup_logging(None)

        log("Setting home directory...")
        directory = None
        file = None

        directory = QDir.homePath()
        log("Setting up GUI")

        # setup webview
        self.view = MainWindow(None, None)
        self.view.setWindowTitle("JupyterQt: %s" % directory)

        # redirect logging to self.view.loggerdock.log
        class QtLogger(QObject):
            newlog = pyqtSignal(str)

            def __init__(self, parent):
                super(QtLogger, self).__init__(parent)

        qtlogger = QtLogger(self.view)
        qtlogger.newlog.connect(self.view.loggerdock.log)
        set_logger(lambda message: qtlogger.newlog.emit(message))

        # start the notebook process
        webaddr = startnotebook(execname, directory=directory)
        self.view.loadmain(webaddr)

        # if notebook file is trying to get opened, open that window as well
        if file is not None and file.endswith('.ipynb'):
            self.view.basewebview.handlelink(QUrl(webaddr + 'notebooks/' + file))
        elif file is not None and file.endswith('.jproj'):
            pass
        elif file is not None:
            # unrecognized file type
            QMessageBox.information(None, "Error", "File type of %s was unrecognized" % file, QMessageBox.Ok)

        log("Starting Qt Event Loop")
        self.setCentralWidget(self.view)

        # resume regular logging
        setup_logging(logfile)

    def closeEvent(self, event):
        #self.sigClosing.emit()
        event.accept()
        # stop the notebook process
        stopnotebook()



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
