import numpy as np
import pyqtgraph as pg
import cv2 
import copy
from qtpy import QtCore, QtWidgets, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap, QImage




from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget



class HistoScanWidget(NapariHybridWidget):
    """ Widget containing HistoScan interface. """


    sigHistoScanInitFilterPos = QtCore.Signal(bool)  # (enabled)
    sigHistoScanShowLast = QtCore.Signal(bool)  # (enabled)
    sigHistoScanStop = QtCore.Signal(bool)  # (enabled)
    sigHistoScanStart = QtCore.Signal(bool)  # (enabled)
    sigHistoSnapPreview = QtCore.Signal(bool)  # (enabled)

    sigShowToggled = QtCore.Signal(bool)  # (enabled)
    sigPIDToggled = QtCore.Signal(bool)  # (enabled)
    sigUpdateRateChanged = QtCore.Signal(float)  # (rate)
    
    sigSliderLaser2ValueChanged = QtCore.Signal(float)  # (value)
    sigSliderLaser1ValueChanged = QtCore.Signal(float)  # (value)
    sigSliderLEDValueChanged = QtCore.Signal(float)  # (value)
    sigHistoFillSelection = QtCore.Signal(bool)  # (enabled)
    sigHistoUndoSelection = QtCore.Signal(bool)  # (enabled)
    sigHistoScanMoveRight = QtCore.Signal(bool)  # (enabled)
    sigHistoScanMoveLeft = QtCore.Signal(bool)  # (enabled)
    sigHistoScanMoveUp = QtCore.Signal(bool)  # (enabled)
    sigHistoScanMoveDown = QtCore.Signal(bool)  # (enabled)
    
    def __post_init__(self):
        #super().__init__(*args, **kwargs)

        self.HistoScanFrame = pg.GraphicsLayoutWidget()
        
        # initialize all GUI elements

        # z-stack
        self.HistoScanLabelZStack  = QtWidgets.QLabel('Z-Stack (min,max,steps):')        
        self.HistoScanValueZmin = QtWidgets.QLineEdit('-100')
        self.HistoScanValueZmax = QtWidgets.QLineEdit('100')
        self.HistoScanValueZsteps = QtWidgets.QLineEdit('10')
        
        # Add Histopainter
        self.canvas = Canvas()

        # Snap Preview Button
        self.HistoSnapPreviewButton = guitools.BetterPushButton('Snap Preview')
        self.HistoSnapPreviewButton.setCheckable(False)
        self.HistoSnapPreviewButton.toggled.connect(self.sigHistoSnapPreview)

        # Undo Button
        self.HistoUndoButton = guitools.BetterPushButton('Undo')
        self.HistoUndoButton.setCheckable(False)
        self.HistoUndoButton.toggled.connect(self.sigHistoUndoSelection)
        
        # Fill holes Button
        self.HistoFillHolesButton = guitools.BetterPushButton('Fill Holes')
        self.HistoFillHolesButton.setCheckable(False)
        self.HistoFillHolesButton.toggled.connect(self.sigHistoFillSelection)

        # Camera LED Button
        self.HistoCamLEDButton = guitools.BetterPushButton('Camera LED')
        self.HistoCamLEDButton.setCheckable(True)
               
        
        # LED
        valueDecimalsLED = 1
        valueRangeLED = (0,2**8)
        tickIntervalLED = 1
        singleStepLED = 1
        
        self.sliderLED, self.HistoScanLabelLED = self.setupSliderGui('Intensity (LED):', valueDecimalsLED, valueRangeLED, tickIntervalLED, singleStepLED)
        self.sliderLED.valueChanged.connect(
            lambda value: self.sigSliderLEDValueChanged.emit(value)
        )
        
        self.HistoScanLabelFileName  = QtWidgets.QLabel('FileName:')
        self.HistoScanEditFileName  = QtWidgets.QLineEdit('HistoScan')
        self.HistoScanLabelInfo  = QtWidgets.QLabel('Info')

        self.HistoScanStartButton = guitools.BetterPushButton('Start')
        self.HistoScanStartButton.setCheckable(False)
        self.HistoScanStartButton.toggled.connect(self.sigHistoScanStart)

        self.HistoScanStopButton = guitools.BetterPushButton('Stop')
        self.HistoScanStopButton.setCheckable(False)
        self.HistoScanStopButton.toggled.connect(self.sigHistoScanStop)

        self.HistoScanShowLastButton = guitools.BetterPushButton('Show Last')
        self.HistoScanShowLastButton.setCheckable(False)
        self.HistoScanShowLastButton.toggled.connect(self.sigHistoScanShowLast)

        self.HistoScanDoZStack = QtWidgets.QCheckBox('Perform Z-Stack')
        self.HistoScanDoZStack.setCheckable(True)
        
        # Joystick
        self.HistoScanMoveUpButton = guitools.BetterPushButton('^')
        self.HistoScanMoveUpButton.setCheckable(False)
        self.HistoScanMoveUpButton.toggled.connect(self.sigHistoScanMoveUp)
        
        self.HistoScanMoveDownButton = guitools.BetterPushButton('v')
        self.HistoScanMoveDownButton.setCheckable(False)
        self.HistoScanMoveDownButton.toggled.connect(self.sigHistoScanMoveDown)

        self.HistoScanMoveLeftButton = guitools.BetterPushButton('<')
        self.HistoScanMoveLeftButton.setCheckable(False)
        self.HistoScanMoveLeftButton.toggled.connect(self.sigHistoScanMoveLeft)
        
        self.HistoScanMoveRightButton = guitools.BetterPushButton('>')
        self.HistoScanMoveRightButton.setCheckable(False)
        self.HistoScanMoveRightButton.toggled.connect(self.sigHistoScanMoveRight)

               
        # Defining layout
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        self.grid.addWidget(self.HistoScanMoveLeftButton, 0, 0, 1, 1)
        self.grid.addWidget(self.HistoScanMoveRightButton, 0, 1, 1, 1)
        self.grid.addWidget(self.HistoScanMoveUpButton, 0, 2, 1, 1)
        self.grid.addWidget(self.HistoScanMoveDownButton, 0, 3, 1, 1)
        
        self.grid.addWidget(self.HistoScanLabelZStack, 1, 0, 1, 1)
        self.grid.addWidget(self.HistoScanValueZmin, 1, 1, 1, 1)
        self.grid.addWidget(self.HistoScanValueZmax, 1, 2, 1, 1)
        self.grid.addWidget(self.HistoScanValueZsteps, 1, 3, 1, 1)
        
        self.grid.addWidget(self.canvas, 2, 0, 3, 3)
        
        self.grid.addWidget(self.HistoCamLEDButton, 3, 0, 1, 1)
        self.grid.addWidget(self.HistoSnapPreviewButton, 3, 1, 1, 1)
        self.grid.addWidget(self.HistoUndoButton, 3, 2, 1, 1)
        self.grid.addWidget(self.HistoFillHolesButton, 3, 3, 1, 1)
        
        self.grid.addWidget(self.HistoScanLabelLED, 4, 0, 1, 1)
        self.grid.addWidget(self.sliderLED, 4, 1, 1, 3)
        
        self.grid.addWidget(self.HistoScanLabelFileName, 5, 0, 1, 1)
        self.grid.addWidget(self.HistoScanEditFileName, 5, 1, 1, 1)
        self.grid.addWidget(self.HistoScanLabelInfo, 5, 2, 1, 1)
        self.grid.addWidget(self.HistoScanStartButton, 8, 0, 1, 1)
        self.grid.addWidget(self.HistoScanStopButton, 8, 1, 1, 1)
        self.grid.addWidget(self.HistoScanShowLastButton,8, 2, 1, 1)
        self.grid.addWidget(self.HistoScanDoZStack, 5, 3, 1, 1)

        self.layer = None
        
        
    def isAutofocus(self):
        if self.autofocusLED1Checkbox.isChecked() or self.autofocusLaser1Checkbox.isChecked() or self.autofocusLaser2Checkbox.isChecked():
            return True
        else:
            return False
        
    def getAutofocusValues(self):
        autofocusParams = {}
        autofocusParams["valueRange"] = self.autofocusRange.text()
        autofocusParams["valueSteps"] = self.autofocusSteps.text()
        autofocusParams["valuePeriod"] = self.autofocusPeriod.text()
        if self.autofocusLED1Checkbox.isChecked():
            autofocusParams["illuMethod"] = 'LED'
        elif self.autofocusLaser1Checkbox.isChecked():
            autofocusParams["illuMethod"] = 'Laser1'
        elif self.autofocusLaser2Checkbox.isChecked():
            autofocusParams["illuMethod"] = 'Laser2'
        else:
            autofocusParams["illuMethod"] = False
        
        return autofocusParams
 
 
    def setupSliderGui(self, label, valueDecimals, valueRange, tickInterval, singleStep):
        HistoScanLabel  = QtWidgets.QLabel(label)     
        valueRangeMin, valueRangeMax = valueRange
        slider = guitools.FloatSlider(QtCore.Qt.Horizontal, self, allowScrollChanges=False,
                                        decimals=valueDecimals)
        slider.setFocusPolicy(QtCore.Qt.NoFocus)
        slider.setMinimum(valueRangeMin)
        slider.setMaximum(valueRangeMax)
        slider.setTickInterval(tickInterval)
        slider.setSingleStep(singleStep)
        slider.setValue(0)
        return slider, HistoScanLabel
        
    def getImage(self):
        if self.layer is not None:
            return self.img.image
        
    def setImage(self, im, colormap="gray", name="", pixelsizeZ=1):
        if self.layer is None or name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False, colormap=colormap, 
                                               scale=(1, 1, pixelsizeZ),
                                               name=name, blending='additive')
        self.layer.data = im

    def getCoordinateList(self):
        return self.canvas.getCoordinateList()
        
    def resetCoodinateList(self):
        self.canvas.resetCoordinateList()
        
    def getZStackValues(self):
        valueZmin = -abs(float(self.HistoScanValueZmin.text()))
        valueZmax = float(self.HistoScanValueZmax.text())
        valueZsteps = float(self.HistoScanValueZsteps.text())
        valueZenabled = bool(self.HistoScanDoZStack.isChecked())
        
        return valueZmin, valueZmax, valueZsteps, valueZenabled
 

    def getFilename(self):
        HistoScanEditFileName = self.HistoScanEditFileName.text()
        return HistoScanEditFileName
    
    def setInformationLabel(self, information):
        self.HistoScanLabelInfo.setText(information)
    
    def setPreviewImage(self, image):
        self.canvas.setImage(image)

