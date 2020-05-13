# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 17:08:54 2020

@author: _Xavi
"""
from pyqtgraph.Qt import QtGui  
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
import numpy as np
import view.guitools as guitools
import os
from pyqtgraph.dockarea import Dock, DockArea
import matplotlib.pyplot as plt
import configparser
import time

class Widget(QtGui.QWidget):
    """ Superclass for all Widgets. 
            All Widgets are subclasses of QWidget and should have a registerListener function. """
            
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def registerListener(self):
        """ Manage interactions with the WidgetController linked to the Widget. """
        raise NotImplementedError 
     
        
# Alignment


class ULensesWidget(Widget):
    """ Alignment widget that shows a grid of points on top of the image in the viewbox."""
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Graphical Elements
        self.ulensesButton = QtGui.QPushButton('uLenses')
        self.ulensesCheck = QtGui.QCheckBox('Show uLenses')
        self.xEdit = QtGui.QLineEdit('0')
        self.yEdit = QtGui.QLineEdit('0')
        self.pxEdit = QtGui.QLineEdit('157.5')
        self.upEdit = QtGui.QLineEdit('1182')
        self.ulensesPlot = pg.ScatterPlotItem()
        
        # Add elements to GridLayout
        ulensesLayout = QtGui.QGridLayout()
        self.setLayout(ulensesLayout)
        ulensesLayout.addWidget(QtGui.QLabel('Pixel Size'), 0, 0)
        ulensesLayout.addWidget(self.pxEdit, 0, 1)
        ulensesLayout.addWidget(QtGui.QLabel('Periodicity'), 1, 0)
        ulensesLayout.addWidget(self.upEdit, 1, 1)
        ulensesLayout.addWidget(QtGui.QLabel('X offset'), 2, 0)
        ulensesLayout.addWidget(self.xEdit, 2, 1)
        ulensesLayout.addWidget(QtGui.QLabel('Y offset'), 3, 0)
        ulensesLayout.addWidget(self.yEdit, 3, 1)
        ulensesLayout.addWidget(self.ulensesButton, 4, 0)
        ulensesLayout.addWidget(self.ulensesCheck, 4, 1)
        
    def registerListener(self, controller):
        """ Manage interactions with ULensesController. """
        controller.addPlot()
        self.ulensesButton.clicked.connect(controller.updateGrid)
        self.ulensesCheck.stateChanged.connect(controller.show)


class AlignWidgetXY(Widget):
    """ Alignment widget that shows the mean over an axis of a selected ROI."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Graphical elements
        self.roiButton = QtGui.QPushButton('Show ROI')
        self.roiButton.setCheckable(True)
        self.XButton = QtGui.QRadioButton('X dimension')
        self.YButton = QtGui.QRadioButton('Y dimension')
        self.ROI = guitools.ROI((50, 50), (0, 0), handlePos=(1, 0),
                       handleCenter=(0, 1), color=pg.mkPen(255, 0, 0),
                       scaleSnap=True, translateSnap=True)
        self.graph = guitools.ProjectionGraph()
        
        # Add elements to GridLayout
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.graph, 0, 0, 1, 6)
        grid.addWidget(self.roiButton, 1, 0, 1, 1)
        grid.addWidget(self.XButton, 1, 1, 1, 1)
        grid.addWidget(self.YButton, 1, 2, 1, 1)
        
    def registerListener(self, controller):
        """ Manage interactions with AlignXYController. """
        controller.addROI()
        self.roiButton.clicked.connect(controller.toggleROI)
        self.XButton.clicked.connect(lambda: controller.setAxis(0))
        self.YButton.clicked.connect(lambda: controller.setAxis(1))        
   
        
class AlignWidgetAverage(Widget):
    """ Alignment widget that shows the mean over a selected ROI."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.roiButton = QtGui.QPushButton('Show ROI')
        self.roiButton.setCheckable(True)
        self.resetButton = QtGui.QPushButton('Reset graph')
        self.ROI = guitools.ROI((50, 50), (0, 0), handlePos=(1, 0),
                       handleCenter=(0, 1), color=pg.mkPen(0, 255, 0),
                       scaleSnap=True, translateSnap=True)
        self.graph = guitools.SumpixelsGraph()
        
        # Add items to GridLayout
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.graph, 0, 0, 1, 6)
        grid.addWidget(self.roiButton, 1, 0, 1, 1)
        grid.addWidget(self.resetButton, 1, 1, 1, 1)
        grid.setRowMinimumHeight(0, 300)

        
    def registerListener(self, controller):
        """ Manage interactions with AlignAverageController. """
        controller.addROI()
        self.roiButton.clicked.connect(controller.toggleROI)
        self.resetButton.clicked.connect(self.graph.resetData)
    

class AlignmentLineWidget(Widget):
    """ Alignment widget that displays a line on top of the image in the viewbox."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Graphical elements
        self.angleEdit = QtGui.QLineEdit('30')
        self.angle = np.float(self.angleEdit.text())
        self.alignmentCheck = QtGui.QCheckBox('Show Alignment Tool')
        self.alignmentLineMakerButton = QtGui.QPushButton('Alignment Line')
        pen = pg.mkPen(color=(255, 255, 0), width=0.5,
                       style=QtCore.Qt.SolidLine, antialias=True)
        self.alignmentLine = pg.InfiniteLine(
            pen=pen, movable=True)
        
        # Add items to GridLayout
        alignmentLayout = QtGui.QGridLayout()
        self.setLayout(alignmentLayout)
        alignmentLayout.addWidget(QtGui.QLabel('Line Angle'), 0, 0)
        alignmentLayout.addWidget(self.angleEdit, 0, 1)
        alignmentLayout.addWidget(self.alignmentLineMakerButton, 1, 0)
        alignmentLayout.addWidget(self.alignmentCheck, 1, 1)
        
    def registerListener(self, controller):
        """ Manage interactions with AlignmentLineController. """
        controller.addLine()
        self.alignmentLineMakerButton.clicked.connect(controller.updateLine)
        self.alignmentCheck.stateChanged.connect(controller.show)
        
        
