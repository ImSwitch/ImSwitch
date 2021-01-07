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

        availableWidgetsInfo = viewSetupInfo.availableWidgets
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

        leftContainer = QtGui.QVBoxLayout()
        leftContainer.setContentsMargins(0, 0, 0, 0)
        middleContainer = QtGui.QVBoxLayout()
        middleContainer.setContentsMargins(0, 0, 0, 0)
        rightContainer = QtGui.QVBoxLayout()
        rightContainer.setContentsMargins(0, 0, 0, 0)

        # Presets
        self.presetsMenu = QtGui.QComboBox()

        for preset in sorted(os.listdir(self.presetDir)):
            self.presetsMenu.addItem(preset)
        self.loadPresetButton = guitools.BetterPushButton('Load preset')

        presetPickerContainer = QtGui.QHBoxLayout()
        presetPickerContainer.addWidget(self.presetsMenu, 1)
        presetPickerContainer.addWidget(self.loadPresetButton)
        leftContainer.addLayout(presetPickerContainer)

        # Dock area
        dockArea = DockArea()

        # Laser dock
        laserDock = Dock("Laser Control", size=(1, 1))
        self.laserWidgets = self.factory.createWidget(widgets.LaserWidget)
        laserDock.addWidget(self.laserWidgets)
        dockArea.addDock(laserDock)

        # Focus lock dock
        focusLockDock = Dock('Focus Lock', size=(1, 1))
        self.focusLockWidget = self.factory.createWidget(widgets.FocusLockWidget)
        focusLockDock.addWidget(self.focusLockWidget)
        dockArea.addDock(focusLockDock, 'above', laserDock)

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
            dockArea.addDock(piezoDock, 'bottom', laserDock)

        # Scan widget dock
        scanDock = Dock('Scan', size=(1, 1))
        self.scanWidget = self.factory.createWidget(widgets.ScanWidget)
        scanDock.addWidget(self.scanWidget)
        dockArea.addDock(scanDock)

        # SLM widget dock
        slmDock = Dock('SLM', size=(1, 1))
        self.slmWidget = self.factory.createWidget(widgets.SLMWidget)
        slmDock.addWidget(self.slmWidget)
        dockArea.addDock(slmDock, 'above', scanDock)

        if availableWidgetsInfo.BeadRecWidget:
            beadDock = Dock('Bead Rec', size=(1, 1))
            self.beadRecWidget = self.factory.createWidget(widgets.BeadRecWidget)
            beadDock.addWidget(self.beadRecWidget)
            dockArea.addDock(beadDock)

        rightContainer.addWidget(dockArea)

        # Add other widgets
        self.imageWidget = self.factory.createWidget(widgets.ImageWidget)
        self.imageWidget.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        middleContainer.addWidget(self.imageWidget)

        self.settingsWidget = self.factory.createWidget(widgets.SettingsWidget)
        leftContainer.addWidget(self.settingsWidget, 1)

        self.viewWidget = self.factory.createWidget(widgets.ViewWidget)
        leftContainer.addWidget(self.viewWidget)

        self.recordingWidget = self.factory.createWidget(widgets.RecordingWidget)
        leftContainer.addWidget(self.recordingWidget)

        console = ConsoleWidget(namespace={'pg': pg, 'np': np})
        console.setMaximumHeight(150)
        leftContainer.addWidget(console)

        # Add containers to layout
        layout.addLayout(leftContainer, 1)
        layout.addLayout(middleContainer, 10)
        layout.addLayout(rightContainer, 1)

    def closeEvent(self, event):
        self.closing.emit()
        event.accept()
