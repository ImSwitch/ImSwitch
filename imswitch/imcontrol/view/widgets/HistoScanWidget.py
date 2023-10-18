import numpy as np
import pyqtgraph as pg
import cv2 
import copy
from qtpy import QtCore, QtWidgets, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap, QImage
from PyQt5 import QtGui, QtWidgets
import PyQt5
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget


class ScanParameters(object):
    def __init__(self, name="Wellplate", physDimX=164, physDimY=109, physOffsetX=0, physOffsetY=0, imagePath="imswitch/_data/images/WellplateAdapter3Slides.png"):
        self.name = name
        self.physDimX = physDimX*1e3 # mm
        self.physDimY = physDimY*1e3 # mm
        self.physOffsetX = physOffsetX
        self.physOffsetY =  physOffsetY
        self.imagePath = imagePath
        
        

class HistoScanWidget(NapariHybridWidget):
    """ Widget containing HistoScan interface. """
    sigSliderIlluValueChanged = QtCore.Signal(float)  # (value)
    sigGoToPosition = QtCore.Signal(float, float)  # (posX, posY)
    sigCurrentOffset = QtCore.Signal(float, float)
    
    def __post_init__(self):
        #super().__init__(*args, **kwargs)
        self._logger = initLogger(self)
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
        
        self.samplePicker = QtWidgets.QComboBox()
        
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
        self.calibrationButton =  QtWidgets.QPushButton('Calibrate Position')
        self.calibrationButton.setCheckable(True)
        self.speedTextedit = QtWidgets.QLineEdit("1000")
        self.grid.addWidget(self.startButton, 9, 0, 1, 1)
        self.grid.addWidget(self.stopButton, 9, 1, 1, 1)
        self.grid.addWidget(self.speedLabel, 10, 0, 1, 1)
        self.grid.addWidget(self.speedTextedit, 10, 1, 1, 1)
        self.grid.addWidget(self.calibrationButton, 9, 2, 1, 1)
        self.grid.addWidget(self.samplePicker, 10, 2, 1, 1)
        

        # define scan parameter per sample
        self.allScanParameters = []
        self.allScanParameters.append(ScanParameters("6 Wellplate", 126, 86, 0, 0, "imswitch/_data/images/Wellplate6.png"))
        self.allScanParameters.append(ScanParameters("3-Slide Wellplateadapter", 164, 109, 0, 0, "imswitch/_data/images/WellplateAdapter3Slides.png"))
        
        # load sample layout
        self.ScanSelectViewWidget = None
        self.loadSampleLayout(0)
        self.grid.addWidget(self.ScanSelectViewWidget, 11, 1, 1, 1)
        
        self.grid.addWidget(self.calibrationButton, 9, 2, 1, 1)
        
        # set combobox with all samples
        self.setSampleLayouts(self.allScanParameters)
        self.samplePicker.currentIndexChanged.connect(self.loadSampleLayout)
        
        self.layer = None
        

    def loadSampleLayout(self, index):
        if self.ScanSelectViewWidget is None:
            self.ScanSelectViewWidget = ScanSelectView(self, self.allScanParameters[index])
        else:
            self.ScanSelectViewWidget.updateParams(self.allScanParameters[index])
        self.ScanSelectViewWidget.setPixmap(QtGui.QPixmap(self.allScanParameters[index].imagePath))
            

    def setSampleLayouts(self, sampleLayoutList):
        self.samplePicker.clear()
        for sample in sampleLayoutList:
            self.samplePicker.addItem(sample.name)
        
        
    def setOffset(self, offsetX, offsetY):
        self.ScanSelectViewWidget.setOffset(offsetX, offsetY)

    def setScanMinMax(self, posXmin, posYmin, posXmax, posYmax):
        self.minPositionXLineEdit.setText(str(np.int64(posXmin)))
        self.maxPositionXLineEdit.setText(str(np.int64(posXmax)))
        self.minPositionYLineEdit.setText(str(np.int64(posYmin)))
        self.maxPositionYLineEdit.setText(str(np.int64(posYmax)))
        self._logger.debug("Setting scan min/max")
        
    def goToPosition(self, posX, posY):
        self._logger.debug("Moving to position")
        self.sigGoToPosition.emit(posX, posY)
                                                    
    def setAvailableIlluSources(self, sources):
        self.illuminationSourceComboBox.clear()
        self.illuminationSourceComboBox.addItems(sources)
            
    def getSpeed(self):
        return np.float32(self.speedTextedit.text())
    
    def getIlluminationSource(self):
        return self.illuminationSourceComboBox.currentText()
    
    def getMinPositionX(self):
        return np.float32(self.minPositionXLineEdit.text())
    
    def getMaxPositionX(self):
        return np.float32(self.maxPositionXLineEdit.text())
    
    def getMinPositionY(self):
        return np.float32(self.minPositionYLineEdit.text())
    
    def getMaxPositionY(self):
        return np.float32(self.maxPositionYLineEdit.text())
        
    def setImageNapari(self, im, colormap="gray", isRGB = False, name="", pixelsize=(1,1), translation=(0,0)):
        if len(im.shape) == 2:
            translation = (translation[0], translation[1])
        if self.layer is None or name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=isRGB, colormap=colormap, 
                                               scale=pixelsize,translate=translation,
                                               name=name, blending='additive')
        self.layer.data = im
        
    def updatePartialImageNapari(self, im, coords, name=""):
        ''' update a sub roi of the already existing napari layer '''
        if self.layer is None or name not in self.viewer.layers:
            return
        try: 
            # coords are x,y,w,h
            self.layer.data[coords[1]-coords[3]:coords[1], coords[0]:coords[0]+coords[2]] = im
            self.layer.refresh()
        except Exception as e:
            self._logger.error(e)
            return

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
    
    def updateBoxPosition(self, posX, posY):
        self.ScanSelectViewWidget.drawRectCurrentPoint(posX, posY)




