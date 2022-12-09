import numpy as np
import pyqtgraph as pg
import cv2 
import copy
from qtpy import QtCore, QtWidgets, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap, QImage

import sys
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget)
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt
from qtpy import QtCore, QtWidgets, QtGui, QtWidgets
import cv2
import numpy as np
import copy
from PyQt5.QtGui import QPixmap, QImage




from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget



class PixelCalibrationWidget(NapariHybridWidget):
    """ Widget containing PixelCalibration interface. """

    def __post_init__(self):
        #super().__init__(*args, **kwargs)
        # initialize all GUI elements

        # Add Painter for drawing a line on pixels
        self.canvas = Canvas()

        # Snap Preview Button
        self.PixelCalibrationSnapPreviewButton = guitools.BetterPushButton('Snap Preview')
        self.PixelCalibrationSnapPreviewButton.setCheckable(False)

        # Undo Button
        self.PixelCalibrationUndoButton = guitools.BetterPushButton('Undo')
        self.PixelCalibrationUndoButton.setCheckable(False)

        # editable for entering pixelvalues         
        self.PixelCalibrationLabelKnownDistance  = QtWidgets.QLabel('Known Distance: (µm)')
        self.PixelCalibrationEditFileName  = QtWidgets.QLineEdit('100')
        self.PixelCalibrationCalibrateButton = guitools.BetterPushButton('Start')
        self.PixelCalibrationCalibrateButton.setCheckable(False)
        self.PixelCalibrationLabelInfo = QtWidgets.QLabel("")

        # Defining layout
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        #
        self.grid.addWidget(self.canvas, 0, 0, 3, 3)
        
        #
        self.grid.addWidget(self.PixelCalibrationSnapPreviewButton, 1, 0, 1, 1)
        self.grid.addWidget(self.PixelCalibrationUndoButton, 1, 1, 1, 1)
        self.grid.addWidget(self.PixelCalibrationCalibrateButton, 1, 2, 1, 1)
        
        #
        self.grid.addWidget(self.PixelCalibrationLabelKnownDistance, 2, 0, 1, 1)
        self.grid.addWidget(self.PixelCalibrationEditFileName, 2, 1, 1, 1)
        self.grid.addWidget(self.PixelCalibrationLabelInfo, 2, 2, 1, 1)

        self.layer = None
        
        
    def getPixelSize(self):
        knownDistance = int(self.PixelCalibrationEditFileName.text())
        lineLength = self.canvas.getLineLength()
        pixelSize = knownDistance/lineLength
        return pixelSize   


    def getCoordinateList(self):
        return self.canvas.getCoordinateList()
    
    def setInformationLabel(self, information):
        self.PixelCalibrationLabelInfo.setText(information)
    
    def setPreviewImage(self, image):
        self.canvas.setImage(image)

class Canvas(QtWidgets.QLabel):
    def __init__(self):
        super().__init__()
        self.dimensions = (400,400)
        self.setFixedSize(self.dimensions[0],self.dimensions[1])
        self.setImage()
        
        self.pos = None
        #self.setMouseTracking(False)
        self.pressPos = (0,0)
        self.lineCoordinates = (0,0,0,0)
        
        self.isTracking = False
        

    def setImage(self, npImage=None, pathImage='histo.jpg'):
        
        if npImage is None:
            npImage = np.array(cv2.imread(pathImage))
            npImage = cv2.resize(npImage, self.dimensions)
        if len(npImage.shape) == 2:
            npImage = np.repeat(npImage[:,:,np.newaxis], 3, axis=2)

        height, width, channel = npImage.shape
        bytesPerLine = 3 * width
        qImage = QImage(npImage.data, width, height, bytesPerLine, QImage.Format_RGB888)
        self.imageNow = QPixmap(qImage)

        self.setPixmap(self.imageNow.scaled(self.dimensions[0], self.dimensions[1], QtCore.Qt.KeepAspectRatio))

    def enterEvent(self, event):
        super().enterEvent(event)
        self.isTracking = True

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.isTracking = False
        
    def mouseMoveEvent(self, event):
        self.pos = event.pos()
        self.update()

    def paintEvent(self, event):
        if self.pos and self.pressPos and self.isTracking:
            painter = QPainter(self)         
            pen = QtGui.QPen()
            pen.setWidth(4)
            pen.setColor(QtGui.QColor('yellow'))
            painter.setPen(pen)   
            try:                
                painter.drawLine(self.pos.x(), self.pos.y(), self.pressPos.x(), self.pressPos.y())
                painter.end()
                self.lineCoordinates = [self.pos.x(), self.pos.y(), self.pressPos.x(), self.pressPos.y()]
            except Exception as e:
                print (e)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressPos = event.pos()
            self.setMouseTracking(True)

    def mouseReleaseEvent(self, event):
        # ensure that the left button was pressed *and* released within the
        # geometry of the widget; if so, emit the signal;
        if (self.pressPos is not None and 
            event.button() == Qt.LeftButton and 
            event.pos() in self.rect()):
                self.setMouseTracking(False)
        self.pressPos = None  
        
    def getLineLength(self):
        try:
            lineLength = np.sqrt(np.abs(self.lineCoordinates[2]-self.lineCoordinates[0])**2+np.abs(self.lineCoordinates[3]-self.lineCoordinates[1])**2)
        except:
            lineLength = 1
        return lineLength 
                
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
