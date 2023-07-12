import numpy as np
import pyqtgraph as pg
from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools
from .basewidgets import Widget


class HyphaWidget(Widget):
    """ Widget containing Hypha interface. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._webrtcURL = ""
        # have a simple text field that determines the webrtc name address
        self._webrtc_name_label = QtWidgets.QLabel('WebRTC name')
        self._webrtc_name = QtWidgets.QLineEdit()
        
        # have a simple link that on click opens the browser with the URL provided by the controller
        self._webrtc_link = QtWidgets.QPushButton('Open WebRTC link')
        
        # connect the gui ellements to functions 
        self._webrtc_link.clicked.connect(self._open_webrtc_link)
        
        # add all gui elements to a simple grid layout
        self._layout = QtWidgets.QGridLayout()
        self._layout.addWidget(self._webrtc_name_label, 0, 0)
        self._layout.addWidget(self._webrtc_name, 0, 1)
        self._layout.addWidget(self._webrtc_link, 1, 0, 1, 2)
        
    def setHyphaURL(self, url):
        """ Set the URL of the Hypha server. """
        self._webrtcURL = url
        
    def _open_webrtc_link(self):
        """ Open the browser with the URL self._webrtcURL. """
        pass
        
        
    
        
        
        
    
    
    
        
# Copyright (C) 2020-2021 ImSwitch developers
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
