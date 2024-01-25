from qtpy import QtCore, QtWidgets
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QTextEdit


from imswitch.imcommon.view.guitools import pyqtgraphtools
from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget

import datetime



class FLIMLabsWidget(NapariHybridWidget):
    """ Displays the FLIMLabs transform of the image. """

    sigPumpDirectionToggled = QtCore.Signal(bool)  # (enabled)
    sigSnapClicked = QtCore.Signal(bool)  # (rate)
    sigSliderFocusValueChanged = QtCore.Signal(float)  # (value)
    sigSliderPumpSpeedValueChanged = QtCore.Signal(float)  # (value)
    sigSliderRotationSpeedValueChanged = QtCore.Signal(float)  # (value)
    sigExposureTimeChanged = QtCore.Signal(float)  # (value)
    sigGainChanged = QtCore.Signal(float)  # (value)
    
    def __post_init__(self):
        self.tabs = QTabWidget()

        self.tab_screening = QWidget()
        self.tab_reference = QWidget()
        self.tab_measuring = QWidget()
        self.tab_settings = QWidget()

        self.tabs.addTab(self.tab_screening, "Screening")
        self.tabs.addTab(self.tab_reference, "Reference")
        self.tabs.addTab(self.tab_measuring, "Measuring")
        self.tabs.addTab(self.tab_settings, "Settings")

        self.init_ui()
        # create the layout of the tabs
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.addWidget(self.tabs)
        self.setLayout(mainLayout)      
        
    def init_ui(self):
        self.init_screening_tab()
        self.init_reference_tab()
        self.init_measuring_tab()
        self.init_settings_tab()

        self.setGeometry(100, 100, 800, 600)


    def init_screening_tab(self):
        layout = QVBoxLayout()

        self.info_label_screening = QLabel("Information")
        self.frames_input_screening = QLineEdit("Enter Number of Frames")
        self.start_button_screening = QPushButton("Start")
        self.stop_button_screening = QPushButton("Stop")
        self.image_view_screening = QLabel("Image View Here")
        self.graph_view_screening = QLabel("Graph View Here")

        layout.addWidget(self.info_label_screening)
        layout.addWidget(self.frames_input_screening)
        layout.addWidget(self.start_button_screening)
        layout.addWidget(self.stop_button_screening)
        layout.addWidget(self.image_view_screening)
        layout.addWidget(self.graph_view_screening)

        self.tab_screening.setLayout(layout)

    def init_reference_tab(self):
        layout = QVBoxLayout()

        self.info_label_reference = QLabel("Information")
        self.frames_input_reference = QLineEdit("Enter Number of Frames")
        self.decay_input_reference = QLineEdit("Enter Decay (ns)")
        self.start_button_reference = QPushButton("Start")
        self.stop_button_reference = QPushButton("Stop")
        self.image_view_reference = QLabel("Image View Here")
        self.graph_view_reference = QLabel("Graph View Here")

        layout.addWidget(self.info_label_reference)
        layout.addWidget(self.frames_input_reference)
        layout.addWidget(self.decay_input_reference)
        layout.addWidget(self.start_button_reference)
        layout.addWidget(self.stop_button_reference)
        layout.addWidget(self.image_view_reference)
        layout.addWidget(self.graph_view_reference)

        self.tab_reference.setLayout(layout)

    def init_measuring_tab(self):
        layout = QVBoxLayout()

        self.info_label_measuring = QLabel("Information")
        self.frames_input_measuring = QLineEdit("Enter Number of Frames")
        self.start_button_measuring = QPushButton("Start")
        self.stop_button_measuring = QPushButton("Stop")
        self.image_view_measuring = QLabel("Image View Here")
        self.graph_view_measuring = QLabel("Graph View Here")

        layout.addWidget(self.info_label_measuring)
        layout.addWidget(self.frames_input_measuring)
        layout.addWidget(self.start_button_measuring)
        layout.addWidget(self.stop_button_measuring)
        layout.addWidget(self.image_view_measuring)
        layout.addWidget(self.graph_view_measuring)

        self.tab_measuring.setLayout(layout)

    def init_settings_tab(self):
        layout = QVBoxLayout()

        self.dropdown_settings = QComboBox()
        self.dropdown_settings.addItems(["Frame", "Frame-Line", "Frame-Line-Pixel"])
        self.textedit_pixel_dwelltime = QTextEdit("Pixel Dwelltime")
        self.textedit_other_settings = QTextEdit("Pixel X, Pixel Y, Pixelsize, Offset X, Offset Y")
        self.info_label_laser_freq = QLabel("Laser Frequency: [Info Here]")
        self.info_label_flimlabs_connected = QLabel("FLIMlabs Connected: [Info Here]")

        layout.addWidget(self.dropdown_settings)
        layout.addWidget(self.textedit_pixel_dwelltime)
        layout.addWidget(self.textedit_other_settings)
        layout.addWidget(self.info_label_laser_freq)
        layout.addWidget(self.info_label_flimlabs_connected)

        self.tab_settings.setLayout(layout)


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
