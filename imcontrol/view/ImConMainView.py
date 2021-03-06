# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:13:24 2020

@author: _Xavi
"""
import os

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.console import ConsoleWidget
from pyqtgraph.dockarea import Dock, DockArea

import constants
import imcontrol.view.guitools as guitools
import imcontrol.view.widgets as widgets


class ImConMainView(QtGui.QMainWindow):
    closing = QtCore.Signal()

    def __init__(self, viewSetupInfo, *args, **kwargs):
        super().__init__(*args, **kwargs)

        availableWidgetsInfo = viewSetupInfo.availableWidgets
        widgetLayoutInfo = viewSetupInfo.widgetLayout

        # Preset controls
        self.presetDir = os.path.join(constants.rootFolderPath, 'presets')
        defaultPreset = guitools.Preset.getDefault(self.presetDir)

        # Widget factory
        self.factory = widgets.WidgetFactory(defaultPreset)

        # Think what is self. and what is not !

        # Shortcuts
        # TODO

        # Menu Bar
        # TODO

        # Window
        self.setWindowTitle('ImSwitch')

        self.cwidget = QtGui.QWidget()
        layout = QtGui.QHBoxLayout()
        self.cwidget.setLayout(layout)
        self.setCentralWidget(self.cwidget)

        # Presets
        #self.presetsMenu = QtGui.QComboBox()

        #for preset in sorted(os.listdir(self.presetDir)):
        #    self.presetsMenu.addItem(preset)
        self.loadPresetButton = guitools.BetterPushButton('Load preset')

        #presetPickerContainer = QtGui.QHBoxLayout()
        #presetPickerContainer.addWidget(self.presetsMenu, 1)
        #presetPickerContainer.addWidget(self.loadPresetButton)
        #imageViewContainer.addLayout(presetPickerContainer)

        # Dock area
        dockArea = DockArea()

        # Laser dock
        laserDock = Dock("Laser Control", size=(1, 1))
        self.laserWidgets = self.factory.createWidget(widgets.LaserWidget)
        laserDock.addWidget(self.laserWidgets)
        dockArea.addDock(laserDock)

        # FFT dock
        if availableWidgetsInfo.FFTWidget:
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
        if availableWidgetsInfo.AlignmentLineWidget:
            self.alignmentLineWidget = self.factory.createWidget(widgets.AlignmentLineWidget)
            addAlignmentDock("Alignment Tool", self.alignmentLineWidget)

        # Z align widget
        if availableWidgetsInfo.AlignWidgetAverage:
            self.alignWidgetAverage = self.factory.createWidget(widgets.AlignWidgetAverage)
            addAlignmentDock("Axial Alignment Tool", self.alignWidgetAverage)

        # Rotational align widget
        if availableWidgetsInfo.AlignWidgetXY:
            self.alignWidgetXY = self.factory.createWidget(widgets.AlignWidgetXY)
            addAlignmentDock("Rotational Alignment Tool", self.alignWidgetXY)

        # ulenses Alignment Tool
        if availableWidgetsInfo.AlignWidgetXY:
            self.ulensesWidget = self.factory.createWidget(widgets.ULensesWidget)
            addAlignmentDock("uLenses Tool", self.ulensesWidget)

        try:
            laserDock.raiseDock()
        except AttributeError:  # raised when laser dock has no siblings
            pass

        # Piezo positioner
        piezoDock = Dock('Piezo positioner', size=(1, 1))
        self.positionerWidget = self.factory.createWidget(widgets.PositionerWidget)
        piezoDock.addWidget(self.positionerWidget)
        if alignmentDockLocation is not None:
            dockArea.addDock(piezoDock, 'bottom', alignmentDockLocation)
        else:
            dockArea.addDock(piezoDock, 'right', laserDock)

        scanDock = Dock('Scan', size=(1, 1))
        self.scanWidget = self.factory.createWidget(widgets.ScanWidget)
        scanDock.addWidget(self.scanWidget)
        dockArea.addDock(scanDock)

        if availableWidgetsInfo.BeadRecWidget:
            self.beadDock = Dock('Bead Rec', size=(1, 100))
            self.beadRecWidget = self.factory.createWidget(widgets.BeadRecWidget)
            self.beadDock.addWidget(self.beadRecWidget)
            dockArea.addDock(self.beadDock)

        # Add other widgets
        self.imageWidget = self.factory.createWidget(widgets.ImageWidget)
        self.recordingWidget = self.factory.createWidget(widgets.RecordingWidget)

        # Image controls container
        imageControlsContainer = QtGui.QVBoxLayout()
        imageControlsContainer.setContentsMargins(0, 9, 0, 0)

        self.settingsWidget = self.factory.createWidget(widgets.SettingsWidget)
        imageControlsContainer.addWidget(self.settingsWidget, 1)

        self.viewWidget = self.factory.createWidget(widgets.ViewWidget)
        imageControlsContainer.addWidget(self.viewWidget)

        imageControlsContainerWidget = QtGui.QWidget()
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
        self._catchingSetVisible(self.beadDock, visible)

        if not visible:
            self.showNormal()

    def closeEvent(self, event):
        self.closing.emit()
        event.accept()

    def _catchingSetVisible(self, widget, visible):
        try:
            widget.setVisible(visible)
        except AttributeError:
            pass
