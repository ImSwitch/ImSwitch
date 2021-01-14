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
# import view.guitools as guitools
from pyqtgraph.dockarea import Dock, DockArea

import constants
import view.guitools as guitools
import view.widgets as widgets


class MainView(QtGui.QMainWindow):
    closing = QtCore.pyqtSignal()

    def __init__(self, viewSetupInfo, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.availableWidgetsInfo = viewSetupInfo.availableWidgets
        widgetLayoutInfo = viewSetupInfo.widgetLayout

        # Style overrides
        self.setStyleSheet('''
            QPushButton { min-width: 20px }
            QPushButton:checked { background-color: #29353D; border: 2px solid #1464A0 }
            
            QLabel { background-color: transparent; }
            
            DockLabel { padding: 0 }
        ''')

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
        self.setCentralWidget(self.cwidget)

        layout = QtGui.QHBoxLayout()
        self.cwidget.setLayout(layout)

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

        if self.availableWidgetsInfo.BeadRecWidget:
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

        # Objective motorized correction collar widget dock
        if self.availableWidgetsInfo.MotCorrWidget:
            motCorrDock = Dock('Objective Mot Corr', size=(1, 1))
            self.motCorrWidget = self.factory.createWidget(widgets.MotCorrWidget)
            motCorrDock.addWidget(self.motCorrWidget)
            dockArea.addDock(motCorrDock, 'below',  self.imageControlsDock)

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
        self.closing.emit()
        event.accept()

    def _catchingSetVisible(self, widget, visible):
        try:
            widget.setVisible(visible)
        except AttributeError:
            pass
