import numpy as np
import pyqtgraph as pg
from qtpy import QtCore, QtWidgets
from pyqtgraph.parametertree import ParameterTree

from imswitch.imcontrol.view import guitools
from .basewidgets import Widget


class SLMWidget(Widget):
    """ Widget containing slm interface. """

    sigSLMDisplayToggled = QtCore.Signal(bool)  # (enabled)
    sigSLMMonitorChanged = QtCore.Signal(int)  # (monitor)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.slmDisplay = None

        self.slmFrame = pg.GraphicsLayoutWidget()
        self.vb = self.slmFrame.addViewBox(row=1, col=1)
        self.img = pg.ImageItem()
        self.img.setImage(np.zeros((792, 600)), autoLevels=True, autoDownsample=True,
                          autoRange=True)
        self.vb.addItem(self.img)
        self.vb.setAspectLocked(True)

        self.slmParameterTree = ParameterTree()
        self.generalparams = [{'name': 'general', 'type': 'group', 'children': [
                            {'name': 'radius', 'type': 'float', 'value': 100, 'limits': (0, 600), 'step': 1,
                            'suffix': 'px'},
                            {'name': 'sigma', 'type': 'float', 'value': 35, 'limits': (1, 599), 'step': 0.1,
                            'suffix': 'px'},
                            {'name': 'rotationAngle', 'type': 'float', 'value': 0, 'limits': (-6.2832, 6.2832), 'step': 0.1,
                            'suffix': 'rad'}
                            ]}]
        self.slmParameterTree.setStyleSheet("""
        QTreeView::item, QAbstractSpinBox, QComboBox {
            padding-top: 0;
            padding-bottom: 0;
            border: none;
        }

        QComboBox QAbstractItemView {
            min-width: 128px;
        }
        """)
        self.slmParameterTree.p = pg.parametertree.Parameter.create(name='params', type='group',
                                                                    children=self.generalparams)
        self.slmParameterTree.setParameters(self.slmParameterTree.p, showTop=False)
        self.slmParameterTree._writable = True

        self.aberParameterTree = pg.parametertree.ParameterTree()
        aberlim = 2
        self.aberparams = [{'name': 'left', 'type': 'group', 'children': [
            {'name': 'tilt', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim),
             'step': 0.01},
            {'name': 'tip', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim),
             'step': 0.01},
            {'name': 'defocus', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim),
             'step': 0.01},
            {'name': 'spherical', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim),
             'step': 0.01},
            {'name': 'verticalComa', 'type': 'float', 'value': 0,
             'limits': (-aberlim, aberlim), 'step': 0.01},
            {'name': 'horizontalComa', 'type': 'float', 'value': 0,
             'limits': (-aberlim, aberlim), 'step': 0.01},
            {'name': 'verticalAstigmatism', 'type': 'float', 'value': 0,
             'limits': (-aberlim, aberlim), 'step': 0.01},
            {'name': 'obliqueAstigmatism', 'type': 'float', 'value': 0,
             'limits': (-aberlim, aberlim), 'step': 0.01}
        ]},
                           {'name': 'right', 'type': 'group', 'children': [
                               {'name': 'tilt', 'type': 'float', 'value': 0,
                                'limits': (-aberlim, aberlim), 'step': 0.01},
                               {'name': 'tip', 'type': 'float', 'value': 0,
                                'limits': (-aberlim, aberlim), 'step': 0.01},
                               {'name': 'defocus', 'type': 'float', 'value': 0,
                                'limits': (-aberlim, aberlim), 'step': 0.01},
                               {'name': 'spherical', 'type': 'float', 'value': 0,
                                'limits': (-aberlim, aberlim), 'step': 0.01},
                               {'name': 'verticalComa', 'type': 'float', 'value': 0,
                                'limits': (-aberlim, aberlim), 'step': 0.01},
                               {'name': 'horizontalComa', 'type': 'float', 'value': 0,
                                'limits': (-aberlim, aberlim), 'step': 0.01},
                               {'name': 'verticalAstigmatism', 'type': 'float', 'value': 0,
                                'limits': (-aberlim, aberlim), 'step': 0.01},
                               {'name': 'obliqueAstigmatism', 'type': 'float', 'value': 0,
                                'limits': (-aberlim, aberlim), 'step': 0.01}
                           ]}]
        self.aberParameterTree.setStyleSheet("""
        QTreeView::item, QAbstractSpinBox, QComboBox {
            padding-top: 0;
            padding-bottom: 0;
            border: none;
        }

        QComboBox QAbstractItemView {
            min-width: 128px;
        }
        """)
        self.aberParameterTree.p = pg.parametertree.Parameter.create(name='params', type='group',
                                                                     children=self.aberparams)
        self.aberParameterTree.setParameters(self.aberParameterTree.p, showTop=False)
        self.aberParameterTree._writable = True

        self.paramtreeDockArea = pg.dockarea.DockArea()
        pmtreeDock = pg.dockarea.Dock('Phase mask parameters', size=(1, 1))
        pmtreeDock.addWidget(self.slmParameterTree)
        self.paramtreeDockArea.addDock(pmtreeDock)
        abertreeDock = pg.dockarea.Dock('Aberration correction parameters', size=(1, 1))
        abertreeDock.addWidget(self.aberParameterTree)
        self.paramtreeDockArea.addDock(abertreeDock, 'above', pmtreeDock)
        
        # Button for showing SLM display and spinbox for monitor selection
        self.slmDisplayLayout = QtWidgets.QHBoxLayout()

        self.slmDisplayButton = guitools.BetterPushButton('Show SLM display (fullscreen)')
        self.slmDisplayButton.setCheckable(True)
        self.slmDisplayButton.toggled.connect(self.sigSLMDisplayToggled)
        self.slmDisplayLayout.addWidget(self.slmDisplayButton, 1)

        self.slmMonitorLabel = QtWidgets.QLabel('Screen:')
        self.slmDisplayLayout.addWidget(self.slmMonitorLabel)

        self.slmMonitorBox = QtWidgets.QSpinBox()
        self.slmMonitorBox.valueChanged.connect(self.sigSLMMonitorChanged)
        self.slmDisplayLayout.addWidget(self.slmMonitorBox)

        # Button to apply changes
        self.applyChangesButton = guitools.BetterPushButton('Apply changes')
        #self.paramtreeDockArea.addWidget(self.applyChangesButton, 'bottom', abertreeDock)

        # Control panel with most buttons
        self.controlPanel = QtWidgets.QFrame()
        self.controlPanel.choiceInterfaceLayout = QtWidgets.QGridLayout()
        self.controlPanel.choiceInterface = QtWidgets.QWidget()
        self.controlPanel.choiceInterface.setLayout(self.controlPanel.choiceInterfaceLayout)

        # Choose which mask to modify
        self.controlPanel.maskComboBox = QtWidgets.QComboBox()
        self.controlPanel.maskComboBox.addItem("Donut (left)")
        self.controlPanel.maskComboBox.addItem("Top hat (right)")
        self.controlPanel.choiceInterfaceLayout.addWidget(QtWidgets.QLabel('Select mask:'), 0, 0)
        self.controlPanel.choiceInterfaceLayout.addWidget(self.controlPanel.maskComboBox, 0, 1)

        # Choose which objective is in use
        self.controlPanel.objlensComboBox = QtWidgets.QComboBox()
        self.controlPanel.objlensComboBox.addItem("No objective")
        self.controlPanel.objlensComboBox.addItem("Oil")
        self.controlPanel.objlensComboBox.addItem("Glycerol")
        self.controlPanel.choiceInterfaceLayout.addWidget(QtWidgets.QLabel('Select objective:'), 1, 0)
        self.controlPanel.choiceInterfaceLayout.addWidget(self.controlPanel.objlensComboBox, 1, 1)

        # Phase mask moving buttons
        self.controlPanel.arrowButtons = []
        self.controlPanel.upButton = guitools.BetterPushButton('Up (YZ)')
        self.controlPanel.arrowButtons.append(self.controlPanel.upButton)
        self.controlPanel.downButton = guitools.BetterPushButton('Down (YZ)')
        self.controlPanel.arrowButtons.append(self.controlPanel.downButton)
        self.controlPanel.leftButton = guitools.BetterPushButton('Left (XZ)')
        self.controlPanel.arrowButtons.append(self.controlPanel.leftButton)
        self.controlPanel.rightButton = guitools.BetterPushButton('Right (XZ)')
        self.controlPanel.arrowButtons.append(self.controlPanel.rightButton)

        for button in self.controlPanel.arrowButtons:
            button.setCheckable(False)
            button.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                 QtWidgets.QSizePolicy.Expanding)
            button.setFixedSize(self.controlPanel.upButton.sizeHint())

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

        self.controlPanel.donutButton = guitools.BetterPushButton("Donut")
        self.controlPanel.tophatButton = guitools.BetterPushButton("Tophat")

        self.controlPanel.blackButton = guitools.BetterPushButton("Black frame")
        self.controlPanel.gaussianButton = guitools.BetterPushButton("Gaussian")

        self.controlPanel.halfButton = guitools.BetterPushButton("Half pattern")
        self.controlPanel.quadrantButton = guitools.BetterPushButton("Quad pattern")
        self.controlPanel.hexButton = guitools.BetterPushButton("Hex pattern")
        self.controlPanel.splitbullButton = guitools.BetterPushButton("Split pattern")

        # Defining layout
        self.controlPanel.arrowsFrame = QtWidgets.QFrame()
        self.controlPanel.arrowsLayout = QtWidgets.QGridLayout()
        self.controlPanel.arrowsFrame.setLayout(self.controlPanel.arrowsLayout)

        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.upButton, 0, 1)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.leftButton, 1, 0)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.incrementInterface, 1, 1)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.rightButton, 1, 2)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.downButton, 2, 1)

        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.loadButton, 0, 3)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.saveButton, 1, 3)

        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.donutButton, 3, 1)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.tophatButton, 3, 2)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.blackButton, 4, 1)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.gaussianButton, 4, 2)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.halfButton, 5, 1)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.quadrantButton, 5, 2)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.hexButton, 6, 1)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.splitbullButton, 6, 2)

        # Definition of the box layout:
        self.controlPanel.boxLayout = QtWidgets.QVBoxLayout()
        self.controlPanel.setLayout(self.controlPanel.boxLayout)

        self.controlPanel.boxLayout.addWidget(self.controlPanel.choiceInterface)
        self.controlPanel.boxLayout.addWidget(self.controlPanel.arrowsFrame)

        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        self.grid.addWidget(self.slmFrame, 0, 0, 1, 2)
        self.grid.addWidget(self.paramtreeDockArea, 1, 0, 2, 1)
        self.grid.addWidget(self.applyChangesButton, 3, 0, 1, 1)
        self.grid.addLayout(self.slmDisplayLayout, 3, 1, 1, 1)
        self.grid.addWidget(self.controlPanel, 1, 1, 2, 1)

    def initSLMDisplay(self, monitor):
        from imswitch.imcontrol.view import SLMDisplay
        self.slmDisplay = SLMDisplay(self, monitor)
        self.slmDisplay.sigClosed.connect(lambda: self.sigSLMDisplayToggled.emit(False))
        self.slmMonitorBox.setValue(monitor)

    def updateSLMDisplay(self, imgArr):
        self.slmDisplay.updateImage(imgArr)

    def setSLMDisplayVisible(self, visible):
        self.slmDisplay.setVisible(visible)
        self.slmDisplayButton.setChecked(visible)

    def setSLMDisplayMonitor(self, monitor):
        self.slmDisplay.setMonitor(monitor, updateImage=True)


# Copyright (C) 2020, 2021 TestaLab
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
