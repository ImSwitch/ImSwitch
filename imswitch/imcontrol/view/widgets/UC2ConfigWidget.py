import numpy as np
import pyqtgraph as pg
from pyqtgraph.parametertree import ParameterTree
from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools
from .basewidgets import Widget


class UC2ConfigWidget(Widget):
    """ Widget containing UC2Config interface. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.UC2ConfigParameterTree = ParameterTree()
        self.generalparams = [{'name': 'general', 'type': 'group', 'children': [
            {'name': 'radius', 'type': 'float', 'value': 100, 'limits': (0, 600), 'step': 1,
             'suffix': 'px'},
            {'name': 'sigma', 'type': 'float', 'value': 35, 'limits': (1, 599), 'step': 0.1,
             'suffix': 'px'},
            {'name': 'rotationAngle', 'type': 'float', 'value': 0, 'limits': (-6.2832, 6.2832),
             'step': 0.1,
             'suffix': 'rad'}
        ]}]
        self.UC2ConfigParameterTree.setStyleSheet("""
        QTreeView::item, QAbstractSpinBox, QComboBox {
            padding-top: 0;
            padding-bottom: 0;
            border: none;
        }

        QComboBox QAbstractItemView {
            min-width: 128px;
        }
        """)
        self.UC2ConfigParameterTree.p = pg.parametertree.Parameter.create(name='params', type='group',
                                                                    children=self.generalparams)
        self.UC2ConfigParameterTree.setParameters(self.UC2ConfigParameterTree.p, showTop=False)
        self.UC2ConfigParameterTree._writable = True

        self.pinDefParameterTree = pg.parametertree.ParameterTree()
        pinDeflim = 64
        
        self.pinDefparams = [{
            'name': 'left', 'type': 'group', 'children': [
            {'name': 'motXstp', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'motXdir', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'motYstp', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'motYdir', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'motZstp', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'motZdir', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'motAstp', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'motAdir', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'motEnable', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'ledArrPin', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'ledArrNum', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'digitalPin1', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'digitalPin2', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'digitalPin3', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'analogPin1', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'analogPin2', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'analogPin3', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'laserPin1', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'laserPin2', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'laserPin3', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'dacFake1', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1},
            {'name': 'dacFake2', 'type': 'int', 'value': 0, 'limits': (0, pinDeflim), 'step': 1}]}]
        
            #{'name': 'identifier', 'type': 'str', 'value': "TEST"},
            #{'name': 'ssid', 'type': 'str', 'value': "UC2"},
            #{'name': 'PW', 'type': 'str', 'value': "PASSWORD"}


        
        self.pinDefParameterTree.setStyleSheet("""
        QTreeView::item, QAbstractSpinBox, QComboBox {
            padding-top: 0;
            padding-bottom: 0;
            border: none;
        }
        QComboBox QAbstractItemView {
            min-width: 128px;
        }
        """)
        self.pinDefParameterTree.p = pg.parametertree.Parameter.create(name='params', type='group',
                                                                     children=self.pinDefparams)
        self.pinDefParameterTree.setParameters(self.pinDefParameterTree.p, showTop=False)
        self.pinDefParameterTree._writable = True

        self.paramtreeDockArea = pg.dockarea.DockArea()
        pmtreeDock = pg.dockarea.Dock('N/A', size=(1, 1))
        pmtreeDock.addWidget(self.UC2ConfigParameterTree)
        self.paramtreeDockArea.addDock(pmtreeDock)
        pinDeftreeDock = pg.dockarea.Dock('Pin definition parameters', size=(1, 1))
        pinDeftreeDock.addWidget(self.pinDefParameterTree)
        self.paramtreeDockArea.addDock(pinDeftreeDock, 'above', pmtreeDock)

        # Button to apply changes
        self.applyChangesButton = guitools.BetterPushButton('Apply changes')

        # Control panel with most buttons
        self.controlPanel = QtWidgets.QFrame()
        self.controlPanel.choiceInterfaceLayout = QtWidgets.QGridLayout()
        self.controlPanel.choiceInterface = QtWidgets.QWidget()
        self.controlPanel.choiceInterface.setLayout(self.controlPanel.choiceInterfaceLayout)

        # Interface to change the amount of displacement induced by the arrows
        self.controlPanel.incrementInterface = QtWidgets.QWidget()
        self.controlPanel.incrementInterfaceLayout = QtWidgets.QVBoxLayout()
        self.controlPanel.incrementInterface.setLayout(self.controlPanel.incrementInterfaceLayout)
        self.controlPanel.incrementlabel = QtWidgets.QLabel("Step (px)")
        self.controlPanel.incrementSpinBox = QtWidgets.QSpinBox()
        self.controlPanel.incrementSpinBox.setRange(1, 50)
        self.controlPanel.incrementSpinBox.setValue(1)
        self.controlPanel.incrementInterfaceLayout.addWidget(self.controlPanel.incrementlabel)
        self.controlPanel.incrementInterfaceLayout.addWidget(self.controlPanel.incrementSpinBox)

        # Buttons for saving, loading, and controlling the various phase patterns
        self.controlPanel.saveButton = guitools.BetterPushButton("Save")
        self.controlPanel.loadButton = guitools.BetterPushButton("Load")
        self.controlPanel.updateFirmwareDeviceButton = guitools.BetterPushButton("Update Firmware")
        self.controlPanel.updateFirmwareDeviceLabel = QtWidgets.QLabel('FW Updater')

        # Defining layout
        self.controlPanel.arrowsFrame = QtWidgets.QFrame()
        self.controlPanel.arrowsLayout = QtWidgets.QGridLayout()
        self.controlPanel.arrowsFrame.setLayout(self.controlPanel.arrowsLayout)

        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.loadButton, 4, 1)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.saveButton, 4, 2)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.updateFirmwareDeviceButton, 5, 1)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.updateFirmwareDeviceLabel, 6, 1)
        
        # Definition of the box layout:
        self.controlPanel.boxLayout = QtWidgets.QVBoxLayout()
        self.controlPanel.setLayout(self.controlPanel.boxLayout)

        self.controlPanel.boxLayout.addWidget(self.controlPanel.choiceInterface)
        self.controlPanel.boxLayout.addWidget(self.controlPanel.arrowsFrame)

        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        self.grid.addWidget(self.paramtreeDockArea, 1, 0, 2, 1)
        self.grid.addWidget(self.applyChangesButton, 3, 0, 1, 1)
        self.grid.addWidget(self.controlPanel, 1, 1, 2, 1)

    
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
