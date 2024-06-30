import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import  QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel

from imswitch.imcontrol.view import guitools
from .basewidgets import Widget


class UC2ConfigWidget(Widget):
    """ Widget containing UC2Config interface. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize the main layout
        mainLayout = QVBoxLayout()

        # Buttons for device and PS controller
        reconnectLayout = QHBoxLayout()
        self.reconnectDeviceLabel = QLabel("State:", self)
        self.reconnectButton = QPushButton("Reconnect to Device", self)
        self.reconnectBaudrateLabel = QLabel("Baudrate:", self)
        self.reconnectBaudrateEdit = QLineEdit(self)
        reconnectLayout.addWidget(self.reconnectButton)
        reconnectLayout.addWidget(self.reconnectDeviceLabel)
        reconnectLayout.addWidget(self.reconnectBaudrateLabel)
        reconnectLayout.addWidget(self.reconnectBaudrateEdit)

        self.stopCommunicationButton = QPushButton("Interrupt communication", self)
        reconnectLayout.addWidget(self.stopCommunicationButton)
        
        self.btpairingButton = QPushButton("Connect to PS Controller", self)

        # Layout for motor positions
        motorsLayout = QHBoxLayout()

        self.motorALabel = QLabel("Motor A:", self)
        self.motorAEdit = QLineEdit(self)
        self.motorAEdit.setText("0")

        self.motorXLabel = QLabel("Motor X:", self)
        self.motorXEdit = QLineEdit(self)
        self.motorXEdit.setText("0")
        
        self.motorYLabel = QLabel("Motor Y:", self)
        self.motorYEdit = QLineEdit(self)
        self.motorYEdit.setText("0")

        self.motorZLabel = QLabel("Motor Z:", self)
        self.motorZEdit = QLineEdit(self)
        self.motorZEdit.setText("0")

        motorsLayout.addWidget(self.motorALabel)
        motorsLayout.addWidget(self.motorAEdit)
        motorsLayout.addWidget(self.motorXLabel)
        motorsLayout.addWidget(self.motorXEdit)
        motorsLayout.addWidget(self.motorYLabel)
        motorsLayout.addWidget(self.motorYEdit)
        motorsLayout.addWidget(self.motorZLabel)
        motorsLayout.addWidget(self.motorZEdit)

        # Button to set motor positions per Axis 
        # Layout for motor positions
        motorsBtnLayout = QHBoxLayout()

        self.setPositionXBtn = QPushButton("Set Motor X Position", self)
        self.setPositionYBtn = QPushButton("Set Motor Y Position", self)
        self.setPositionZBtn = QPushButton("Set Motor Z Position", self)
        self.setPositionABtn = QPushButton("Set Motor A Position", self)
        motorsBtnLayout.addWidget(self.setPositionXBtn)
        motorsBtnLayout.addWidget(self.setPositionYBtn)
        motorsBtnLayout.addWidget(self.setPositionZBtn)
        motorsBtnLayout.addWidget(self.setPositionABtn)
        
        # Button for motor auto enable
        self.autoEnableBtn = QPushButton("Set Auto Enable", self)
        self.unsetAutoEnableBtn = QPushButton("Unset Auto Enable", self)

        # Add widgets to main layout
        mainLayout.addLayout(reconnectLayout)
        mainLayout.addWidget(self.btpairingButton)
        mainLayout.addLayout(motorsLayout)
        mainLayout.addLayout(motorsBtnLayout)
        mainLayout.addWidget(self.autoEnableBtn)
        mainLayout.addWidget(self.unsetAutoEnableBtn)

        self.setLayout(mainLayout)

    def setBaudRateGui(self, baudrate):
        self.reconnectBaudrateEdit.setText(str(baudrate))
        
    def getBaudRateGui(self):
        try:return int(self.reconnectBaudrateEdit.text())
        except:return None

            
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
