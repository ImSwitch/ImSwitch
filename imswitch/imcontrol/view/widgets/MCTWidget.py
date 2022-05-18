import numpy as np
import pyqtgraph as pg
from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget


class MCTWidget(NapariHybridWidget):
    """ Widget containing mct interface. """

    sigMCTDisplayToggled = QtCore.Signal(bool)  # (enabled)
    sigMCTMonitorChanged = QtCore.Signal(int)  # (monitor)
    sigPatternID = QtCore.Signal(int)  # (display pattern id)

    def __post_init__(self):
        #super().__init__(*args, **kwargs)

        self.mctDisplay = None

        self.mctFrame = pg.GraphicsLayoutWidget()
        self.vb = self.mctFrame.addViewBox(row=1, col=1)
        self.img = pg.ImageItem()
        self.img.setImage(np.zeros((792, 600)), autoLevels=True, autoDownsample=True,
                          autoRange=True)
        self.vb.addItem(self.img)
        self.vb.setAspectLocked(True)

        # Button for showing MCT display and spinbox for monitor selection
        self.mctDisplayLayout = QtWidgets.QHBoxLayout()

        self.mctDisplayButton = guitools.BetterPushButton('Show MCT display (fullscreen)')
        self.mctDisplayButton.setCheckable(True)
        self.mctDisplayButton.toggled.connect(self.sigMCTDisplayToggled)
        self.mctDisplayLayout.addWidget(self.mctDisplayButton, 1)

        self.mctMonitorLabel = QtWidgets.QLabel('Screen:')
        self.mctDisplayLayout.addWidget(self.mctMonitorLabel)

        self.mctMonitorBox = QtWidgets.QSpinBox()
        self.mctMonitorBox.valueChanged.connect(self.sigMCTMonitorChanged)
        self.mctDisplayLayout.addWidget(self.mctMonitorBox)

        # Button to apply changes
        self.applyChangesButton = guitools.BetterPushButton('Apply changes')
        
        self.startMCTAcquisition = guitools.BetterPushButton('Start MCT')
        self.stopMCTAcquisition = guitools.BetterPushButton('Stop MCT')
        

        # Control panel with most buttons
        self.controlPanel = QtWidgets.QFrame()
        self.controlPanel.choiceInterfaceLayout = QtWidgets.QGridLayout()
        self.controlPanel.choiceInterface = QtWidgets.QWidget()
        self.controlPanel.choiceInterface.setLayout(self.controlPanel.choiceInterfaceLayout)

        # Buttons for saving, loading, and controlling the various phase patterns
        self.controlPanel.saveButton = guitools.BetterPushButton("Save")
        self.controlPanel.loadButton = guitools.BetterPushButton("Load")
        
        # Display patterns
        self.patternIDLabel = QtWidgets.QLabel('Pattern ID:')
        self.mctDisplayLayout.addWidget(self.patternIDLabel)

        self.patternIDBox = QtWidgets.QSpinBox()
        self.patternIDBox.valueChanged.connect(self.sigPatternID)
        self.mctDisplayLayout.addWidget(self.patternIDBox)


        # Defining layout
        self.controlPanel.arrowsFrame = QtWidgets.QFrame()
        self.controlPanel.arrowsLayout = QtWidgets.QGridLayout()
        self.controlPanel.arrowsFrame.setLayout(self.controlPanel.arrowsLayout)

        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.loadButton, 0, 3)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.saveButton, 1, 3)

        # Definition of the box layout:
        self.controlPanel.boxLayout = QtWidgets.QVBoxLayout()
        self.controlPanel.setLayout(self.controlPanel.boxLayout)

        #self.controlPanel.boxLayout.addWidget(self.controlPanel.choiceInterface)
        self.controlPanel.boxLayout.addWidget(self.controlPanel.arrowsFrame)

        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        self.grid.addWidget(self.mctFrame, 0, 0, 1, 2)
        #self.grid.addWidget(self.paramtreeDockArea, 1, 0, 2, 1)
        self.grid.addWidget(self.applyChangesButton, 3, 0, 1, 1)
        self.grid.addWidget(self.startMCTAcquisition, 1, 0, 1, 1)
        self.grid.addWidget(self.stopMCTAcquisition, 2, 0, 1, 1)
        self.grid.addLayout(self.mctDisplayLayout, 3, 1, 1, 1)
        self.grid.addWidget(self.controlPanel, 1, 1, 2, 1)
        
        self.layer = None

    def initMCTDisplay(self, monitor):
        from imswitch.imcontrol.view import MCTDisplay
        self.mctDisplay = MCTDisplay(self, monitor)
        self.mctDisplay.sigClosed.connect(lambda: self.sigMCTDisplayToggled.emit(False))
        self.mctMonitorBox.setValue(monitor)

    def updateMCTDisplay(self, imgArr):
        self.mctDisplay.updateImage(imgArr)

    def setMCTDisplayVisible(self, visible):
        self.mctDisplay.setVisible(visible)
        self.mctDisplayButton.setChecked(visible)

    def setMCTDisplayMonitor(self, monitor):
        self.mctDisplay.setMonitor(monitor, updateImage=True)

    def getImage(self):
        if self.layer is not None:
            return self.img.image
        
    def setImage(self, im):
        if self.layer is None or self.layer.name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False, name="MCT Reconstruction", blending='additive')
        self.layer.data = im
        

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
