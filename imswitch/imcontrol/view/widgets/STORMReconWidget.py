import pyqtgraph as pg
from qtpy import QtCore, QtWidgets

# microeye gui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from microEye.fitting.fit import BlobDetectionWidget, DoG_FilterWidget, BandpassFilterWidget, TemporalMedianFilterWidget
from microEye.fitting.results import FittingMethod, FittingResults
from microEye.checklist_dialog import ChecklistDialog, Checklist

from imswitch.imcommon.view.guitools import pyqtgraphtools
from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget


class STORMReconWidget(NapariHybridWidget):
    """ Displays the STORMRecon transform of the image. """

    sigShowToggled = QtCore.Signal(bool)  # (enabled)
    sigUpdateRateChanged = QtCore.Signal(float)  # (rate)
    sigSliderValueChanged = QtCore.Signal(float)  # (value)

    def __post_init__(self):

        # Napari image layer for results
        self.layer = None
        

        # Main GUI 
        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

        # Side TabView
        self.tabView = QTabWidget()
        self.layout.addWidget(self.tabView, 0)

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

        # Add tabView
        self.tabView.addTab(self.controls_group, 'Prefit Options')
        self.tabView.addTab(self.loc_group, 'Fitting')
        self.tabView.addTab(self.data_filters, 'Data Filters')

        #self.detection = QCheckBox('Enable Realtime localization.')
        #self.detection.setChecked(False)

        #self.saveCropped = QPushButton(
        #    'Save Cropped Image',
        #    clicked=lambda: self.save_cropped_img())

        #self.image_control_layout.addWidget(self.detection)
        #self.image_control_layout.addWidget(self.saveCropped)

        '''
        PREFIT OPTIONS
        '''

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

        self.controls_layout.addStretch()
        
        
        
        
        '''
        FITTING 
        '''

        # Localization / Render layout
        self.fitting_cbox = QComboBox()
        self.fitting_cbox.addItem(
            '2D Phasor-Fit (CPU)',
            FittingMethod._2D_Phasor_CPU)
        self.fitting_cbox.addItem(
            '2D MLE Gauss-Fit fixed sigma (GPU/CPU)',
            FittingMethod._2D_Gauss_MLE_fixed_sigma)
        self.fitting_cbox.addItem(
            '2D MLE Gauss-Fit free sigma (GPU/CPU)',
            FittingMethod._2D_Gauss_MLE_free_sigma)
        self.fitting_cbox.addItem(
            '2D MLE Gauss-Fit elliptical sigma (GPU/CPU)',
            FittingMethod._2D_Gauss_MLE_elliptical_sigma)
        self.fitting_cbox.addItem(
            '2D MLE Gauss-Fit cspline (GPU/CPU)',
            FittingMethod._3D_Gauss_MLE_cspline_sigma)

        self.render_cbox = QComboBox()
        self.render_cbox.addItem('2D Histogram', 0)
        self.render_cbox.addItem('2D Gaussian Histogram', 1)

        self.frc_cbox = QComboBox()
        self.frc_cbox.addItem('Binomial')
        self.frc_cbox.addItem('Check Pattern')

        self.export_options = Checklist(
                'Exported Columns',
                ['Super-res image', ] + FittingResults.uniqueKeys(None),
                checked=True)

        self.export_precision = QLineEdit('%10.5f')

        self.px_size = QDoubleSpinBox()
        self.px_size.setMinimum(0)
        self.px_size.setMaximum(20000)
        self.px_size.setValue(117.5)

        self.super_px_size = QSpinBox()
        self.super_px_size.setMinimum(0)
        self.super_px_size.setMaximum(200)
        self.super_px_size.setValue(10)

        self.fit_roi_size = QSpinBox()
        self.fit_roi_size.setMinimum(7)
        self.fit_roi_size.setMaximum(99)
        self.fit_roi_size.setSingleStep(2)
        self.fit_roi_size.lineEdit().setReadOnly(True)
        self.fit_roi_size.setValue(13)

        self.drift_cross_args = QHBoxLayout()
        self.drift_cross_bins = QSpinBox()
        self.drift_cross_bins.setValue(10)
        self.drift_cross_px = QSpinBox()
        self.drift_cross_px.setValue(10)
        self.drift_cross_up = QSpinBox()
        self.drift_cross_up.setMaximum(1000)
        self.drift_cross_up.setValue(100)
        self.drift_cross_args.addWidget(self.drift_cross_bins)
        self.drift_cross_args.addWidget(self.drift_cross_px)
        self.drift_cross_args.addWidget(self.drift_cross_up)

        self.nneigh_merge_args = QHBoxLayout()
        self.nn_neighbors = QSpinBox()
        self.nn_neighbors.setValue(1)
        self.nn_min_distance = QDoubleSpinBox()
        self.nn_min_distance.setMaximum(20000)
        self.nn_min_distance.setValue(0)
        self.nn_max_distance = QDoubleSpinBox()
        self.nn_max_distance.setMaximum(20000)
        self.nn_max_distance.setValue(30)
        self.nn_max_off = QSpinBox()
        self.nn_max_off.setValue(1)
        self.nn_max_length = QSpinBox()
        self.nn_max_length.setMaximum(20000)
        self.nn_max_length.setValue(500)
        self.nneigh_merge_args.addWidget(self.nn_neighbors)
        self.nneigh_merge_args.addWidget(self.nn_min_distance)
        self.nneigh_merge_args.addWidget(self.nn_max_distance)
        self.nneigh_merge_args.addWidget(self.nn_max_off)
        self.nneigh_merge_args.addWidget(self.nn_max_length)

        self.loc_btn = QPushButton(
            'Localize',
            clicked=lambda: self.localize())
        self.refresh_btn = QPushButton(
            'Refresh SuperRes Image',
            clicked=lambda: self.renderLoc())
        self.frc_res_btn = QPushButton(
            'FRC Resolution',
            clicked=lambda: self.FRC_estimate())
        self.drift_cross_btn = QPushButton(
            'Drift cross-correlation',
            clicked=lambda: self.drift_cross())

        self.nn_layout = QHBoxLayout()
        self.nneigh_btn = QPushButton(
            'Nearest-neighbour',
            clicked=lambda: self.nneigh())
        self.merge_btn = QPushButton(
            'Merge Tracks',
            clicked=lambda: self.merge())
        self.nneigh_merge_btn = QPushButton(
            'NM + Merging',
            clicked=lambda: self.nneigh_merge())

        self.drift_fdm_btn = QPushButton(
            'Fiducial marker drift correction',
            clicked=lambda: self.drift_fdm())

        self.nn_layout.addWidget(self.nneigh_btn)
        self.nn_layout.addWidget(self.merge_btn)
        self.nn_layout.addWidget(self.nneigh_merge_btn)

        self.im_exp_layout = QHBoxLayout()
        self.import_loc_btn = QPushButton(
            'Import',
            clicked=lambda: self.import_loc())
        self.export_loc_btn = QPushButton(
            'Export',
            clicked=lambda: self.export_loc())

        self.im_exp_layout.addWidget(self.import_loc_btn)
        self.im_exp_layout.addWidget(self.export_loc_btn)

        self.loc_form.addRow(
            QLabel('Fitting:'),
            self.fitting_cbox
        )
        self.loc_form.addRow(
            QLabel('Rendering Method:'),
            self.render_cbox
        )
        self.loc_form.addRow(
            QLabel('Fitting roi-size [pixel]:'),
            self.fit_roi_size
        )
        self.loc_form.addRow(
            QLabel('Pixel-size [nm]:'),
            self.px_size
        )
        self.loc_form.addRow(
            QLabel('S-res pixel-size [nm]:'),
            self.super_px_size
        )
        
        # activate live localization 
        self.showCheck = QtWidgets.QCheckBox('Show STORMRecon')
        self.showCheck.setCheckable(True)
        self.showCheck.toggled.connect(self.sigShowToggled)
        
        self.show_liveloc = QHBoxLayout()
        self.show_liveloc.addWidget(self.showCheck)
        self.loc_form.addRow(self.show_liveloc)
        
        self.loc_ref_lay = QHBoxLayout()
        self.loc_ref_lay.addWidget(self.loc_btn)
        self.loc_ref_lay.addWidget(self.refresh_btn)
        self.loc_form.addRow(self.loc_ref_lay)

        self.loc_form.addRow(self.frc_res_btn)

        self.loc_form.addRow(
            QLabel('Drift X-Corr. (bins, pixelSize, upsampling):'))
        self.loc_form.addRow(self.drift_cross_args)
        self.loc_form.addRow(self.drift_cross_btn)
        self.loc_form.addRow(
            QLabel('NN (n-neighbor, min, max-distance, max-off, max-len):'))
        self.loc_form.addRow(self.nneigh_merge_args)
        self.loc_form.addRow(self.nn_layout)
        self.loc_form.addRow(self.drift_fdm_btn)
        self.loc_form.addRow(self.export_options)
        self.loc_form.addRow(
            QLabel('Format:'),
            self.export_precision)
        self.loc_form.addRow(self.im_exp_layout)



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