class QPaletteButton(QtWidgets.QPushButton):
    
    def __init__(self, color):
        super().__init__()
        self.setFixedSize(QtCore.QSize(24,24))
        self.color = color
        self.setStyleSheet("background-color: %s;" % color)
        
COLORS = ['#000000', '#ffffff']


class ScanSelectView(QtWidgets.QGraphicsView):
    def __init__(self, parent, scanParameters):
        super().__init__(parent)
        scene = QtWidgets.QGraphicsScene(self)
        self.setScene(scene)

        self._pixmap_item = QtWidgets.QGraphicsPixmapItem()
        scene.addItem(self.pixmap_item)

        self.selection_rect = None
        self.start_point = None
        self.parent = parent
        
        # real-world coordinates for the scan region that is represented by the image
        self.physDimX = scanParameters.physDimX
        self.physDimY = scanParameters.physDimY
        self.physOffsetX = scanParameters.physOffsetX
        self.physOffsetY = scanParameters.physOffsetY
        self.clickedCoordinates = (0,0)
        
    def updateParams(self, scanParameters):
        # real-world coordinates for the scan region that is represented by the image
        self.physDimX = scanParameters.physDimX
        self.physDimY = scanParameters.physDimY
        self.physOffsetX = scanParameters.physOffsetX
        self.physOffsetY = scanParameters.physOffsetY
        
    def setOffset(self, offsetX, offsetY):
        self.physOffsetX = offsetX
        self.physOffsetY = offsetY

    @property
    def pixmap_item(self):
        return self._pixmap_item

    def setPixmap(self, pixmap):
        self.pixmap_item.setPixmap(pixmap)

    def resizeEvent(self, event):
        self.fitInView(self.pixmap_item, PyQt5.QtCore.Qt.KeepAspectRatio)
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        sp = self.mapToScene(event.pos())
        lp = self.pixmap_item.mapFromScene(sp).toPoint()

        if event.button() == PyQt5.QtCore.Qt.LeftButton:
            self.start_point = lp
            if self.selection_rect:
                self.scene().removeItem(self.selection_rect)
            self.selection_rect = QtWidgets.QGraphicsRectItem(PyQt5.QtCore.QRectF(self.start_point, lp))
            self.selection_rect.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0)))
            self.scene().addItem(self.selection_rect)

    def mouseMoveEvent(self, event):
        if self.start_point:
            sp = self.mapToScene(event.pos())
            lp = self.pixmap_item.mapFromScene(sp).toPoint()
            rect = PyQt5.QtCore.QRectF(self.start_point, lp)
            self.selection_rect.setRect(rect.normalized())

    def drawRectCurrentPoint(self, posX, posY):
        '''
        draw the current coordinates in the map converted from real-world coordinates into pixelmaps
        '''
        try: self.scene().removeItem(self.selection_rect_current)
        except: pass
         
        left = ((posX - self.physOffsetX)/self.physDimX)*self.pixmap_item.pixmap().width()
        top = -((posY - self.physOffsetY)/+self.physDimY*self.pixmap_item.pixmap().height()-self.pixmap_item.pixmap().height())
                
        self.selection_rect_current = QtWidgets.QGraphicsRectItem(PyQt5.QtCore.QRectF(left-5, top-5, 5, 5))
        self.selection_rect_current.setPen(QtGui.QPen(QtGui.QColor(0, 255, 0)))
        self.scene().addItem(self.selection_rect_current)     

    def mouseReleaseEvent(self, event):
        if event.button() == PyQt5.QtCore.Qt.LeftButton and self.start_point:
            self.start_point = None
            # Calculate the selected coordinates here based on self.selection_rect.rect()
            selected_rect = self.selection_rect.rect()
            left = selected_rect.left()
            top = selected_rect.top()
            right = selected_rect.right()
            bottom = selected_rect.bottom()
            self._logger.debug("Selected coordinates:", left, top, right, bottom)


            # differentiate between single point and rectangle
            if np.abs(left-right)<5 and np.abs(top-bottom)<5:
                # single 
                self.scene().removeItem(self.selection_rect)
                self.selection_rect = QtWidgets.QGraphicsRectItem(PyQt5.QtCore.QRectF(left-5, top-5, 5, 5))
                self.selection_rect.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0)))
                self.scene().addItem(self.selection_rect)                
                # calculate real-world coordinates
                if self.parent.calibrationButton.isChecked():
                    self.physOffsetX, self.physOffsetY = 0,0 # reset offset because we estimate a new one
                posX = left/self.pixmap_item.pixmap().width()*self.physDimX+self.physOffsetX
                posY = (self.pixmap_item.pixmap().height()-top)/self.pixmap_item.pixmap().height()*self.physDimY+self.physOffsetY
                
                if self.parent.calibrationButton.isChecked():
                    self.clickedCoordinates = (posX,posY)
                    self.parent.sigCurrentOffset.emit(posX, posY)
                else:
                    self.parent.goToPosition(posX, posY)
                    self.drawRectCurrentPoint(posX, posY)
            else:
                # rectangle => send min/max X/Y position to parent
                # calculate real-world coordinates
                posXmin = left/self.pixmap_item.pixmap().width()*self.physDimX+self.physOffsetX
                posXmax = right/self.pixmap_item.pixmap().width()*self.physDimX+self.physOffsetX
                posYmin = (self.pixmap_item.pixmap().height()-bottom)/self.pixmap_item.pixmap().height()*self.physDimY+self.physOffsetY
                posYmax = (self.pixmap_item.pixmap().height()-top)/self.pixmap_item.pixmap().height()*self.physDimY+self.physOffsetY
                
                self.parent.setScanMinMax(posXmin, posYmin, posXmax, posYmax)
                
                





        
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
