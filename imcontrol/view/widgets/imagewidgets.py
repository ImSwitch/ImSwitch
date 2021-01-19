# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 17:08:54 2020

@author: _Xavi
"""
import os
import time

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.parametertree import Parameter, ParameterTree

import imcontrol.view.guitools as guitools
from .basewidgets import Widget


class CamParamTree(ParameterTree):
    """ Making the ParameterTree for configuration of the detector during imaging
    """

    def __init__(self, roiInfos, detectorParameters, supportedBinnings, *args, **kwargs):
        super().__init__(*args, **kwargs)

        BinTip = ("Sets binning mode. Binning mode specifies if and how \n"
                  "many pixels are to be read out and interpreted as a \n"
                  "single pixel value.")

        # Parameter tree for the detector configuration
        params = [{'name': 'Model', 'type': 'str', 'readonly': True},
                  {'name': 'Image frame', 'type': 'group', 'children': [
                      {'name': 'Binning', 'type': 'list', 'value': 1,
                       'values': supportedBinnings, 'tip': BinTip},
                      {'name': 'Mode', 'type': 'list', 'value': 'Full chip',
                       'values': ['Full chip'] + list(roiInfos.keys()) + ['Custom']},
                      {'name': 'X0', 'type': 'int', 'value': 0, 'limits': (0, 65535)},
                      {'name': 'Y0', 'type': 'int', 'value': 0, 'limits': (0, 65535)},
                      {'name': 'Width', 'type': 'int', 'value': 1, 'limits': (1, 65535)},
                      {'name': 'Height', 'type': 'int', 'value': 1, 'limits': (1, 65535)},
                      {'name': 'Apply', 'type': 'action', 'title': 'Apply'},
                      {'name': 'New ROI', 'type': 'action', 'title': 'New ROI'},
                      {'name': 'Abort ROI', 'type': 'action', 'title': 'Abort ROI'},
                      {'name': 'Save mode', 'type': 'action',
                       'title': 'Save current parameters as mode'},
                      {'name': 'Delete mode', 'type': 'action',
                       'title': 'Remove current mode from list'},
                      {'name': 'Update all detectors', 'type': 'bool', 'value': False}
                  ]}]

        detectorParamGroups = {}
        for detectorParameterName, detectorParameter in detectorParameters.items():
            if detectorParameter.group not in detectorParamGroups:
                # Create group
                detectorParamGroups[detectorParameter.group] = {
                    'name': detectorParameter.group, 'type': 'group', 'children': []
                }

            detectorParameterType = type(detectorParameter).__name__
            if detectorParameterType == 'DetectorNumberParameter':
                pyqtParam = {
                    'name': detectorParameterName,
                    'type': 'float',
                    'value': detectorParameter.value,
                    'readonly': not detectorParameter.editable,
                    'siPrefix': detectorParameter.valueUnits in ['s'],
                    'suffix': detectorParameter.valueUnits,
                    'decimals': 5
                }
            elif detectorParameterType == 'DetectorListParameter':
                pyqtParam = {
                    'name': detectorParameterName,
                    'type': 'list',
                    'value': detectorParameter.value,
                    'readonly': not detectorParameter.editable,
                    'values': detectorParameter.options
                }
            else:
                raise TypeError(f'Unsupported detector parameter type "{detectorParameterType}"')

            detectorParamGroups[detectorParameter.group]['children'].append(pyqtParam)

        params += list(detectorParamGroups.values())

        self.p = Parameter.create(name='params', type='group', children=params)
        self.setParameters(self.p, showTop=False)
        self._writable = True

    def enableCropMode(self):
        value = self.frameTransferParam.value()
        if value:
            self.cropModeEnableParam.setWritable(True)
        else:
            self.cropModeEnableParam.setValue(False)
            self.cropModeEnableParam.setWritable(False)

    @property
    def writable(self):
        return self._writable

    @writable.setter
    def writable(self, value):
        """
        property to set basically the whole parameters tree as writable
        (value=True) or not writable (value=False)
        useful to set it as not writable during recording
        """
        self._writable = value
        framePar = self.p.param('Image frame')
        framePar.param('Binning').setWritable(value)
        framePar.param('Mode').setWritable(value)
        framePar.param('X0').setWritable(value)
        framePar.param('Y0').setWritable(value)
        framePar.param('Width').setWritable(value)
        framePar.param('Height').setWritable(value)

        # WARNING: If Apply and New ROI button are included here they will
        # emit status changed signal and their respective functions will be
        # called... -> problems.
        timingPar = self.p.param('Timings')
        timingPar.param('Set exposure time').setWritable(value)

    def attrs(self):
        attrs = []
        for ParName in self.p.getValues():
            Par = self.p.param(str(ParName))
            if not (Par.hasChildren()):
                attrs.append((str(ParName), Par.value()))
            else:
                for sParName in Par.getValues():
                    sPar = Par.param(str(sParName))
                    if sPar.type() != 'action':
                        if not (sPar.hasChildren()):
                            attrs.append((str(sParName), sPar.value()))
                        else:
                            for ssParName in sPar.getValues():
                                ssPar = sPar.param(str(ssParName))
                                attrs.append((str(ssParName), ssPar.value()))
        return attrs


class SettingsWidget(Widget):
    """ Detector settings and ROI parameters. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        detectorTitle = QtGui.QLabel('<h2><strong>Detector settings</strong></h2>')
        detectorTitle.setTextFormat(QtCore.Qt.RichText)
        self.ROI = guitools.ROI((0, 0), (0, 0), handlePos=(1, 0),
                                handleCenter=(0, 1), color='y', scaleSnap=True,
                                translateSnap=True)

        # Add elements to GridLayout
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(detectorTitle)

    def initControls(self, roiInfos, settingsPerDetector):
        self.stack = QtGui.QStackedWidget()

        self.trees = {}
        for detectorName, (detectorParameters, supportedBinnings) in settingsPerDetector.items():
            self.trees[detectorName] = CamParamTree(roiInfos, detectorParameters, supportedBinnings)
            self.stack.addWidget(self.trees[detectorName])

        self.layout.addWidget(self.stack)

    def setDisplayedDetector(self, detectorName):
        # Remember previously displayed detector settings widget scroll position
        prevDetectorWidget = self.stack.currentWidget()
        scrollX = prevDetectorWidget.horizontalScrollBar().value()
        scrollY = prevDetectorWidget.verticalScrollBar().value()

        # Switch to new detector settings widget and set scroll position to same as previous widget
        newDetectorWidget = self.trees[detectorName]
        self.stack.setCurrentWidget(newDetectorWidget)
        newDetectorWidget.horizontalScrollBar().setValue(scrollX)
        newDetectorWidget.verticalScrollBar().setValue(scrollY)


