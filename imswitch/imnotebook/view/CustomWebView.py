from PyQt5.QtCore import pyqtSlot, QSettings, QTimer, QUrl, Qt
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QDockWidget, QPlainTextEdit, QTabWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView as QWebView, QWebEnginePage as QWebPage
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtWebEngineWidgets import QWebEngineProfile
from PyQt5.QtCore import QSettings, QDir, QObject, pyqtSignal, QUrl
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QApplication
SETTING_BASEDIR = "io.github.openuc2/JupyterQt/basedir"
SETTING_EXECUTABLE = "io.github.openuc2/JupyterQt/executable"
DEBUG = True



class CustomWebView(QWebView):

    def __init__(self, mainwindow, log=None, main=False):
        super(CustomWebView, self).__init__(None)
        self.log = log          
        self.parent = mainwindow
        self.tabIndex = -1
        self.main = main
        self.loadedPage = None
        self.loadFinished.connect(self.onpagechange)

    @pyqtSlot(bool)
    def onpagechange(self, ok):
        self.log("on page change: %s, %s" % (self.url(), ok))
        if self.loadedPage is not None:
            self.log("disconnecting on close and linkclicked signal")
            self.loadedPage.windowCloseRequested.disconnect(self.close)
            self.loadedPage.selectionChanged.disconnect(self.handlelink)

        self.log("connecting on close and linkclicked signal")
        self.loadedPage = self.page()
        interceptor = MyUrlRequestInterceptor()
        profile = QWebEngineProfile.defaultProfile()
        profile.setUrlRequestInterceptor(interceptor)
        self.loadedPage.windowCloseRequested.connect(self.close)
        self.loadedPage.urlChanged.connect(self.handlelink)
        self.setWindowTitle(self.title())
        if not self.main:
            self.parent.tabs.setTabText(self.tabIndex, self.title())
        if not ok:
            QMessageBox.information(self, "Error", "Error loading page!", QMessageBox.Ok)
            
    @pyqtSlot(QUrl)
    def handlelink(self, url):
        urlstr = url.toString()
        self.log("handling link : %s" % urlstr)
        # check if url is for the current page
        if url.matches(self.url(), QUrl.RemoveFragment):
            # do nothing, probably a JS link
            return True

        # check other windows to see if url is loaded there
        for i in range(len(self.parent.tabs)):
            window = self.parent.tabs.widget(i)
            if url.matches(window.url(), QUrl.RemoveFragment):
                self.parent.tabs.setCurrentIndex(i)
                # if this is a tree window and not the main one, close it
                if self.url().toString().startswith(self.parent.homepage + "tree") and not self.main:
                    QTimer.singleShot(0, self.close)  # calling self.close() is no good
                return True

        if "/files/" in urlstr:
            # save, don't load new page
            self.parent.savefile(url)
        elif "/tree/" in urlstr or urlstr.startswith(self.parent.homepage + "tree"):
            # keep in same window
            self.load(url)
        else:
            # open in new window
            newwindow = self.parent.createBrowserTab(QWebPage.WebBrowserWindow, js=False)
            newwindow.load(url)

        # if this is a tree window and not the main one, close it
        if self.url().toString().startswith(self.parent.homepage + "/tree") and not self.main:
            QTimer.singleShot(0, self.close) # calling self.close() is no good
        return True

    def createWindow(self, windowtype):
        return self.parent.createBrowserTab(windowtype, js=True)

    def closeEvent(self, event):
        if self.loadedPage is not None:
            self.log("disconnecting on close and linkClicked signals")
            self.loadedPage.windowCloseRequested.disconnect(self.close)
            self.loadedPage.linkClicked.disconnect(self.handlelink)

        if not self.main:
            if self in self.parent.windows:
                self.parent.windows.remove(self)
            self.log("Window count: %s" % (len(self.parent.windows)+1))
        event.accept()