class FFTWidget(Widget):
    """ Displays the FFT transform of the image. """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Graphical elements
        self.showCheck = QtGui.QCheckBox('Show FFT')
        self.showCheck.setCheckable = True
        self.changePosButton = QtGui.QPushButton('Period (pix)')
        self.linePos = QtGui.QLineEdit('4')
        self.lineRate = QtGui.QLineEdit('10')
        self.labelRate = QtGui.QLabel('Update rate')
        
            # Vertical and horizontal lines 
        self.vline = pg.InfiniteLine()
        self.hline = pg.InfiniteLine()
        self.rvline = pg.InfiniteLine()
        self.lvline = pg.InfiniteLine()
        self.uhline = pg.InfiniteLine()
        self.dhline = pg.InfiniteLine()

            # Viewbox
        self.cwidget = pg.GraphicsLayoutWidget()
        self.vb = self.cwidget.addViewBox(row=1, col=1)
        self.vb.setMouseMode(pg.ViewBox.RectMode)
        self.img = pg.ImageItem()
        self.img.translate(-0.5, -0.5)
        self.vb.addItem(self.img)
        self.vb.setAspectLocked(True)
        self.hist = pg.HistogramLUTItem(image=self.img)
        self.hist.vb.setLimits(yMin=0, yMax=66000)
        self.cubehelixCM = pg.ColorMap(np.arange(0, 1, 1/256), guitools.cubehelix().astype(int))
        self.hist.gradient.setColorMap(self.cubehelixCM)
        for tick in self.hist.gradient.ticks:
            tick.hide()
        self.cwidget.addItem(self.hist, row=1, col=2)
        
            # Add lines to viewbox
        self.vb.addItem(self.vline)
        self.vb.addItem(self.hline)
        self.vb.addItem(self.lvline)
        self.vb.addItem(self.rvline)
        self.vb.addItem(self.uhline)
        self.vb.addItem(self.dhline)

        # Add elements to GridLayout
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.cwidget, 0, 0, 1, 6)
        grid.addWidget(self.showCheck, 1, 0, 1, 1)
        grid.addWidget(self.changePosButton, 2, 0, 1, 1)
        grid.addWidget(self.linePos, 2, 1, 1, 1)
        grid.addWidget(self.labelRate, 2, 2, 1, 1)
        grid.addWidget(self.lineRate, 2, 3, 1, 1)   
        grid.setRowMinimumHeight(0, 300)
        
    def registerListener(self, controller):
        """ Manage interactions with AlignmentLineController. """
        self.showCheck.stateChanged.connect(controller.showFFT)
        self.changePosButton.clicked.connect(controller.changePos)
        self.linePos.textChanged.connect(controller.changePos)
        self.lineRate.textChanged.connect(controller.changeRate)
            

# Image related Widgets
  

