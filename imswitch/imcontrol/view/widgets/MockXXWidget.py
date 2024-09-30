import numpy as np
import pyqtgraph as pg
from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget


class MockXXWidget(NapariHybridWidget):
    """ Widget containing MockXX interface. """


    sigMockXXInitFilterPos = QtCore.Signal(bool)  # (enabled)
    sigMockXXShowLast = QtCore.Signal(bool)  # (enabled)
    sigMockXXStop = QtCore.Signal(bool)  # (enabled)
    sigMockXXStart = QtCore.Signal(bool)  # (enabled)
    sigMockXXSelectScanCoordinates = QtCore.Signal(bool)


    sigShowToggled = QtCore.Signal(bool)  # (enabled)
    sigPIDToggled = QtCore.Signal(bool)  # (enabled)
    sigUpdateRateChanged = QtCore.Signal(float)  # (rate)
    
    
    sigSliderLaser2ValueChanged = QtCore.Signal(float)  # (value)
    sigSliderLaser1ValueChanged = QtCore.Signal(float)  # (value)
    sigSliderLEDValueChanged = QtCore.Signal(float)  # (value)

    def __post_init__(self):
        #super().__init__(*args, **kwargs)


        self.MockXXFrame = pg.GraphicsLayoutWidget()
        
        # initialize all GUI elements
        
        # period
        self.MockXXLabelTimePeriod  = QtWidgets.QLabel('Period T (s):')
        self.MockXXValueTimePeriod = QtWidgets.QLineEdit('5')
        
        # duration
        self.MockXXLabelTimeDuration  = QtWidgets.QLabel('N Measurements:')
        self.MockXXValueTimeDuration = QtWidgets.QLineEdit('1')
        
        # z-stack
        self.MockXXLabelZStack  = QtWidgets.QLabel('Z-Stack (min,max,steps):')        
        self.MockXXValueZmin = QtWidgets.QLineEdit('-100')
        self.MockXXValueZmax = QtWidgets.QLineEdit('100')
        self.MockXXValueZsteps = QtWidgets.QLineEdit('10')
        
        # xy-scanning
        self.MockXXLabelXScan  = QtWidgets.QLabel('X Scan (min,max,steps):')        
        self.MockXXValueXmin = QtWidgets.QLineEdit('-1000')
        self.MockXXValueXmax = QtWidgets.QLineEdit('1000')
        self.MockXXValueXsteps = QtWidgets.QLineEdit('100')
        
        self.MockXXLabelYScan  = QtWidgets.QLabel('Y Scan (min,max,steps):')        
        self.MockXXValueYmin = QtWidgets.QLineEdit('-1000')
        self.MockXXValueYmax = QtWidgets.QLineEdit('1000')
        self.MockXXValueYsteps = QtWidgets.QLineEdit('100')
        
        # autofocus
        self.autofocusLabel = QtWidgets.QLabel('Autofocus (range, steps, every n-th measurement): ')        
        self.autofocusRange = QtWidgets.QLineEdit('200')
        self.autofocusSteps = QtWidgets.QLineEdit('20')
        self.autofocusPeriod = QtWidgets.QLineEdit('10')
        
        self.autofocusLaser1Checkbox = QtWidgets.QCheckBox('Laser 1')
        self.autofocusLaser1Checkbox.setCheckable(True)
        
        self.autofocusLaser2Checkbox = QtWidgets.QCheckBox('Laser 2')
        self.autofocusLaser2Checkbox.setCheckable(True)
        
        self.autofocusLED1Checkbox = QtWidgets.QCheckBox('LED 1')
        self.autofocusLED1Checkbox.setCheckable(True)
        
        self.autofocusSelectionLabel = QtWidgets.QLabel('Lightsource for AF:')        
        
        
        # Laser 1
        valueDecimalsLaser = 1
        valueRangeLaser = (0,2**15)
        tickIntervalLaser = 1
        singleStepLaser = 1
        
        self.sliderLaser1, self.MockXXLabelLaser1 = self.setupSliderGui('Intensity (Laser 1):', valueDecimalsLaser, valueRangeLaser, tickIntervalLaser, singleStepLaser)
        self.sliderLaser1.valueChanged.connect(
            lambda value: self.sigSliderLaser1ValueChanged.emit(value)
        )
        
        self.sliderLaser2, self.MockXXLabelLaser2 = self.setupSliderGui('Intensity (Laser 2):', valueDecimalsLaser, valueRangeLaser, tickIntervalLaser, singleStepLaser)
        self.sliderLaser2.valueChanged.connect(
            lambda value: self.sigSliderLaser2ValueChanged.emit(value)
        )
                        
        # LED
        valueDecimalsLED = 1
        valueRangeLED = (0,2**8)
        tickIntervalLED = 1
        singleStepLED = 1
        
        self.sliderLED, self.MockXXLabelLED = self.setupSliderGui('Intensity (LED):', valueDecimalsLED, valueRangeLED, tickIntervalLED, singleStepLED)
        self.sliderLED.valueChanged.connect(
            lambda value: self.sigSliderLEDValueChanged.emit(value)
        )
        
        self.MockXXLabelFileName  = QtWidgets.QLabel('FileName:')
        self.MockXXEditFileName  = QtWidgets.QLineEdit('MockXX')
        self.MockXXNImages  = QtWidgets.QLabel('Number of images: ')

        # loading scan position list
        self.MockXXLabelScanPositionList = QtWidgets.QLabel("Scan Position List:")
        self.MockXXSelectScanPositionList = guitools.BetterPushButton('Select XY Coordinates')
        self.MockXXSelectScanPositionList.setCheckable(True)
        self.MockXXSelectScanPositionList.toggled.connect(self.sigMockXXSelectScanCoordinates)

        # Start scan
        self.MockXXStartButton = guitools.BetterPushButton('Start')
        self.MockXXStartButton.setCheckable(False)
        self.MockXXStartButton.toggled.connect(self.sigMockXXStart)

        self.MockXXStopButton = guitools.BetterPushButton('Stop')
        self.MockXXStopButton.setCheckable(False)
        self.MockXXStopButton.toggled.connect(self.sigMockXXStop)

        self.MockXXShowLastButton = guitools.BetterPushButton('Show Last')
        self.MockXXShowLastButton.setCheckable(False)
        self.MockXXShowLastButton.toggled.connect(self.sigMockXXShowLast)

        self.MockXXInitFilterButton = guitools.BetterPushButton('Init Filter Pos.')
        self.MockXXInitFilterButton.setCheckable(False)
        self.MockXXInitFilterButton.toggled.connect(self.sigMockXXInitFilterPos)
        
        self.MockXXDoZStack = QtWidgets.QCheckBox('Perform Z-Stack')
        self.MockXXDoZStack.setCheckable(True)
        
        self.MockXXDoXYScan = QtWidgets.QCheckBox('Perform XY Scan')
        self.MockXXDoXYScan.setCheckable(True)
        
        
        # Defining layout
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        self.grid.addWidget(self.MockXXLabelTimePeriod, 0, 0, 1, 1)
        self.grid.addWidget(self.MockXXValueTimePeriod, 0, 1, 1, 1)
        self.grid.addWidget(self.MockXXLabelTimeDuration, 0, 2, 1, 1)
        self.grid.addWidget(self.MockXXValueTimeDuration, 0, 3, 1, 1)
        #z-stack
        self.grid.addWidget(self.MockXXLabelZStack, 1, 0, 1, 1)
        self.grid.addWidget(self.MockXXValueZmin, 1, 1, 1, 1)
        self.grid.addWidget(self.MockXXValueZmax, 1, 2, 1, 1)
        self.grid.addWidget(self.MockXXValueZsteps, 1, 3, 1, 1)
        
        #xy-scanning
        self.grid.addWidget(self.MockXXLabelXScan, 2, 0, 1, 1)
        self.grid.addWidget(self.MockXXValueXmin, 2, 1, 1, 1)
        self.grid.addWidget(self.MockXXValueXmax, 2, 2, 1, 1)
        self.grid.addWidget(self.MockXXValueXsteps, 2, 3, 1, 1)

        self.grid.addWidget(self.MockXXLabelYScan, 3, 0, 1, 1)
        self.grid.addWidget(self.MockXXValueYmin, 3, 1, 1, 1)
        self.grid.addWidget(self.MockXXValueYmax, 3, 2, 1, 1)
        self.grid.addWidget(self.MockXXValueYsteps, 3, 3, 1, 1)

        self.grid.addWidget(self.MockXXLabelLaser1, 4, 0, 1, 1)
        self.grid.addWidget(self.sliderLaser1, 4, 1, 1, 3)
        self.grid.addWidget(self.MockXXLabelLaser2, 5, 0, 1, 1)
        self.grid.addWidget(self.sliderLaser2, 5, 1, 1, 3)        
        self.grid.addWidget(self.MockXXLabelLED, 6, 0, 1, 1)
        self.grid.addWidget(self.sliderLED, 6, 1, 1, 3)

        # filesettings
        self.grid.addWidget(self.MockXXLabelFileName, 7, 0, 1, 1)
        self.grid.addWidget(self.MockXXEditFileName, 7, 1, 1, 1)
        self.grid.addWidget(self.MockXXNImages, 7, 2, 1, 1)
        self.grid.addWidget(self.MockXXDoZStack, 7, 3, 1, 1)
        
        # autofocus
        self.grid.addWidget(self.autofocusLabel, 8, 0, 1, 1)
        self.grid.addWidget(self.autofocusRange, 8, 1, 1, 1)
        self.grid.addWidget(self.autofocusSteps, 8, 2, 1, 1)
        self.grid.addWidget(self.autofocusPeriod, 8, 3, 1, 1)
        
        self.grid.addWidget(self.autofocusSelectionLabel, 9, 0, 1, 1)        
        self.grid.addWidget(self.autofocusLaser1Checkbox, 9, 1, 1, 1)
        self.grid.addWidget(self.autofocusLaser2Checkbox, 9, 2, 1, 1)
        self.grid.addWidget(self.autofocusLED1Checkbox, 9, 3, 1, 1)

        # start stop
        self.grid.addWidget(self.MockXXStartButton, 10, 0, 1, 1)
        self.grid.addWidget(self.MockXXStopButton, 10, 1, 1, 1)
        self.grid.addWidget(self.MockXXShowLastButton, 10, 2, 1, 1)
        self.grid.addWidget(self.MockXXDoXYScan, 10, 3, 1, 1)
        # self.grid.addWidget(self.MockXXInitFilterButton,8, 3, 1, 1)
        
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
        MockXXLabel  = QtWidgets.QLabel(label)     
        valueRangeMin, valueRangeMax = valueRange
        slider = guitools.FloatSlider(QtCore.Qt.Horizontal, self, allowScrollChanges=False,
                                        decimals=valueDecimals)
        slider.setFocusPolicy(QtCore.Qt.NoFocus)
        slider.setMinimum(valueRangeMin)
        slider.setMaximum(valueRangeMax)
        slider.setTickInterval(tickInterval)
        slider.setSingleStep(singleStep)
        slider.setValue(0)
        return slider, MockXXLabel
        
    def getImage(self):
        if self.layer is not None:
            return self.img.image
        
    def setImage(self, im, colormap="gray", name="", pixelsize=(1,1,1), translation=(0,0,0)):
        if len(im.shape) == 2:
            translation = (translation[0], translation[1])
        if self.layer is None or name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False, colormap=colormap, 
                                               scale=pixelsize,translate=translation,
                                               name=name, blending='additive')
        self.layer.data = im
        
        
    def getZStackValues(self):
        valueZmin = -abs(float(self.MockXXValueZmin.text()))
        valueZmax = float(self.MockXXValueZmax.text())
        valueZsteps = float(self.MockXXValueZsteps.text())
        valueZenabled = bool(self.MockXXDoZStack.isChecked())
        
        return valueZmin, valueZmax, valueZsteps, valueZenabled
 
 
    def getXYScanValues(self):
        valueXmin = -abs(float(self.MockXXValueXmin.text()))
        valueXmax = float(self.MockXXValueXmax.text())
        valueXsteps = float(self.MockXXValueXsteps.text())
        
        valueYmin = -abs(float(self.MockXXValueYmin.text()))
        valueYmax = float(self.MockXXValueYmax.text())
        valueYsteps = float(self.MockXXValueYsteps.text())
        
        valueXYenabled = bool(self.MockXXDoXYScan.isChecked())
        
        return valueXmin, valueXmax, valueXsteps, valueYmin, valueYmax, valueYsteps, valueXYenabled
 
 
    def getTimelapseValues(self):
        MockXXValueTimePeriod = float(self.MockXXValueTimePeriod.text())
        MockXXValueTimeDuration = int(self.MockXXValueTimeDuration.text())
        return MockXXValueTimePeriod, MockXXValueTimeDuration
    
    def getFilename(self):
        MockXXEditFileName = self.MockXXEditFileName.text()
        return MockXXEditFileName
    
    def setMessageGUI(self, nImages):
        nImages2Do = self.getTimelapseValues()[-1]
        self.MockXXNImages.setText('Number of images: '+str(nImages) + " / " + str(nImages2Do))
    
    
    
        
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