class ViewWidget(Widget):
    """ View settings (liveview, grid, crosshair). """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        # Grid
        self.gridButton = guitools.BetterPushButton('Grid')
        self.gridButton.setCheckable(True)
        self.gridButton.setEnabled(False)
        self.gridButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                      QtGui.QSizePolicy.Expanding)

        # Crosshair
        self.crosshairButton = guitools.BetterPushButton('Crosshair')
        self.crosshairButton.setCheckable(True)
        self.crosshairButton.setEnabled(False)
        self.crosshairButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                           QtGui.QSizePolicy.Expanding)
        # liveview
        self.liveviewButton = guitools.BetterPushButton('LIVEVIEW')
        self.liveviewButton.setStyleSheet("font-size:20px")
        self.liveviewButton.setCheckable(True)
        self.liveviewButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                          QtGui.QSizePolicy.Expanding)
        self.liveviewButton.setEnabled(True)

        # Detector list
        self.detectorListBox = QtGui.QHBoxLayout()
        self.detectorListLabel = QtGui.QLabel('Current detector:')
        self.detectorList = QtGui.QComboBox()
        self.nextDetectorButton = guitools.BetterPushButton('Next')
        self.detectorListBox.addWidget(self.detectorListLabel)
        self.detectorListBox.addWidget(self.detectorList, 1)
        self.detectorListBox.addWidget(self.nextDetectorButton)

        # Add elements to GridLayout
        self.viewCtrlLayout = QtGui.QGridLayout()
        self.setLayout(self.viewCtrlLayout)
        self.viewCtrlLayout.addLayout(self.detectorListBox, 0, 0, 1, 2)
        self.viewCtrlLayout.addWidget(self.liveviewButton, 1, 0, 1, 2)
        self.viewCtrlLayout.addWidget(self.gridButton, 2, 0)
        self.viewCtrlLayout.addWidget(self.crosshairButton, 2, 1)

    def initControls(self, detectorModels):
        if len(detectorModels) <= 1:
            self.nextDetectorButton.hide()

        for detectorName, detectorModel in detectorModels.items():
            self.detectorList.addItem(f'{detectorModel} ({detectorName})', detectorName)


