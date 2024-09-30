from qtpy import QtCore, QtWidgets
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QTextEdit
from PyQt5.QtWidgets import QGridLayout

from imswitch.imcommon.view.guitools import pyqtgraphtools
from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget



class ObjectiveRevolverWidget(NapariHybridWidget):
    """ Displays the ObjectiveRevolver transform of the image. """

    def __post_init__(self):
        # Create widgets
        self.btnObj1 = QPushButton("Objective 1", self)
        self.btnObj2 = QPushButton("Objective 2", self)
        
        self.lblPosObj1 = QLabel("Pos Objective 1", self)
        self.txtPosObj1 = QTextEdit(self)
        self.lblPosObj2 = QLabel("Pos Objective 2", self)
        self.txtPosObj2 = QTextEdit(self)

        self.btnCalibrate = QPushButton("Calibrate", self)
        self.btnMovePlus = QPushButton("Move +", self)
        self.btnMoveMinus = QPushButton("Move -", self)
        self.btnSetPosObj1 = QPushButton("Set Position Objective 1", self)

        self.lblCurrentObjective = QLabel("Current Objective:", self)
        
        # Grid layout
        layout = QGridLayout()
        layout.addWidget(self.btnObj1, 0, 0)
        layout.addWidget(self.btnObj2, 0, 1)
        layout.addWidget(self.lblPosObj1, 1, 0)
        layout.addWidget(self.txtPosObj1, 1, 1)
        layout.addWidget(self.lblPosObj2, 2, 0)
        layout.addWidget(self.txtPosObj2, 2, 1)
        layout.addWidget(self.btnCalibrate, 3, 0) 
        layout.addWidget(self.btnSetPosObj1, 3, 1)
        layout.addWidget(self.btnMovePlus, 4, 0)
        layout.addWidget(self.btnMoveMinus, 4, 1    )
        layout.addWidget(self.lblCurrentObjective, 5, 0) # Spanning two columns

        # Set the layout to the main window
        self.setLayout(layout)
        
    def setCurrentObjectiveInfo(self, currentObjective):
        self.lblCurrentObjective.setText("Current Objective: " + str(currentObjective))
        
# Copyright (C) 2020-2024 ImSwitch developers
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
