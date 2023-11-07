import numpy as np
import pyqtgraph as pg
from qtpy import QtCore, QtWidgets
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QListWidget, QWidget

from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget


class ROIScanWidget(NapariHybridWidget):
    """ Widget containing mct interface. """


    sigROIScanInitFilterPos = QtCore.Signal(bool)  # (enabled)
    sigROIScanShowLast = QtCore.Signal(bool)  # (enabled)
    sigROIScanStop = QtCore.Signal(bool)  # (enabled)
    sigROIScanStart = QtCore.Signal(bool)  # (enabled)
    sigROIScanSelectScanCoordinates = QtCore.Signal(bool)
    
    sigShowToggled = QtCore.Signal(bool)  # (enabled)
    sigPIDToggled = QtCore.Signal(bool)  # (enabled)
    sigUpdateRateChanged = QtCore.Signal(float)  # (rate)
    
    sigSliderLaser2ValueChanged = QtCore.Signal(float)  # (value)
    sigSliderLaser1ValueChanged = QtCore.Signal(float)  # (value)
    sigSliderLEDValueChanged = QtCore.Signal(float)  # (value)

    def __post_init__(self):
        #super().__init__(*args, **kwargs)
        mainLayout = QHBoxLayout() # Main layout is now horizontal

        # First section
        firstSectionLayout = QVBoxLayout()

        arrowButtonLayout = QHBoxLayout()
        self.upButton = QPushButton("↑")
        self.downButton = QPushButton("↓")
        self.leftButton = QPushButton("←")
        self.rightButton = QPushButton("→")
        arrowButtonLayout.addWidget(self.upButton)
        arrowButtonLayout.addWidget(self.downButton)
        arrowButtonLayout.addWidget(self.leftButton)
        arrowButtonLayout.addWidget(self.rightButton)
        
        focusLayout = QHBoxLayout()
        self.plusButton = QPushButton("+")
        self.minusButton = QPushButton("-")
        focusLayout.addWidget(self.plusButton)
        focusLayout.addWidget(self.minusButton)

        self.labelX = QLabel("X: 0")
        self.labelY = QLabel("Y: 0")
        self.labelZ = QLabel("Z: 0")
        
        self.saveButton = QPushButton("Save XYZ")
        self.coordinatesList = QListWidget()
        self.deleteButton = QPushButton("Delete")
        self.gotoButton = QPushButton("Go To")

        firstSectionLayout.addLayout(arrowButtonLayout)
        firstSectionLayout.addLayout(focusLayout)
        firstSectionLayout.addWidget(self.labelX)
        firstSectionLayout.addWidget(self.labelY)
        firstSectionLayout.addWidget(self.labelZ)
        firstSectionLayout.addWidget(self.saveButton)
        firstSectionLayout.addWidget(self.coordinatesList)
        firstSectionLayout.addWidget(self.deleteButton)
        firstSectionLayout.addWidget(self.gotoButton)

        # Second section
        secondSectionLayout = QVBoxLayout()

        self.timeIntervalField = QLineEdit()
        self.timeIntervalField.setPlaceholderText("Time Interval (s)")
        
        self.numberOfScansField = QLineEdit()
        self.numberOfScansField.setPlaceholderText("Number of Scans")

        self.startButton = QPushButton("Start")
        self.stopButton = QPushButton("Stop")
        
        self.experimentNameField = QLineEdit()
        self.experimentNameField.setPlaceholderText("Experiment Name")
        
        self.infoText = QLabel("Info: ")

        secondSectionLayout.addWidget(self.timeIntervalField)
        secondSectionLayout.addWidget(self.numberOfScansField)
        secondSectionLayout.addWidget(self.startButton)
        secondSectionLayout.addWidget(self.stopButton)
        secondSectionLayout.addWidget(self.experimentNameField)
        secondSectionLayout.addWidget(self.infoText)

        mainLayout.addLayout(firstSectionLayout)
        mainLayout.addLayout(secondSectionLayout) # Second section is added to the main horizontal layout

        self.setLayout(mainLayout)

        self.layer = None
            
    def setImage(self, im, colormap="gray", name="", pixelsize=(1,1,1), translation=(0,0,0)):
        if len(im.shape) == 2:
            translation = (translation[0], translation[1])
        if self.layer is None or name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False, colormap=colormap, 
                                               scale=pixelsize,translate=translation,
                                               name=name, blending='additive')
        self.layer.data = im
        
        
    
        
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
