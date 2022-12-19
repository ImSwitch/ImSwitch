import uuid

from PyQt5.QtWebEngineWidgets import *
from PyQt5 import Qsci
from qtpy import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


from .guitools import BetterPushButton


class BlocklyView(QtWidgets.QTabWidget):
    """ View that displays a variable amount of blockly instances in different
    tabs, where the user can edit scripts. """

    sigRunAllClicked = QtCore.Signal(str, str)  # (instanceID, text)
    sigRunSelectedClicked = QtCore.Signal(str, str)  # (instanceID, selectedText)
    sigStopClicked = QtCore.Signal(str)  # (instanceID)
    sigTextChanged = QtCore.Signal(str)  # (instanceID)
    sigInstanceCloseClicked = QtCore.Signal(str)  # (instanceID)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        '''
        self.setTabsClosable(True)

        self.tabCloseRequested.connect(
            lambda index: self.sigInstanceCloseClicked.emit(self.widget(index).getID())
        )
        '''
        
        self.url = "http://0.0.0.0:1889/imblockly/view/static/index.html"
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl(self.url))

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        topContainer = QtWidgets.QHBoxLayout()
        topContainer.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(topContainer, 0)
        
        topContainer.addWidget(self.browser, 0)
        






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
