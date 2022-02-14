from qtpy import QtCore, QtWidgets
from PyQt5.QtCore import Qt


from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget
from imswitch.imcommon.model import initLogger

class WellPlateWidget(Widget):
    """ Widget in control of the piezo movement. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pars = {}
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        
        self.__logger = initLogger(self, instanceName="WellPlateWidget")


    def add_plate_view(self):
        """Create Plate Layout Interface"""

        # Create dictionary to hold buttons
        self.Wells = {}
        # Create grid layout for wells (buttons)
        wellLayout = self.grid

        # Create dictionary to store well names (button texts)
        buttons = {
                " ": (0,0),  "1": (0,1),  "2": (0,2),  "3": (0,3),  "4": (0,4),  "5": (0,5),  "6": (0,6),  "7": (0,7),  "8": (0,8),  "9": (0,9),  "10": (0,10),  "11": (0,11),  "12": (0,12),
                "A": (1,0), "A1": (1,1), "A2": (1,2), "A3": (1,3), "A4": (1,4), "A5": (1,5), "A6": (1,6), "A7": (1,7), "A8": (1,8), "A9": (1,9), "A10": (1,10), "A11": (1,11), "A12": (1,12),
                "B": (2,0), "B1": (2,1), "B2": (2,2), "B3": (2,3), "B4": (2,4), "B5": (2,5), "B6": (2,6), "B7": (2,7), "B8": (2,8), "B9": (2,9), "B10": (2,10), "B11": (2,11), "B12": (2,12),
                "C": (3,0), "C1": (3,1), "C2": (3,2), "C3": (3,3), "C4": (3,4), "C5": (3,5), "C6": (3,6), "C7": (3,7), "C8": (3,8), "C9": (3,9), "C10": (3,10), "C11": (3,11), "C12": (3,12),
                "D": (4,0), "D1": (4,1), "D2": (4,2), "D3": (4,3), "D4": (4,4), "D5": (4,5), "D6": (4,6), "D7": (4,7), "D8": (4,8), "D9": (4,9), "D10": (4,10), "D11": (4,11), "D12": (4,12),
                "E": (5,0), "E1": (5,1), "E2": (5,2), "E3": (5,3), "E4": (5,4), "E5": (5,5), "E6": (5,6), "E7": (5,7), "E8": (5,8), "E9": (5,9), "E10": (5,10), "E11": (5,11), "E12": (5,12),
                "F": (6,0), "F1": (6,1), "F2": (6,2), "F3": (6,3), "F4": (6,4), "F5": (6,5), "F6": (6,6), "F7": (6,7), "F8": (6,8), "F9": (6,9), "F10": (6,10), "F11": (6,11), "F12": (6,12),
                "G": (7,0), "G1": (7,1), "G2": (7,2), "G3": (7,3), "G4": (7,4), "G5": (7,5), "G6": (7,6), "G7": (7,7), "G8": (7,8), "G9": (7,9), "G10": (7,10), "G11": (7,11), "G12": (7,12),
                "H": (8,0), "H1": (8,1), "H2": (8,2), "H3": (8,3), "H4": (8,4), "H5": (8,5), "H6": (8,6), "H7": (8,7), "H8": (8,8), "H9": (8,9), "H10": (8,10), "H11": (8,11), "H12": (8,12)
                }

        # Create wells (buttons) and add them to the grid layout
        for corrds, pos in buttons.items():
            if 0 in pos:
                self.Wells[corrds] = QtWidgets.QLabel(corrds)
                self.Wells[corrds].setAlignment(Qt.AlignCenter)
                self.Wells[corrds].setFixedSize(50, 30)
                self.Wells[corrds].setStyleSheet("""background-color: white; font-weight: bold;
                                                font-size: 20px""")
            else:
                self.Wells[corrds] =  guitools.BetterPushButton(corrds) #  QtWidgets.QPushButton(corrds)
                self.Wells[corrds].setFixedSize(50, 30)
                self.Wells[corrds].setStyleSheet("background-color: grey; font-size: 14px")
            # Set style for empty cell
            self.Wells[" "].setStyleSheet("background-color: none")
            # Add button/label to layout
            wellLayout.addWidget(self.Wells[corrds], pos[0], pos[1])
        # Add button layout to base well layout
        self.setLayout(wellLayout)
  
        '''
        for i in range(len(axes)):
            axis = axes[i]
            parNameSuffix = self._getParNameSuffix(positionerName, axis)
            label = f'{positionerName} -- {axis}' if positionerName != axis else positionerName

            
            self.pars['Label' + parNameSuffix] = QtWidgets.QLabel(f'<strong>{label}</strong>')
            self.pars['Label' + parNameSuffix].setTextFormat(QtCore.Qt.RichText)
            self.pars['Position' + parNameSuffix] = QtWidgets.QLabel(f'<strong>{0:.2f} µm</strong>')
            self.pars['Position' + parNameSuffix].setTextFormat(QtCore.Qt.RichText)
            self.pars['UpButton' + parNameSuffix] = guitools.BetterPushButton('+')
            self.pars['DownButton' + parNameSuffix] = guitools.BetterPushButton('-')
            self.pars['StepEdit' + parNameSuffix] = QtWidgets.QLineEdit('1000')
            self.pars['StepUnit' + parNameSuffix] = QtWidgets.QLabel(' µm')

            self.grid.addWidget(self.pars['Label' + parNameSuffix], self.numPositioners, 0)
            self.grid.addWidget(self.pars['Position' + parNameSuffix], self.numPositioners, 1)
            self.grid.addWidget(self.pars['UpButton' + parNameSuffix], self.numPositioners, 2)
            self.grid.addWidget(self.pars['DownButton' + parNameSuffix], self.numPositioners, 3)
            self.grid.addWidget(QtWidgets.QLabel('Step'), self.numPositioners, 4)
            self.grid.addWidget(self.pars['StepEdit' + parNameSuffix], self.numPositioners, 5)
            self.grid.addWidget(self.pars['StepUnit' + parNameSuffix], self.numPositioners, 6)

            self.numPositioners += 1

            # Connect signals
            self.pars['UpButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepUpClicked.emit(positionerName, axis)
            )
            self.pars['DownButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepDownClicked.emit(positionerName, axis)
            )
            '''

    def getStepSize(self, positionerName, axis):
        """ Returns the step size of the specified positioner axis in
        micrometers. """
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        return float(self.pars['StepEdit' + parNameSuffix].text())

    def setStepSize(self, positionerName, axis, stepSize):
        """ Sets the step size of the specified positioner axis to the
        specified number of micrometers. """
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        self.pars['StepEdit' + parNameSuffix].setText(stepSize)

    def updatePosition(self, positionerName, axis, position):
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        self.pars['Position' + parNameSuffix].setText(f'<strong>{position:.2f} µm</strong>')

    def _getParNameSuffix(self, positionerName, axis):
        return f'{positionerName}--{axis}'
  

    # Copyright (C) 2020, 2021 TestaLab
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
