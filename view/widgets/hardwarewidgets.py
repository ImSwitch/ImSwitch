# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 17:08:54 2020

@author: _Xavi
"""
import textwrap
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from model.managers.SLMManager import MaskMode
import view.guitools as guitools
from .basewidgets import Widget


class PositionerWidget(Widget):
    """ Widget in control of the piezzo movement. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pars = {}
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)

    def initControls(self, positionerInfos):
        gridpos = 0
        for index, (positionerName, positionerInfo) in enumerate(positionerInfos.items()):
            axes = positionerInfo.managerProperties['axisCount']
            axislabels = textwrap.wrap(positionerInfo.managerProperties['axisLabels'],1)
            for axis in range(axes):
                self.pars['Label' + positionerName + axislabels[axis]] = QtGui.QLabel("<strong>{}-{} </strong>".format(positionerName, axislabels[axis]))
                self.pars['Label' + positionerName + axislabels[axis]].setTextFormat(QtCore.Qt.RichText)
                self.pars['Position' + positionerName + axislabels[axis]] = QtGui.QLabel("<strong>{:.2f} µm</strong>".format(0))
                self.pars['Position' + positionerName + axislabels[axis]].setTextFormat(QtCore.Qt.RichText)
                self.pars['UpButton' + positionerName + axislabels[axis]] = guitools.BetterPushButton("+")
                self.pars['DownButton' + positionerName + axislabels[axis]] = guitools.BetterPushButton("-")
                self.pars['StepEdit' + positionerName + axislabels[axis]] = QtGui.QLineEdit("0")
                self.pars['StepUnit' + positionerName + axislabels[axis]] = QtGui.QLabel(" µm")

                self.grid.addWidget(self.pars['Label' + positionerName + axislabels[axis]], gridpos, 0)
                self.grid.addWidget(self.pars['Position' + positionerName + axislabels[axis]], gridpos, 1)
                self.grid.addWidget(self.pars['UpButton' + positionerName + axislabels[axis]], gridpos, 2)
                self.grid.addWidget(self.pars['DownButton' + positionerName + axislabels[axis]], gridpos, 3)
                self.grid.addWidget(QtGui.QLabel("Step"), gridpos, 4)
                self.grid.addWidget(self.pars['StepEdit' + positionerName + axislabels[axis]], gridpos, 5)
                self.grid.addWidget(self.pars['StepUnit' + positionerName + axislabels[axis]], gridpos, 6)
                gridpos = gridpos + 1


class LaserWidget(Widget):
    """ Laser widget containing digital modulation and normal control. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.laserModules = {}
        self.digModule = DigitalModule()

        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)

    def initControls(self, lasersManager):
        self.laserModules = {}
        for index, (laserName, laserManager) in enumerate(lasersManager):
            control = LaserModule(
                name=laserName, units=laserManager.valueUnits,
                laser=laserName, wavelength=laserManager.wavelength,
                prange=(laserManager.valueRangeMin, laserManager.valueRangeMax),
                tickInterval=5, singleStep=1, init_power=laserManager.valueRangeMin,
                isBinary=laserManager.isBinary
            )

            self.laserModules[laserName] = control
            self.grid.addWidget(control, 0, index, 4, 1)

        self.digModule = DigitalModule()
        self.digModule.initControls(lasersManager)
        self.grid.addWidget(self.digModule, 4, 0, 2, -1)


class DigitalModule(QtGui.QFrame):
    """ Module from LaserWidget to handle digital modulation. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.powers = {}

        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)

        title = QtGui.QLabel('<h3>Digital modulation<h3>')
        title.setTextFormat(QtCore.Qt.RichText)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size:12px")
        title.setFixedHeight(20)
        self.grid.addWidget(title, 0, 0, 1, -1)

        self.DigitalControlButton = guitools.BetterPushButton('Enable')
        self.DigitalControlButton.setCheckable(True)
        self.updateDigPowersButton = guitools.BetterPushButton('Update powers')
        self.grid.addWidget(self.DigitalControlButton, 2, 0, 1, -1)

    def initControls(self, lasersManager):
        self.powers = {}

        for index, (laserName, laserManager) in enumerate(lasersManager):
            power = QtGui.QLineEdit(str(laserManager.valueRangeMin))
            unit = QtGui.QLabel(laserManager.valueUnits)
            unit.setFixedWidth(20)
            modFrame = QtGui.QFrame()
            modGrid = QtGui.QGridLayout()
            modFrame.setLayout(modGrid)
            modGrid.addWidget(power, 0, 0)
            modGrid.addWidget(unit, 0, 1)

            self.powers[laserName] = power
            self.grid.addWidget(modFrame, 1, index, 1, 1)
            if laserManager.isBinary:
                sizePolicy = modFrame.sizePolicy()
                sizePolicy.setRetainSizeWhenHidden(True)
                modFrame.setSizePolicy(sizePolicy)
                modFrame.hide()