class SettingsWidget(Widget):
    """ Camera settings and ROI parameters. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        cameraTitle = QtGui.QLabel('<h2><strong>Camera settings</strong></h2>')
        cameraTitle.setTextFormat(QtCore.Qt.RichText)
        self.tree = guitools.CamParamTree()
        self.ROI = guitools.ROI((0, 0), (0, 0), handlePos=(1, 0),
                                handleCenter=(0, 1), color='y', scaleSnap=True,
                                translateSnap=True)
        
        # Add elements to GridLayout
        cameraGrid = QtGui.QGridLayout()
        self.setLayout(cameraGrid)
        cameraGrid.addWidget(cameraTitle, 0, 0)
        cameraGrid.addWidget(self.tree, 1, 0)
          
    def registerListener(self, controller):
        """ Manage interactions with SettingsController. """
        controller.addROI()
        controller.getParameters()
        controller.setExposure()
        controller.adjustFrame()
        self.ROI.sigRegionChangeFinished.connect(controller.ROIchanged)
 
 
class ViewWidget(Widget):
    """ View settings (liveview, grid, crosshair). """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Graphical elements
            # Grid
        self.gridButton = QtGui.QPushButton('Grid')
        self.gridButton.setCheckable(True)
        self.gridButton.setEnabled(False)
        self.gridButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                      QtGui.QSizePolicy.Expanding)
    
            # Crosshair
        self.crosshairButton = QtGui.QPushButton('Crosshair')
        self.crosshairButton.setCheckable(True)
        self.crosshairButton.setEnabled(False)
        self.crosshairButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                           QtGui.QSizePolicy.Expanding)
            # liveview
        self.liveviewButton = QtGui.QPushButton('LIVEVIEW')
        self.liveviewButton.setStyleSheet("font-size:20px")
        self.liveviewButton.setCheckable(True)
        self.liveviewButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                          QtGui.QSizePolicy.Expanding)
        self.liveviewButton.setEnabled(True)
    
        # Add elements to GridLayout
        self.viewCtrlLayout = QtGui.QGridLayout()
        self.setLayout(self.viewCtrlLayout)
        self.viewCtrlLayout.addWidget(self.liveviewButton, 0, 0, 1, 2)
        self.viewCtrlLayout.addWidget(self.gridButton, 1, 0)
        self.viewCtrlLayout.addWidget(self.crosshairButton, 1, 1)
    
    def registerListener(self, controller):
        """ Manage interactions with ViewController. """
        self.gridButton.clicked.connect(controller.gridToggle)
        self.crosshairButton.pressed.connect(controller.crosshairToggle)
        self.liveviewButton.clicked.connect(controller.liveview)
        
        
class ImageWidget(pg.GraphicsLayoutWidget):
    """ Widget containing viewbox that displays the new camera frames.  """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Graphical elements
        self.levelsButton = QtGui.QPushButton('Update Levels')
        self.levelsButton.setEnabled(False)
        self.levelsButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                        QtGui.QSizePolicy.Expanding)
        proxy = QtGui.QGraphicsProxyWidget()
        proxy.setWidget(self.levelsButton)
        self.addItem(proxy, row=0, col=2)
        
            # Viewbox and related elements
        self.vb = self.addViewBox(row=1, col=1)
        self.vb.setMouseMode(pg.ViewBox.RectMode)
        self.img = pg.ImageItem()
        self.img.translate(-0.5, -0.5)
        self.vb.addItem(self.img)
        self.vb.setAspectLocked(True)
        self.setAspectLocked(True)
        self.hist = pg.HistogramLUTItem(image=self.img)
        self.hist.vb.setLimits(yMin=0, yMax=66000)
        self.cubehelixCM = pg.ColorMap(np.arange(0, 1, 1/256),
                                       guitools.cubehelix().astype(int))
        self.hist.gradient.setColorMap(self.cubehelixCM)
        self.grid = guitools.Grid(self.vb)
        self.crosshair = guitools.Crosshair(self.vb)
        for tick in self.hist.gradient.ticks:
            tick.hide()
        self.addItem(self.hist, row=1, col=2)
        for tick in self.hist.gradient.ticks:
            tick.hide()
        self.addItem(self.hist, row=1, col=2)
            # x and y profiles
        xPlot = self.addPlot(row=0, col=1)
        xPlot.hideAxis('left')
        xPlot.hideAxis('bottom')
        self.xProfile = xPlot.plot()
        self.ci.layout.setRowMaximumHeight(0, 40)
        xPlot.setXLink(self.vb)
        yPlot = self.addPlot(row=1, col=0)
        yPlot.hideAxis('left')
        yPlot.hideAxis('bottom')
        self.yProfile = yPlot.plot()
        self.yProfile.rotate(90)
        self.ci.layout.setColumnMaximumWidth(0, 40)
        yPlot.setYLink(self.vb)
    
    def registerListener(self, controller): 
        """ Manage interactions with ImageController. """
        self.levelsButton.pressed.connect(controller.autoLevels)
        
    
class RecordingWidget(Widget):
    """ Widget to control image or sequence recording.
    Recording only possible when liveview active. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        recTitle = QtGui.QLabel('<h2><strong>Recording settings</strong></h2>')
        recTitle.setTextFormat(QtCore.Qt.RichText)
  
            # Folder and filename fields
        self.dataDir = r"D:\Data"
        self.initialDir = os.path.join(self.dataDir, time.strftime('%Y-%m-%d'))
        self.folderEdit = QtGui.QLineEdit(self.initialDir)
        self.openFolderButton = QtGui.QPushButton('Open')
        self.specifyfile = QtGui.QCheckBox('Specify file name')
        self.filenameEdit = QtGui.QLineEdit('Current time')

            # Snap and recording buttons
        self.snapTIFFButton = QtGui.QPushButton('Snap')
        self.snapTIFFButton.setStyleSheet("font-size:16px")
        self.snapTIFFButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                          QtGui.QSizePolicy.Expanding)
        self.recButton = QtGui.QPushButton('REC')
        self.recButton.setStyleSheet("font-size:16px")
        self.recButton.setCheckable(True)
        self.recButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                     QtGui.QSizePolicy.Expanding)
            # Number of frames and measurement timing
        modeTitle = QtGui.QLabel('<strong>Mode</strong>')
        modeTitle.setTextFormat(QtCore.Qt.RichText)
        self.specifyFrames = QtGui.QRadioButton('Number of frames')
        self.specifyTime = QtGui.QRadioButton('Time (s)')
        self.recScanOnceBtn = QtGui.QRadioButton('Scan once')
        self.recScanLapseBtn = QtGui.QRadioButton('Time-lapse scan')
        self.currentLapse = QtGui.QLabel('0 / ')
        self.timeLapseEdit = QtGui.QLineEdit('5')
        self.freqLabel = QtGui.QLabel('Freq [s]')
        self.freqEdit = QtGui.QLineEdit('0')
        self.dimLapse = QtGui.QRadioButton('3D-lapse')
        self.currentSlice = QtGui.QLabel('0 / ')
        self.totalSlices = QtGui.QLineEdit('5')
        self.stepSizeLabel = QtGui.QLabel('Step size [um]')
        self.stepSizeEdit = QtGui.QLineEdit('0.05')
        self.untilSTOPbtn = QtGui.QRadioButton('Run until STOP')
        self.timeToRec = QtGui.QLineEdit('1')
        self.currentTime = QtGui.QLabel('0 / ')
        self.currentTime.setAlignment((QtCore.Qt.AlignRight |
                                       QtCore.Qt.AlignVCenter))
        self.currentFrame = QtGui.QLabel('0 /')
        self.currentFrame.setAlignment((QtCore.Qt.AlignRight |
                                        QtCore.Qt.AlignVCenter))
        self.numExpositionsEdit = QtGui.QLineEdit('100')
        self.tRemaining = QtGui.QLabel()
        self.tRemaining.setAlignment((QtCore.Qt.AlignCenter |
                                      QtCore.Qt.AlignVCenter))

        # Add items to GridLayout
        buttonWidget = QtGui.QWidget()
        buttonGrid = QtGui.QGridLayout()
        buttonWidget.setLayout(buttonGrid)
        buttonGrid.addWidget(self.snapTIFFButton, 0, 0)
        buttonWidget.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                   QtGui.QSizePolicy.Expanding)
        buttonGrid.addWidget(self.recButton, 0, 2)

        recGrid = QtGui.QGridLayout()
        self.setLayout(recGrid)

        recGrid.addWidget(recTitle, 0, 0, 1, 3)
        recGrid.addWidget(QtGui.QLabel('Folder'), 2, 0)
        recGrid.addWidget(self.folderEdit, 2, 1, 1, 2)
        recGrid.addWidget(self.openFolderButton, 2, 3)
        recGrid.addWidget(self.filenameEdit, 3, 1, 1, 2)

        recGrid.addWidget(self.specifyfile, 3, 0)

        recGrid.addWidget(modeTitle, 4, 0)
        recGrid.addWidget(self.specifyFrames, 5, 0, 1, 5)
        recGrid.addWidget(self.currentFrame, 5, 1)
        recGrid.addWidget(self.numExpositionsEdit, 5, 2)
        recGrid.addWidget(self.specifyTime, 6, 0, 1, 5)
        recGrid.addWidget(self.currentTime, 6, 1)
        recGrid.addWidget(self.timeToRec, 6, 2)
        recGrid.addWidget(self.tRemaining, 6, 3, 1, 2)
        recGrid.addWidget(self.recScanOnceBtn, 7, 0, 1, 5)
        recGrid.addWidget(self.recScanLapseBtn, 8, 0, 1, 5)
        recGrid.addWidget(self.currentLapse, 8, 1)
        recGrid.addWidget(self.timeLapseEdit, 8, 2)
        recGrid.addWidget(self.freqLabel, 8, 3)
        recGrid.addWidget(self.freqEdit, 8, 4)
        recGrid.addWidget(self.dimLapse, 9, 0, 1, 5)
        recGrid.addWidget(self.currentSlice, 9, 1)
        recGrid.addWidget(self.totalSlices, 9, 2)
        recGrid.addWidget(self.stepSizeLabel, 9, 3)
        recGrid.addWidget(self.stepSizeEdit, 9, 4)
        recGrid.addWidget(self.untilSTOPbtn, 10, 0, 1, 5)
        recGrid.addWidget(buttonWidget, 11, 0, 1, 0)

        recGrid.setColumnMinimumWidth(0, 70)

        # Initial condition of fields and checkboxes.
        self.writable = True
        self.readyToRecord = False
        self.filenameEdit.setEnabled(False)
        self.untilSTOPbtn.setChecked(True)

    def registerListener(self, controller):
        controller.untilStop()
        self.openFolderButton.clicked.connect(controller.openFolder)
        self.specifyfile.clicked.connect(controller.specFile)
        self.snapTIFFButton.clicked.connect(controller.snap)
        self.recButton.clicked.connect(controller.toggleREC)
        self.specifyFrames.clicked.connect(controller.specFrames)
        self.specifyTime.clicked.connect(controller.specTime)
        self.recScanOnceBtn.clicked.connect(controller.recScanOnce)
        self.recScanLapseBtn.clicked.connect(controller.recScanLapse)
        self.dimLapse.clicked.connect(controller.dimLapse)
        self.untilSTOPbtn.clicked.connect(controller.untilStop)
        
        
