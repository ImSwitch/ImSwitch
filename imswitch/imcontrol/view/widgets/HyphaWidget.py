import webbrowser
from PyQt5 import QtWidgets, QtWebEngineWidgets
import numpy as np
import pyqtgraph as pg
from imswitch.imcontrol.view import guitools
from qtpy import QtCore, QtWidgets
from imswitch.imcommon.model import initLogger
from .basewidgets import Widget
from imjoy_rpc.hypha.sync import login


class HyphaWidget(Widget):
    """ Widget containing Hypha interface. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        self._webrtcURL = ""
        
        self.tabWidget = QtWidgets.QTabWidget(self)
        
        # add a button to login to the Hypha server
        self._hypha_login = QtWidgets.QPushButton('Login to Hypha')
        self._hypha_login.clicked.connect(self._login_to_hypha)

        # have a simple text field that determines the webrtc name address
        self._webrtc_service_name_label = QtWidgets.QLabel('WebRTC Service name')
        self._webrtc_service_name = QtWidgets.QLineEdit()
        
        # set the URL for the chat service
        self._chatURLLabel = QtWidgets.QLabel('Chat URL')
        self._chatURL = "https://imjoy.io"
        self._chatURLTextEdit =  QtWidgets.QLineEdit()
        self._chatURLTextEdit.setText(self._chatURL)
        self._chatURLButton = QtWidgets.QPushButton('Set Chat URL')
        self._chatURLButton.clicked.connect(self.setChatURL)

        # have a simple link that on click opens the browser with the URL provided by the controller
        self._webrtc_link = QtWidgets.QPushButton('Open WebRTC link')
        
        # connect the gui ellements to functions 
        self._webrtc_link.clicked.connect(self._open_webrtc_link)
        
        # add all gui elements to a simple grid layout
        self._layout = QtWidgets.QGridLayout()
        self._layout.addWidget(self._hypha_login, 0, 0)
        self._layout.addWidget(self._webrtc_service_name_label, 0, 1)
        self._layout.addWidget(self._webrtc_service_name, 0, 2)
        self._layout.addWidget(self._chatURLLabel, 1, 0)
        self._layout.addWidget(self._chatURLTextEdit, 1, 1)
        self._layout.addWidget(self._chatURLButton, 1, 2)
        
        self._layout.addWidget(self._webrtc_link, 2, 0)
        
        # Add the first tab
        self.tab1 = QtWidgets.QWidget()
        self.tab1.setLayout(self._layout)
        self.tabWidget.addTab(self.tab1, "Hypha Login")
        
        # add a webview to the tab widget
        # Create the second tab
        self.tab2 = QtWidgets.QWidget()
        self.tab2_layout = QtWidgets.QVBoxLayout(self.tab2)

        # Add a web view to the second tab
        self.webView = QtWebEngineWidgets.QWebEngineView()
        self.webView.load(QtCore.QUrl("https://imjoy.io/"))  # Replace with your desired URL
        self.tab2_layout.addWidget(self.webView)

        # Add the second tab to the tab widget
        self.tabWidget.addTab(self.tab2, "Chat")

        # set layout 
        # Add the self.tabWidget to the main layout of the widget
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.addWidget(self.tabWidget)
        self.setLayout(mainLayout)        
        
    def setHyphaURL(self, url):
        """ Set the URL of the Hypha server. """
        self._webrtcURL = url
        
    def setChatURL(self, url=None):
        """ Set the URL of the chat. """
        if url is None or not url:
            url = self._chatURLTextEdit.text()
            
        self._chatURL = url
        try:
            self.webView.load(QtCore.QUrl(self._chatURL))
        except Exception as e:
            self.__logger.error(f"Could not load URL {url}: {e}")
            
    def _open_webrtc_link(self):
        """ Open the browser with the URL self._webrtcURL. """
        webbrowser.open(f"https://oeway.github.io/webrtc-hypha-demo/?service_id={self._webrtc_service_name.text()}")
        
    def _login_callback(self, context):
        """
        Callback function for login.
        This function is used for display the login URL,
        Or launch the browser, display a QR code etc. for the user to login
        Once done, it should return;

        The context is a dictionary contains the following keys:
        - login_url: the login URL
        - report_url: the report URL
        - key: the key for the login
        """
        self.__logger.debug(f"Please go to the login url: {context['login_url']}")
        webbrowser.open(context['login_url'])
        
    def _login_to_hypha(self):
        """ Login to the Hypha server. """
        
        # try to load token from .hypha-token file
        # try:
        #     with open(".hypha-token", "r") as f:
        #         token_info = json.loads(f.read())
        #         token = token_info["token"]
        #         # check if the token is expired
        #         if time.time() - token_info["time"] > 3600 * 12:
        #             raise Exception("Token expired")
        # except Exception:
        #     token = await login({"server_url": SERVER_URL})
        #     # write token into .hypha-token file and save the current time as json file
        #     with open(".hypha-token", "w") as f:
        #         f.write(json.dumps({"token": token, "time": time.time()}))
        
        # Documentation about the login function: https://ha.amun.ai/#/
        token = login({"server_url": "https://ai.imjoy.io", "login_callback": self._login_callback})
        # show alert if login successful
        self.__logger.debug(f'Login successful, token: {token}')
        # TODO: pass it to connect_to_server({....token: token})
    
        
        
        
    
    
    
        
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