class Canvas(QtWidgets.QLabel):

    def __init__(self):
        super().__init__()
        self.dimensions = (200,200)
        self.penwidth = 4
        self.setFixedSize(self.dimensions[0],self.dimensions[1])
        
        self.coordinateList = []
        self.imageLast = None
        self.setImage()
        
        self.last_x, self.last_y = None, None
        self.pen_color = QtGui.QColor('#FF0000') # RGB=255,0,0
        
    def overlayImage(self, npImage, alpha=0.5):
        """Overlay image on top of canvas image"""
        if self.imageLast is not None:
            self.setImage(self.imageLast)
        else:
            self.setImage()
        self.imageLast = self.imageNow.toImage()
        painter = QtGui.QPainter(self.pixmap())
        painter.setOpacity(alpha)
        
        if len(npImage.shape) == 2:
            npImage = np.repeat(npImage[:,:,np.newaxis], 3, axis=2)
        height, width, channel = npImage.shape
        bytesPerLine = 3 * width
        qImage = QImage(npImage.data, width, height, bytesPerLine, QImage.Format_RGB888)
        
        self.setPixmap(self.imageNow.scaled(self.dimensions[0], self.dimensions[1], QtCore.Qt.KeepAspectRatio))

        painter.drawImage(0, 0, qImage)
        painter.end()
        self.update()
        
    def setImage(self, npImage=None, pathImage='/Users/bene/Downloads/histo.png'):
        
        if npImage is None:
            npImage = np.array(cv2.imread(pathImage))
            npImage = cv2.resize(npImage, self.dimensions)
        if len(npImage.shape) == 2:
            npImage = np.repeat(npImage[:,:,np.newaxis], 3, axis=2)
        self.imageLast=copy.deepcopy(npImage) # store for undo
        height, width, channel = npImage.shape
        bytesPerLine = 3 * width
        qImage = QImage(npImage.data, width, height, bytesPerLine, QImage.Format_RGB888)
        self.imageNow = QPixmap(qImage)
        
        self.setPixmap(self.imageNow.scaled(self.dimensions[0], self.dimensions[1], QtCore.Qt.KeepAspectRatio))

    def undoSelection(self):
        if self.imageLast is not None:
            self.setImage(self.imageLast)
            self.coordinateList = []
    
    def fillHoles(self):
        # fill gaps in selection 
        image = np.uint8(self.imageLast)
        selectionOverlay = image.copy()*0
        # render selection
        tmp = np.array(self.coordinateList)
        selectionOverlay[tmp[:,0],tmp[:,1]] = 255
        nKernel = self.penwidth
        kernel =  np.ones((nKernel,nKernel)) 
        # binary coordinates (without physical units ) of the scan region
        selectionOverlay = cv2.filter2D(selectionOverlay, -1, kernel)>1
        
        # filling holes in selection
        kernelClosing =  np.ones((20,20)) 
        selectionOverlay = cv2.morphologyEx(np.uint8(selectionOverlay), cv2.MORPH_CLOSE, kernelClosing)
        
        # overlay selection
        image[(selectionOverlay[:,:,0]>0),]=(255,0,0)
        self.setImage(image)
        
        # update coordinate list
        self.coordinateList = list(np.argwhere(selectionOverlay[:,:,0]>0))
        
    def set_pen_color(self, c):
        self.pen_color = QtGui.QColor(c)

    def mouseMoveEvent(self, e):
        if self.last_x is None: # First event.
            self.last_x = e.x()
            self.last_y = e.y()
            return # Ignore the first time.

        painter = QtGui.QPainter(self.pixmap())
        p = painter.pen()
        p.setWidth(self.penwidth)
        p.setColor(self.pen_color)
        painter.setPen(p)
        painter.drawLine(self.last_x, self.last_y, e.x(), e.y())
        painter.end()
        self.update()
        if self.last_x is not None and self.last_y is not None:
            self.last_x = e.x()
            self.last_y = e.y()
            self.coordinateList.append([e.y(), e.x()])
        
    def getCoordinateList(self):
        return self.coordinateList
    
    def resetCoordinateList(self):
        self.coordinateList = []
        
    def mouseReleaseEvent(self, e):
        self.last_x = None
        self.last_y = None



COLORS = ['#000000', '#ffffff']


class QPaletteButton(QtWidgets.QPushButton):
    
    def __init__(self, color):
        super().__init__()
        self.setFixedSize(QtCore.QSize(24,24))
        self.color = color
        self.setStyleSheet("background-color: %s;" % color)
        
COLORS = ['#000000', '#ffffff']

    
        
# Copyright (C) 2020-2021 ImSwitch developers
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
