from qtpy import QtCore, QtWidgets
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QTextEdit


from imswitch.imcommon.view.guitools import pyqtgraphtools
from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget



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

        self.tab_scouting = QWidget()
        self.tab_reference = QWidget()
        self.tab_imaging = QWidget()
        self.tab_settings = QWidget()
        self.tab_stage_scanning = QWidget()

        self.tabs.addTab(self.tab_scouting, "Scouting")
        self.tabs.addTab(self.tab_reference, "Reference")
        self.tabs.addTab(self.tab_imaging, "Measuring")
        self.tabs.addTab(self.tab_settings, "Settings")
        self.tabs.addTab(self.tab_stage_scanning, "Stage Scanning")
        

        self.init_ui()
        # create the layout of the tabs
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.addWidget(self.tabs)
        self.setLayout(mainLayout)      
        
    def init_ui(self):
        self.init_scouting_tab()
        self.init_reference_tab()
        self.init_imaging_tab()
        self.init_settings_tab()
        self.init_stage_scanning_tab()

        self.setGeometry(100, 100, 800, 600)


    def init_scouting_tab(self):
        layout = QVBoxLayout()

        self.info_label_scouting = QLabel("Information")
        self.frames_input_scouting = self.create_label_and_edit(layout, "Number of Frames", "10")
        self.start_button_scouting = QPushButton("Start")
        self.stop_button_scouting = QPushButton("Stop")
        self.image_view_scouting = QLabel("Image View Here")
        self.graph_view_scouting = QLabel("Graph View Here")

        layout.addWidget(self.info_label_scouting)
        layout.addWidget(self.frames_input_scouting)
        layout.addWidget(self.start_button_scouting)
        layout.addWidget(self.stop_button_scouting)
        layout.addWidget(self.image_view_scouting)
        layout.addWidget(self.graph_view_scouting)

        self.tab_scouting.setLayout(layout)

    def init_reference_tab(self):
        layout = QVBoxLayout()

        self.info_label_reference = QLabel("Information")
        self.frames_input_reference = self.create_label_and_edit(layout, "Number of Frames", "10")
        self.decay_input_reference = self.create_label_and_edit(layout, "Decay Time", "10")
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

    def init_imaging_tab(self):
        layout = QVBoxLayout()

        self.info_label_imaging = QLabel("Information")
        self.frames_input_imaging = self.create_label_and_edit(layout, "Number of Frames", "10")
        self.start_button_imaging = QPushButton("Start")
        self.stop_button_imaging = QPushButton("Stop")
        self.image_view_imaging = QLabel("Image View Here")
        self.graph_view_imaging = QLabel("Graph View Here")

        layout.addWidget(self.info_label_imaging)
        layout.addWidget(self.frames_input_imaging)
        layout.addWidget(self.start_button_imaging)
        layout.addWidget(self.stop_button_imaging)
        layout.addWidget(self.image_view_imaging)
        layout.addWidget(self.graph_view_imaging)

        self.tab_imaging.setLayout(layout)

    def init_settings_tab(self):
        layout = QVBoxLayout()

        self.dropdown_settings = QComboBox()
        self.dropdown_settings.addItems(["Frame", "Frame-Line", "Frame-Line-Pixel"])
        
        self.pixel_dwelltime = self.create_label_and_edit(layout, "Pixel Dwelltime (ns):", "1")
        self.Npixel_x = self.create_label_and_edit(layout, "Number of Pixels X:", "100")
        self.Npixel_y = self.create_label_and_edit(layout, "Number of Pixels Y:", "100")
        self.pixeloffsetLeft = self.create_label_and_edit(layout, "Pixel Offset left:", "0")
        self.pixeloffsetRight = self.create_label_and_edit(layout, "Pixel Offset right:", "0")
        self.pixeloffsetTop = self.create_label_and_edit(layout, "Pixel Offset top:", "0")
        self.pixeloffsetBottom = self.create_label_and_edit(layout, "Pixel Offset bottom:", "0")
        self.pixelsize = self.create_label_and_edit(layout, "Pixel Size (um):", "1")
        
        self.info_label_laser_freq = QLabel("Laser Frequency: [Info Here]")
        self.info_label_flimlabs_connected = QLabel("FLIMlabs Connected: [Info Here]")

        layout.addWidget(self.dropdown_settings)
        layout.addWidget(self.pixel_dwelltime)
        layout.addWidget(self.Npixel_x)
        layout.addWidget(self.Npixel_y)
        layout.addWidget(self.pixeloffsetLeft)
        layout.addWidget(self.pixeloffsetRight)
        layout.addWidget(self.pixeloffsetTop)
        layout.addWidget(self.pixeloffsetBottom)
        layout.addWidget(self.pixelsize)
        layout.addWidget(self.info_label_laser_freq)
        layout.addWidget(self.info_label_flimlabs_connected)

        self.tab_settings.setLayout(layout)


    def init_stage_scanning_tab(self):
        layout = QVBoxLayout()

        # Create labels and line edits for each parameter
        self.nStepsLine_edit = self.create_label_and_edit(layout, "Number of Steps Line (nStepsLine):", "100")
        self.dStepsLine_edit = self.create_label_and_edit(layout, "Delta Steps Line (dStepsLine):", "1")
        self.nTriggerLine_edit = self.create_label_and_edit(layout, "Number of Trigger Line (nTriggerLine):", "1")
        self.nStepsPixel_edit = self.create_label_and_edit(layout, "Number of Steps Pixel (nStepsPixel):", "100")
        self.dStepsPixel_edit = self.create_label_and_edit(layout, "Delta Steps Pixel (dStepsPixel):", "1")
        self.nTriggerPixel_edit = self.create_label_and_edit(layout, "Number of Trigger Pixel (nTriggerPixel):", "1")
        self.delayTimeStep_edit = self.create_label_and_edit(layout, "Delay Time Step (delayTimeStep):", "10")
        self.nFrames_edit = self.create_label_and_edit(layout, "Number of Frames (nFrames):", "5")

        # Start and Stop buttons
        self.start_button_stage_scanning = QPushButton("Start")
        self.stop_button_stage_scanning = QPushButton("Stop")
        layout.addWidget(self.start_button_stage_scanning)
        layout.addWidget(self.stop_button_stage_scanning)

        self.tab_stage_scanning.setLayout(layout)

    def create_label_and_edit(self, layout, label_text, default_text=""):
        label = QLabel(label_text)
        edit = QLineEdit(default_text)
        layout.addWidget(label)
        layout.addWidget(edit)
        return edit

    # Method to start stage scanning
    def getStageScanningParameters(self):
        # Retrieve values from line edits and convert them to the appropriate types
        nStepsLine = int(self.nStepsLine_edit.text())
        dStepsLine = int(self.dStepsLine_edit.text())
        nTriggerLine = int(self.nTriggerLine_edit.text())
        nStepsPixel = int(self.nStepsPixel_edit.text())
        dStepsPixel = int(self.dStepsPixel_edit.text())
        nTriggerPixel = int(self.nTriggerPixel_edit.text())
        delayTimeStep = int(self.delayTimeStep_edit.text())
        nFrames = int(self.nFrames_edit.text())

        return {"nStepsLine": nStepsLine, "dStepsLine": dStepsLine, "nTriggerLine": nTriggerLine,
                "dStepsLine": dStepsLine, "nStepsPixel": nStepsPixel, "dStepsPixel": dStepsPixel,
                "nTriggerPixel": nTriggerPixel, "delayTimeStep": delayTimeStep, "nFrames": nFrames}

    def getSettingsParameters(self):
        # Retrieve values from line edits and convert them to the appropriate types
        pixelDwelltime = int(self.pixel_dwelltime.text())
        Npixel_x = int(self.Npixel_x.text())
        Npixel_y = int(self.Npixel_y.text())
        pixeloffsetLeft = int(self.pixeloffsetLeft.text())
        pixeloffsetRight = int(self.pixeloffsetRight.text())
        pixeloffsetTop = int(self.pixeloffsetTop.text())
        pixeloffsetBottom = int(self.pixeloffsetBottom.text())
        pixelsize = int(self.pixelsize.text())

        return {"pixelDwelltime": pixelDwelltime, "Npixel_x": Npixel_x, "Npixel_y": Npixel_y,
                "pixelOffsetLeft":pixeloffsetLeft, "pixelOffsetRight": pixeloffsetRight,
                "pixelOffsetTop": pixeloffsetTop, "pixelOffsetBottom": pixeloffsetBottom,
                "pixelsize": pixelsize}
    
    def getScoutingParameters(self):
        
        # get general parameters
        generalParameters = self.getSettingsParameters()
        
        # Retrieve values from line edits and convert them to the appropriate types
        nFrames = int(self.frames_input_scouting.text())
        generalParameters["nFrames"] =  nFrames
        return generalParameters
    
    def getReferenceParameters(self):
        
        # get general parameters
        generalParameters = self.getSettingsParameters()
        
        # Retrieve values from line edits and convert them to the appropriate types
        nFrames = int(self.frames_input_reference.text())
        generalParameters["nFrames"] =  nFrames
        decayTime = int(self.decay_input_reference.text())
        generalParameters["decayTime"] =  decayTime
        return generalParameters
     
    def getImagingParameters(self):
        
        # get general parameters
        generalParameters = self.getSettingsParameters()
        
        # Retrieve values from line edits and convert them to the appropriate types
        nFrames = int(self.frames_input_imaging.text())
        generalParameters["nFrames"] =  nFrames
        return generalParameters   
        


    
        
        
# Copyright (C) 2020-2024 ImSwitch developers
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
