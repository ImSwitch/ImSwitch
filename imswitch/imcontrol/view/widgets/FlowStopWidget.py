from qtpy import QtCore, QtWidgets


from imswitch.imcommon.view.guitools import pyqtgraphtools
from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget

import datetime

class FlowStopWidget(NapariHybridWidget):
    """ Displays the FlowStop transform of the image. """

    sigPumpDirectionToggled = QtCore.Signal(bool)  # (enabled)
    sigSnapClicked = QtCore.Signal(bool)  # (rate)
    sigSliderFocusValueChanged = QtCore.Signal(float)  # (value)
    sigSliderPumpSpeedValueChanged = QtCore.Signal(float)  # (value)
    sigSliderRotationSpeedValueChanged = QtCore.Signal(float)  # (value)
    sigExposureTimeChanged = QtCore.Signal(float)  # (value)
    sigGainChanged = QtCore.Signal(float)  # (value)
    
    def __post_init__(self):
        #super().__init__()

        # Create tabs
        self.tabs = QtWidgets.QTabWidget()
        self.tabManual = QtWidgets.QWidget()
        self.tabAuto = QtWidgets.QWidget()
        self.tabs.addTab(self.tabManual, "Manual Acquisition Settings")
        self.tabs.addTab(self.tabAuto, "Automatic Settings")

        # Create layout for the tabs
        self.tabManualLayout = QtWidgets.QGridLayout()
        self.tabAutoLayout = QtWidgets.QGridLayout()
        self.tabManual.setLayout(self.tabManualLayout)
        self.tabAuto.setLayout(self.tabAutoLayout)

        # Add widgets to Manual Acquisition tab
        self.createManualAcquisitionTab()

        # Add widgets to Automatic Settings tab
        self.createAutomaticSettingsTab()

        # Main layout
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.addWidget(self.tabs)
        
        self.setLayout(mainLayout)
        self.layer = None

        # Connect signals
        self.switchPumpDirection.toggled.connect(self.sigPumpDirectionToggled)

        self.sliderFocus.valueChanged.connect(
            lambda value: self.sigSliderFocusValueChanged.emit(value)
        )
        self.sliderPumpSpeed.valueChanged.connect(
            lambda value: self.sigSliderPumpSpeedValueChanged.emit(value)
        )
        
        self.textEditExposureTime.textChanged.connect(
            lambda value: self.sigExposureTimeChanged.emit(float(value))
        )
        
        self.textEditGain.textChanged.connect(
            lambda value: self.sigGainChanged.emit(float(value))
        )
        
        self.snapButton.clicked.connect(self.sigSnapClicked)
        
    def createManualAcquisitionTab(self):
        # TAB 1 - Manual Acquisition Settings
        self.labelFocus = QtWidgets.QLabel('Focus')
        self.labelPumpSpeed = QtWidgets.QLabel('Pump Speed')
        self.snapButton = QtWidgets.QPushButton('Snap')
        self.labelExposureTime = QtWidgets.QLabel('Exposure Time')
        self.textEditExposureTime = QtWidgets.QLineEdit("0.1")
        self.labelGain = QtWidgets.QLabel('Gain')
        self.textEditGain = QtWidgets.QLineEdit("0")
        
        self.labelMovePump = QtWidgets.QLabel('Move Pump:')
        self.labelMovePumpValue = QtWidgets.QLabel('Flowrate Pump 0 [stp\s]')
        self.textEditMovePump = QtWidgets.QLineEdit("0")
        self.pumpMovePosButton = QtWidgets.QPushButton('Move Pump +')
        self.pumpMoveNegButton = QtWidgets.QPushButton('Move Pump -')
        self.pumpMoveStopButton = QtWidgets.QPushButton('Stop Pump')
            
        # Slider to set the focus value
        valueRangeFocus = (0,100)
        tickIntervalFocus = 5
        singleStepFocus = 1
        self.sliderFocus = self.createSlider('Focus', 0, valueRangeFocus, tickIntervalFocus, singleStepFocus)
        
        # Slider to set the focus value
        valueRangePump = (300,700)
        tickIntervalPump = 1
        singleStepPump = 1
        self.sliderPumpSpeed = self.createSlider('Pump Speed', 0, valueRangePump, tickIntervalPump, singleStepPump)
            
        # Add widgets for Manual Acquisition Settings
        self.tabManualLayout.addWidget(self.labelFocus, 0, 0)
        self.tabManualLayout.addWidget(self.sliderFocus, 0, 1)
        self.tabManualLayout.addWidget(self.labelPumpSpeed, 1, 0)
        self.tabManualLayout.addWidget(self.sliderPumpSpeed, 1, 1)

        self.tabManualLayout.addWidget(self.snapButton, 2, 0)
        self.tabManualLayout.addWidget(self.labelExposureTime, 3, 0)
        self.tabManualLayout.addWidget(self.textEditExposureTime, 3, 1)
        self.tabManualLayout.addWidget(self.labelGain, 4, 0)
        self.tabManualLayout.addWidget(self.textEditGain, 4, 1)

        self.tabManualLayout.addWidget(self.labelMovePump, 5, 0)
        self.tabManualLayout.addWidget(self.labelMovePumpValue, 6, 0)
        self.tabManualLayout.addWidget(self.textEditMovePump, 6, 1)
        self.tabManualLayout.addWidget(self.pumpMovePosButton, 7, 0)
        self.tabManualLayout.addWidget(self.pumpMoveNegButton, 7, 1)
        self.tabManualLayout.addWidget(self.pumpMoveStopButton, 7, 2)

    def createAutomaticSettingsTab(self):

        # TAB 2 - Automatic Settings
        self.labelMetaData = QtWidgets.QLabel('Meta Data:')
        self.labelExperimentName = QtWidgets.QLabel('Experiment Name')
        self.textEditExperimentName = QtWidgets.QLineEdit('Test')
        self.labelExperimentDescription = QtWidgets.QLabel('Experiment Description')
        self.textEditExperimentDescription = QtWidgets.QLineEdit('Some description')
        self.labelUniqueId = QtWidgets.QLabel('Unique ID')
        self.textEditUniqueId = QtWidgets.QLineEdit('0')
        self.labelNumImages = QtWidgets.QLabel('Number of Images')
        self.textEditNumImages = QtWidgets.QLineEdit('100')
        self.labelVolumePerImage = QtWidgets.QLabel('Volume per Image (ml)')
        self.textEditVolumePerImage = QtWidgets.QLineEdit('1')
        self.labelTimeToStabilize = QtWidgets.QLabel('Time to Stabilize')
        self.textEditTimeToStabilize = QtWidgets.QLineEdit('0.5')
        self.labelPumpSpeed = QtWidgets.QLabel('Pump Speed')
        self.textEditPumpSpeed = QtWidgets.QLineEdit('1000')
        
        self.labelExperimentalSettings = QtWidgets.QLabel('Experimental Settings:')
        self.switchPumpDirection = QtWidgets.QPushButton('Switch Pump Direction')
        self.buttonStart = QtWidgets.QPushButton('Start')
        self.buttonStop = QtWidgets.QPushButton('Stop')
        
        self.labelStatus = QtWidgets.QLabel('Status:')
        self.labelStatusValue = QtWidgets.QLabel('Stopped')
        
        # Add widgets for Automatic Settings
        self.tabAutoLayout.addWidget(self.labelMetaData, 0, 0)
        self.tabAutoLayout.addWidget(self.labelExperimentName, 1, 0)
        self.tabAutoLayout.addWidget(self.textEditExperimentName, 1, 1)
        self.tabAutoLayout.addWidget(self.labelExperimentDescription, 2, 0)
        self.tabAutoLayout.addWidget(self.textEditExperimentDescription, 2, 1)
        self.tabAutoLayout.addWidget(self.labelUniqueId, 3, 0)
        self.tabAutoLayout.addWidget(self.textEditUniqueId, 3, 1)
        self.tabAutoLayout.addWidget(self.labelNumImages, 4, 0)
        self.tabAutoLayout.addWidget(self.textEditNumImages, 4, 1)
        self.tabAutoLayout.addWidget(self.labelVolumePerImage, 5, 0)
        self.tabAutoLayout.addWidget(self.textEditVolumePerImage, 5, 1)
        self.tabAutoLayout.addWidget(self.labelTimeToStabilize, 6, 0)
        self.tabAutoLayout.addWidget(self.textEditTimeToStabilize, 6, 1)
        self.tabAutoLayout.addWidget(self.labelPumpSpeed, 7, 0)
        self.tabAutoLayout.addWidget(self.textEditPumpSpeed, 7, 1)

        self.tabAutoLayout.addWidget(self.labelExperimentalSettings, 8, 0)
        self.tabAutoLayout.addWidget(self.switchPumpDirection, 9, 0)
        self.tabAutoLayout.addWidget(self.buttonStart, 10, 0)
        self.tabAutoLayout.addWidget(self.buttonStop, 10, 1)

        self.tabAutoLayout.addWidget(self.labelStatus, 12, 0)
        #self.tabAutoLayout.addWidget(self.label)

    def setStatus(self, status):
        self.labelStatusValue.setText(status)
        
    def createSlider(self, label, value, valueRange, tickInterval, singleStep):
        slider = guitools.FloatSlider(QtCore.Qt.Horizontal, self, allowScrollChanges=False,
                                        decimals=1)
        slider.setFocusPolicy(QtCore.Qt.NoFocus)
        valueRangeMin, valueRangeMax = valueRange

        slider.setMinimum(valueRangeMin)
        slider.setMaximum(valueRangeMax)
        slider.setTickInterval(tickInterval)
        slider.setSingleStep(singleStep)
        slider.setValue(value)
        return slider

    def getAutomaticImagingParameters(self):
        """ Returns the automatic imaging parameters. """
        return {
            'timeStamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'experimentName': self.textEditExperimentName.text(),
            'experimentDescription': self.textEditExperimentDescription.text(),
            'uniqueId': self.textEditUniqueId.text(),
            'numImages': self.textEditNumImages.text(),
            'volumePerImage': self.textEditVolumePerImage.text(),
            'timeToStabilize': self.textEditTimeToStabilize.text(),
            'pumpSpeed': self.textEditPumpSpeed.text(),
        }
        
    def getImage(self):
        if self.layer is not None:
            return self.img.image

    def setImage(self, im):
        if self.layer is None or self.layer.name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False, name="FlowStop", blending='additive')
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
