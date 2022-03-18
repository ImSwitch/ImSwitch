from qtpy import QtCore, QtWidgets
from PyQt5.QtCore import Qt


from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget
from imswitch.imcommon.model import initLogger

class LEDMatrixWidget(Widget):
    """ Widget in control of the piezo movement. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pars = {}
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        self.__logger = initLogger(self, instanceName="LEDMatrixWidget")


    def add_matrix_view(self, nLedsX = 8, nLedsY=8):
        """Create matrix Layout Interface"""

        # Create dictionary to hold buttons
        self.leds = {}
        # Create grid layout for leds (buttons)
        wellLayout = self.grid

        # Create dictionary to store well names (button texts)
        buttons = {}
        for ix in range(nLedsX): 
            for iy in range(nLedsY):
                buttons["L"+str(nLedsX*ix+iy)]=(ix,iy)                
        
        # Create leds (buttons) and add them to the grid layout
        for corrds, pos in buttons.items():
            self.leds[corrds] = QtWidgets.QLabel(corrds)
            self.leds[corrds].setAlignment(Qt.AlignCenter)
            self.leds[corrds].setFixedSize(30, 30)
            self.leds[corrds].setStyleSheet("""background-color: grey; font-weight: bold;
                                            font-size: 20px""")
            # Add button/label to layout
            wellLayout.addWidget(self.leds[corrds], pos[0], pos[1])
        
        # Add button layout to base well layout
        self.setLayout(wellLayout)
  
    def _getParNameSuffix(self, positionerName, axis):
        return f'{positionerName}--{axis}'
  

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