class ImageWidget(pg.GraphicsLayoutWidget):
    """ Widget containing viewbox that displays the new detector frames.  """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.levelsButton = guitools.BetterPushButton('Update Levels')
        self.levelsButton.setEnabled(False)
        self.levelsButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                        QtGui.QSizePolicy.Expanding)
        proxy = QtGui.QGraphicsProxyWidget()
        proxy.setWidget(self.levelsButton)
        self.addItem(proxy, row=0, col=2)

        # Viewbox and related elements
        self.vb = self.addViewBox(row=1, col=1)
        self.vb.setMouseMode(pg.ViewBox.RectMode)
        self.img = guitools.OptimizedImageItem(axisOrder='row-major')
        self.img.translate(-0.5, -0.5)
        self.vb.addItem(self.img)
        self.vb.setAspectLocked(True)
        self.setAspectLocked(True)
        self.hist = pg.HistogramLUTItem(image=self.img)
        self.hist.vb.setLimits(yMin=0, yMax=66000)
        self.hist.gradient.loadPreset('greyclip')
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


class RecordingWidget(Widget):
    """ Widget to control image or sequence recording.
    Recording only possible when liveview active. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        recTitle = QtGui.QLabel('<h2><strong>Recording settings</strong></h2>')
        recTitle.setTextFormat(QtCore.Qt.RichText)

        # Detector list
        self.detectorList = QtGui.QComboBox()

        # Folder and filename fields
        baseOutputFolder = self._defaultPreset.recording.outputFolder
        if self._defaultPreset.recording.includeDateInOutputFolder:
            self.initialDir = os.path.join(baseOutputFolder, time.strftime('%Y-%m-%d'))
        else:
            self.initialDir = baseOutputFolder

        self.folderEdit = QtGui.QLineEdit(self.initialDir)
        self.openFolderButton = guitools.BetterPushButton('Open')
        self.specifyfile = QtGui.QCheckBox('Specify file name')
        self.filenameEdit = QtGui.QLineEdit('Current time')

        # Snap and recording buttons
        self.snapTIFFButton = guitools.BetterPushButton('Snap')
        self.snapTIFFButton.setStyleSheet("font-size:16px")
        self.snapTIFFButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                          QtGui.QSizePolicy.Expanding)
        self.recButton = guitools.BetterPushButton('REC')
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

        self.keepInMemoryCheckbox = QtGui.QCheckBox('Keep recordings in memory for reconstruction')

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
        recGrid.addWidget(QtGui.QLabel('Detector to capture'), 1, 0)
        recGrid.addWidget(self.detectorList, 1, 1, 1, 4)
        recGrid.addWidget(QtGui.QLabel('Folder'), 2, 0)
        recGrid.addWidget(self.folderEdit, 2, 1, 1, 3)
        recGrid.addWidget(self.openFolderButton, 2, 4)
        recGrid.addWidget(self.filenameEdit, 3, 1, 1, 3)

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
        recGrid.addWidget(self.untilSTOPbtn, 10, 0, 1, -1)
        recGrid.addWidget(self.keepInMemoryCheckbox, 11, 0, 1, -1)
        recGrid.addWidget(buttonWidget, 12, 0, 1, -1)

        # Initial condition of fields and checkboxes.
        self.writable = True
        self.readyToRecord = False
        self.filenameEdit.setEnabled(False)
        self.untilSTOPbtn.setChecked(True)

    def initControls(self, detectorModels):
        if len(detectorModels) > 1:
            self.detectorList.addItem('Current detector at start', -1)
            self.detectorList.addItem('All detectors', -2)

        for detectorName, detectorModel in detectorModels.items():
            self.detectorList.addItem(f'{detectorModel} ({detectorName})', detectorName)