# Hardware widgets


class PositionerWidget(Widget):
    """ Widget in control of the piezzo movement. """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Graphical elements
        self.xLabel = QtGui.QLabel(
            "<strong>x = {0:.2f} µm</strong>".format(0))
        self.xLabel.setTextFormat(QtCore.Qt.RichText)
        self.xUpButton = QtGui.QPushButton("+")
        self.xDownButton = QtGui.QPushButton("-")
        self.xStepEdit = QtGui.QLineEdit("0.05")
        self.xStepUnit = QtGui.QLabel(" µm")

        self.yLabel = QtGui.QLabel(
            "<strong>y = {0:.2f} µm</strong>".format(0))
        self.yLabel.setTextFormat(QtCore.Qt.RichText)
        self.yUpButton = QtGui.QPushButton("+")
        self.yDownButton = QtGui.QPushButton("-")
        self.yStepEdit = QtGui.QLineEdit("0.05")
        self.yStepUnit = QtGui.QLabel(" µm")

        self.zLabel = QtGui.QLabel(
            "<strong>z = {0:.2f} µm</strong>".format(0))
        self.zLabel.setTextFormat(QtCore.Qt.RichText)
        self.zUpButton = QtGui.QPushButton("+")
        self.zDownButton = QtGui.QPushButton("-")
        self.zStepEdit = QtGui.QLineEdit("0.05")
        self.zStepUnit = QtGui.QLabel(" µm")

        # Add elements to GridLayout
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.xLabel, 1, 0)
        layout.addWidget(self.xUpButton, 1, 1)
        layout.addWidget(self.xDownButton, 1, 2)
        layout.addWidget(QtGui.QLabel("Step"), 1, 3)
        layout.addWidget(self.xStepEdit, 1, 4)
        layout.addWidget(self.xStepUnit, 1, 5)
        layout.addWidget(self.yLabel, 2, 0)
        layout.addWidget(self.yUpButton, 2, 1)
        layout.addWidget(self.yDownButton, 2, 2)
        layout.addWidget(QtGui.QLabel("Step"), 2, 3)
        layout.addWidget(self.yStepEdit, 2, 4)
        layout.addWidget(self.yStepUnit, 2, 5)
        layout.addWidget(self.zLabel, 3, 0)
        layout.addWidget(self.zUpButton, 3, 1)
        layout.addWidget(self.zDownButton, 3, 2)
        layout.addWidget(QtGui.QLabel("Step"), 3, 3)
        layout.addWidget(self.zStepEdit, 3, 4)
        layout.addWidget(self.zStepUnit, 3, 5)

    def registerListener(self, controller): 
        """ Manage interactions with PositionerController. """
        self.xUpButton.pressed.connect(lambda: controller.move(0, float(self.xStepEdit.text())))
        self.xDownButton.pressed.connect(lambda: controller.move(0, -float(self.xStepEdit.text())))
        self.yUpButton.pressed.connect(lambda: controller.move(1, float(self.yStepEdit.text())))
        self.yDownButton.pressed.connect(lambda: controller.move(1, -float(self.yStepEdit.text())))
        self.zUpButton.pressed.connect(lambda: controller.move(2, float(self.zStepEdit.text())))
        self.zDownButton.pressed.connect(lambda: controller.move(2, -float(self.zStepEdit.text())))
        

