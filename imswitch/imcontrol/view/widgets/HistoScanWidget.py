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


    sigSliderIlluValueChanged = QtCore.Signal(float)  # (value)
    
    def __post_init__(self):
        #super().__init__(*args, **kwargs)

        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        # Pull-down menu for the illumination source
        self.illuminationSourceComboBox = QtWidgets.QComboBox()
        self.illuminationSourceLabel = QtWidgets.QLabel("Illumination Source:")
        self.illuminationSourceComboBox.addItems(["Laser 1", "Laser 2", "LED"])
        self.grid.addWidget(self.illuminationSourceComboBox, 3, 0, 1, 1)

        # Slider for setting the value for the illumination source
        self.illuminationSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.illuminationSlider.setMinimum(0)
        self.illuminationSlider.setMaximum(100)
        self.illuminationSlider.valueChanged.connect(
            lambda value: self.sigSliderIlluValueChanged.emit(value)
        )
        
        self.grid.addWidget(self.illuminationSlider, 3, 1, 1, 1)

        # Pull-down menu for the stage axis
        self.stageAxisComboBox = QtWidgets.QComboBox()
        self.stageAxisLabel = QtWidgets.QLabel("Stage Axis:")
        self.stageAxisComboBox.addItems(["X", "Y", "Z", "A"])
        self.grid.addWidget(self.stageAxisLabel, 4, 0, 1, 1)
        self.grid.addWidget(self.stageAxisComboBox, 4, 1, 1, 1)

        # Text fields for minimum and maximum position for X
        self.minPositionXLineEdit = QtWidgets.QLineEdit("-1000")
        self.maxPositionXLineEdit = QtWidgets.QLineEdit("1000")
        self.grid.addWidget(QtWidgets.QLabel("Min Position (X):"), 5, 0, 1, 1)
        self.grid.addWidget(self.minPositionXLineEdit, 5, 1, 1, 1)
        self.grid.addWidget(QtWidgets.QLabel("Max Position (X):"), 6, 0, 1, 1)
        self.grid.addWidget(self.maxPositionXLineEdit, 6, 1, 1, 1)
        
        # Text fields for minimum and maximum position for Y
        self.minPositionYLineEdit = QtWidgets.QLineEdit("-1000")
        self.maxPositionYLineEdit = QtWidgets.QLineEdit("1000")
        self.grid.addWidget(QtWidgets.QLabel("Min Position (Y):"), 7, 0, 1, 1)
        self.grid.addWidget(self.minPositionYLineEdit, 7, 1, 1, 1)
        self.grid.addWidget(QtWidgets.QLabel("Max Position (Y):"), 8, 0, 1, 1)
        self.grid.addWidget(self.maxPositionYLineEdit, 8, 1, 1, 1)
        
        # Start and Stop buttons
        self.startButton = QtWidgets.QPushButton('Start')
        self.stopButton = QtWidgets.QPushButton('Stop')
        self.speedLabel = QtWidgets.QLabel("Speed:")
        self.speedTextedit = QtWidgets.QLineEdit("1000")
        self.grid.addWidget(self.startButton, 9, 0, 1, 1)
        self.grid.addWidget(self.stopButton, 9, 1, 1, 1)
        self.grid.addWidget(self.speedLabel, 10, 0, 1, 1)
        self.grid.addWidget(self.speedTextedit, 10, 1, 1, 1)
        
        self.layer = None
        
    def setAvailableIlluSources(self, sources):
        self.illuminationSourceComboBox.clear()
        self.illuminationSourceComboBox.addItems(sources)
    
    def setAvailableStageAxes(self, axes):
        self.stageAxisComboBox.clear()
        self.stageAxisComboBox.addItems(axes)
        
    def getSpeed(self):
        return np.float32(self.speedTextedit.text())
    
    def getIlluminationSource(self):
        return self.illuminationSourceComboBox.currentText()
    
    def getStageAxis(self):
        return self.stageAxisComboBox.currentText()
    
    def getMinPositionX(self):
        return np.float32(self.minPositionXLineEdit.text())
    
    def getMaxPositionX(self):
        return np.float32(self.maxPositionXLineEdit.text())
    
    def getMinPositionY(self):
        return np.float32(self.minPositionYLineEdit.text())
    
    def getMaxPositionY(self):
        return np.float32(self.maxPositionYLineEdit.text())
    
    
        
    def setImageNapari(self, im, colormap="gray", name="", pixelsize=(1,1,1), translation=(0,0,0)):
        if len(im.shape) == 2:
            translation = (translation[0], translation[1])
        if self.layer is None or name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False, colormap=colormap, 
                                               scale=pixelsize,translate=translation,
                                               name=name, blending='additive')
        self.layer.data = im
        
        

    def isAutofocus(self):
        if self.autofocusCheckbox.isChecked():
            return True
        else:
            return False
        
    def getAutofocusValues(self):
        autofocusParams = {}
        autofocusParams["valueRange"] = self.autofocusRange.text()
        autofocusParams["valueSteps"] = self.autofocusSteps.text()
        autofocusParams["valuePeriod"] = self.autofocusPeriod.text()
        autofocusParams["illuMethod"] = 'LED'
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
        
    def setImage(self, npImage=None, pathImage='histo.jpg'):
        
        if npImage is None:
            npImage = np.array(cv2.imread(pathImage))
            if npImage.max() is None:
                npImage = np.random.randint(0,255,(self.dimensions[0],self.dimensions[1],3))
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
        tmp = np.clip(tmp, 0, np.min(selectionOverlay.shape[0:2])-1)
        selectionOverlay[tmp[:,0],tmp[:,1]] = 255
        nKernel = self.penwidth
        kernel =  np.ones((nKernel,nKernel)) 
        # binary coordinates (without physical units ) of the scan region
        selectionOverlay = cv2.filter2D(selectionOverlay, -1, kernel)>1
        
        # filling holes in selection
        kernelSize = 40
        kernelClosing =  np.ones((kernelSize,kernelSize)) 
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
