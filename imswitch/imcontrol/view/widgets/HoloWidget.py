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
    sigSliderValueChanged = QtCore.Signal(float)  # (value)

    def __post_init__(self):

        # Graphical elements
        
        self.tabs = QTabWidget()

        self.tab_inlineholo = QtWidgets.QWidget()
        self.tab_offaxisholo = QtWidgets.QWidget()
        self.tabs.addTab(self.tab_inlineholo, "Inline Holo")
        self.tabs.addTab(self.tab_offaxisholo, "Off-axis Holo")
        
        # add all tabs to the main window
        self.init_ui()
        
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.addWidget(self.tabs)
        self.setLayout(mainLayout)      
        
    def init_ui(self):
        self.init_inlineholo_tab()
        self.init_offaxisholo_tab()
        self.setGeometry(300, 300, 300, 200)
    
    def init_offaxisholo_tab(self):
        self.showCheck = QtWidgets.QCheckBox('Show Holo')
        self.showCheck.setCheckable(True)
        self.lineRate = QtWidgets.QLineEdit('0')
        self.labelRate = QtWidgets.QLabel('Update rate')
        self.wvlLabel = QtWidgets.QLabel('Wavelength [um]')
        self.wvlEdit = QtWidgets.QLineEdit('0.488')
        self.pixelSizeLabel = QtWidgets.QLabel('Pixel size [um]')
        self.pixelSizeEdit = QtWidgets.QLineEdit('3.45')
        self.naLabel = QtWidgets.QLabel('NA')
        self.naEdit = QtWidgets.QLineEdit('0.3')

        valueDecimals = 1
        valueRange = (0,500)
        tickInterval = 5
        singleStep = 1
        self.slider = guitools.FloatSlider(QtCore.Qt.Horizontal, self, allowScrollChanges=False,
                                           decimals=valueDecimals)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        valueRangeMin, valueRangeMax = valueRange

        self.slider.setMinimum(valueRangeMin)
        self.slider.setMaximum(valueRangeMax)
        self.slider.setTickInterval(tickInterval)
        self.slider.setSingleStep(singleStep)
        self.slider.setValue(0)

        # Add elements to GridLayout
        grid = QtWidgets.QGridLayout()
        grid.addWidget(self.wvlLabel, 0, 0, 1, 1)
        grid.addWidget(self.wvlEdit, 0, 1, 1, 1)
        grid.addWidget(self.pixelSizeLabel, 1, 0, 1, 1)
        grid.addWidget(self.pixelSizeEdit, 1, 1, 1, 1)
        grid.addWidget(self.naLabel, 2, 0, 1, 1)
        grid.addWidget(self.naEdit, 2, 1, 1, 1)
        grid.addWidget(self.showCheck, 3, 0, 1, 1)
        grid.addWidget(self.slider, 3, 1, 1, 1)
        grid.addWidget(self.labelRate, 3, 2, 1, 1)
        grid.addWidget(self.lineRate, 3, 3, 1, 1)

        # grid.setRowMinimumHeight(0, 300)
        self.tab_offaxisholo.setLayout(grid)
    
    def init_inlineholo_tab(self):
        
        self.showCheck = QtWidgets.QCheckBox('Show Holo')
        self.showCheck.setCheckable(True)
        self.lineRate = QtWidgets.QLineEdit('0')
        self.labelRate = QtWidgets.QLabel('Update rate')
        self.wvlLabel = QtWidgets.QLabel('Wavelength [um]')
        self.wvlEdit = QtWidgets.QLineEdit('0.488')
        self.pixelSizeLabel = QtWidgets.QLabel('Pixel size [um]')
        self.pixelSizeEdit = QtWidgets.QLineEdit('3.45')
        self.naLabel = QtWidgets.QLabel('NA')
        self.naEdit = QtWidgets.QLineEdit('0.3')

        valueDecimals = 1
        valueRange = (0,500)
        tickInterval = 5
        singleStep = 1
        self.slider = guitools.FloatSlider(QtCore.Qt.Horizontal, self, allowScrollChanges=False,
                                           decimals=valueDecimals)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        valueRangeMin, valueRangeMax = valueRange

        self.slider.setMinimum(valueRangeMin)
        self.slider.setMaximum(valueRangeMax)
        self.slider.setTickInterval(tickInterval)
        self.slider.setSingleStep(singleStep)
        self.slider.setValue(0)

        # Add elements to GridLayout
        grid = QtWidgets.QGridLayout()
        grid.addWidget(self.wvlLabel, 0, 0, 1, 1)
        grid.addWidget(self.wvlEdit, 0, 1, 1, 1)
        grid.addWidget(self.pixelSizeLabel, 1, 0, 1, 1)
        grid.addWidget(self.pixelSizeEdit, 1, 1, 1, 1)
        grid.addWidget(self.naLabel, 2, 0, 1, 1)
        grid.addWidget(self.naEdit, 2, 1, 1, 1)
        grid.addWidget(self.showCheck, 3, 0, 1, 1)
        grid.addWidget(self.slider, 3, 1, 1, 1)
        grid.addWidget(self.labelRate, 3, 2, 1, 1)
        grid.addWidget(self.lineRate, 3, 3, 1, 1)

        # grid.setRowMinimumHeight(0, 300)

        # Connect signals
        self.showCheck.toggled.connect(self.sigShowToggled)
        self.slider.valueChanged.connect(
            lambda alue: self.sigSliderValueChanged.emit(value)
        )
        self.lineRate.textChanged.connect(
            lambda: self.sigUpdateRateChanged.emit(self.getUpdateRate())
        )
        self.layer = None
        
        self.tab_inlineholo.setLayout(grid)

    def getWvl(self):
        return float(self.wvlEdit.text())

    def getPixelSize(self):
        return float(self.pixelSizeEdit.text())

    def getNA(self):
        return float(self.naEdit.text())

    def getShowHoloChecked(self):
        return self.showCheck.isChecked()

    def getUpdateRate(self):
        return float(self.lineRate.text())

    def getImage(self):
        if self.layer is not None:
            return self.img.image

    def setImage(self, im):
        if self.layer is None or self.layer.name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False, name="Holo", blending='additive')
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