class LaserWidget(Widget):
    """ Laser widget containing digital modulation and normal control. """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Create laser modules
        actControl = LaserModule('<h3>405<h3>', 'mW', '405', color=(130, 0, 200), prange=(0, 200), tickInterval=5, singleStep=0.1, init_power = 10)
        offControl = LaserModule('<h3>488<h3>', 'mW', '488', color=(0, 247, 255), prange=(0, 200), tickInterval=100, singleStep=10, init_power = 10)
        excControl = LaserModule('<h3>473<h3>', 'V', '473', color=(0, 183, 255), prange=(0, 5), tickInterval=1, singleStep=0.1, init_power = 0.5)
        self.digModule = DigitalModule()

        self.laserModules = {'405': actControl, '488': offControl, '473': excControl}
        
        # Add modules to GridLayout
        grid = QtGui.QGridLayout()
        self.setLayout(grid) 
        grid.addWidget(actControl, 0, 0, 4, 1)
        grid.addWidget(offControl, 0, 1, 4, 1)
        grid.addWidget(excControl, 0, 2, 4, 1)
        grid.addWidget(self.digModule, 4, 0, 2, 3)
        
    def registerListener(self, controller):
        """ Manage interactions with LaserController. """
        self.laserModules['405'].registerListener(controller)
        self.laserModules['488'].registerListener(controller)
        self.laserModules['473'].registerListener(controller)
        self.digModule.registerListener(controller)
      
        
