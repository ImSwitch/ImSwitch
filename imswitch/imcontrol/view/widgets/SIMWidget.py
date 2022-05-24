import numpy as np
import pyqtgraph as pg
from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget


class SIMWidget(NapariHybridWidget):
    """ Widget containing sim interface. """

    sigSIMDisplayToggled = QtCore.Signal(bool)  # (enabled)
    sigSIMMonitorChanged = QtCore.Signal(int)  # (monitor)
    sigPatternID = QtCore.Signal(int)  # (display pattern id)

    def __post_init__(self):
        #super().__init__(*args, **kwargs)

        self.simDisplay = None

        self.simFrame = pg.GraphicsLayoutWidget()
        self.vb = self.simFrame.addViewBox(row=1, col=1)
        self.img = pg.ImageItem()
        self.img.setImage(np.zeros((792, 600)), autoLevels=True, autoDownsample=True,
                          autoRange=True)
        self.vb.addItem(self.img)
        self.vb.setAspectLocked(True)

        # Button for showing SIM display and spinbox for monitor selection
        self.simDisplayLayout = QtWidgets.QHBoxLayout()

        self.simDisplayButton = guitools.BetterPushButton('Show SIM display (fullscreen)')
        self.simDisplayButton.setCheckable(True)
        self.simDisplayButton.toggled.connect(self.sigSIMDisplayToggled)
        self.simDisplayLayout.addWidget(self.simDisplayButton, 1)

        self.simMonitorLabel = QtWidgets.QLabel('Screen:')
        self.simDisplayLayout.addWidget(self.simMonitorLabel)

        self.simMonitorBox = QtWidgets.QSpinBox()
        self.simMonitorBox.valueChanged.connect(self.sigSIMMonitorChanged)
        self.simDisplayLayout.addWidget(self.simMonitorBox)

        # Button to apply changes
        self.applyChangesButton = guitools.BetterPushButton('Apply changes')
        
        self.startSIMAcquisition = guitools.BetterPushButton('Start SIM')
        self.stopSIMAcquisition = guitools.BetterPushButton('Stop SIM')
        

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
        self.simDisplayLayout.addWidget(self.patternIDLabel)

        self.patternIDBox = QtWidgets.QSpinBox()
        self.patternIDBox.valueChanged.connect(self.sigPatternID)
        self.simDisplayLayout.addWidget(self.patternIDBox)


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

        self.grid.addWidget(self.simFrame, 0, 0, 1, 2)
        #self.grid.addWidget(self.paramtreeDockArea, 1, 0, 2, 1)
        self.grid.addWidget(self.applyChangesButton, 3, 0, 1, 1)
        self.grid.addWidget(self.startSIMAcquisition, 1, 0, 1, 1)
        self.grid.addWidget(self.stopSIMAcquisition, 2, 0, 1, 1)
        self.grid.addLayout(self.simDisplayLayout, 3, 1, 1, 1)
        self.grid.addWidget(self.controlPanel, 1, 1, 2, 1)
        
        self.layer = None

    def initSIMDisplay(self, monitor):
        from imswitch.imcontrol.view import SIMDisplay
        self.simDisplay = SIMDisplay(self, monitor)
        self.simDisplay.sigClosed.connect(lambda: self.sigSIMDisplayToggled.emit(False))
        self.simMonitorBox.setValue(monitor)

    def updateSIMDisplay(self, imgArr):
        self.simDisplay.updateImage(imgArr)

    def setSIMDisplayVisible(self, visible):
        self.simDisplay.setVisible(visible)
        self.simDisplayButton.setChecked(visible)

    def setSIMDisplayMonitor(self, monitor):
        self.simDisplay.setMonitor(monitor, updateImage=True)

    def getImage(self):
        if self.layer is not None:
            return self.img.image
        
    def setImage(self, im):
        if self.layer is None or self.layer.name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False, name="SIM Reconstruction", blending='additive')
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
