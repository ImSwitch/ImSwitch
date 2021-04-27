from dataclasses import dataclass

from pyqtgraph.Qt import QtCore, QtWidgets
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
        self.docks = {}
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
        enabledDockKeys = viewSetupInfo.availableWidgets

        prevRightDock = None
        prevRightDockYPosition = -1
        def addRightDock(widgetKey, dockInfo):
            nonlocal prevRightDock, prevRightDockYPosition
            self.docks[widgetKey] = Dock(dockInfo.name, size=(1, 1))
            self.widgets[widgetKey] = self.factory.createWidget(
                getattr(widgets, f'{widgetKey}Widget')
            )
            self.docks[widgetKey].addWidget(self.widgets[widgetKey])
            if prevRightDock is None:
                dockArea.addDock(self.docks[widgetKey])
            elif dockInfo.yPosition > prevRightDockYPosition:
                dockArea.addDock(self.docks[widgetKey], 'bottom', prevRightDock)
            else:
                dockArea.addDock(self.docks[widgetKey], 'above', prevRightDock)
            prevRightDock = self.docks[widgetKey]
            prevRightDockYPosition = dockInfo.yPosition

        rightDocks = {
            'FocusLock': _DockInfo(name='Focus Lock', yPosition=0),
            'SLM': _DockInfo(name='SLM', yPosition=0),
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

        for widgetKey, dockInfo in rightDocks.items():
            if widgetKey in enabledDockKeys:
                addRightDock(widgetKey, dockInfo)

        if 'Image' in enabledDockKeys:
            self.docks['Image'] = Dock('Image Display', size=(1, 1))
            self.widgets['Image'] = self.factory.createWidget(widgets.ImageWidget)
            self.docks['Image'].addWidget(self.widgets['Image'])
            dockArea.addDock(self.docks['Image'], 'left')

        prevLeftDock = None
        prevLeftDockYPosition = -1
        def addLeftDock(widgetKey, dockInfo):
            nonlocal prevLeftDock, prevLeftDockYPosition
            self.docks[widgetKey] = Dock(dockInfo.name, size=(1, 1))
            self.widgets[widgetKey] = self.factory.createWidget(
                getattr(widgets, f'{widgetKey}Widget')
            )
            self.docks[widgetKey].addWidget(self.widgets[widgetKey])
            if prevLeftDock is None:
                dockArea.addDock(self.docks[widgetKey], 'left')
            elif dockInfo.yPosition > prevLeftDockYPosition:
                dockArea.addDock(self.docks[widgetKey], 'bottom', prevLeftDock)
            else:
                dockArea.addDock(self.docks[widgetKey], 'above', prevLeftDock)
            prevLeftDock = self.docks[widgetKey]
            prevLeftDockYPosition = dockInfo.yPosition

        leftDocks = {
            'Settings': _DockInfo(name='Detector Settings', yPosition=0),
            'View': _DockInfo(name='Image Controls', yPosition=1),
            'Recording': _DockInfo(name='Recording', yPosition=2),
            'Console': _DockInfo(name='Console', yPosition=3)
        }

        for widgetKey, dockInfo in leftDocks.items():
            if widgetKey in enabledDockKeys:
                addLeftDock(widgetKey, dockInfo)

        # Add dock area to layout
        layout.addWidget(dockArea)

        # Maximize window
        self.showMaximized()

        # Adjust dock sizes
        if 'Settings' in self.docks:
            self.docks['Settings'].setStretch(1, 10)
            self.docks['Settings'].container().setStretch(3, 1)
        if prevRightDock is not None:
            prevRightDock.setStretch(1, 10)
        if 'Image' in self.docks:
            self.docks['Image'].setStretch(10, 1)

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