class DigitalModule(QtGui.QFrame):
    """ Module from LaserWidget to handle digital modulation. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)   
        
        # Graphical elements
        title = QtGui.QLabel('<h3>Digital modulation<h3>')
        title.setTextFormat(QtCore.Qt.RichText)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size:12px")
        title.setFixedHeight(20)
        ActPower = QtGui.QLineEdit('100')
        OffPower = QtGui.QLineEdit('100')
        ExcPower = QtGui.QLineEdit('0.5')
        self.powers = {'405' : ActPower, '488' : OffPower, '473' : ExcPower}
        self.DigitalControlButton = QtGui.QPushButton('Enable')
        self.DigitalControlButton.setCheckable(True)
        style = "background-color: rgb{}".format((160, 160, 160))
        self.DigitalControlButton.setStyleSheet(style)
        self.updateDigPowersButton = QtGui.QPushButton('Update powers')   
        actUnit = QtGui.QLabel('mW')
        actUnit.setFixedWidth(20)
        
        actModFrame = QtGui.QFrame()
        actModGrid = QtGui.QGridLayout()
        actModFrame.setLayout(actModGrid)
        actModGrid.addWidget(ActPower, 0, 0)
        actModGrid.addWidget(actUnit, 0, 1)
        
        offUnit = QtGui.QLabel('mW')
        offUnit.setFixedWidth(20)
        offModFrame = QtGui.QFrame()
        offModGrid = QtGui.QGridLayout()
        offModFrame.setLayout(offModGrid)
        offModGrid.addWidget(OffPower, 0, 0)
        offModGrid.addWidget(offUnit, 0, 1)

        excUnit = QtGui.QLabel('V')
        excUnit.setFixedWidth(20)
        excModFrame = QtGui.QFrame()
        excModGrid = QtGui.QGridLayout()
        excModFrame.setLayout(excModGrid)
        excModGrid.addWidget(ExcPower, 0, 0)
        excModGrid.addWidget(excUnit, 0, 1)

        # Add elements to GridLayout
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(title, 0, 0)
        grid.addWidget(actModFrame, 1, 0)
        grid.addWidget(offModFrame, 1, 1)
        grid.addWidget(excModFrame, 1, 2)
        grid.addWidget(self.DigitalControlButton, 2, 0, 1, 3)
    
    def registerListener(self, controller):
        """ Manage interactions with LaserController. """
        self.powers['405'].textChanged.connect(lambda: controller.updateDigitalPowers(['405']))
        self.powers['488'].textChanged.connect(lambda: controller.updateDigitalPowers(['488']))
        self.powers['473'].textChanged.connect(lambda: controller.updateDigitalPowers(['473']))
        self.DigitalControlButton.clicked.connect(lambda: controller.GlobalDigitalMod(['405', '473', '488']))
        self.updateDigPowersButton.clicked.connect(lambda: controller.updateDigitalPowers(['405','473', '488']))
      
        
class LaserModule(QtGui.QFrame):
    """ Module from LaserWidget to handle a single laser. """
    def __init__(self, name,  units, laser, color, prange, tickInterval, singleStep, init_power,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Graphical elements
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        self.laser = laser
        self.name = QtGui.QLabel(name)
        self.name.setTextFormat(QtCore.Qt.RichText)
        self.name.setAlignment(QtCore.Qt.AlignCenter)
        self.name.setStyleSheet("font-size:16px")
        self.name.setFixedHeight(40)
        self.init_power = init_power
        self.setPointLabel = QtGui.QLabel('Setpoint')
        self.setPointEdit = QtGui.QLineEdit(str(self.init_power))
        self.setPointEdit.setFixedWidth(50)
        self.setPointEdit.setAlignment(QtCore.Qt.AlignRight)
        self.powerLabel = QtGui.QLabel('Power')
        self.powerIndicator = QtGui.QLabel(str(self.init_power))
        self.powerIndicator.setFixedWidth(50)
        self.powerIndicator.setAlignment(QtCore.Qt.AlignRight)
        self.maxpower = QtGui.QLabel(str(prange[1]))
        self.maxpower.setAlignment(QtCore.Qt.AlignCenter)
        self.slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.slider.setMinimum(prange[0])
        self.slider.setMaximum(prange[1])
        self.slider.setTickInterval(tickInterval)
        self.slider.setSingleStep(singleStep)
        self.slider.setValue(0)
        self.minpower = QtGui.QLabel(str(prange[0]))
        self.minpower.setAlignment(QtCore.Qt.AlignCenter)

        powerFrame = QtGui.QFrame(self)
        self.powerGrid = QtGui.QGridLayout()
        powerFrame.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Plain)
        powerFrame.setLayout(self.powerGrid)
        self.powerGrid.addWidget(self.setPointLabel, 1, 0, 1, 2)
        self.powerGrid.addWidget(self.setPointEdit, 2, 0)
        self.powerGrid.addWidget(QtGui.QLabel(units), 2, 1)
        self.powerGrid.addWidget(self.powerLabel, 3, 0, 1, 2)
        self.powerGrid.addWidget(self.powerIndicator, 4, 0)
        self.powerGrid.addWidget(QtGui.QLabel(units), 4, 1)
        self.powerGrid.addWidget(self.maxpower, 0, 3)
        self.powerGrid.addWidget(self.slider, 1, 3, 8, 1)
        self.powerGrid.addWidget(self.minpower, 9, 3)

        self.enableButton = QtGui.QPushButton('ON')
        style = "background-color: rgb{}".format(color)
        self.enableButton.setStyleSheet(style)
        self.enableButton.setCheckable(True)

        # Add elements to GridLayout
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)
        self.grid.addWidget(self.name, 0, 0, 1, 2)
        self.grid.addWidget(powerFrame, 1, 0, 1, 2)
        self.grid.addWidget(self.enableButton, 8, 0, 1, 2)

    def registerListener(self, controller):
        """ Manage interactions with LaserController. """
        if not self.laser=='473': controller.changeEdit(self.laser)
        self.enableButton.toggled.connect(lambda: controller.toggleLaser(self.laser))
        self.slider.valueChanged[int].connect(lambda: controller.changeSlider(self.laser))
        self.setPointEdit.returnPressed.connect(lambda: controller.changeEdit(self.laser))
        
        
class ScanWidget(Widget):
    ''' Widget containing scanner interface and beadscan reconstruction.
            This class uses the classes GraphFrame, MultipleScanWidget and IllumImageWidget'''
            
    def __init__(self, deviceInfo, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.allDevices = [x[0] for x in deviceInfo]
        self.controlFolder = os.path.split(os.path.realpath(__file__))[0]
        os.chdir(self.controlFolder)
        self.scanDir = os.path.join(self.controlFolder, 'scans')

        if not os.path.exists(self.scanDir):
            os.makedirs(self.scanDir)
            
        self.scanInLiveviewWar = QtGui.QMessageBox()
        self.scanInLiveviewWar.setInformativeText(
            "You need to be in liveview to scan")

        self.digModWarning = QtGui.QMessageBox()
        self.digModWarning.setInformativeText(
            "You need to be in digital laser modulation and external "
            "frame-trigger acquisition mode")
        
        self.saveScanBtn = QtGui.QPushButton('Save Scan')
        self.loadScanBtn = QtGui.QPushButton('Load Scan')
        
        self.sampleRateEdit = QtGui.QLineEdit()
        self.sizeXPar = QtGui.QLineEdit('2')
        self.sizeYPar = QtGui.QLineEdit('2')
        self.sizeZPar = QtGui.QLineEdit('10')
        self.seqTimePar = QtGui.QLineEdit('10')     # ms
        self.nrFramesPar = QtGui.QLabel()
        self.scanDuration = 0
        self.scanDurationLabel = QtGui.QLabel(str(self.scanDuration))
        self.stepSizeXPar = QtGui.QLineEdit('0.1')
        self.stepSizeYPar = QtGui.QLineEdit('0.1')
        self.stepSizeZPar = QtGui.QLineEdit('1')
        
        self.primScanDim = QtGui.QComboBox()
        self.scanDims = ['X', 'Y', 'Z']
        self.primScanDim.addItems(self.scanDims)
        self.primScanDim.setCurrentIndex(0)
        
        self.secScanDim = QtGui.QComboBox()
        self.secScanDim.addItems(self.scanDims)
        self.secScanDim.setCurrentIndex(1)
        
        self.thirdScanDim = QtGui.QComboBox()
        self.thirdScanDim.addItems(self.scanDims)
        self.thirdScanDim.setCurrentIndex(2)
        
        self.scanPar = {'sizeX': self.sizeXPar,
                         'sizeY': self.sizeYPar,
                         'sizeZ': self.sizeZPar,
                         'seqTime': self.seqTimePar,
                         'stepSizeX': self.stepSizeXPar,
                         'stepSizeY': self.stepSizeYPar,
                         'stepSizeZ': self.stepSizeZPar}
                               
        self.pxParameters = dict()
        self.pxParValues = dict()                       
      
        for i in range(0, len(self.allDevices)):
     
            self.pxParameters['sta'+self.allDevices[i]] = QtGui.QLineEdit('0')
            self.pxParameters['end'+self.allDevices[i]] = QtGui.QLineEdit('10')
            
        self.scanRadio = QtGui.QRadioButton('Scan')
        self.scanRadio.setChecked(True)
        self.contLaserPulsesRadio = QtGui.QRadioButton('Cont. Laser Pulses')
        self.scanButton = QtGui.QPushButton('Scan')
        self.scanning = False
    
        self.previewButton = QtGui.QPushButton('Plot scan path')
        self.previewButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                         QtGui.QSizePolicy.Expanding)
    
        self.continuousCheck = QtGui.QCheckBox('Repeat')
        
        self.sampleRate = 10000
        self.graph = GraphFrame()
        self.graph.plot.getAxis('bottom').setScale(1000/self.sampleRate)
        self.graph.setFixedHeight(100)
        
        self.multiScanWgt = MultipleScanWidget()

        grid = QtGui.QGridLayout()
        self.setLayout(grid)

        grid.addWidget(self.loadScanBtn, 0, 0)
        grid.addWidget(self.saveScanBtn, 0, 1)
        grid.addWidget(self.scanRadio, 0, 2) 
        grid.addWidget(self.contLaserPulsesRadio, 0, 3) #
        grid.addWidget(self.scanButton, 0, 4, 1, 2)
        grid.addWidget(self.continuousCheck, 0, 6)

        grid.addWidget(QtGui.QLabel('Size X (µm):'), 2, 0)
        grid.addWidget(self.sizeXPar, 2, 1)
        grid.addWidget(QtGui.QLabel('Size Y (µm):'), 3, 0)
        grid.addWidget(self.sizeYPar, 3, 1)
        grid.addWidget(QtGui.QLabel('Size Z (µm):'), 4, 0)
        grid.addWidget(self.sizeZPar, 4, 1)
        grid.addWidget(QtGui.QLabel('Step X (µm):'), 2, 2)
        grid.addWidget(self.stepSizeXPar, 2, 3)
        grid.addWidget(QtGui.QLabel('Step Y (µm):'), 3, 2)
        grid.addWidget(self.stepSizeYPar, 3, 3)
        grid.addWidget(QtGui.QLabel('Step Z (µm):'), 4, 2)
        grid.addWidget(self.stepSizeZPar, 4, 3)

        grid.addWidget(QtGui.QLabel('First dimension:'), 2, 4)
        grid.addWidget(self.primScanDim, 2, 5)
        grid.addWidget(QtGui.QLabel('Second dimension:'), 3, 4)
        grid.addWidget(self.secScanDim, 3, 5)
        grid.addWidget(QtGui.QLabel('Third dimension:'), 4, 4)
        grid.addWidget(self.thirdScanDim, 4, 5)
        grid.addWidget(QtGui.QLabel('Number of frames:'), 5, 4)
        grid.addWidget(self.nrFramesPar, 5, 5)
        grid.addWidget(self.previewButton, 2, 6, 3, 2)

        grid.addWidget(QtGui.QLabel('Dwell time (ms):'), 7, 0)
        grid.addWidget(self.seqTimePar, 7, 1)
        grid.addWidget(QtGui.QLabel('Total time (s):'), 7, 2)
        grid.addWidget(self.scanDurationLabel, 7, 3)
        grid.addWidget(QtGui.QLabel('Start (ms):'), 8, 1)
        grid.addWidget(QtGui.QLabel('End (ms):'), 8, 2)
        
        start_row = 9
        for i in range(0, len(self.allDevices)):
            grid.addWidget(QtGui.QLabel(self.allDevices[i]), start_row+i, 0)
            grid.addWidget(
                self.pxParameters['sta'+self.allDevices[i]], start_row+i, 1)
            grid.addWidget(
                self.pxParameters['end'+self.allDevices[i]], start_row+i, 2)
        
        grid.addWidget(self.graph, 8, 3, 5, 5)
        grid.addWidget(self.multiScanWgt, 13, 0, 4, 9)

        grid.setColumnMinimumWidth(6, 160)
        grid.setRowMinimumHeight(1, 10)
        grid.setRowMinimumHeight(6, 10)
        grid.setRowMinimumHeight(13, 10)
    
    def registerListener(self, controller):
        self.saveScanBtn.clicked.connect(controller.saveScan)
        self.loadScanBtn.clicked.connect(controller.loadScan)
        self.scanButton.clicked.connect(controller.runScan)
        self.previewButton.clicked.connect(controller.previewScan)
   
class GraphFrame(pg.GraphicsWindow):
    """Creates the plot that plots the preview of the pulses.
    Fcn update() updates the plot of "device" with signal "signal"."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Take params from model
        #self.pxCycle = pxCycle
        #devs = list(pxCycle.sigDict.keys())
        self.plot = self.addPlot(row=1, col=0)
        self.plot.setYRange(0, 1)
        self.plot.showGrid(x=False, y=False)
        #self.plotSigDict = dict()
