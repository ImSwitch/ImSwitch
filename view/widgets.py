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


        