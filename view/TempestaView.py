# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:13:24 2020

@author: _Xavi
"""
import os

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
from pyqtgraph.console import ConsoleWidget
# import view.guitools as guitools
from pyqtgraph.dockarea import Dock, DockArea

import constants
import view.widgets as widgets


class TempestaView(QtGui.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Devices
        self.deviceInfo = [['405', 0, [130, 0, 200]],
                           ['488', 1, [0, 247, 255]],
                           ['473', 2, [0, 183, 255]],
                           ['CAM', 3, [255, 255, 255]]]

        # Think what is self. and what is not !

        # Shortcuts
        # TODO

        # Menu Bar
        # TODO

        # Window
        self.setWindowTitle('Tempesta 2.0')
        self.cwidget = QtGui.QWidget()
        self.setCentralWidget(self.cwidget)

        layout = QtGui.QGridLayout()
        self.cwidget.setLayout(layout)

        # Presets
        self.presetsMenu = QtGui.QComboBox()
        self.presetDir = os.path.join(constants.rootFolderPath, 'presets')

        if not os.path.exists(self.presetDir):
            os.makedirs(self.presetDir)

        for preset in os.listdir(self.presetDir):
            self.presetsMenu.addItem(preset)
        self.loadPresetButton = QtGui.QPushButton('Load preset')

        layout.addWidget(self.presetsMenu, 0, 0)
        layout.addWidget(self.loadPresetButton, 0, 1)

        # def loadPresetFunction(): return guitools.loadPreset(self)
        # self.loadPresetButton.pressed.connect(loadPresetFunction)
        # Alignment area
        self.illumDockArea = DockArea()

        FFTDock = Dock("FFT Tool", size=(1, 1))
        self.fftWidget = widgets.FFTWidget()
        FFTDock.addWidget(self.fftWidget)
        self.illumDockArea.addDock(FFTDock)

        # Line Alignment Tool
        self.alignmentLineWidget = widgets.AlignmentLineWidget()
        alignmentLineDock = Dock("Alignment Tool", size=(1, 1))
        alignmentLineDock.addWidget(self.alignmentLineWidget)
        self.illumDockArea.addDock(alignmentLineDock, 'right')

        # Z align widget
        ZalignDock = Dock("Axial Alignment Tool", size=(1, 1))
        self.alignWidgetAverage = widgets.AlignWidgetAverage()
        ZalignDock.addWidget(self.alignWidgetAverage)
        self.illumDockArea.addDock(ZalignDock, 'above', alignmentLineDock)

        # Rotational align widget
        RotalignDock = Dock("Rotational Alignment Tool", size=(1, 1))
        self.alignWidgetXY = widgets.AlignWidgetXY()
        RotalignDock.addWidget(self.alignWidgetXY)
        self.illumDockArea.addDock(RotalignDock, 'above', alignmentLineDock)

        # ulenses Alignment Tool
        self.ulensesWidget = widgets.ULensesWidget()
        ulensesDock = Dock("uLenses Tool", size=(1, 1))
        ulensesDock.addWidget(self.ulensesWidget)
        self.illumDockArea.addDock(ulensesDock, 'above', alignmentLineDock)

        # Laser dock
        laserDock = Dock("Laser Control", size=(300, 1))
        self.laserWidgets = widgets.LaserWidget()
        laserDock.addWidget(self.laserWidgets)
        self.illumDockArea.addDock(laserDock, 'above', FFTDock)

        layout.addWidget(self.illumDockArea, 0, 3, 2, 1)

        # Dock Area
        dockArea = DockArea()

        scanDock = Dock('Scan', size=(1, 1))
        self.scanWidget = widgets.ScanWidget(self.deviceInfo)
        scanDock.addWidget(self.scanWidget)
        dockArea.addDock(scanDock)

        beadDock = Dock('Bead Rec', size=(1, 1))
        self.beadRecWidget = widgets.BeadRecWidget()
        beadDock.addWidget(self.beadRecWidget)
        dockArea.addDock(beadDock, 'bottom', scanDock)

        # Piezo positioner
        piezoDock = Dock('Piezo positioner', size=(1, 1))
        self.positionerWidget = widgets.PositionerWidget()
        piezoDock.addWidget(self.positionerWidget)
        dockArea.addDock(piezoDock, 'bottom', alignmentLineDock)

        layout.addWidget(dockArea, 2, 3, 4, 1)
        # Add all other Widgets
        self.settingsWidget = widgets.SettingsWidget()
        layout.addWidget(self.settingsWidget, 1, 0, 2, 2)

        self.imageWidget = widgets.ImageWidget()
        layout.addWidget(self.imageWidget, 0, 2, 6, 1)

        self.viewWidget = widgets.ViewWidget()
        layout.addWidget(self.viewWidget, 3, 0, 1, 2)

        self.recordingWidget = widgets.RecordingWidget()
        layout.addWidget(self.recordingWidget, 4, 0, 1, 2)

        console = ConsoleWidget(namespace={'pg': pg, 'np': np})
        layout.addWidget(console, 5, 0, 1, 2)
        # TODO
        layout.setRowMinimumHeight(2, 175)
        layout.setRowMinimumHeight(3, 100)
        layout.setRowMinimumHeight(5, 175)
        layout.setColumnMinimumWidth(0, 275)
        layout.setColumnMinimumWidth(2, 1350)
        self.imageWidget.ci.layout.setColumnFixedWidth(1, 1150)
        self.imageWidget.ci.layout.setRowFixedHeight(1, 1150)

    def registerController(self, controller):
        self.imageWidget.registerListener(controller.imageController)
        self.scanWidget.registerListener(controller.scanController)
        self.beadRecWidget.registerListener(controller.beadController)
        self.positionerWidget.registerListener(controller.positionerController)
        self.ulensesWidget.registerListener(controller.uLensesController)
        self.alignWidgetXY.registerListener(controller.alignXYController)
        self.alignWidgetAverage.registerListener(controller.alignAverageController)
        self.alignmentLineWidget.registerListener(controller.alignmentLineController)
        self.laserWidgets.registerListener(controller.laserController)
        self.fftWidget.registerListener(controller.fftController)
        self.recordingWidget.registerListener(controller.recorderController)
        self.viewWidget.registerListener(controller.viewController)
        self.settingsWidget.registerListener(controller.settingsController)
        self.close = controller.closeEvent

    def closeEvent(self, event):
        self.close()
        event.accept()