#        for i in range(0, len(pxCycle.sigDict)):
#            r = deviceInfo[i][2][0]
#            g = deviceInfo[i][2][1]
#            b = deviceInfo[i][2][2]
#            self.plotSigDict[devs[i]] = self.plot.plot(pen=pg.mkPen(r, g, b))
    
class MultipleScanWidget(Widget):

    def __init__(self):
        super().__init__()
        illumPlotsDockArea = DockArea()
        
        self.illumWgt = IllumImageWidget()
        fovDock = Dock("2D scanning")
        fovDock.addWidget(self.illumWgt)
        
        self.illumWgt3D = pg.ImageView()
        pos, rgba = zip(*guitools.cmapToColormap(plt.get_cmap('inferno')))
        self.illumWgt3D.setColorMap(pg.ColorMap(pos, rgba))
        for tick in self.illumWgt3D.ui.histogram.gradient.ticks:
            tick.hide()
        volDock = Dock("3D scanning")
        volDock.addWidget(self.illumWgt3D)

        illumPlotsDockArea.addDock(volDock)
        illumPlotsDockArea.addDock(fovDock, 'above', volDock)

        self.makeImgBox = QtGui.QCheckBox('Build scan image')
        self.saveScanButton = QtGui.QPushButton('Save scan image')
        
        
        # Crosshair
        self.crosshair = guitools.Crosshair(self.illumWgt.vb)
        self.crossButton = QtGui.QPushButton('Crosshair')
        self.crossButton.setCheckable(True)

        self.analysis_btn = QtGui.QPushButton('Analyze')
        self.analysis_btn.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                        QtGui.QSizePolicy.Expanding)
        self.show_beads_btn = QtGui.QPushButton('Show beads')

        self.quality_label = QtGui.QLabel('Quality level of points')
        self.quality_edit = QtGui.QLineEdit('0.05')
                           
        self.win_size_label = QtGui.QLabel('Window size [px]')
        self.win_size_edit = QtGui.QLineEdit('10')
        

        self.beads_label = QtGui.QLabel('Bead number')
        self.beadsBox = QtGui.QComboBox()
        self.change_beads_button = QtGui.QPushButton('Change')
        self.overlayBox = QtGui.QComboBox()
        self.overlay_check = QtGui.QCheckBox('Overlay')
        self.clear_btn = QtGui.QPushButton('Clear')

        grid = QtGui.QGridLayout()
        self.setLayout(grid)

        grid.addWidget(self.crossButton, 0, 0)
        grid.addWidget(self.makeImgBox, 0, 1)
        grid.addWidget(self.saveScanButton, 0, 2)
        grid.addWidget(illumPlotsDockArea, 1, 0, 1, 8)

        grid.addWidget(self.quality_label, 2, 0)
        grid.addWidget(self.quality_edit, 2, 1)
        grid.addWidget(self.win_size_label, 3, 0)
        grid.addWidget(self.win_size_edit, 3, 1)
        grid.addWidget(self.show_beads_btn, 2, 2)
        grid.addWidget(self.analysis_btn, 3, 2)

        grid.addWidget(self.beads_label, 2, 4)
        grid.addWidget(self.beadsBox, 2, 5)
        grid.addWidget(self.change_beads_button, 3, 4, 1, 2)
        grid.addWidget(self.overlay_check, 2, 6)
        grid.addWidget(self.overlayBox, 2, 7)
        grid.addWidget(self.clear_btn, 3, 6, 1, 2)

        grid.setColumnMinimumWidth(3, 100)
    
    def registerListener(self, controller):
        self.saveScanButton.pressed.connect(controller.saveScan)
        self.crossButton.pressed.connect(controller.toggleCrossHair)
        self.analysis_btn.clicked.connect(controller.analyzeWorker)
        self.show_beads_btn.clicked.connect(controller.find_fpWorker)
        self.quality_edit.editingFinished.connect(controller.find_fpWorker)
        self.win_size_edit.editingFinished.connect(controller.find_fpWorker)
        self.beadsBox.activated.connect(controller.change_illum_image)
        self.change_beads_button.clicked.connect(controller.nextBead)
        self.overlayBox.activated.connect(controller.overlayWorker)
        self.overlay_check.stateChanged.connect(controller.overlayWorker)
        self.clear_btn.clicked.connect(controller.clear)
        
