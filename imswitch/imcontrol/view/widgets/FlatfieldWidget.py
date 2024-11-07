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
import os


class FlatfieldWidget(NapariHybridWidget):
    """ Widget containing Flatfield interface. """

    def __post_init__(self):
        #super().__init__(*args, **kwargs)
        self._logger = initLogger(self)
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        
        # define the grid layout
        self.maxStepsizeLabel = QtWidgets.QLabel("Max Step Size:")
        self.maxStepsizeTextedit = QtWidgets.QLineEdit("1000")
        self.nImagesToAverageLabel = QtWidgets.QLabel("Number of Images to Average:")
        self.nImagesToAverageTextedit = QtWidgets.QLineEdit("10")
        self.nGaussLabel = QtWidgets.QLabel("Gauss Kernel:")
        self.nGaussTextedit = QtWidgets.QLineEdit("50")
        
        # Start and Stop buttons
        self.startButton = QtWidgets.QPushButton('Start')
        self.stopButton = QtWidgets.QPushButton('Stop')
        
        # add gui elements to grid
        self.grid.addWidget(self.maxStepsizeLabel, 0, 0, 1, 1)
        self.grid.addWidget(self.maxStepsizeTextedit, 0, 1, 1, 1)
        self.grid.addWidget(self.nImagesToAverageLabel, 1, 0, 1, 1)
        self.grid.addWidget(self.nImagesToAverageTextedit, 1, 1, 1, 1)
        self.grid.addWidget(self.startButton, 2, 0, 1, 1)
        self.grid.addWidget(self.stopButton, 2, 1, 1, 1)
        
        self.layer = None

    def getGaussKernelSize(self):
        return np.int32(self.nGaussTextedit.text())
        
    def getNImagesToAverage(self):
        return np.int32(self.nImagesToAverageTextedit.text())
    
    def getMaxStepSize(self):
        return np.float32(self.maxStepsizeTextedit.text())
    
    def setImageNapari(self, im, colormap="gray", isRGB = False, name="", pixelsize=(1,1), translation=(0,0)):
        if len(im.shape) == 2:
            translation = (translation[0], translation[1])
        if self.layer is None or name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=isRGB, colormap=colormap,
                                               scale=pixelsize,translate=translation,
                                               name=name, blending='additive')
        self.layer.data = im




# Copyright (C) 2020-2023 ImSwitch developers
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
