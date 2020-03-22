# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 17:08:54 2020

@author: _Xavi
"""
from pyqtgraph.Qt import QtGui  
from pyqtgraph.Qt import QtCore
from pyqtgraph.parametertree import Parameter, ParameterTree
import pyqtgraph as pg
import numpy as np
import view.guitools as guitools
import time
from pyqtgraph.dockarea import Dock, DockArea
import matplotlib.pyplot as plt

class ScanWidget(QtGui.QMainWindow):
    ''' Widget containing scanner interface and beadscan reconstruction.
            This class uses the classes GraphFrame, MultipleScanWidget and IllumImageWidget'''
            
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        self.stepSizeXYPar = QtGui.QLineEdit('0.1')
        self.stepSizeZPar = QtGui.QLineEdit('1')
        
        self.sampleRate = 100000 # Take from model

        self.scanMode = QtGui.QComboBox()
        self.scanModes = ['FOV scan', 'VOL scan', 'Line scan']
        self.scanMode.addItems(self.scanModes)

        self.primScanDim = QtGui.QComboBox()
        self.scanDims = ['x', 'y']
        self.primScanDim.addItems(self.scanDims)
        
        self.scanRadio = QtGui.QRadioButton('Scan')
        self.scanRadio.setChecked(True)
        self.contLaserPulsesRadio = QtGui.QRadioButton('Cont. Laser Pulses')
        self.scanButton = QtGui.QPushButton('Scan')
        self.scanning = False
    
        self.previewButton = QtGui.QPushButton('Plot scan path')
        self.previewButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                         QtGui.QSizePolicy.Expanding)
    
        self.continuousCheck = QtGui.QCheckBox('Repeat')
        
        self.graph = GraphFrame()
        self.graph.plot.getAxis('bottom').setScale(1000/self.sampleRate)
        self.graph.setFixedHeight(100)
        
        self.multiScanWgt = MultipleScanWidget()

        self.cwidget = QtGui.QWidget()
        self.setCentralWidget(self.cwidget)
        grid = QtGui.QGridLayout()
        self.cwidget.setLayout(grid)

        grid.addWidget(self.loadScanBtn, 0, 0)
        grid.addWidget(self.saveScanBtn, 0, 1)
        grid.addWidget(self.scanRadio, 0, 2) #nop
        grid.addWidget(self.contLaserPulsesRadio, 0, 3) #nop
        grid.addWidget(self.scanButton, 0, 4, 1, 2)
        grid.addWidget(self.continuousCheck, 0, 6)

        grid.addWidget(QtGui.QLabel('Size X (µm):'), 2, 0)
        grid.addWidget(self.sizeXPar, 2, 1)
        grid.addWidget(QtGui.QLabel('Size Y (µm):'), 3, 0)
        grid.addWidget(self.sizeYPar, 3, 1)
        grid.addWidget(QtGui.QLabel('Size Z (µm):'), 4, 0)
        grid.addWidget(self.sizeZPar, 4, 1)
        grid.addWidget(QtGui.QLabel('Step XY (µm):'), 2, 2)
        grid.addWidget(self.stepSizeXYPar, 2, 3)
        grid.addWidget(QtGui.QLabel('Step Z (µm):'), 4, 2)
        grid.addWidget(self.stepSizeZPar, 4, 3)

        grid.addWidget(QtGui.QLabel('Mode:'), 2, 4)
        grid.addWidget(self.scanMode, 2, 5)
        grid.addWidget(QtGui.QLabel('Primary dimension:'), 3, 4)
        grid.addWidget(self.primScanDim, 3, 5)
        grid.addWidget(QtGui.QLabel('Number of frames:'), 4, 4)
        grid.addWidget(self.nrFramesPar, 4, 5)
        grid.addWidget(self.previewButton, 2, 6, 3, 2)

        grid.addWidget(QtGui.QLabel('Dwell time (ms):'), 7, 0)
        grid.addWidget(self.seqTimePar, 7, 1)
        grid.addWidget(QtGui.QLabel('Total time (s):'), 7, 2)
        grid.addWidget(self.scanDurationLabel, 7, 3)
        grid.addWidget(QtGui.QLabel('Start (ms):'), 8, 1)
        grid.addWidget(QtGui.QLabel('End (ms):'), 8, 2)
        
        grid.addWidget(self.graph, 8, 3, 5, 5)
        grid.addWidget(self.multiScanWgt, 13, 0, 4, 9)

        grid.setColumnMinimumWidth(6, 160)
        grid.setRowMinimumHeight(1, 10)
        grid.setRowMinimumHeight(6, 10)
        grid.setRowMinimumHeight(13, 10)
    
    def registerListener(self, controller):
        self.saveScanBtn.clicked.connect(controller.scanController.saveScan)
        self.loadScanBtn.clicked.connect(controller.scanController.loadScan)
        self.sizeXPar.textChanged.connect(
            lambda: controller.scanController.scanParameterChanged('sizeX'))
        self.sizeYPar.textChanged.connect(
            lambda: controller.scanController.scanParameterChanged('sizeY'))
        self.sizeZPar.textChanged.connect(
            lambda: controller.scanController.scanParameterChanged('sizeZ'))
        self.seqTimePar.textChanged.connect(
            lambda: controller.scanController.scanParameterChanged('seqTime'))
        self.stepSizeXYPar.textChanged.connect(
            lambda: controller.scanController.scanParameterChanged('stepSizeXY'))
        self.stepSizeZPar.textChanged.connect(
            lambda: controller.scanController.scanParameterChanged('stepSizeZ'))
        self.scanMode.currentIndexChanged.connect(
            lambda: controller.scanController.setScanMode(self.scanMode.currentText()))
        self.primScanDim.currentIndexChanged.connect(
            lambda: controller.scanController.setPrimScanDim(self.primScanDim.currentText()))
        self.scanRadio.clicked.connect(lambda: controller.scanController.setScanOrNot(True))
        self.contLaserPulsesRadio.clicked.connect(
            lambda: controller.scanController.setScanOrNot(False))
        self.scanButton.clicked.connect(controller.scanController.scanOrAbort)
        self.previewButton.clicked.connect(controller.scanController.previewScan)
        self.multiScanWgt.registerListener(controller)
        
        
        
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
    
class MultipleScanWidget(QtGui.QFrame):

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
        self.saveScanButton.pressed.connect(controller.multiScanController.saveScan)
        self.crossButton.pressed.connect(controller.multiScanController.toggleCrossHair)
        self.analysis_btn.clicked.connect(controller.multiScanController.analyzeWorker)
        self.show_beads_btn.clicked.connect(controller.multiScanController.find_fpWorker)
        self.quality_edit.editingFinished.connect(controller.multiScanController.find_fpWorker)
        self.win_size_edit.editingFinished.connect(controller.multiScanController.find_fpWorker)
        self.beadsBox.activated.connect(controller.multiScanController.change_illum_image)
        self.change_beads_button.clicked.connect(controller.multiScanController.nextBead)
        self.overlayBox.activated.connect(controller.multiScanController.overlayWorker)
        self.overlay_check.stateChanged.connect(controller.multiScanController.overlayWorker)
        self.clear_btn.clicked.connect(controller.multiScanController.clear)
        
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
        
class FocusWidget(QtGui.QFrame):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Focus lock widgets
        self.kpEdit = QtGui.QLineEdit('0.008')
        self.kpLabel = QtGui.QLabel('kp')
        self.kiEdit = QtGui.QLineEdit('0.0006')
        self.kiLabel = QtGui.QLabel('ki')
        self.lockButton = QtGui.QPushButton('Lock')
        self.lockButton.setCheckable(True)
        self.lockButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                      QtGui.QSizePolicy.Expanding)
        self.focusDataBox = QtGui.QCheckBox('Save focus data')
        self.twoFociBox = QtGui.QCheckBox('Two foci')

        # PZT position widgets
        time.sleep(0.1)
        self.positionLabel = QtGui.QLabel('Position[um]')
        self.positionEdit = QtGui.QLineEdit('0')
        self.positionSetButton = QtGui.QPushButton('Set')
        

        # focus calibration widgets
        self.CalibFromLabel = QtGui.QLabel('from [um]')
        self.CalibFromEdit = QtGui.QLineEdit('49')
        self.CalibToLabel = QtGui.QLabel('to [um]')
        self.CalibToEdit = QtGui.QLineEdit('51')
        self.focusCalibButton = QtGui.QPushButton('Calib')
        self.focusCalibButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                            QtGui.QSizePolicy.Expanding)
        
        self.CalibCurveButton = QtGui.QPushButton('See Calib')
        self.calibrationDisplay = QtGui.QLineEdit('0 px --> 0 nm')
        self.focusLockGraph = pg.GraphicsWindow()
        self.webcamGraph =pg.GraphicsWindow()
        
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.focusLockGraph, 0, 0, 1, 8)
        grid.addWidget(self.webcamGraph, 1, 0, 1, 8)
        grid.addWidget(self.focusCalibButton, 2, 2, 2, 1)
        grid.addWidget(self.calibrationDisplay, 4, 0, 1, 2)
        grid.addWidget(self.kpLabel, 2, 3)
        grid.addWidget(self.kpEdit, 2, 4)
        grid.addWidget(self.kiLabel, 3, 3)
        grid.addWidget(self.kiEdit, 3, 4)
        grid.addWidget(self.lockButton, 2, 5, 2, 1)
        grid.addWidget(self.focusDataBox, 4, 4, 1, 2)
        grid.addWidget(self.twoFociBox, 4, 6)
        grid.addWidget(self.CalibFromLabel, 2, 0)
        grid.addWidget(self.CalibFromEdit, 2, 1)
        grid.addWidget(self.CalibToLabel, 3, 0)
        grid.addWidget(self.CalibToEdit, 3, 1)
        grid.addWidget(self.CalibCurveButton, 4, 2)
        grid.addWidget(self.positionLabel, 2, 6)
        grid.addWidget(self.positionEdit, 2, 7)
        grid.addWidget(self.positionSetButton, 3, 6, 1, 2)
        
    def registerListener(self, controller):
        self.kpEdit.textChanged.connect(controller.focusLockController.unlockFocus)
        self.kiEdit.textChanged.connect(controller.focusLockController.unlockFocus)
        self.lockButton.clicked.connect(controller.focusLockController.toggleFocus)
        self.positionSetButton.clicked.connect(controller.focusLockController.movePZT)
        self.focusCalibButton.clicked.connect(controller.focusLockController.focusCalibThreadStart)
        self.CalibCurveButton.clicked.connect(controller.focusLockController.showCalibCurve)
        
class PositionerWidget(QtGui.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        self.xUpButton.pressed.connect(controller.positionerController.xMoveUp)
        self.xDownButton.pressed.connect(controller.positionerController.xMoveDown)
        self.yUpButton.pressed.connect(controller.positionerController.yMoveUp)
        self.yDownButton.pressed.connect(controller.positionerController.yMoveDown)
        self.zUpButton.pressed.connect(controller.positionerController.zMoveUp)
        self.zDownButton.pressed.connect(controller.positionerController.zMoveDown)
        
class ULensesWidget(QtGui.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ulensesLayout = QtGui.QGridLayout()
        self.setLayout(ulensesLayout)
        self.xEdit = QtGui.QLineEdit('0')
        self.yEdit = QtGui.QLineEdit('0')
        self.pxEdit = QtGui.QLineEdit('157.5')
        self.upEdit = QtGui.QLineEdit('1182')
        self.ulensesButton = QtGui.QPushButton('uLenses')
        self.x = np.float(self.xEdit.text())
        self.y = np.float(self.yEdit.text())
        self.px = np.float(self.pxEdit.text())
        self.up = np.float(self.upEdit.text())
        self.ulensesCheck = QtGui.QCheckBox('Show uLenses')
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
        self.ulensesButton.clicked.connect(controller.uLensesController.ulensesToolAux)
        
class AlignWidgetXYProject(QtGui.QFrame):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        # From model
#        self.ROI = ROI((50, 50), self.main.vb, (0, 0), handlePos=(1, 0),
#                       handleCenter=(0, 1), color=pg.mkPen(255, 0, 0),
#                       scaleSnap=True, translateSnap=True)

#        self.ROI.hide()
        self.graph = guitools.ProjectionGraph()
        self.roiButton = QtGui.QPushButton('Show ROI')
        self.roiButton.setCheckable(True)
       
        self.Xradio = QtGui.QRadioButton('X dimension')
        self.Yradio = QtGui.QRadioButton('Y dimension')

        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.graph, 0, 0, 1, 6)
        grid.addWidget(self.roiButton, 1, 0, 1, 1)
        grid.addWidget(self.Xradio, 1, 1, 1, 1)
        grid.addWidget(self.Yradio, 1, 2, 1, 1)

        self.scansPerS = 10
        self.alignTime = 1000 / self.scansPerS
        self.alignTimer = QtCore.QTimer()
        #self.alignTimer.start(self.alignTime)

        # 2 zeros because it has to have the attribute "len"
        self.latest_values = np.zeros(2)
        self.s_fac = 0.3
        
    def registerListener(self, controller):
        self.roiButton.clicked.connect(controller.alignXYController.ROItoggle)
        self.alignTimer.timeout.connect(controller.alignXYController.updateValue)

class AlignWidgetAverage(QtGui.QFrame):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        #self.ROI = ROI((50, 50), self.main.vb, (0, 0), handlePos=(1, 0),
         #              handleCenter=(0, 1), color=pg.mkPen(255, 0, 0),
          #             scaleSnap=True, translateSnap=True)

        #self.ROI.hide()
        self.graph = guitools.SumpixelsGraph()
        self.roiButton = QtGui.QPushButton('Show ROI')
        self.roiButton.setCheckable(True)
        self.resetButton = QtGui.QPushButton('Reset graph')

        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.graph, 0, 0, 1, 6)
        grid.addWidget(self.roiButton, 1, 0, 1, 1)
        grid.addWidget(self.resetButton, 1, 1, 1, 1)
        grid.setRowMinimumHeight(0, 300)

        self.scansPerS = 10
        self.alignTime = 1000 / self.scansPerS
        self.alignTimer = QtCore.QTimer()
        #self.alignTimer.start(self.alignTime)
        
    def registerListener(self, controller):
        self.roiButton.clicked.connect(controller.alignAverageController.ROItoggle)
        self.resetButton.clicked.connect(controller.alignAverageController.resetGraph)
        self.alignTimer.timeout.connect(controller.alignAverageController.updateValue)
        
class AlignmentWidget(QtGui.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        alignmentLayout = QtGui.QGridLayout()
        self.setLayout(alignmentLayout)
        self.angleEdit = QtGui.QLineEdit('30')
        self.alignmentLineMakerButton = QtGui.QPushButton('Alignment Line')
        self.angle = np.float(self.angleEdit.text())
        self.alignmentCheck = QtGui.QCheckBox('Show Alignment Tool')
        alignmentLayout.addWidget(QtGui.QLabel('Line Angle'), 0, 0)
        alignmentLayout.addWidget(self.angleEdit, 0, 1)
        alignmentLayout.addWidget(self.alignmentLineMakerButton, 1, 0)
        alignmentLayout.addWidget(self.alignmentCheck, 1, 1)
        
    def registerListener(self, controller):
        self.alignmentLineMakerButton.clicked.connect(controller.alignmentController.alignmentToolAux)
        
class LaserWidget(QtGui.QFrame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.actControl = LaserControl('<h3>405<h3>',405, color=(130, 0, 200))
        self.offControl = LaserControl('<h3>488<h3>',488, color=(0, 247, 255))
        self.excControl = LaserControl('<h3>473<h3>',473, color=(0, 183, 255))      
        
        self.DigCtrl = DigitalControl()

        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        
        grid.addWidget(self.actControl, 0, 0, 4, 1)
        grid.addWidget(self.offControl, 0, 1, 4, 1)
        grid.addWidget(self.excControl, 0, 2, 4, 1)
        grid.addWidget(self.DigCtrl, 4, 0, 2, 3)
        
    def registerListener(self, controller):
        self.actControl.registerListener(controller)
        self.offControl.registerListener(controller)
        self.excControl.registerListener(controller)
        self.DigCtrl.registerListener(controller)
        
class DigitalControl(QtGui.QFrame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)   
        
        title = QtGui.QLabel('<h3>Digital modulation<h3>')
        title.setTextFormat(QtCore.Qt.RichText)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size:12px")
        title.setFixedHeight(20)
        
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        #From model actPower = str(self.controls[0].laser.power_mod.magnitude)
        self.ActPower = QtGui.QLineEdit('actPower')
        #offPower = str(self.controls[1].laser.power_mod.magnitude)
        self.OffPower = QtGui.QLineEdit('offPower')
        #excPower = str(self.controls[2].laser.power)
        self.ExcPower = QtGui.QLineEdit('excPower')
    
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
        actModGrid.addWidget(self.ActPower, 0, 0)
        actModGrid.addWidget(actUnit, 0, 1)

        offUnit = QtGui.QLabel('mW')
        offUnit.setFixedWidth(20)
        offModFrame = QtGui.QFrame()
        offModGrid = QtGui.QGridLayout()
        offModFrame.setLayout(offModGrid)
        offModGrid.addWidget(self.OffPower, 0, 0)
        offModGrid.addWidget(offUnit, 0, 1)

        excUnit = QtGui.QLabel('V')
        excUnit.setFixedWidth(20)
        excModFrame = QtGui.QFrame()
        excModGrid = QtGui.QGridLayout()
        excModFrame.setLayout(excModGrid)
        excModGrid.addWidget(self.ExcPower, 0, 0)
        excModGrid.addWidget(excUnit, 0, 1)

        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(title, 0, 0)
        grid.addWidget(actModFrame, 1, 0)
        grid.addWidget(offModFrame, 1, 1)
        grid.addWidget(excModFrame, 1, 2)
        grid.addWidget(self.DigitalControlButton, 2, 0, 1, 3)
    
    def registerListener(self, controller):
        self.ActPower.textChanged.connect(controller.laserController.updateDigitalPowers)
        self.OffPower.textChanged.connect(controller.laserController.updateDigitalPowers)
        self.ExcPower.textChanged.connect(controller.laserController.updateDigitalPowers)
        self.DigitalControlButton.clicked.connect(controller.laserController.GlobalDigitalMod)
        self.updateDigPowersButton.clicked.connect(controller.laserController.updateDigitalPowers)
        
class LaserControl(QtGui.QFrame):
    def __init__(self, name, laser, color, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        self.laser = laser
        self.name = QtGui.QLabel(name)
        self.name.setTextFormat(QtCore.Qt.RichText)
        self.name.setAlignment(QtCore.Qt.AlignCenter)
        self.name.setStyleSheet("font-size:16px")
        self.name.setFixedHeight(40)
        
        # Power widget
        self.setPointLabel = QtGui.QLabel('Setpoint')
        self.setPointEdit = QtGui.QLineEdit('0')
        self.setPointEdit.setFixedWidth(50)
        self.setPointEdit.setAlignment(QtCore.Qt.AlignRight)

        self.powerLabel = QtGui.QLabel('Power')
        #powerMag = self.laser.power From model
        self.powerIndicator = QtGui.QLabel('str(powerMag)')
        self.powerIndicator.setFixedWidth(50)
        self.powerIndicator.setAlignment(QtCore.Qt.AlignRight)
        
        # Slider
        self.maxpower = QtGui.QLabel('5')
        self.maxpower.setAlignment(QtCore.Qt.AlignCenter)
        self.slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.slider.setMinimum(0)
        self.slider.setMaximum(5)
        self.slider.setTickInterval(5)
        self.slider.setSingleStep(0.1)
        self.slider.setValue(0)
        self.minpower = QtGui.QLabel('0')
        self.minpower.setAlignment(QtCore.Qt.AlignCenter)

        powerFrame = QtGui.QFrame(self)
        self.powerGrid = QtGui.QGridLayout()
        powerFrame.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Plain)
        powerFrame.setLayout(self.powerGrid)
        self.powerGrid.addWidget(self.setPointLabel, 1, 0, 1, 2)
        self.powerGrid.addWidget(self.setPointEdit, 2, 0)
        self.powerGrid.addWidget(QtGui.QLabel('V'), 2, 1)
        self.powerGrid.addWidget(self.powerLabel, 3, 0, 1, 2)
        self.powerGrid.addWidget(self.powerIndicator, 4, 0)
        self.powerGrid.addWidget(QtGui.QLabel('V'), 4, 1)
        self.powerGrid.addWidget(self.maxpower, 0, 3)
        self.powerGrid.addWidget(self.slider, 1, 3, 8, 1)
        self.powerGrid.addWidget(self.minpower, 9, 3)

        # ON/OFF button
        self.enableButton = QtGui.QPushButton('ON')
        style = "background-color: rgb{}".format(color)
        self.enableButton.setStyleSheet(style)
        self.enableButton.setCheckable(True)
        #if self.laser.enabled:
         #   self.enableButton.setChecked(True)

        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)
        self.grid.addWidget(self.name, 0, 0, 1, 2)
        self.grid.addWidget(powerFrame, 1, 0, 1, 2)
        self.grid.addWidget(self.enableButton, 8, 0, 1, 2)

    def registerListener(self, controller):
        self.enableButton.toggled.connect(lambda: controller.laserController.toggleLaser(self.laser))
        self.slider.valueChanged[int].connect(lambda: controller.laserController.changeSlider(self.laser))
        self.setPointEdit.returnPressed.connect(lambda: controller.laserController.changeEdit(self.laser))
        
        
        
class FFTWidget(QtGui.QFrame):
    """ FFT Transform window for alignment """
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        # Do FFT button
        self.doButton = QtGui.QPushButton('Do FFT')

        # Period button and text for changing the vertical lines
        self.changePosButton = QtGui.QPushButton('Period (pix)')
        
        self.linePos = QtGui.QLineEdit('4')
        
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
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
        
        # Vertical and horizontal lines 
        self.vline = pg.InfiniteLine()
        self.hline = pg.InfiniteLine()
        self.rvline = pg.InfiniteLine()
        self.lvline = pg.InfiniteLine()
        self.uhline = pg.InfiniteLine()
        self.dhline = pg.InfiniteLine()
        
        self.vline.hide()
        self.hline.hide()
        self.rvline.hide()
        self.lvline.hide()
        self.uhline.hide()
        self.dhline.hide()

        self.vb.addItem(self.vline)
        self.vb.addItem(self.hline)
        self.vb.addItem(self.lvline)
        self.vb.addItem(self.rvline)
        self.vb.addItem(self.uhline)
        self.vb.addItem(self.dhline)
        

        grid.addWidget(self.cwidget, 0, 0, 1, 6)
        grid.addWidget(self.doButton, 1, 0, 1, 1)
        grid.addWidget(self.changePosButton, 2, 0, 1, 1)
        grid.addWidget(self.linePos, 2, 1, 1, 1)
        grid.setRowMinimumHeight(0, 300)

        self.init = False
        
    def registerListener(self, controller):
        self.doButton.clicked.connect(controller.fftController.doFFT)
        self.changePosButton.clicked.connect(controller.fftController.changePos)

# Widget to control image or sequence recording. Recording only possible when
# liveview active. StartRecording called when "Rec" presset. Creates recording
# thread with RecWorker, recording is then done in this seperate thread.
class RecordingWidget(QtGui.QFrame):
    '''Widget to control image or sequence recording.
    Recording only possible when liveview active.
    StartRecording called when "Rec" presset.
    Creates recording thread with RecWorker, recording is then done in this
    seperate thread.'''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Title
        recTitle = QtGui.QLabel('<h2><strong>Recording settings</strong></h2>')
        recTitle.setTextFormat(QtCore.Qt.RichText)
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)

        # Folder and filename fields
        self.folderEdit = QtGui.QLineEdit('self.initialDir')
        openFolderButton = QtGui.QPushButton('Open')
        #openFolderButton.clicked.connect(self.openFolder)
        self.specifyfile = QtGui.QCheckBox('Specify file name')
        #self.specifyfile.clicked.connect(self.specFile)
        self.filenameEdit = QtGui.QLineEdit('Current_time')
        self.formatBox = QtGui.QComboBox()
        self.formatBox.addItem('tiff')
        self.formatBox.addItem('hdf5')

        # Snap and recording buttons
        self.snapTIFFButton = QtGui.QPushButton('Snap')
        self.snapTIFFButton.setStyleSheet("font-size:16px")
        self.snapTIFFButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                          QtGui.QSizePolicy.Expanding)
        #self.snapTIFFButton.clicked.connect(self.snapTIFF)
        self.recButton = QtGui.QPushButton('REC')
        self.recButton.setStyleSheet("font-size:16px")
        self.recButton.setCheckable(True)
        self.recButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                     QtGui.QSizePolicy.Expanding)
        #self.recButton.clicked.connect(self.startRecording)

        # Number of frames and measurement timing
        modeTitle = QtGui.QLabel('<strong>Mode</strong>')
        modeTitle.setTextFormat(QtCore.Qt.RichText)
        self.specifyFrames = QtGui.QRadioButton('Number of frames')
        #self.specifyFrames.clicked.connect(self.specFrames)
        self.specifyTime = QtGui.QRadioButton('Time (s)')
        #self.specifyTime.clicked.connect(self.specTime)
        self.recScanOnceBtn = QtGui.QRadioButton('Scan once')
        #self.recScanOnceBtn.clicked.connect(self.recScanOnce)
        self.recScanLapseBtn = QtGui.QRadioButton('Time-lapse scan')
        #self.recScanLapseBtn.clicked.connect(self.recScanLapse)
        self.timeLapseEdit = QtGui.QLineEdit('5')
        self.timeLapseLabel = QtGui.QLabel('Each/Total [s]')
        self.timeLapseLabel.setAlignment(QtCore.Qt.AlignRight)
        self.timeLapseTotalEdit = QtGui.QLineEdit('60')
        self.timeLapseScan = 0
        self.untilSTOPbtn = QtGui.QRadioButton('Run until STOP')
        #self.untilSTOPbtn.clicked.connect(self.untilStop)
        self.timeToRec = QtGui.QLineEdit('1')
        #self.timeToRec.textChanged.connect(self.filesizeupdate)
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
        #self.numExpositionsEdit.textChanged.connect(self.filesizeupdate)

        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setTextVisible(False)

        self.filesizeBar = QtGui.QProgressBar()
        self.filesizeBar.setTextVisible(False)
        self.filesizeBar.setRange(0, 2000000000)

        # Layout
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

#        if len(self.main.cameras) > 1:
#            self.DualCam = QtGui.QCheckBox('Two-cam rec')
#            recGrid.addWidget(self.DualCam, 1, 3)
#            recGrid.addWidget(self.folderEdit, 2, 1, 1, 2)
#            recGrid.addWidget(openFolderButton, 2, 3)
#            recGrid.addWidget(self.filenameEdit, 3, 1, 1, 2)
#            recGrid.addWidget(self.formatBox, 3, 3)
#        else:
        recGrid.addWidget(self.folderEdit, 2, 1, 1, 2)
        recGrid.addWidget(openFolderButton, 2, 3)
        recGrid.addWidget(self.filenameEdit, 3, 1, 1, 2)
        recGrid.addWidget(self.formatBox, 3, 3)

        recGrid.addWidget(self.specifyfile, 3, 0)

        recGrid.addWidget(modeTitle, 4, 0)
        recGrid.addWidget(self.specifyFrames, 5, 0, 1, 5)
        recGrid.addWidget(self.currentFrame, 5, 1)
        recGrid.addWidget(self.numExpositionsEdit, 5, 2)
        recGrid.addWidget(self.specifyTime, 6, 0, 1, 5)
        recGrid.addWidget(self.currentTime, 6, 1)
        recGrid.addWidget(self.timeToRec, 6, 2)
        recGrid.addWidget(self.tRemaining, 6, 3, 1, 2)
#        recGrid.addWidget(self.progressBar, 5, 4, 1, 2)
        recGrid.addWidget(self.recScanOnceBtn, 7, 0, 1, 5)
        recGrid.addWidget(self.recScanLapseBtn, 8, 0, 1, 5)
        recGrid.addWidget(self.timeLapseLabel, 8, 1)
        recGrid.addWidget(self.timeLapseEdit, 8, 2)
        recGrid.addWidget(self.timeLapseTotalEdit, 8, 3)
        recGrid.addWidget(self.untilSTOPbtn, 9, 0, 1, 5)
        recGrid.addWidget(buttonWidget, 10, 0, 1, 0)

        recGrid.setColumnMinimumWidth(0, 70)

        # Initial condition of fields and checkboxes.
        self.writable = True
        self.readyToRecord = False
        self.filenameEdit.setEnabled(False)
        self.specifyTime.setChecked(True)

        
class ViewCtrlWidget(QtGui.QWidget):
    def __init__(self, vb, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vb = vb
         # Liveview functionality
        self.liveviewButton = QtGui.QPushButton('LIVEVIEW')
        self.liveviewButton.setStyleSheet("font-size:20px")
        self.liveviewButton.setCheckable(True)
        self.liveviewButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                          QtGui.QSizePolicy.Expanding)
        # Link button click to funciton liveview
        #self.liveviewButton.clicked.connect(self.liveview)
#        self.liveviewButton.setEnabled(True)
#        self.viewtimer = QtCore.QTimer()
#        self.viewtimer.timeout.connect(self.updateView)

        self.alignmentON = False
        self.ulensesON = False
        # Liveview control buttons
        self.viewCtrlLayout = QtGui.QGridLayout()
        self.setLayout(self.viewCtrlLayout)
        self.viewCtrlLayout.addWidget(self.liveviewButton, 0, 0, 1, 2)
#        if len(self.cameras) > 1:
#            self.toggleCamButton = QtGui.QPushButton('Toggle camera')
#            self.toggleCamButton.setStyleSheet("font-size:18px")
#            self.toggleCamButton.clicked.connect(self.toggleCamera)
#            self.camLabel = QtGui.QLabel('Hamamatsu0')
#            self.camLabel.setStyleSheet("font-size:18px")
#            self.viewCtrlLayout.addWidget(self.toggleCamButton, 2, 0)
#            self.viewCtrlLayout.addWidget(self.camLabel, 2, 1)
        self.grid = guitools.Grid(self.vb)
        self.gridButton = QtGui.QPushButton('Grid')
        self.gridButton.setCheckable(True)
        self.gridButton.setEnabled(False)
        self.gridButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                      QtGui.QSizePolicy.Expanding)
        self.gridButton.clicked.connect(self.grid.toggle)
        self.viewCtrlLayout.addWidget(self.gridButton, 1, 0)

        self.crosshair = guitools.Crosshair(self.vb)
        self.crosshairButton = QtGui.QPushButton('Crosshair')
        self.crosshairButton.setCheckable(True)
        self.crosshairButton.setEnabled(False)
        self.crosshairButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                           QtGui.QSizePolicy.Expanding)
        self.crosshairButton.pressed.connect(self.crosshair.toggle)
        self.viewCtrlLayout.addWidget(self.crosshairButton, 1, 1)
        
class ImageWidget(pg.GraphicsLayoutWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        for tick in self.hist.gradient.ticks:
            tick.hide()
        self.addItem(self.hist, row=1, col=2)
        for tick in self.hist.gradient.ticks:
            tick.hide()
        self.addItem(self.hist, row=1, col=2)
        self.ROI = guitools.ROI((0, 0), self.vb, (0, 0), handlePos=(1, 0),
                                handleCenter=(0, 1), color='y', scaleSnap=True,
                                translateSnap=True)
        #self.ROI.sigRegionChangeFinished.connect(self.ROIchanged)
        self.ROI.hide()

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

        self.levelsButton = QtGui.QPushButton('Update Levels')
        self.levelsButton.setEnabled(False)
        self.levelsButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                        QtGui.QSizePolicy.Expanding)
        #self.levelsButton.pressed.connect(self.autoLevels)

        proxy = QtGui.QGraphicsProxyWidget()
        proxy.setWidget(self.levelsButton)
        self.addItem(proxy, row=0, col=2)
    
class SettingsWidget(QtGui.QFrame):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO retrieve model from TempestaModel
        self.tree = CamParamTree('v3')
        # TODO retrieve parameters from Tree and coordinate with Model or Controller
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        cameraTitle = QtGui.QLabel('<h2><strong>Camera settings</strong></h2>')
        cameraTitle.setTextFormat(QtCore.Qt.RichText)
        cameraGrid = QtGui.QGridLayout()
        self.setLayout(cameraGrid)
        cameraGrid.addWidget(cameraTitle, 0, 0)
        cameraGrid.addWidget(self.tree, 1, 0)
        
class CamParamTree(ParameterTree):
    """ Making the ParameterTree for configuration of the camera during imaging
    """
    def __init__(self, camera, *args, **kwargs):
        super().__init__(*args, **kwargs)

        BinTip = ("Sets binning mode. Binning mode specifies if and how \n"
                  "many pixels are to be read out and interpreted as a \n"
                  "single pixel value.")

        # Parameter tree for the camera configuration
        params = [{'name': 'Model', 'type': 'str', 'readonly': True,
                   'value': camera},
                  {'name': 'Pixel size', 'type': 'float',
                   'value': 0.159, 'readonly': False, 'suffix': ' µm'},
                  {'name': 'Image frame', 'type': 'group', 'children': [
                      {'name': 'Binning', 'type': 'list',
                       'values': [1, 2, 4], 'tip': BinTip},
                      {'name': 'Mode', 'type': 'list', 'values':
                          ['Full Widefield', 'Full chip', 'Microlenses',
                           'alignROI', 'Custom']},
                      {'name': 'X0', 'type': 'int', 'value': 0,
                       'limits': (0, 2044)},
                      {'name': 'Y0', 'type': 'int', 'value': 0,
                       'limits': (0, 2044)},
                      {'name': 'Width', 'type': 'int', 'value': 2048,
                       'limits': (1, 2048)},
                      {'name': 'Height', 'type': 'int', 'value': 2048,
                       'limits': (1, 2048)},
                      {'name': 'Apply', 'type': 'action'},
                      {'name': 'New ROI', 'type': 'action'},
                      {'name': 'Abort ROI', 'type': 'action',
                       'align': 'right'}]},
                  {'name': 'Timings', 'type': 'group', 'children': [
                      {'name': 'Set exposure time', 'type': 'float',
                       'value': 0.01, 'limits': (0, 9999),
                       'siPrefix': True, 'suffix': 's'},
                      {'name': 'Real exposure time', 'type': 'float',
                       'value': 0, 'readonly': True, 'siPrefix': True,
                       'suffix': ' s'},
                      {'name': 'Internal frame interval', 'type': 'float',
                       'value': 0, 'readonly': True, 'siPrefix': True,
                       'suffix': ' s'},
                      {'name': 'Readout time', 'type': 'float',
                       'value': 0, 'readonly': True, 'siPrefix': True,
                       'suffix': 's'},
                      {'name': 'Internal frame rate', 'type': 'float',
                       'value': 0, 'readonly': True, 'siPrefix': False,
                       'suffix': ' fps'}]},
                  {'name': 'Acquisition mode', 'type': 'group', 'children': [
                      {'name': 'Trigger source', 'type': 'list',
                       'values': ['Internal trigger',
                                  'External "Start-trigger"',
                                  'External "frame-trigger"'],
                       'siPrefix': True, 'suffix': 's'}]}]
#                        {'name': 'High Dynamic Range', 'type': 'list',
#                         'values': ['OFF',
#                                  'ON',],
#                       'siPrefix': True, 'suffix': 's'}]}]

        self.p = Parameter.create(name='params', type='group', children=params)
        self.setParameters(self.p, showTop=False)
        self._writable = True


        