class IllumImageWidget(pg.GraphicsLayoutWidget):
    
    def __init__(self):
        super().__init__()
        self.vb = self.addViewBox(row=1, col=1)
        self.vb.setAspectLocked(True)
        self.vb.enableAutoRange()

        self.img = pg.ImageItem()
        self.vb.addItem(self.img)
        self.hist = pg.HistogramLUTItem(image=self.img)
        self.hist.vb.setLimits(yMin=0, yMax=66000)
        redsColormap = pg.ColorMap([0, 1], [(0, 0, 0), (255, 0, 0)])
        self.hist.gradient.setColorMap(redsColormap)
        for tick in self.hist.gradient.ticks:
            tick.hide()
        self.addItem(self.hist, row=1, col=2)

        self.imgBack = pg.ImageItem()
        self.vb.addItem(self.imgBack)
        self.imgBack.setZValue(10)
        self.imgBack.setOpacity(0.5)
        self.histBack = pg.HistogramLUTItem(image=self.imgBack)
        self.histBack.vb.setLimits(yMin=0, yMax=66000)
        pos, rgba = zip(*guitools.cmapToColormap(plt.get_cmap('viridis')))
        greensColormap = pg.ColorMap(pos, rgba)
        self.histBack.gradient.setColorMap(greensColormap)
        for tick in self.histBack.gradient.ticks:
            tick.hide()
        self.addItem(self.histBack, row=1, col=3)

        self.first = True
        self.firstBack = True           



        

        

        
    
            


        