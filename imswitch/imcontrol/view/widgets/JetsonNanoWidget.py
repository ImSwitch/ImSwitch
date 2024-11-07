import numpy as np
import pyqtgraph as pg
from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget


class JetsonNanoWidget(NapariHybridWidget):
    """ Widget containing jetsonnano interface. """


    sigJetsonNanoInitFilterPos = QtCore.Signal(bool)  # (enabled)
    sigJetsonNanoShowLast = QtCore.Signal(bool)  # (enabled)
    sigJetsonNanoStop = QtCore.Signal(bool)  # (enabled)
    sigJetsonNanoStart = QtCore.Signal(bool)  # (enabled)
    sigJetsonNanoSelectScanCoordinates = QtCore.Signal(bool)

    sigShowToggled = QtCore.Signal(bool)  # (enabled)
    sigPIDToggled = QtCore.Signal(bool)  # (enabled)
    sigUpdateRateChanged = QtCore.Signal(float)  # (rate)
    
    sigSliderLaser2ValueChanged = QtCore.Signal(float)  # (value)
    sigSliderLaser1ValueChanged = QtCore.Signal(float)  # (value)
    sigSliderLEDValueChanged = QtCore.Signal(float)  # (value)

    def __post_init__(self):
        #super().__init__(*args, **kwargs)
        self.jetsonnanoFrame = pg.GraphicsLayoutWidget()
        
        
        '''
        setup the GUI 
        '''
        # Main GUI 
        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

        # Side TabView
        self.tabWidget = QtWidgets.QTabWidget(self)
        self.layout.addWidget(self.tabWidget, 0)
        
        #self.tabWidget.setGeometry(80, 90, 221, 311)
        self.tabWidget.setCurrentIndex(1)
        
        # Tab 1: Acquire
        self.tab = QtWidgets.QWidget()
        self.tabWidget.addTab(self.tab, "Acquire")
        
        self.verticalLayoutWidget = QtWidgets.QWidget(self.tab)
        self.verticalLayoutWidget.setGeometry(20, 20, 160, 233)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.gridLayout = QtWidgets.QGridLayout()
        self.verticalLayout.addLayout(self.gridLayout)
        
        self.pushButtonFocusUp = QtWidgets.QPushButton("++")
        self.gridLayout.addWidget(self.pushButtonFocusUp, 0, 0)
        
        self.pushButtonAutofocus = QtWidgets.QPushButton("AF")
        self.gridLayout.addWidget(self.pushButtonAutofocus, 1, 0)
        
        self.pushButtonIlluOn = QtWidgets.QPushButton("On")
        self.gridLayout.addWidget(self.pushButtonIlluOn, 0, 1)
        
        self.pushButtonIlluOff = QtWidgets.QPushButton("Off")
        self.gridLayout.addWidget(self.pushButtonIlluOff, 1, 1)
        
        self.pushButtonFocusDown = QtWidgets.QPushButton("--")
        self.gridLayout.addWidget(self.pushButtonFocusDown, 2, 0)
        
        self.labelIlluValue = QtWidgets.QLabel("TextLabel")
        self.verticalLayout.addWidget(self.labelIlluValue)
        
        self.sliderIllu = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.verticalLayout.addWidget(self.sliderIllu)
        
        self.pushButtonSnap = QtWidgets.QPushButton("SNAP!")
        self.verticalLayout.addWidget(self.pushButtonSnap)
        
        self.pushButtonRec = QtWidgets.QPushButton("REC!")
        self.verticalLayout.addWidget(self.pushButtonRec)
        
        # Tab 2: Settings
        self.tab_2 = QtWidgets.QWidget()
        self.tabWidget.addTab(self.tab_2, "Settings")
        
        self.gridLayoutWidget_3 = QtWidgets.QWidget(self.tab_2)
        self.gridLayoutWidget_3.setGeometry(20, 20, 204, 162)
        self.gridLayout_3 = QtWidgets.QGridLayout(self.gridLayoutWidget_3)
        
        self.labelExposureTime = QtWidgets.QLabel("Exposure Time")
        self.gridLayout_3.addWidget(self.labelExposureTime, 0, 0)
        self.spinBoxExposure = QtWidgets.QSpinBox()
        self.spinBoxExposure.setMinimum(0)
        self.spinBoxExposure.setMaximum(100000000)
        self.gridLayout_3.addWidget(self.spinBoxExposure, 0, 1)
        
        self.labelGain = QtWidgets.QLabel("Gain")
        self.gridLayout_3.addWidget(self.labelGain, 1, 0)
        self.spinBoxGain = QtWidgets.QSpinBox()
        self.spinBoxGain.setMinimum(0)
        self.spinBoxGain.setMaximum(23)
        self.gridLayout_3.addWidget(self.spinBoxGain, 1, 1)
        
        self.labelBlackelvel = QtWidgets.QLabel("Blacklevel")
        self.gridLayout_3.addWidget(self.labelBlackelvel, 2, 0)
        self.spinBoxBlacklevel = QtWidgets.QSpinBox()
        self.gridLayout_3.addWidget(self.spinBoxBlacklevel,2,1)
        
        self.checkBoxAutosettings = QtWidgets.QCheckBox("Auto Settings")
        self.gridLayout_3.addWidget(self.checkBoxAutosettings, 3, 0)
        

        
        # initialize all GUI elements
        '''
        old settings
        '''
        # period
        self.grid = QtWidgets.QGridLayout()


        self.jetsonnanoLabelTimePeriod  = QtWidgets.QLabel('Period T (s):')
        self.jetsonnanoValueTimePeriod = QtWidgets.QLineEdit('5')
        
        # duration
        self.jetsonnanoLabelTimeDuration  = QtWidgets.QLabel('N Measurements:')
        self.jetsonnanoValueTimeDuration = QtWidgets.QLineEdit('1')
        
        # z-stack
        self.jetsonnanoLabelZStack  = QtWidgets.QLabel('Z-Stack (min,max,steps):')        
        self.jetsonnanoValueZmin = QtWidgets.QLineEdit('-100')
        self.jetsonnanoValueZmax = QtWidgets.QLineEdit('100')
        self.jetsonnanoValueZsteps = QtWidgets.QLineEdit('10')
        
        # xy-scanning
        self.jetsonnanoLabelXScan  = QtWidgets.QLabel('X Scan (min,max,steps):')        
        self.jetsonnanoValueXmin = QtWidgets.QLineEdit('-1000')
        self.jetsonnanoValueXmax = QtWidgets.QLineEdit('1000')
        self.jetsonnanoValueXsteps = QtWidgets.QLineEdit('100')
        
        self.jetsonnanoLabelYScan  = QtWidgets.QLabel('Y Scan (min,max,steps):')        
        self.jetsonnanoValueYmin = QtWidgets.QLineEdit('-1000')
        self.jetsonnanoValueYmax = QtWidgets.QLineEdit('1000')
        self.jetsonnanoValueYsteps = QtWidgets.QLineEdit('100')
        
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
        
        self.layer = None
        
        
    
    def setImage(self, im, colormap="gray", name="", pixelsize=(1,1,1), translation=(0,0,0)):
        if len(im.shape) == 2:
            translation = (translation[0], translation[1])
        if self.layer is None or name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False, colormap=colormap, 
                                               scale=pixelsize,translate=translation,
                                               name=name, blending='opaque')
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
