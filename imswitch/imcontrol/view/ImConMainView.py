from dataclasses import dataclass

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
from pyqtgraph.console import ConsoleWidget
from pyqtgraph.dockarea import Dock, DockArea

from . import widgets


class ImConMainView(QtWidgets.QMainWindow):
    sigLoadParamsFromHDF5 = QtCore.Signal()
    sigPickSetup = QtCore.Signal()
    sigClosing = QtCore.Signal()

    def __init__(self, options, viewSetupInfo, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Widget factory
        self.factory = widgets.WidgetFactory(options)
        self.widgets = {}

        # Menu Bar
        menuBar = self.menuBar()
        file = menuBar.addMenu('&File')
        tools = menuBar.addMenu('&Tools')

        self.loadParamsAction = QtWidgets.QAction('Load parameters from saved HDF5 file…', self)
        self.loadParamsAction.setShortcut('Ctrl+O')
        self.loadParamsAction.triggered.connect(self.sigLoadParamsFromHDF5)
        file.addAction(self.loadParamsAction)

        self.pickSetupAction = QtWidgets.QAction('Pick setup…', self)
        self.pickSetupAction.triggered.connect(self.sigPickSetup)
        tools.addAction(self.pickSetupAction)

        # Window
        self.setWindowTitle('ImSwitch')

        self.cwidget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        self.cwidget.setLayout(layout)
        self.setCentralWidget(self.cwidget)

        # Dock area
        dockArea = DockArea()

        prevRightDock = None
        prevRightDockYPosition = -1
        def addRightDock(widgetKey, dockInfo):
            nonlocal prevRightDock, prevRightDockYPosition
            dock = Dock(dockInfo.name, size=(1, 1))
            self.widgets[widgetKey] = self.factory.createWidget(
                getattr(widgets, f'{widgetKey}Widget')
            )
            dock.addWidget(self.widgets[widgetKey])
            if prevRightDock is None:
                dockArea.addDock(dock)
            elif dockInfo.yPosition > prevRightDockYPosition:
                dockArea.addDock(dock, 'bottom', prevRightDock)
            else:
                dockArea.addDock(dock, 'above', prevRightDock)
            prevRightDock = dock
            prevRightDockYPosition = dockInfo.yPosition

        rightDocks = {
            'Laser': _DockInfo(name='Laser Control', yPosition=0),
            'Positioner': _DockInfo(name='Positioner', yPosition=1),
            'Scan': _DockInfo(name='Scan', yPosition=2),
            'BeadRec': _DockInfo(name='Bead Rec', yPosition=3),
            'AlignmentLine': _DockInfo(name='Alignment Tool', yPosition=3),
            'AlignAverage': _DockInfo(name='Axial Alignment Tool', yPosition=3),
            'AlignXY': _DockInfo(name='Rotational Alignment Tool', yPosition=3),
            'ULenses': _DockInfo(name='uLenses Tool', yPosition=3),
            'FFT': _DockInfo(name='FFT Tool', yPosition=3)
        }

        enabledRightDockKeys = ['Positioner', 'Scan'] + viewSetupInfo.availableWidgets
        for widgetKey, dockInfo in rightDocks.items():
            if widgetKey in enabledRightDockKeys:
                addRightDock(widgetKey, dockInfo)

        # Add other widgets
        self.widgets['Image'] = self.factory.createWidget(widgets.ImageWidget)
        self.widgets['Recording'] = self.factory.createWidget(widgets.RecordingWidget)

        # Image controls container
        imageControlsContainer = QtWidgets.QVBoxLayout()
        imageControlsContainer.setContentsMargins(0, 9, 0, 0)

        self.widgets['Settings'] = self.factory.createWidget(widgets.SettingsWidget)
        imageControlsContainer.addWidget(self.widgets['Settings'], 1)

        self.widgets['View'] = self.factory.createWidget(widgets.ViewWidget)
        imageControlsContainer.addWidget(self.widgets['View'])

        imageControlsContainerWidget = QtWidgets.QWidget()
        imageControlsContainerWidget.setLayout(imageControlsContainer)

        # Console
        console = ConsoleWidget(namespace={'pg': pg, 'np': np})

        # Docks
        self.imageDock = Dock('Image Display', size=(1, 1))
        self.imageDock.addWidget(self.widgets['Image'])
        dockArea.addDock(self.imageDock, 'left')

        self.imageControlsDock = Dock('Image Controls', size=(1, 100))
        self.imageControlsDock.addWidget(imageControlsContainerWidget)
        dockArea.addDock(self.imageControlsDock, 'left')

        self.recordingDock = Dock('Recording', size=(1, 1))
        self.recordingDock.addWidget(self.widgets['Recording'])
        dockArea.addDock(self.recordingDock, 'bottom', self.imageControlsDock)

        consoleDock = Dock('Console', size=(1, 1))
        consoleDock.addWidget(console)
        dockArea.addDock(consoleDock, 'bottom', self.recordingDock)

        # Add dock area to layout
        layout.addWidget(dockArea)

        self.showMaximized()
        self.imageControlsDock.container().setStretch(1, 1)
        prevRightDock.container().setStretch(1, 100)
        self.imageDock.setStretch(100, 100)

    def setDetectorRelatedDocksVisible(self, visible):
        for dock in ['imageDock', 'recordingDock', 'imageControlsDock', 'beadDock']:
            try:
                getattr(self, dock).setVisible(visible)
            except AttributeError:
                pass  # Happens if widget not added as part of configuration

        if not visible:
            self.showNormal()

    def closeEvent(self, event):
        self.sigClosing.emit()
        event.accept()


@dataclass
class _DockInfo:
    name: str
    yPosition: int


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