class LaserModule(QtGui.QFrame):
    """ Module from LaserWidget to handle a single laser. """

    def __init__(self, name, units, laser, wavelength, prange, tickInterval, singleStep, init_power,
                 isBinary, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        self.laser = laser

        self.name = QtGui.QLabel(f'<h3>{name}<h3>')
        self.name.setTextFormat(QtCore.Qt.RichText)
        self.name.setAlignment(QtCore.Qt.AlignCenter)
        color = guitools.color_utils.wavelength_to_hex(wavelength)
        self.name.setStyleSheet(f'font-size:16px; border-bottom: 4px solid {color}')
        self.name.setFixedHeight(40)

        self.setPointLabel = QtGui.QLabel('Setpoint')
        self.setPointEdit = QtGui.QLineEdit(str(init_power))
        self.setPointEdit.setFixedWidth(50)
        self.setPointEdit.setAlignment(QtCore.Qt.AlignRight)

        self.powerLabel = QtGui.QLabel('Power')
        self.powerIndicator = QtGui.QLabel(str(init_power))
        self.powerIndicator.setFixedWidth(50)
        self.powerIndicator.setAlignment(QtCore.Qt.AlignRight)

        self.maxpower = QtGui.QLabel(str(prange[1]))
        self.maxpower.setAlignment(QtCore.Qt.AlignCenter)

        self.slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        if not isBinary:
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

        self.enableButton = guitools.BetterPushButton('ON')
        self.enableButton.setCheckable(True)

        # Add elements to GridLayout
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)
        self.grid.addWidget(self.name, 0, 0, 1, 2)
        self.grid.addWidget(powerFrame, 1, 0, 1, 2)
        if isBinary:
            sizePolicy = powerFrame.sizePolicy()
            sizePolicy.setRetainSizeWhenHidden(True)
            powerFrame.setSizePolicy(sizePolicy)
            powerFrame.hide()
        self.grid.addWidget(self.enableButton, 8, 0, 1, 2)


