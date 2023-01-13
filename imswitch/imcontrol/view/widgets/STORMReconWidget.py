import pyqtgraph as pg
from qtpy import QtCore, QtWidgets

# microeye gui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from microEye.fitting.fit import BlobDetectionWidget, DoG_FilterWidget, BandpassFilterWidget, TemporalMedianFilterWidget


from imswitch.imcommon.view.guitools import pyqtgraphtools
from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget


class STORMReconWidget(NapariHybridWidget):
    """ Displays the STORMRecon transform of the image. """

    sigShowToggled = QtCore.Signal(bool)  # (enabled)
    sigUpdateRateChanged = QtCore.Signal(float)  # (rate)
    sigSliderValueChanged = QtCore.Signal(float)  # (value)

    def __post_init__(self):

        # Graphical elements
        self.showCheck = QtWidgets.QCheckBox('Show STORMRecon')
        self.showCheck.setCheckable(True)

        # Side TabView
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)


        # Localization / Render tab layout
        self.loc_group = QWidget()
        self.loc_form = QFormLayout()
        self.loc_group.setLayout(self.loc_form)

        # results stats tab layout
        self.data_filters = QWidget()
        self.data_filters_layout = QVBoxLayout()
        self.data_filters.setLayout(self.data_filters_layout)
        
        # Tiff Options tab layout
        self.controls_group = QWidget()
        self.controls_layout = QVBoxLayout()
        self.controls_group.setLayout(self.controls_layout)

        self.image_control_layout = QFormLayout()

        # Add grid
        self.grid.addWidget(self.controls_group, 0, 0, 1, 2)
        self.grid.addWidget(self.loc_group, 1, 0, 1, 2)
        self.grid.addWidget(self.data_filters, 2, 0, 1, 2)

        #self.detection = QCheckBox('Enable Realtime localization.')
        #self.detection.setChecked(False)

        #self.saveCropped = QPushButton(
        #    'Save Cropped Image',
        #    clicked=lambda: self.save_cropped_img())

        #self.image_control_layout.addWidget(self.detection)
        #self.image_control_layout.addWidget(self.saveCropped)

        self.controls_layout.addLayout(
            self.image_control_layout)
        
        self.blobDetectionWidget = BlobDetectionWidget()
        #self.blobDetectionWidget.update.connect(
        #    lambda: self.update_display())

        self.detection_method = QComboBox()
        # self.detection_method.currentIndexChanged.connect()
        self.detection_method.addItem(
            'OpenCV Blob Detection',
            self.blobDetectionWidget
        )

        self.doG_FilterWidget = DoG_FilterWidget()
        self.doG_FilterWidget.update.connect(
            lambda: self.update_display())
        self.bandpassFilterWidget = BandpassFilterWidget()
        self.bandpassFilterWidget.setVisible(False)
        #self.bandpassFilterWidget.update.connect(
        #    lambda: self.update_display())

        self.image_filter = QComboBox()
        self.image_filter.addItem(
            'Difference of Gaussians',
            self.doG_FilterWidget)
        self.image_filter.addItem(
            'Fourier Bandpass Filter',
            self.bandpassFilterWidget)

        # displays the selected item
        def update_visibility(box: QComboBox):
            for idx in range(box.count()):
                box.itemData(idx).setVisible(
                    idx == box.currentIndex())

        self.detection_method.currentIndexChanged.connect(
            lambda: update_visibility(self.detection_method))
        self.image_filter.currentIndexChanged.connect(
            lambda: update_visibility(self.image_filter))

        self.image_control_layout.addRow(
            QLabel('Approx. Loc. Method:'),
            self.detection_method)
        self.image_control_layout.addRow(
            QLabel('Image filter:'),
            self.image_filter)

        self.th_min_label = QLabel('Relative threshold:')
        self.th_min_slider = QDoubleSpinBox()
        self.th_min_slider.setMinimum(0)
        self.th_min_slider.setMaximum(100)
        self.th_min_slider.setSingleStep(0.01)
        self.th_min_slider.setDecimals(3)
        self.th_min_slider.setValue(0.2)
        #self.th_min_slider.valueChanged.connect(self.slider_changed)

        self.image_control_layout.addRow(
            self.th_min_label,
            self.th_min_slider)

        self.tempMedianFilter = TemporalMedianFilterWidget()
        #self.tempMedianFilter.update.connect(lambda: self.update_display())
        #self.controls_layout.addWidget(self.tempMedianFilter)

        self.controls_layout.addWidget(self.blobDetectionWidget)
        self.controls_layout.addWidget(self.doG_FilterWidget)
        self.controls_layout.addWidget(self.bandpassFilterWidget)

        #self.pages_slider.valueChanged.connect(self.slider_changed)
        #self.min_slider.valueChanged.connect(self.slider_changed)
        #self.max_slider.valueChanged.connect(self.slider_changed)
        #self.autostretch.stateChanged.connect(self.slider_changed)
        #self.detection.stateChanged.connect(self.slider_changed)


        '''
        self.lineRate = QtWidgets.QLineEdit('0')
        self.labelRate = QtWidgets.QLabel('Update rate')
        self.wvlLabel = QtWidgets.QLabel('Wavelength [um]')
        self.wvlEdit = QtWidgets.QLineEdit('0.488')
        self.pixelSizeLabel = QtWidgets.QLabel('Pixel size [um]')
        self.pixelSizeEdit = QtWidgets.QLineEdit('3.45')
        self.naLabel = QtWidgets.QLabel('NA')
        self.naEdit = QtWidgets.QLineEdit('0.3')

        valueDecimals = 1
        valueRange = (0,100)
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
        self.setLayout(grid)
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
            lambda value: self.sigSliderValueChanged.emit(value)
        )
        self.lineRate.textChanged.connect(
            lambda: self.sigUpdateRateChanged.emit(self.getUpdateRate())
        )
        '''
        self.layer = None

    def getImage(self):
        if self.layer is not None:
            return self.img.image

    def setImage(self, im):
        if self.layer is None or self.layer.name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False, name="STORMRecon", blending='additive')
        self.layer.data = im
        
    def getShowSTORMReconChecked(self):
        return self.showCheck.isChecked()


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
