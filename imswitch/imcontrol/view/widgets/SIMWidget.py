import numpy as np
import pyqtgraph as pg
from qtpy import QtCore, QtWidgets
from pyqtgraph.parametertree import ParameterTree
from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget

from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget,
                             QVBoxLayout, QHBoxLayout, QComboBox, QPushButton,
                             QCheckBox, QLabel, QLineEdit)


class SIMWidget(NapariHybridWidget):
    """ Widget containing sim interface. """

    sigSIMMonitorChanged = QtCore.Signal(int)  # (monitor)
    sigPatternID = QtCore.Signal(int)  # (display pattern id)

    def __post_init__(self):
        #super().__init__(*args, **kwargs)


        # Main GUI 
        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

        # Side TabView
        self.tabView = QTabWidget()
        self.layout.addWidget(self.tabView, 0)
        

        # Add tabs
        self.manual_control_tab = self.create_manual_control_tab()
        self.experiment_tab = self.create_experiment_tab()
        self.reconstruction_parameters_tab = self.create_reconstruction_parameters_tab()
        self.timelapse_settings_tab = self.create_timelapse_settings_tab()
        self.zstack_settings_tab = self.create_zstack_settings_tab()
        
        
        self.tabView.addTab(self.manual_control_tab, "Manual Control")
        self.tabView.addTab(self.experiment_tab, "Experiment")
        self.tabView.addTab(self.reconstruction_parameters_tab, "Reconstruction Parameters")
        self.tabView.addTab(self.timelapse_settings_tab, "TimeLapse Settings")
        self.tabView.addTab(self.zstack_settings_tab, "Z-stack Settings")
        
        self.layer = None
        
        
    def getImage(self):
        if self.layer is not None:
            return self.img.image
        
    def setImage(self, im, name="SIM Reconstruction"):
        if self.layer is None or name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False, name=name, blending='additive')
        else:
            self.viewer.layers[name].data = im

    def create_manual_control_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Laser dropdown
        self.laser_dropdown = QComboBox()
        self.laser_dropdown.addItems(["Laser 488nm", "Laser 635nm"])
        layout.addWidget(self.laser_dropdown)

        # Number dropdown
        self.number_dropdown = QComboBox()
        self.number_dropdown.addItems([str(i) for i in range(9)])
        layout.addWidget(self.number_dropdown)

        tab.setLayout(layout)
        return tab

    def create_experiment_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Buttons
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)

        # Select reconstructor
        '''
        ProcessorLabel = QtWidgets.QLabel('<strong>SIM Processor:</strong>')
        self.SIMReconstructorList = QtWidgets.QComboBox()
        self.SIMReconstructorList.addItems(['napari', 'mcsim'])
        '''
        
        # Checkboxes
        checkboxes = [
            "Enable Reconstruction", "Enable Record Reconstruction",
            "Enable Record RAW", "Enable Laser 488", "Enable Laser 635",
            "Enable TimeLapse", "Enable Z-stack", "Use GPU?",
            
        ]
        self.checkbox_reconstruction = QCheckBox(checkboxes[0])
        self.checkbox_record_reconstruction = QCheckBox(checkboxes[1])
        self.checkbox_record_raw = QCheckBox(checkboxes[2])
        layout.addWidget(self.checkbox_reconstruction)
        layout.addWidget(self.checkbox_record_reconstruction)
        layout.addWidget(self.checkbox_record_raw)
        
        tab.setLayout(layout)
        return tab

    def create_reconstruction_parameters_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Label/textedit pairs
        params = [
            ("Wavelength 1", "488"), ("Wavelength 2", "635"), ("NA", "1.4"),
            ("n", "1."),
            ("Pixelsize (eff)", "1"), ("Alpha", "0.5"), ("Beta", "0.5"),
            ("w", "1"), ("eta", "2")
        ]
        
        # create widget per label
        self.wavelength1_label = QLabel(params[0][0])
        self.wavelength1_textedit = QLineEdit(params[0][1])
        self.wavelength2_label = QLabel(params[1][0])
        self.wavelength2_textedit = QLineEdit(params[1][1])
        self.NA_label = QLabel(params[2][0])
        self.NA_textedit = QLineEdit(params[2][1])
        self.pixelsize_label = QLabel(params[3][0])
        self.pixelsize_textedit = QLineEdit(params[3][1])
        self.alpha_label = QLabel(params[4][0])
        self.alpha_textedit = QLineEdit(params[4][1])
        self.beta_label = QLabel(params[5][0])
        self.beta_textedit = QLineEdit(params[5][1])
        self.w_label = QLabel(params[6][0])
        self.w_textedit = QLineEdit(params[6][1])
        self.eta_label = QLabel(params[7][0])
        self.eta_textedit = QLineEdit(params[7][1])
        self.n_label = QLabel(params[8][0])
        self.n_textedit = QLineEdit(params[8][1])
        row_layout_1 = QHBoxLayout()
        row_layout_1.addWidget(self.wavelength1_label)
        row_layout_1.addWidget(self.wavelength1_textedit)
        row_layout_2 = QHBoxLayout()
        row_layout_2.addWidget(self.wavelength2_label)
        row_layout_2.addWidget(self.wavelength2_textedit)
        row_layout_3 = QHBoxLayout()
        row_layout_3.addWidget(self.NA_label)
        row_layout_3.addWidget(self.NA_textedit)
        row_layout_4 = QHBoxLayout()
        row_layout_4.addWidget(self.pixelsize_label)
        row_layout_4.addWidget(self.pixelsize_textedit)
        row_layout_5 = QHBoxLayout()
        row_layout_5.addWidget(self.alpha_label)
        row_layout_5.addWidget(self.alpha_textedit)
        row_layout_6 = QHBoxLayout()
        row_layout_6.addWidget(self.beta_label)
        row_layout_6.addWidget(self.beta_textedit)
        row_layout_7 = QHBoxLayout()
        row_layout_7.addWidget(self.w_label)
        row_layout_7.addWidget(self.w_textedit)
        row_layout_8 = QHBoxLayout()
        row_layout_8.addWidget(self.eta_label)
        row_layout_8.addWidget(self.eta_textedit)
        row_layout_9 = QHBoxLayout()
        row_layout_9.addWidget(self.n_label)
        row_layout_9.addWidget(self.n_textedit)
        
        layout.addLayout(row_layout_1)
        layout.addLayout(row_layout_2)
        layout.addLayout(row_layout_3)
        layout.addLayout(row_layout_4)
        layout.addLayout(row_layout_5)
        layout.addLayout(row_layout_6)
        layout.addLayout(row_layout_7)
        layout.addLayout(row_layout_8)
        layout.addLayout(row_layout_9)
        

        tab.setLayout(layout)
        return tab

    def create_timelapse_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Label/textedit pairs
        settings = [
            ("Period", "60s"), ("Number of frames", "10")
        ]
        
        # create widget per label
        self.period_label = QLabel(settings[0][0])
        self.period_textedit = QLineEdit(settings[0][1])
        self.frames_label = QLabel(settings[1][0])
        self.frames_textedit = QLineEdit(settings[1][1])
        row_layout_1 = QHBoxLayout()
        row_layout_1.addWidget(self.period_label)
        row_layout_1.addWidget(self.period_textedit)
        row_layout_2 = QHBoxLayout()
        row_layout_2.addWidget(self.frames_label)
        row_layout_2.addWidget(self.frames_textedit)
        layout.addLayout(row_layout_1)
        layout.addLayout(row_layout_2)

        tab.setLayout(layout)
        return tab
        

    def create_zstack_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Label/textedit pairs
        settings = [
            ("Z-min", "-100µm"), ("Z-max", "100µm"), ("NSteps", "10")
        ]
        # create widget per label
        self.zmin_label = QLabel(settings[0][0])
        self.zmin_textedit = QLineEdit(settings[0][1])
        self.zmax_label = QLabel(settings[1][0])
        self.zmax_textedit = QLineEdit(settings[1][1])
        self.nsteps_label = QLabel(settings[2][0])
        self.nsteps_textedit = QLineEdit(settings[2][1])
        row_layout_1 = QHBoxLayout()
        row_layout_1.addWidget(self.zmin_label)
        row_layout_1.addWidget(self.zmin_textedit)
        row_layout_2 = QHBoxLayout()
        row_layout_2.addWidget(self.zmax_label)
        row_layout_2.addWidget(self.zmax_textedit)
        row_layout_3 = QHBoxLayout()
        row_layout_3.addWidget(self.nsteps_label)
        row_layout_3.addWidget(self.nsteps_textedit)
        layout.addLayout(row_layout_1)
        layout.addLayout(row_layout_2)
        layout.addLayout(row_layout_3)

        tab.setLayout(layout)
        
        
    def getZStackParameters(self):
        return (np.float32(self.zmin_textedit.text()), np.float323(self.zmax_textedit.text()), np.float32(self.nsteps_textedit.text()))
    
    def getTimeLaspeParameters(self):
        return (np.float32(self.period_textedit.text()), np.float32(self.frames_textedit.text()))
    

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
