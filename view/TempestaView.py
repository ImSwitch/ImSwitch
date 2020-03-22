# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:13:24 2020

@author: _Xavi
"""
from pyqtgraph.Qt import QtGui
import view.widgets as widgets
import sys
from pyqtgraph.console import ConsoleWidget
import pyqtgraph as pg
import numpy as np
import os
#import view.guitools as guitools
from pyqtgraph.dockarea import Dock, DockArea

class TempestaView():
    
    def __init__(self, model):

        self.model = model
        self.app = QtGui.QApplication([])
        self.win = QtGui.QMainWindow()    

    def setController(self, controller):
        self.controller = controller
        
    def startView(self):
        # Think what is self. and what is not !
        
        # Shortcuts
        # TODO
        
        # Menu Bar
        # TODO

        # Window
        self.win.setWindowTitle('Tempesta 2.0')
        self.win.cwidget = QtGui.QWidget()
        self.win.setCentralWidget(self.win.cwidget)

        layout = QtGui.QGridLayout()
        self.win.cwidget.setLayout(layout)
        
        # Presets
        self.presetsMenu = QtGui.QComboBox()
        self.controlFolder = os.path.split(os.path.realpath(__file__))[0]
        os.chdir(self.controlFolder)
        self.presetDir = os.path.join(self.controlFolder, 'presets')

        if not os.path.exists(self.presetDir):
            os.makedirs(self.presetDir)

        for preset in os.listdir(self.presetDir):
            self.presetsMenu.addItem(preset)
        self.loadPresetButton = QtGui.QPushButton('Load preset')
        
        layout.addWidget(self.presetsMenu, 0, 0)
        layout.addWidget(self.loadPresetButton, 0, 1)

        #def loadPresetFunction(): return guitools.loadPreset(self)
        #self.loadPresetButton.pressed.connect(loadPresetFunction)
        # Alignment area
        self.illumDockArea = DockArea()
        
        FFTDock = Dock("FFT Tool", size=(1, 1))
        self.FFTWidget = widgets.FFTWidget()
        self.FFTWidget.registerListener(self.controller)
        FFTDock.addWidget(self.FFTWidget)
        self.illumDockArea.addDock(FFTDock)
        
        # Line Alignment Tool
        alignmentWidget = widgets.AlignmentWidget()
        alignmentWidget.registerListener(self.controller)
        alignmentDock = Dock("Alignment Tool", size=(1, 1))
        alignmentDock.addWidget(alignmentWidget)
        self.illumDockArea.addDock(alignmentDock, 'right')
        
        # Z align widget
        ZalignDock = Dock("Axial Alignment Tool", size=(1, 1))
        self.ZalignWidget = widgets.AlignWidgetAverage()
        self.ZalignWidget.registerListener(self.controller)
        ZalignDock.addWidget(self.ZalignWidget)
        self.illumDockArea.addDock(ZalignDock, 'above', alignmentDock)

        # Rotational align widget
        RotalignDock = Dock("Rotational Alignment Tool", size=(1, 1))
        self.RotalignWidget = widgets.AlignWidgetXYProject()
        self.RotalignWidget.registerListener(self.controller)
        RotalignDock.addWidget(self.RotalignWidget)
        self.illumDockArea.addDock(RotalignDock, 'above', alignmentDock)
        
        # ulenses Alignment Tool
        self.ulensesWidget = widgets.ULensesWidget()
        ulensesDock = Dock("uLenses Tool", size=(1, 1))
        self.ulensesWidget.registerListener(self.controller)
        ulensesDock.addWidget(self.ulensesWidget)
        self.illumDockArea.addDock(ulensesDock, 'above', alignmentDock)
        
        # Laser dock
        laserDock = Dock("Laser Control", size=(300, 1))
        self.laserWidgets = widgets.LaserWidget()
        self.laserWidgets.registerListener(self.controller)
        laserDock.addWidget(self.laserWidgets)
        self.illumDockArea.addDock(laserDock, 'above', FFTDock) 

        layout.addWidget(self.illumDockArea, 0, 3, 2, 1)
        
        # Dock Area
        dockArea = DockArea()

        FocusLockDock = Dock("Focus Lock", size=(400, 400))
        self.FocusLockWidget = widgets.FocusWidget()
        self.FocusLockWidget.registerListener(self.controller)
        FocusLockDock.addWidget(self.FocusLockWidget)
        dockArea.addDock(FocusLockDock)
        
        scanDock = Dock('Scan', size=(1, 1))
        self.scanWidget = widgets.ScanWidget()
        self.scanWidget.registerListener(self.controller)
        scanDock.addWidget(self.scanWidget)
        dockArea.addDock(scanDock, 'below', FocusLockDock)
        
      
        # Piezo positioner
        piezoDock = Dock('Piezo positioner', size=(1, 1))
        self.piezoWidget = widgets.PositionerWidget()
        self.piezoWidget.registerListener(self.controller)
        piezoDock.addWidget(self.piezoWidget)
        dockArea.addDock(piezoDock, 'bottom', alignmentDock)
        
        layout.addWidget(dockArea, 2, 3, 4, 1)
        # Add all other Widgets
        self.settingsWidget = widgets.SettingsWidget()
        layout.addWidget(self.settingsWidget, 1, 0, 2, 2)
        
        self.imageWidget = widgets.ImageWidget()
        self.imageWidget.registerListener(self.controller)
        layout.addWidget(self.imageWidget, 0, 2, 6, 1)
        
        self.viewCtrlWidget = widgets.ViewCtrlWidget(self.imageWidget.vb)
        self.viewCtrlWidget.registerListener(self.controller)
        layout.addWidget(self.viewCtrlWidget, 3, 0, 1, 2)
        
        self.recordingWidget = widgets.RecordingWidget()
        self.recordingWidget.registerListener(self.controller)
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
        
        self.win.show()
        sys.exit(self.app.exec_())
        
