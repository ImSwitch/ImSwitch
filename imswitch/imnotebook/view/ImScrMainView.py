from imswitch import IS_HEADLESS
from qtpy import QtCore, QtWidgets
from imswitch.imcommon.model import dirtools


if not IS_HEADLESS:
    from PyQt5.QtCore import pyqtSlot, QSettings, QTimer, QUrl, Qt
    from PyQt5.QtGui import QCloseEvent
    from PyQt5.QtWidgets import QMainWindow, QMessageBox, QDockWidget, QPlainTextEdit, QTabWidget
    from PyQt5.QtCore import QSettings, QDir, QObject, pyqtSignal, QUrl
    from PyQt5.QtWidgets import QFileDialog, QMessageBox, QApplication
    from .MainWindow import MainWindow
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView as QWebView, QWebEnginePage as QWebPage
    from PyQt5.QtWebEngineWidgets import QWebEngineView as QWebView, QWebEnginePage as QWebPage
    from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
    from PyQt5.QtWebEngineWidgets import QWebEngineProfile
    IS_QTWEBENGINE = True
except:
    IS_QTWEBENGINE = False

from .logger import set_logger
from .notebook_process import testnotebook, startnotebook, stopnotebook
import os
import sys
from .logger import log

SETTING_BASEDIR = "io.github.openuc2/JupyterQt/basedir"
SETTING_EXECUTABLE = "io.github.openuc2/JupyterQt/executable"
DEBUG = True


class LaunchNotebookServer:
    
    def __init__(self):
        pass
    
    def startServer(self):

        python_exec_path = os.path.dirname(sys.executable)
        execname = os.path.join(python_exec_path, 'jupyter-notebook')
        
        # check if jupyter notebook is installed
        if not testnotebook(execname):
            if not IS_HEADLESS: QMessageBox.information(None, "Error", "It appears that Jupyter Notebook isn't where it usually is. " +
                                    "Ensure you've installed Jupyter correctly in your current environment "+
                                    "test it by running  'jupyter-notebook' in your terminal"+ 
                                    "ImSwitch will run without it now. If you don't wanted to "+
                                    "use imnotebook module in the firstplace, remove it from the config.json", QMessageBox.Ok)
            else: print("No jupyter notebook found")
            return False
                
        directory = None
        directory =  os.path.join(dirtools.UserFileDirs.Root, "imnotebook")
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # start the notebook process
        webaddr = startnotebook(execname, directory=directory)
        return webaddr
    


class ImScrMainView(QtWidgets.QMainWindow):
    """ Main self.view of ImNotebook. """
    
    sigClosing = QtCore.Signal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Notebook')
        
        # Actions in menubar
        if IS_HEADLESS:
            return 
        
        # test and launch notebook server        
        notebookServer = LaunchNotebookServer()
        webaddr = notebookServer.start()

        # setup webview
        self.view = MainWindow(None, None)
        self.view.setWindowTitle("JupyterQt%s")

        # redirect logging to self.view.loggerdock.log
        class QtLogger(QObject):
            newlog = pyqtSignal(str)

            def __init__(self, parent):
                super(QtLogger, self).__init__(parent)

        qtlogger = QtLogger(self.view)
        qtlogger.newlog.connect(self.view.loggerdock.log)
        set_logger(lambda message: qtlogger.newlog.emit(message))

        # start the notebook process
        self.view.loadmain(webaddr)

        # if notebook file is trying to get opened, open that window as well
        file = None
        if file is not None and file.endswith('.ipynb'):
            self.view.basewebview.handlelink(QUrl(webaddr + 'notebooks/' + file))
        elif file is not None and file.endswith('.jproj'):
            pass
        elif file is not None:
            # unrecognized file type
            QMessageBox.information(None, "Error", "File type of %s was unrecognized" % file, QMessageBox.Ok)

        self.setCentralWidget(self.view)

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
