import numpy as np
import pyqtgraph as pg
from qtpy import QtCore, QtWidgets
from pyqtgraph.parametertree import ParameterTree
from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget


class DPCWidget(NapariHybridWidget):
    """ Widget containing dpc interface. """

    sigDPCDisplayToggled = QtCore.Signal(bool)  # (enabled)
    sigDPCMonitorChanged = QtCore.Signal(int)  # (monitor)
    sigPatternID = QtCore.Signal(int)  # (display pattern id)

    def __post_init__(self):
        #super().__init__(*args, **kwargs)

        self.dpcDisplay = None

        self.dpcFrame = pg.GraphicsLayoutWidget()

        # Button for showing DPC display and spinbox for monitor selection
        self.dpcDisplayLayout = QtWidgets.QHBoxLayout()


        self.dpcMonitorBox = QtWidgets.QSpinBox()
        #self.dpcMonitorBox.valueChanged.connect(self.sigDPCMonitorChanged)
        #self.dpcDisplayLayout.addWidget(self.dpcMonitorBox)

        self.startDPCAcquisition = guitools.BetterPushButton('Start')
        self.isRecordingButton = guitools.BetterPushButton("Start Recording")

        #Enter the frames to wait for frame-sync
        self.dpcFrameSyncLabel  = QtWidgets.QLabel('N-Framesync (e.g. 1):')        
        self.dpcFrameSyncVal = QtWidgets.QLineEdit('1')
        

        # parameter tree for DPC reconstruction paramters
        self.DPCParameterTree = ParameterTree()
        self.generalparams = [{'name': 'general', 'type': 'group', 'children': [
            {
                'name': 'pixelsize',
                'type': 'int',
                'value': 0.2,
                'limits': (0,50),
                'step': .01,
                'suffix': 'µm',
                },
            {
                'name': 'wavelength',
                'type': 'float',
                'value': 0.53,
                'limits': (0,2),
                'step': .01,
                'suffix': 'µm',
                },
            {
                'name': 'NA',
                'type': 'float',
                'value': 0.3,
                'limits': (0, 1.6),
                'step': 0.05,
                'suffix': 'A.U.',
                },
            {
                'name': 'NAi',
                'type': 'float',
                'value': 0.3,
                'limits': (0, 1.6),
                'step': 0.05,
                'suffix': 'A.U.',
                },            
            {
                'name': 'n',
                'type': 'float',
                'value': 1.0,
                'limits': (1.0, 1.6),
                'step': 0.1,
                'suffix': 'A.U.',
                },
           ]}]

        self.DPCParameterTree.setStyleSheet("""
        QTreeView::item, QAbstractSpinBox, QComboBox {
            padding-top: 0;
            padding-bottom: 0;
            border: none;
        }

        QComboBox QAbstractItemView {
            min-width: 128px;
        }
        """)
        self.DPCParameterTree.p = pg.parametertree.Parameter.create(name='params', type='group',
                                                                    children=self.generalparams)
        self.DPCParameterTree.setParameters(self.DPCParameterTree.p, showTop=False)
        self.DPCParameterTree._writable = True

        self.paramtreeDockArea = pg.dockarea.DockArea()
        pmtreeDock = pg.dockarea.Dock('DPC Recon Parameters', size=(1, 1))
        pmtreeDock.addWidget(self.DPCParameterTree)
        self.paramtreeDockArea.addDock(pmtreeDock)
        

        # Assign locations for gui elements
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        self.grid.addWidget(self.startDPCAcquisition, 1, 0, 1, 1)
        self.grid.addWidget(self.isRecordingButton, 1, 1, 1, 1)
        
        # DPC parameters 
        self.grid.addWidget(self.paramtreeDockArea, 4, 0, 3, 2)
        
        self.layer = None
        self.layers={}

    def getImage(self):
        if self.layer is not None:
            return self.img.image
        
    def setImage(self, im, name):
        if not name in self.layers:
            self.layers[name] = self.viewer.add_image(im, rgb=False, name=name, blending='additive')
        self.layers[name].data = im
        
    def getFrameSyncVal(self):
        return abs(int(self.dpcFrameSyncVal.text()))
        

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
