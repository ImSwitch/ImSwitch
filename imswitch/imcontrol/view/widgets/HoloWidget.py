import pyqtgraph as pg
from qtpy import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from imswitch.imcommon.view.guitools import pyqtgraphtools
from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget


class HoloWidget(NapariHybridWidget):
    """ Displays the Holo transform of the image. """

    sigShowToggled = QtCore.Signal(bool)  # (enabled)
    sigUpdateRateChanged = QtCore.Signal(float)  # (rate)
    sigInLineSliderValueChanged = QtCore.Signal(float)  # (value)
    sigOffAxisSliderValueChanged = QtCore.Signal(float)  # (value)
    sigShowInLineToggled = QtCore.Signal(bool)  # (enabled)
    sigShowOffAxisToggled = QtCore.Signal(bool)  # (enabled)

    def __post_init__(self):

        # Graphical elements
        
        self.tabs = QTabWidget()

        self.tab_inlineholo = QtWidgets.QWidget()
        self.tab_offaxisholo = QtWidgets.QWidget()
        self.tab_generalsettings = QtWidgets.QWidget()
        self.tabs.addTab(self.tab_inlineholo, "Inline Holo")
        self.tabs.addTab(self.tab_offaxisholo, "Off-axis Holo")
        self.tabs.addTab(self.tab_generalsettings, "General Settings")
        
        # add all tabs to the main window
        self.init_ui()
        
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.addWidget(self.tabs)
        self.setLayout(mainLayout)      
        
    def init_ui(self):
        self.init_inlineholo_tab()
        self.init_offaxisholo_tab()
        self.init_generalsettings_tab()
        self.setGeometry(300, 300, 300, 200)
    
    def init_offaxisholo_tab(self):
        self.showCheckOffAxis = QtWidgets.QCheckBox('Show OffAxis Holo')
        self.showCheckOffAxis.setCheckable(True)

        # Slider for OffAxis focus
        valueDecimals = 1
        valueRange = (250,250)
        tickInterval = 5
        singleStep = 1

        self.btnSelectCCCenter = QtWidgets.QPushButton('Select Center')
        self.labelCCCenter = QtWidgets.QLabel('CC Center: ')
        self.textEditCCCenterX = QtWidgets.QLineEdit('0')
        self.textEditCCCenterY = QtWidgets.QLineEdit('0')
        self.labelCCRadius = QtWidgets.QLabel('CC Radius: ')
        self.textEditCCRadius = QtWidgets.QLineEdit('100')
        
        self.labelOffAxisFocus = QtWidgets.QLabel('OffAxis Focus')
        self.sliderOffAxisFocus = guitools.FloatSlider(QtCore.Qt.Horizontal, self, allowScrollChanges=False,
                                           decimals=valueDecimals)
        self.sliderOffAxisFocus.setFocusPolicy(QtCore.Qt.NoFocus)
        valueRangeMin, valueRangeMax = valueRange        
        self.sliderOffAxisFocus.setMinimum(valueRangeMin)
        self.sliderOffAxisFocus.setMaximum(valueRangeMax)
        self.sliderOffAxisFocus.setTickInterval(tickInterval)
        self.sliderOffAxisFocus.setSingleStep(singleStep)
        self.sliderOffAxisFocus.setValue(0)

        # Add elements to GridLayout
        grid = QtWidgets.QGridLayout()
        grid.addWidget(self.btnSelectCCCenter, 0, 0, 1, 1)
        grid.addWidget(self.labelCCCenter, 0, 1, 1, 1)
        grid.addWidget(self.textEditCCCenterX, 0, 2, 1, 1)
        grid.addWidget(self.textEditCCCenterY, 0, 3, 1, 1)
        grid.addWidget(self.labelCCRadius, 1, 0, 1, 1)
        grid.addWidget(self.textEditCCRadius, 1, 1, 1, 1)
        
        grid.addWidget(self.showCheckOffAxis, 2, 0, 1, 1)
        grid.addWidget(self.labelOffAxisFocus, 3, 0, 1, 1)
        grid.addWidget(self.sliderOffAxisFocus, 3, 1, 1, 1)

        # Connect signals
        self.showCheckOffAxis.toggled.connect(self.sigShowOffAxisToggled)
        self.sliderOffAxisFocus.valueChanged.connect(
            lambda value: self.sigOffAxisSliderValueChanged.emit(value)
        )
        
        # grid.setRowMinimumHeight(0, 300)
        self.tab_offaxisholo.setLayout(grid)
    
    def init_inlineholo_tab(self):
        self.showCheckInLine = QtWidgets.QCheckBox('Show InLine Holo')
        self.showCheckInLine.setCheckable(True)

        valueDecimals = 1
        valueRange = (0,500)
        tickInterval = 5
        singleStep = 1
        self.sliderInLineFocus = guitools.FloatSlider(QtCore.Qt.Horizontal, self, allowScrollChanges=False,
                                           decimals=valueDecimals)
        self.sliderInLineFocus.setFocusPolicy(QtCore.Qt.NoFocus)
        valueRangeMin, valueRangeMax = valueRange

        self.sliderInLineFocus.setMinimum(valueRangeMin)
        self.sliderInLineFocus.setMaximum(valueRangeMax)
        self.sliderInLineFocus.setTickInterval(tickInterval)
        self.sliderInLineFocus.setSingleStep(singleStep)
        self.sliderInLineFocus.setValue(0)

        # Add elements to GridLayout
        grid = QtWidgets.QGridLayout()

        # Connect signals
        self.showCheckInLine.toggled.connect(self.sigShowInLineToggled)
        self.sliderInLineFocus.valueChanged.connect(
            lambda value: self.sigOffAxisSliderValueChanged.emit(value)
        )
        self.layer = None
        grid.addWidget(self.showCheckInLine, 1, 0, 1, 1)
        grid.addWidget(self.sliderInLineFocus, 2, 0, 1, 1)
        
        
        self.tab_inlineholo.setLayout(grid)

    def silenceLayer(self, name, enabled):
        """Change visibility of layer without emitting signal."""
        if name in self.viewer.layers:
            self.viewer.layers[name].visible = enabled
                
    def init_generalsettings_tab(self):
        self.lineRate = QtWidgets.QLineEdit('2')
        self.labelRate = QtWidgets.QLabel('Update rate')
        self.wvlLabel = QtWidgets.QLabel('Wavelength [um]')
        self.wvlEdit = QtWidgets.QLineEdit('0.488')
        self.pixelSizeLabel = QtWidgets.QLabel('Pixel size [um]')
        self.pixelSizeEdit = QtWidgets.QLineEdit('3.45')
        self.naLabel = QtWidgets.QLabel('NA')
        self.naEdit = QtWidgets.QLineEdit('0.3')
        
        grid = QtWidgets.QGridLayout()
        grid.addWidget(self.wvlLabel, 0, 0, 1, 1)
        grid.addWidget(self.wvlEdit, 0, 1, 1, 1)
        grid.addWidget(self.pixelSizeLabel, 1, 0, 1, 1)
        grid.addWidget(self.pixelSizeEdit, 1, 1, 1, 1)
        grid.addWidget(self.naLabel, 2, 0, 1, 1)
        grid.addWidget(self.naEdit, 2, 1, 1, 1)
        grid.addWidget(self.sliderInLineFocus, 3, 1, 1, 1)
        grid.addWidget(self.labelRate, 3, 2, 1, 1)
        grid.addWidget(self.lineRate, 3, 3, 1, 1)
        
        self.lineRate.textChanged.connect(
            lambda: self.sigUpdateRateChanged.emit(self.getUpdateRate())
        )
        self.tab_generalsettings.setLayout(grid)
        
        
    def getWvl(self):
        return float(self.wvlEdit.text())

    def getPixelSize(self):
        return float(self.pixelSizeEdit.text())

    def getNA(self):
        return float(self.naEdit.text())

    def getShowInLineHoloChecked(self):
        return self.showCheckInLine.isChecked()

    def getShowOffAxisHoloChecked(self):
        return self.showCheckOffAxis.isChecked()
    
    def getUpdateRate(self):
        return float(self.lineRate.text())

    def getImage(self):
        if self.layer is not None:
            return self.img.image

    def setImage(self, im, name="Holo"):
        if name not in self.viewer.layers:
            self.viewer.add_image(im, rgb=False, name=name, blending='additive')
        else:
            self.viewer.layers[name].data = im

    def getCCCenterFromNapari(self):
        """ Get the center of the cross correlation from the napari viewer. """
        if not "Center of Cross Correlation" in self.viewer.layers:
            return [0, 0]
        CCCenter = self.viewer.layers['Center of Cross Correlation'].data[0]
        # set in gui 
        self.textEditCCCenterX.setText(str(int(CCCenter[0])))
        self.textEditCCCenterY.setText(str(int(CCCenter[1])))
        return CCCenter

    def createPointsLayer(self):
        if "Center of Cross Correlation" in self.viewer.layers:
            self.viewer.layers.remove('Center of Cross Correlation')
        self.viewer.add_points(size=10, face_color='red', name='Center of Cross Correlation')
        
    def getCCRadius(self):
        return float(self.textEditCCRadius.text())
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
