import os

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
from pyqtgraph.console import ConsoleWidget
from pyqtgraph.dockarea import Dock, DockArea

from imswitch.imcommon import constants
from . import guitools, widgets


class ImConMainView(QtWidgets.QMainWindow):
    sigLoadParamsFromHDF5 = QtCore.Signal()
    sigClosing = QtCore.Signal()

    def __init__(self, options, viewSetupInfo, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.availableWidgetsInfo = viewSetupInfo.availableWidgets
        widgetLayoutInfo = viewSetupInfo.widgetLayout

        # Widget factory
        self.factory = widgets.WidgetFactory(options)

        # Menu Bar
        menuBar = self.menuBar()
        file = menuBar.addMenu('&File')

        self.loadParamsAction = QtWidgets.QAction('Load parameters from saved HDF5 file…', self)
        self.loadParamsAction.setShortcut('Ctrl+O')
        self.loadParamsAction.triggered.connect(self.sigLoadParamsFromHDF5)
        file.addAction(self.loadParamsAction)

        # Window
        self.setWindowTitle('ImSwitch')

        self.cwidget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        self.cwidget.setLayout(layout)
        self.setCentralWidget(self.cwidget)

        # Dock area
        dockArea = DockArea()

        # Laser dock
        laserDock = Dock("Laser Control", size=(1, 1))
        self.laserWidgets = self.factory.createWidget(widgets.LaserWidget)
        laserDock.addWidget(self.laserWidgets)
        dockArea.addDock(laserDock)

        # Focus lock dock
        if self.availableWidgetsInfo.FocusLockWidget:
            focusLockDock = Dock('Focus Lock', size=(1, 1))
            self.focusLockWidget = self.factory.createWidget(widgets.FocusLockWidget)
            focusLockDock.addWidget(self.focusLockWidget)
            dockArea.addDock(focusLockDock, 'above', laserDock)

        # FFT dock
        if self.availableWidgetsInfo.FFTWidget:
            FFTDock = Dock("FFT Tool", size=(1, 1))
            self.fftWidget = self.factory.createWidget(widgets.FFTWidget)
            FFTDock.addWidget(self.fftWidget)
            dockArea.addDock(FFTDock, 'below', laserDock)

        alignmentDockLocation = (
            laserDock if widgetLayoutInfo.lasersAndAlignmentInSingleDock else None
        )

        def addAlignmentDock(name, alignmentWidget):
            nonlocal alignmentDockLocation
            alignmentDock = Dock(name, size=(1, 1))
            alignmentDock.addWidget(alignmentWidget)
            dockArea.addDock(alignmentDock,
                             'right' if alignmentDockLocation is None else 'above',
                             alignmentDockLocation)
            alignmentDockLocation = alignmentDock

        # Line Alignment Tool
        if self.availableWidgetsInfo.AlignmentLineWidget:
            self.alignmentLineWidget = self.factory.createWidget(widgets.AlignmentLineWidget)
            addAlignmentDock("Alignment Tool", self.alignmentLineWidget)

        # Z align widget
        if self.availableWidgetsInfo.AlignWidgetAverage:
            self.alignWidgetAverage = self.factory.createWidget(widgets.AlignWidgetAverage)
            addAlignmentDock("Axial Alignment Tool", self.alignWidgetAverage)

        # Rotational align widget
        if self.availableWidgetsInfo.AlignWidgetXY:
            self.alignWidgetXY = self.factory.createWidget(widgets.AlignWidgetXY)
            addAlignmentDock("Rotational Alignment Tool", self.alignWidgetXY)

        # ulenses Alignment Tool
        if self.availableWidgetsInfo.AlignWidgetXY:
            self.ulensesWidget = self.factory.createWidget(widgets.ULensesWidget)
            addAlignmentDock("uLenses Tool", self.ulensesWidget)

        # Piezo positioner
        piezoDock = Dock('Piezo positioner', size=(1, 1))
        self.positionerWidget = self.factory.createWidget(widgets.PositionerWidget)
        piezoDock.addWidget(self.positionerWidget)
        if alignmentDockLocation is not None:
            dockArea.addDock(piezoDock, 'bottom', alignmentDockLocation)
        else:
            dockArea.addDock(piezoDock, 'bottom', laserDock)

        # Scan widget dock
        scanDock = Dock('Scan', size=(1, 1))
        self.scanWidget = self.factory.createWidget(widgets.ScanWidget)
        scanDock.addWidget(self.scanWidget)
        dockArea.addDock(scanDock)

        # SLM widget dock
        if self.availableWidgetsInfo.SLMWidget:
            slmDock = Dock('SLM', size=(1, 1))
            self.slmWidget = self.factory.createWidget(widgets.SLMWidget)
            slmDock.addWidget(self.slmWidget)
            dockArea.addDock(slmDock, 'above', scanDock)

        # Bead reconstruction
        if self.availableWidgetsInfo.BeadRecWidget:
            self.beadDock = Dock('Bead Rec', size=(1, 100))
            self.beadRecWidget = self.factory.createWidget(widgets.BeadRecWidget)
            self.beadDock.addWidget(self.beadRecWidget)
            dockArea.addDock(self.beadDock)

        # Add other widgets
        self.imageWidget = self.factory.createWidget(widgets.ImageWidget)
        self.recordingWidget = self.factory.createWidget(widgets.RecordingWidget)

        # Image controls container
        imageControlsContainer = QtWidgets.QVBoxLayout()
        imageControlsContainer.setContentsMargins(0, 9, 0, 0)

        self.settingsWidget = self.factory.createWidget(widgets.SettingsWidget)
        imageControlsContainer.addWidget(self.settingsWidget, 1)

        self.viewWidget = self.factory.createWidget(widgets.ViewWidget)
        imageControlsContainer.addWidget(self.viewWidget)

        imageControlsContainerWidget = QtWidgets.QWidget()
        imageControlsContainerWidget.setLayout(imageControlsContainer)

        # Console
        console = ConsoleWidget(namespace={'pg': pg, 'np': np})

        # Docks
        self.imageDock = Dock('Image Display', size=(1, 1))
        self.imageDock.addWidget(self.imageWidget)
        dockArea.addDock(self.imageDock, 'left')

        self.imageControlsDock = Dock('Image Controls', size=(1, 100))
        self.imageControlsDock.addWidget(imageControlsContainerWidget)
        dockArea.addDock(self.imageControlsDock, 'left')

        self.recordingDock = Dock('Recording', size=(1, 1))
        self.recordingDock.addWidget(self.recordingWidget)
        dockArea.addDock(self.recordingDock, 'bottom', self.imageControlsDock)

        consoleDock = Dock('Console', size=(1, 1))
        consoleDock.addWidget(console)
        dockArea.addDock(consoleDock, 'bottom', self.recordingDock)

        # Objective motorized correction collar widget dock
        if self.availableWidgetsInfo.MotCorrWidget:
            motCorrDock = Dock('Objective Mot Corr', size=(1, 1))
            self.motCorrWidget = self.factory.createWidget(widgets.MotCorrWidget)
            motCorrDock.addWidget(self.motCorrWidget)
            dockArea.addDock(motCorrDock, 'below',  self.imageControlsDock)

        # Raise important docks
        self._raiseDock(self.imageControlsDock)
        self._raiseDock(laserDock)

        # Add dock area to layout
        layout.addWidget(dockArea)

        self.showMaximized()
        self.imageControlsDock.container().setStretch(1, 1)
        scanDock.container().setStretch(1, 1)
        self.imageDock.setStretch(100, 100)

    def setDetectorRelatedDocksVisible(self, visible):
        self._catchingSetVisible(self.imageDock, visible)
        self._catchingSetVisible(self.recordingDock, visible)
        self._catchingSetVisible(self.imageControlsDock, visible)
        if self.availableWidgetsInfo.BeadRecWidget:
            self._catchingSetVisible(self.beadDock, visible)

        if not visible:
            self.showNormal()

    def closeEvent(self, event):
        self.sigClosing.emit()
        event.accept()

    def _catchingSetVisible(self, widget, visible):
        try:
            widget.setVisible(visible)
        except AttributeError:
            pass

    def _raiseDock(self, dock):
        try:
            dock.raiseDock()
        except AttributeError:  # raised when dock has no siblings
            pass

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
