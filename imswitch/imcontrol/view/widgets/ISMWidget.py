import numpy as np
import pyqtgraph as pg
from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget


class ISMWidget(NapariHybridWidget):
    """ Widget containing ISM interface. """


    sigISMShowSinglePattern = QtCore.Signal(bool)  # (enabled)
    sigISMShowLast = QtCore.Signal(bool)  # (enabled)
    sigISMStop = QtCore.Signal(bool)  # (enabled)
    sigISMStart = QtCore.Signal(bool)  # (enabled)


    sigShowToggled = QtCore.Signal(bool)  # (enabled)
    sigPIDToggled = QtCore.Signal(bool)  # (enabled)
    sigUpdateRateChanged = QtCore.Signal(float)  # (rate)
    
    sigSliderLaser1ValueChanged = QtCore.Signal(float)  # (value)

    def __post_init__(self):
        #super().__init__(*args, **kwargs)


        self.ISMFrame = pg.GraphicsLayoutWidget()
        
        # initialize all GUI elements
        
        # ROI
        self.ISMLabelROI  = QtWidgets.QLabel('ROI X(min/max), Y(min/max):')
        self.ISMValueROIxMin = QtWidgets.QLineEdit('0')
        self.ISMValueROIxMax = QtWidgets.QLineEdit('255')
        self.ISMValueROIyMin = QtWidgets.QLineEdit('0')
        self.ISMValueROIyMax = QtWidgets.QLineEdit('255')
        
        # Spacing
        self.ISMLabelSteps = QtWidgets.QLabel('STEPS (X/Y): ')
        self.ISMValueStepsX = QtWidgets.QLineEdit('25')
        self.ISMValueStepsY = QtWidgets.QLineEdit('25')
        
        # Timing
        self.ISMLabelExposure  = QtWidgets.QLabel('Laser Exposure (µs):')
        self.ISMValueExposure = QtWidgets.QLineEdit('500')
        self.ISMLabelDelay  = QtWidgets.QLabel('Laser Delay (µs):')
        self.ISMValueLabelDelay = QtWidgets.QLineEdit('500')
        
        # z-stack
        self.ISMLabelZStack  = QtWidgets.QLabel('Z-Stack (min,max,steps):')        
        self.ISMValueZmin = QtWidgets.QLineEdit('0')
        self.ISMValueZmax = QtWidgets.QLineEdit('100')
        self.ISMValueZsteps = QtWidgets.QLineEdit('10')
        
        # Laser 1
        valueDecimalsLaser = 1
        valueRangeLaser = (0,2**15)
        tickIntervalLaser = 1
        singleStepLaser = 1
        
        self.ISMLabelLaser1  = QtWidgets.QLabel('Intensity (Laser 1):')        
        
        valueRangeMinLaser, valueRangeMaxLaser = valueRangeLaser
        self.sliderLaser1 = guitools.FloatSlider(QtCore.Qt.Horizontal, self, allowScrollChanges=False,
                                        decimals=valueDecimalsLaser)
        self.sliderLaser1.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sliderLaser1.setMinimum(valueRangeMinLaser)
        self.sliderLaser1.setMaximum(valueRangeMaxLaser)
        self.sliderLaser1.setTickInterval(tickIntervalLaser)
        self.sliderLaser1.setSingleStep(singleStepLaser)
        self.sliderLaser1.setValue(0)
        
        self.sliderLaser1.valueChanged.connect(
            lambda value: self.sigSliderLaser1ValueChanged.emit(value)
        )
                        
        self.ISMLabelFileName  = QtWidgets.QLabel('FileName:')
        self.ISMEditFileName  = QtWidgets.QLineEdit('ISM')
        self.ISMNImages  = QtWidgets.QLabel('Number of images: ')

        self.ISMStartButton = guitools.BetterPushButton('Start')
        self.ISMStartButton.setCheckable(False)
        self.ISMStartButton.toggled.connect(self.sigISMStart)

        self.ISMStopButton = guitools.BetterPushButton('Stop')
        self.ISMStopButton.setCheckable(False)
        self.ISMStopButton.toggled.connect(self.sigISMStop)

        self.ISMShowLastButton = guitools.BetterPushButton('Show Last')
        self.ISMShowLastButton.setCheckable(False)
        self.ISMShowLastButton.toggled.connect(self.sigISMShowLast)

        self.ISMShowSinglePatternButton = guitools.BetterPushButton('Show Single ISM pattern')
        self.ISMShowSinglePatternButton.setCheckable(True)
        self.ISMShowSinglePatternButton.toggled.connect(self.sigISMShowSinglePattern)
        
        #self.ISMDoZStack = QtWidgets.QCheckBox('Perform Z-Stack')
        #self.ISMDoZStack.setCheckable(True)
        
        # Defining layout
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        self.grid.addWidget(self.ISMLabelROI, 0, 0, 1, 1)
        self.grid.addWidget(self.ISMValueROIxMin, 0, 1, 1, 1)
        self.grid.addWidget(self.ISMValueROIxMax, 0, 2, 1, 1)
        self.grid.addWidget(self.ISMValueROIyMax, 0, 3, 1, 1)
        self.grid.addWidget(self.ISMValueROIyMax, 0, 4, 1, 1)
        
        self.grid.addWidget(self.ISMLabelSteps, 1, 0, 1, 1)
        self.grid.addWidget(self.ISMValueStepsX, 1, 1, 1, 1)
        self.grid.addWidget(self.ISMValueStepsY, 1, 2, 1, 1)
        
        self.grid.addWidget(self.ISMLabelLaser1, 2, 0, 1, 1)
        self.grid.addWidget(self.sliderLaser1, 2, 1, 1, 3)
        
        self.grid.addWidget(self.ISMLabelExposure, 3, 0, 1, 1)
        self.grid.addWidget(self.ISMValueExposure, 3, 1, 1, 3)        
        self.grid.addWidget(self.ISMLabelDelay, 3, 2, 1, 3)        
        self.grid.addWidget(self.ISMValueLabelDelay, 3, 3, 1, 1)

        self.grid.addWidget(self.ISMLabelFileName, 4, 0, 1, 1)
        self.grid.addWidget(self.ISMEditFileName, 4, 1, 1, 1)
        self.grid.addWidget(self.ISMNImages, 4, 2, 1, 1)
        self.grid.addWidget(self.ISMStartButton, 5, 0, 1, 1)
        self.grid.addWidget(self.ISMStopButton, 5, 1, 1, 1)
        self.grid.addWidget(self.ISMShowLastButton, 5, 2, 1, 1)
        self.grid.addWidget(self.ISMShowSinglePatternButton, 5, 3, 1, 1)
        
        #self.grid.addWidget(self.ISMDoZStack, 5, 3, 1, 1)

        
        self.layer = None
        
        
    def getImage(self):
        if self.layer is not None:
            return self.img.image
        
    def setImage(self, im, colormap="gray", name=""):
        if self.layer is None or name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False, colormap=colormap, name=name, blending='additive')
        self.layer.data = im
        
    def getTimingValues(self): 
        ISMValueLabelDelay = float(self.ISMValueLabelDelay.text())
        ISMValueExposure = int(self.ISMValueExposure.text())
        return ISMValueLabelDelay, ISMValueExposure
    
    def getFilename(self):
        ISMEditFileName = self.ISMEditFileName.text()
        return ISMEditFileName
    
    def setText(self, text):
        self.ISMNImages.setText(text)
    
    
    
        
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