class BeadRecWidget(Widget):
    """ Displays the FFT transform of the image. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Viewbox
        self.cwidget = pg.GraphicsLayoutWidget()
        self.vb = self.cwidget.addViewBox(row=1, col=1)
        self.vb.setMouseMode(pg.ViewBox.RectMode)
        self.img = pg.ImageItem(axisOrder='row-major')
        self.img.translate(-0.5, -0.5)
        self.vb.addItem(self.img)
        self.vb.setAspectLocked(True)
        self.hist = pg.HistogramLUTItem(image=self.img)
        self.hist.vb.setLimits(yMin=0, yMax=66000)
        self.hist.gradient.loadPreset('greyclip')
        for tick in self.hist.gradient.ticks:
            tick.hide()
        self.cwidget.addItem(self.hist, row=1, col=2)

        self.roiButton = guitools.BetterPushButton('Show ROI')
        self.roiButton.setCheckable(True)
        self.runButton = QtGui.QCheckBox('Run')
        self.ROI = guitools.ROI((0, 0), (0, 0), handlePos=(1, 0),
                                handleCenter=(0, 1), color='y', scaleSnap=True,
                                translateSnap=True)

        # Add elements to GridLayout
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.cwidget, 0, 0, 1, 6)
        grid.addWidget(self.roiButton, 1, 0, 1, 1)
        grid.addWidget(self.runButton, 1, 1, 1, 1)
        # grid.setRowMinimumHeight(0, 300)


class SLMWidget(Widget):
    ''' Widget containing slm interface. '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.slmFrame = pg.GraphicsLayoutWidget()
        self.vb = self.slmFrame.addViewBox(row=1, col=1)
        self.img = pg.ImageItem()
        self.img.setImage(np.zeros((792,600)), autoLevels=True, autoDownsample=True, autoRange=True)
        self.vb.addItem(self.img)
        self.vb.setAspectLocked(True)

        self.slmParameterTree = pg.parametertree.ParameterTree()
        self.generalparams = [{'name': 'General parameters', 'type': 'group', 'children': [
                  {'name': 'Radius', 'type': 'float', 'value': 100, 'limits': (0, 600), 'step': 1, 'suffix': 'px'},
                  {'name': 'Sigma', 'type': 'float', 'value': 35, 'limits': (1, 599), 'step': 0.1, 'suffix': 'px'},
                  #{'name': 'Angle', 'type': 'float', 'value': 0.15, 'limits': (0, 0.3), 'step': 0.01, 'suffix': 'rad'},
                  #{'name': 'Wavelength', 'type': 'float', 'value': 775, 'limits': (0, 1200), 'step': 1, 'suffix': 'nm'},
                  #{'name': 'Helix rotation', 'type': 'bool', 'value': True},
                  ]},
                  {'name': 'Apply', 'type': 'action'}
                  ]
        self.slmParameterTree.setStyleSheet('''
        QTreeView::item, QAbstractSpinBox, QComboBox {
            padding-top: 0;
            padding-bottom: 0;
            border: none;
        }
        
        QComboBox QAbstractItemView {
            min-width: 128px;
        }
        ''')
        self.slmParameterTree.p = pg.parametertree.Parameter.create(name='params', type='group', children=self.generalparams)
        self.slmParameterTree.setParameters(self.slmParameterTree.p, showTop=False)
        self.slmParameterTree._writable = True

        self.aberParameterTree = pg.parametertree.ParameterTree()
        aberlim = 2
        self.aberparams = [{'name': 'Donut', 'type': 'group', 'children': [
                    {'name': 'Tilt factor', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim), 'step': 0.01},
                    {'name': 'Tip factor', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim), 'step': 0.01},
                    {'name': 'Defocus factor', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim), 'step': 0.01},
                    {'name': 'Spherical factor', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim), 'step': 0.01},
                    {'name': 'Vertical coma factor', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim), 'step': 0.01},
                    {'name': 'Horizontal coma factor', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim), 'step': 0.01},
                    {'name': 'Vertical astigmatism factor', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim), 'step': 0.01},
                    {'name': 'Oblique astigmatism factor', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim), 'step': 0.01}
                 ]},
                  {'name': 'Tophat', 'type': 'group', 'children': [
                    {'name': 'Tilt factor', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim), 'step': 0.01},
                    {'name': 'Tip factor', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim), 'step': 0.01},
                    {'name': 'Defocus factor', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim), 'step': 0.01},
                    {'name': 'Spherical factor', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim), 'step': 0.01},
                    {'name': 'Vertical coma factor', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim), 'step': 0.01},
                    {'name': 'Horizontal coma factor', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim), 'step': 0.01},
                    {'name': 'Vertical astigmatism factor', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim), 'step': 0.01},
                    {'name': 'Oblique astigmatism factor', 'type': 'float', 'value': 0, 'limits': (-aberlim, aberlim), 'step': 0.01}
                  ]},
                  {'name': 'Apply', 'type': 'action'}
                  ] 
        self.aberParameterTree.setStyleSheet('''
        QTreeView::item, QAbstractSpinBox, QComboBox {
            padding-top: 0;
            padding-bottom: 0;
            border: none;
        }
        
        QComboBox QAbstractItemView {
            min-width: 128px;
        }
        ''')
        self.aberParameterTree.p = pg.parametertree.Parameter.create(name='params', type='group', children=self.aberparams)
        self.aberParameterTree.setParameters(self.aberParameterTree.p, showTop=False)
        self.aberParameterTree._writable = True

        self.paramtreeDockArea = pg.dockarea.DockArea()
        pmtreeDock = pg.dockarea.Dock('Phase mask parameters', size=(1, 1))
        pmtreeDock.addWidget(self.slmParameterTree)
        self.paramtreeDockArea.addDock(pmtreeDock)
        abertreeDock = pg.dockarea.Dock('Aberration correction parameters', size=(1, 1))
        abertreeDock.addWidget(self.aberParameterTree)
        self.paramtreeDockArea.addDock(abertreeDock, 'above', pmtreeDock)

        # Control panel with most buttons
        self.controlPanel = QtGui.QFrame()
        self.controlPanel.choiceInterfaceLayout = QtGui.QGridLayout()
        self.controlPanel.choiceInterface = QtGui.QWidget()
        self.controlPanel.choiceInterface.setLayout(self.controlPanel.choiceInterfaceLayout)

        # Choose which mask to modify
        self.controlPanel.maskComboBox = QtGui.QComboBox()
        self.controlPanel.maskComboBox.addItem("Donut (left)")
        self.controlPanel.maskComboBox.addItem("Top hat (right)")
        self.controlPanel.choiceInterfaceLayout.addWidget(QtGui.QLabel('Select mask:'), 0, 0)
        self.controlPanel.choiceInterfaceLayout.addWidget(self.controlPanel.maskComboBox, 0, 1)

        # Choose which objective is in use
        self.controlPanel.objlensComboBox = QtGui.QComboBox()
        self.controlPanel.objlensComboBox.addItem("No objective")
        self.controlPanel.objlensComboBox.addItem("Oil")
        self.controlPanel.objlensComboBox.addItem("Glycerol")
        self.controlPanel.choiceInterfaceLayout.addWidget(QtGui.QLabel('Select objective:'), 1, 0)
        self.controlPanel.choiceInterfaceLayout.addWidget(self.controlPanel.objlensComboBox, 1, 1)

        # Phase mask moving buttons
        self.controlPanel.arrowButtons = []
        self.controlPanel.upButton = guitools.BetterPushButton('Up (YZ)')
        self.controlPanel.arrowButtons.append(self.controlPanel.upButton)
        self.controlPanel.downButton = guitools.BetterPushButton('Down (YZ)')
        self.controlPanel.arrowButtons.append(self.controlPanel.downButton)
        self.controlPanel.leftButton = guitools.BetterPushButton('Left (XZ)')
        self.controlPanel.arrowButtons.append(self.controlPanel.leftButton)
        self.controlPanel.rightButton = guitools.BetterPushButton('Right (XZ)')
        self.controlPanel.arrowButtons.append(self.controlPanel.rightButton)

        for button in self.controlPanel.arrowButtons:
            button.setCheckable(False)
            button.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                 QtGui.QSizePolicy.Expanding)                   
            button.setFixedSize(self.controlPanel.upButton.sizeHint())

        # Interface to change the amount of displacement induced by the arrows
        self.controlPanel.incrementInterface = QtGui.QWidget()
        self.controlPanel.incrementInterfaceLayout = QtGui.QVBoxLayout()
        self.controlPanel.incrementInterface.setLayout(self.controlPanel.incrementInterfaceLayout)
        self.controlPanel.incrementlabel = QtGui.QLabel("Step (px)")
        self.controlPanel.incrementSpinBox = QtGui.QSpinBox()
        self.controlPanel.incrementSpinBox.setRange(1, 50)
        self.controlPanel.incrementSpinBox.setValue(1)
        self.controlPanel.incrementInterfaceLayout.addWidget(self.controlPanel.incrementlabel)
        self.controlPanel.incrementInterfaceLayout.addWidget(self.controlPanel.incrementSpinBox)

        # Interface to change the rotation angle of phase pattern
        self.controlPanel.rotationInterface = QtGui.QWidget()
        self.controlPanel.rotationInterfaceLayout = QtGui.QVBoxLayout()
        self.controlPanel.rotationInterface.setLayout(self.controlPanel.rotationInterfaceLayout)
        self.controlPanel.rotationLabel = QtGui.QLabel('Pattern angle (rad)')
        self.controlPanel.rotationEdit = QtGui.QLineEdit('0')
        self.controlPanel.rotationInterfaceLayout.addWidget(self.controlPanel.rotationLabel)
        self.controlPanel.rotationInterfaceLayout.addWidget(self.controlPanel.rotationEdit)

        # Buttons for saving, loading, and controlling the various phase patterns
        self.controlPanel.saveButton = guitools.BetterPushButton("Save")
        self.controlPanel.loadButton = guitools.BetterPushButton("Load")

        self.controlPanel.donutButton = guitools.BetterPushButton("Donut")
        self.controlPanel.tophatButton = guitools.BetterPushButton("Tophat")

        self.controlPanel.blackButton = guitools.BetterPushButton("Black frame")
        self.controlPanel.gaussianButton = guitools.BetterPushButton("Gaussian")

        self.controlPanel.halfButton = guitools.BetterPushButton("Half pattern")
        self.controlPanel.quadrantButton = guitools.BetterPushButton("Quad pattern")
        self.controlPanel.hexButton = guitools.BetterPushButton("Hex pattern")
        self.controlPanel.splitbullButton = guitools.BetterPushButton("Split pattern")

        # Defining layout
        self.controlPanel.arrowsFrame = QtGui.QFrame()
        self.controlPanel.arrowsLayout = QtGui.QGridLayout()
        self.controlPanel.arrowsFrame.setLayout(self.controlPanel.arrowsLayout)

        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.upButton, 0, 1)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.leftButton, 1, 0)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.incrementInterface, 1, 1)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.rightButton, 1, 2)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.downButton, 2, 1)

        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.loadButton, 0, 3)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.saveButton, 1, 3)

        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.donutButton, 3, 0)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.tophatButton, 3, 1)

        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.blackButton, 4, 0)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.gaussianButton, 4, 1)

        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.halfButton, 5, 0)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.quadrantButton, 5, 1)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.hexButton, 6, 0)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.splitbullButton, 6, 1)
        self.controlPanel.arrowsLayout.addWidget(self.controlPanel.rotationInterface, 5, 2, 2, 1)

        # Definition of the box layout:
        self.controlPanel.boxLayout = QtGui.QVBoxLayout()
        self.controlPanel.setLayout(self.controlPanel.boxLayout)

        self.controlPanel.boxLayout.addWidget(self.controlPanel.choiceInterface)
        self.controlPanel.boxLayout.addWidget(self.controlPanel.arrowsFrame)

        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)

    def initControls(self):
        self.grid.addWidget(self.slmFrame, 0, 0, 1, 2)
        self.grid.addWidget(self.paramtreeDockArea, 1, 0, 1, 1)
        self.grid.addWidget(self.controlPanel, 1, 1, 1, 1)


class FocusLockWidget(Widget):
    ''' Widget containing focus lock interface. '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Focus lock
        self.kpEdit = QtGui.QLineEdit('5')
        self.kpLabel = QtGui.QLabel('kp')
        self.kiEdit = QtGui.QLineEdit('0.1')
        self.kiLabel = QtGui.QLabel('ki')
        
        self.lockButton = guitools.BetterPushButton('Lock')
        self.lockButton.setCheckable(True)
        self.lockButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                      QtGui.QSizePolicy.Expanding)
        
        self.zStackBox = QtGui.QCheckBox('Z-stack')
        self.twoFociBox = QtGui.QCheckBox('Two foci')

        self.zStepFromEdit = QtGui.QLineEdit('40')
        self.zStepFromLabel = QtGui.QLabel('Min step (nm)')
        self.zStepToEdit = QtGui.QLineEdit('100')
        self.zStepToLabel = QtGui.QLabel('Max step (nm)')

        #self.focusDataBox = QtGui.QCheckBox('Save data')  # Connect to exportData
        self.camDialogButton = guitools.BetterPushButton('Camera Dialog')

        # Piezo absolute positioning
        self.positionLabel = QtGui.QLabel('Position (µm)')  # Potentially disregard this and only use in the positioning widget?
        self.positionEdit = QtGui.QLineEdit('50')
        self.positionSetButton = guitools.BetterPushButton('Set')

        # Focus lock calibration
        self.calibFromLabel = QtGui.QLabel('From (µm)')
        self.calibFromEdit = QtGui.QLineEdit('49')
        self.calibToLabel = QtGui.QLabel('To (µm)')
        self.calibToEdit = QtGui.QLineEdit('51')
        self.focusCalibButton = guitools.BetterPushButton('Calib')
        self.focusCalibButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                            QtGui.QSizePolicy.Expanding)
        self.calibCurveButton = guitools.BetterPushButton('See calib')
        self.calibrationDisplay = QtGui.QLineEdit('Previous calib: none')  # Edit this from the controller with calibration values
        self.calibrationDisplay.setReadOnly(True)
        # CREATE CALIBRATION CURVE WINDOW AND FOCUS CALIBRATION GRAPH SOMEHOW

        # Focus lock graph
        self.focusLockGraph = pg.GraphicsLayoutWidget()
        self.focusLockGraph.setAntialiasing(True)
        self.focusPlot = self.focusLockGraph.addPlot(row=1, col=0)
        self.focusPlot.setLabels(bottom=('Time', 's'), left=('Laser position', 'px'))
        self.focusPlot.showGrid(x=True, y=True)
        self.focusPlotCurve = self.focusPlot.plot(pen='y')   # update this (self.focusPlotCurve.setData(X,Y)) with update(focusSignal) function

        # Webcam graph
        self.webcamGraph = pg.GraphicsLayoutWidget()
        self.camImg = pg.ImageItem(border='w')
        self.camImg.setImage(np.zeros((100,100)))
        self.vb = self.webcamGraph.addViewBox(invertY=True, invertX=False)
        self.vb.setAspectLocked(True)
        self.vb.addItem(self.camImg)

        # PROCESS DATA THREAD - ADD SOMEWHERE ELSE, NOT HERE, AS IT HAS NO GRAPHICAL ELEMENTS!

        # GUI layout below
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
        #grid.addWidget(self.focusDataBox, 4, 0, 1, 2)
        grid.addWidget(self.calibFromLabel, 1, 0)
        grid.addWidget(self.calibFromEdit, 1, 1)
        grid.addWidget(self.calibToLabel, 2, 0)
        grid.addWidget(self.calibToEdit, 2, 1)
        grid.addWidget(self.calibCurveButton, 3, 2)
        grid.addWidget(self.positionLabel, 1, 6)
        grid.addWidget(self.positionEdit, 1, 7)
        grid.addWidget(self.positionSetButton, 2, 6, 1, 2)
        grid.addWidget(self.camDialogButton, 3, 6, 1, 2)
