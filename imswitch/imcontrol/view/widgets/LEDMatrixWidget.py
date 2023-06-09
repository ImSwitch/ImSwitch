from qtpy import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QPushButton, QColorDialog
from PyQt5.QtGui import QPainter, QColor, QPixmap, QIcon

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
        gridLayout = self.grid

        # Create dictionary to store well names (button texts)
        buttons = {}
        for ix in range(nLedsX): 
            for iy in range(nLedsY):
                buttons[str(nLedsX*ix+iy)]=(ix,iy)
        
        # Create leds (buttons) and add them to the grid layout
        for corrds, pos in buttons.items():
            self.leds[corrds] = guitools.BetterPushButton(corrds)
            self.leds[corrds].setSizePolicy(QtWidgets.QSizePolicy.Minimum,
                            QtWidgets.QSizePolicy.Expanding)
            self.leds[corrds].setCheckable(True)
            self.leds[corrds].setStyleSheet("""background-color: grey;
                                            font-size: 15px""")

            # Add button/label to layout
            gridLayout.addWidget(self.leds[corrds], pos[0], pos[1])
        
        self.ButtonAllOn = guitools.BetterPushButton("All On")
        gridLayout.addWidget(self.ButtonAllOn, 0, 8, 1, 1)
        
        self.ButtonAllOff = guitools.BetterPushButton("All Off")
        gridLayout.addWidget(self.ButtonAllOff, 1, 8, 1, 1)
                
        self.slider = guitools.FloatSlider(QtCore.Qt.Horizontal, self, allowScrollChanges=False,
                                           decimals=1)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
                    
        self.slider.setMinimum(0)
        self.slider.setMaximum(255)
        self.slider.setTickInterval(5)
        self.slider.setSingleStep(5)
        self.slider.setValue(255)
        gridLayout.addWidget(self.slider, 9, 0, 1, 8)
         
        # Add button layout to base well layout
        self.setLayout(gridLayout)
  
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
