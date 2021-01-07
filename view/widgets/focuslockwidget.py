# -*- coding: utf-8 -*-
"""
Created on Tue Jan 5 17:04:00 2021

@author: jonatan.alvelid
"""
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from controller.helpers.SLMHelper import MaskMode
import view.guitools as guitools
from .basewidgets import Widget


class FocusLockWidget(Widget):
    ''' Widget containing focus lock interface. '''
     def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Focus lock
        self.kpEdit = QtGui.QLineEdit('5')  # Connect to unlockFocus
        self.kpLabel = QtGui.QLabel('kp')
        self.kiEdit = QtGui.QLineEdit('0.1')  # Connect to unlockFocus
        self.kiLabel = QtGui.QLabel('ki')
        
        self.lockButton = guitools.BetterPushButton('Lock')  # Connect to toggleFocus
        self.lockButton.setCheckable(True)
        self.lockButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                      QtGui.QSizePolicy.Expanding)
        
        self.zStackBox = QtGui.QCheckBox('Z-stack')
        self.twoFociBox = QtGui.QCheckBox('Two foci')
        
        self.zStepFromEdit = QtGui.QLineEdit('40')
        self.zStepFromLabel = QtGui.QLabel('Min step (nm)')
        self.zStepToEdit = QtGui.QLineEdit('100')
        self.zStepToLabel = QtGui.QLabel('Max step (nm)')

        self.focusDataBox = QtGui.QCheckBox('Save data')  # Connect to exportData
        self.camDialogButton = guitools.BetterPushButton('Camera Dialog')  # Connect to webcam.show_dialog

        # Piezo absolute positioning
        self.positionLabel = QtGui.QLabel('Position (µm)')  # Potentially disregard this and only use in the positioning widget?
        self.positionEdit = QtGui.QLineEdit('50')
        self.positionSetButton = guitools.BetterPushButton('Set')  # Connect to movePZT

        # Focus lock calibration
        self.calibFromLabel = QtGui.QLabel('From (µm)')
        self.calibFromEdit = QtGui.QLineEdit('49')
        self.calibToLabel = QtGui.QLabel('To (µm)')
        self.calibToEdit = QtGui.QLineEdit('51')
        self.focusCalibButton = guitools.BetterPushButton('Calib')  # Connect to focuscalibthread.start
        self.focusCalibButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                            QtGui.QSizePolicy.Expanding)
        self.calibCurveButton = guitools.BetterPushButton('See calib')  # Connect to showCalibCurve
        self.calibrationDisplay = QtGui.QLineEdit('Previous calibration: none')  # Edit this from the controller with calibration values
        self.calibrationDisplay.setReadOnly(True)
        # CREATE CALIBRATION CURVE WINDOW AND FOCUS CALIBRATION GRAPH SOMEHOW


        # Focus lock graph
        self.focusLockGraph = FocusLockGraph(self, main)  # Don't create this as a separate class maybe? Or at least do not add all functionality to that class as it had previously, some of it must go in the controller and helper.
        
        # Webcam graph
        self.webcamGraph = pg.GraphicsWindow()
        self.img = pg.ImageItem(border='w')
        self.img.setImage(np.zeros((100,100)))
        self.vb = self.webcamGraph.addViewBox(invertY=True, invertX=False)
        self.vb.setAspectLocked(True)
        self.vb.addItem(self.img)

        # PROCESS DATA THREAD - ADD SOMEWHERE ELSE, NOT HERE, AS IT HAS NO GRAPHICAL ELEMENTS!

        # GUI layout below
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.focusLockGraph, 0, 0, 1, 9)
        grid.addWidget(self.webcamGraph, 0, 9, 4, 1)
        grid.addWidget(self.focusCalibButton, 1, 2, 2, 1)
        grid.addWidget(self.calibrationDisplay, 3, 0, 1, 2)
        grid.addWidget(self.kpLabel, 1, 3)
        grid.addWidget(self.kpEdit, 1, 4)
        grid.addWidget(self.kiLabel, 2, 3)
        grid.addWidget(self.kiEdit, 2, 4)
        grid.addWidget(self.lockButton, 1, 5, 2, 1)
        grid.addWidget(self.zStackBox, 4, 2)
        grid.addWidget(self.twoFociBox, 4, 6)
        grid.addWidget(self.zStepFromLabel, 3, 4)
        grid.addWidget(self.zStepFromEdit, 4, 4)
        grid.addWidget(self.zStepToLabel, 3, 5)
        grid.addWidget(self.zStepToEdit, 4, 5)
        grid.addWidget(self.focusDataBox, 4, 0, 1, 2)
        grid.addWidget(self.calibFromLabel, 1, 0)
        grid.addWidget(self.calibFromEdit, 1, 1)
        grid.addWidget(self.calibToLabel, 2, 0)
        grid.addWidget(self.calibToEdit, 2, 1)
        grid.addWidget(self.calibCurveButton, 3, 2)
        grid.addWidget(self.positionLabel, 1, 6)
        grid.addWidget(self.positionEdit, 1, 7)
        grid.addWidget(self.positionSetButton, 2, 6, 1, 2)
        grid.addWidget(self.camDialogButton, 3, 6, 1, 2)
