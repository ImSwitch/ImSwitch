import numpy as np
import pyqtgraph as pg
from qtpy import QtCore, QtWidgets
from pyqtgraph.parametertree import ParameterTree
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
        #self.simDisplayLayout.addWidget(self.simDisplayButton, 1)

        self.simMonitorLabel = QtWidgets.QLabel('Screen:')
        #self.simDisplayLayout.addWidget(self.simMonitorLabel)

        self.simMonitorBox = QtWidgets.QSpinBox()
        #self.simMonitorBox.valueChanged.connect(self.sigSIMMonitorChanged)
        #self.simDisplayLayout.addWidget(self.simMonitorBox)

        # Button to apply changes
        #self.applyChangesButton = guitools.BetterPushButton('Apply changes')
        
        self.startSIMAcquisition = guitools.BetterPushButton('Start')
        self.isRecordingButton = guitools.BetterPushButton("Start Recording")
        self.is488LaserButton = guitools.BetterPushButton("488 on")
        self.is635LaserButton = guitools.BetterPushButton("635 on")
        

        #Enter the frames to wait for frame-sync
        self.simFrameSyncLabel  = QtWidgets.QLabel('N-Framesync (e.g. 1):')        
        self.simFrameSyncVal = QtWidgets.QLineEdit('5')
        
        # Display patterns
        self.patternIDLabel = QtWidgets.QLabel('Pattern ID:')
        #self.simDisplayLayout.addWidget(self.patternIDLabel)

        self.patternIDBox = QtWidgets.QSpinBox()
        self.patternIDBox.valueChanged.connect(self.sigPatternID)
        #self.simDisplayLayout.addWidget(self.patternIDBox)

        # parameter tree for SIM reconstruction paramters
        self.SIMParameterTree = ParameterTree()
        self.generalparams = [{'name': 'general', 'type': 'group', 'children': [
            {'name': 'wavelength (p1)', 'type': 'int', 'value': 488, 'limits': (400, 700), 'step': 1,
             'suffix': 'nm'},
            {'name': 'wavelength (p2)', 'type': 'int', 'value': 635, 'limits': (400, 700), 'step': 1,
             'suffix': 'nm'},
            {'name': 'NA', 'type': 'float', 'value': 0.85, 'limits': (0, 1.6), 'step': 0.05,
             'suffix': 'A.U.'},
            {'name': 'n', 'type': 'float', 'value': 1.0, 'limits': (1.0, 1.6),
             'step': 0.1,
             'suffix': 'A.U.'},
            {'name': 'pixelsize', 'type': 'float', 'value': 6.5, 'limits': (0.1, 20),
             'step': 0.1,
             'suffix': 'µm'}
        ]}]
        self.SIMParameterTree.setStyleSheet("""
        QTreeView::item, QAbstractSpinBox, QComboBox {
            padding-top: 0;
            padding-bottom: 0;
            border: none;
        }

        QComboBox QAbstractItemView {
            min-width: 128px;
        }
        """)
        self.SIMParameterTree.p = pg.parametertree.Parameter.create(name='params', type='group',
                                                                    children=self.generalparams)
        self.SIMParameterTree.setParameters(self.SIMParameterTree.p, showTop=False)
        self.SIMParameterTree._writable = True

        self.paramtreeDockArea = pg.dockarea.DockArea()
        pmtreeDock = pg.dockarea.Dock('SIM Recon Parameters', size=(1, 1))
        pmtreeDock.addWidget(self.SIMParameterTree)
        self.paramtreeDockArea.addDock(pmtreeDock)
        
        # Select reconstructor
        self.SIMReconstructorLabel = QtWidgets.QLabel('<strong>SIM Processor:</strong>')
        self.SIMReconstructorList = QtWidgets.QComboBox()
        self.SIMReconstructorList.addItems(['napari', 'mcsim'])
        
        self.useGPUCheckbox = QtWidgets.QCheckBox('Use GPU?')
        self.useGPUCheckbox.setCheckable(True)

        # Assign locations for gui elements
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        self.grid.addWidget(self.simFrame, 0, 0, 1, 2)
        self.grid.addWidget(self.startSIMAcquisition, 1, 0, 1, 1)
        self.grid.addWidget(self.isRecordingButton, 1, 1, 1, 1)
        
        
        # Laser control
        self.grid.addWidget(self.is488LaserButton, 2, 0, 1, 1)
        self.grid.addWidget(self.is635LaserButton, 2, 1, 1, 1)
        self.grid.addWidget(self.useGPUCheckbox, 2,2,1,1)
        
        self.grid.addWidget(self.simFrameSyncLabel, 3,0,1,1)
        self.grid.addWidget(self.simFrameSyncVal, 3,1,1,1)

        # Reconstructor
        self.grid.addWidget(self.SIMReconstructorLabel, 4, 0, 1, 1)
        self.grid.addWidget(self.SIMReconstructorList, 4, 1, 1, 1)
            
        # SIM parameters 
        self.grid.addWidget(self.paramtreeDockArea, 5, 0, 3, 2)
        
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
        
    def setImage(self, im, name="SIM Reconstruction"):
        if self.layer is None or self.layer.name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False, name=name, blending='additive')
        self.layer.data = im
    
    def getFrameSyncVal(self):
        return abs(int(self.simFrameSyncVal.text()))
        

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
