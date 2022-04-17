import pyqtgraph as pg
from qtpy import QtCore, QtWidgets

from imswitch.imcommon.view.guitools import pyqtgraphtools
from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget


class SquidStageScanWidget(NapariHybridWidget):
    """ Displays the SquidStageScan transform of the image. """

    sigShowToggled = QtCore.Signal(bool)  # (enabled)
    sigUpdateRateChanged = QtCore.Signal(float)  # (rate)
    sigSliderFocusValueChanged = QtCore.Signal(float)  # (value)
    sigSliderPumpSpeedValueChanged = QtCore.Signal(float)  # (value)
    sigSliderRotationSpeedValueChanged = QtCore.Signal(float)  # (value)

    def __post_init__(self):

        # Graphical elements
        '''
        we need:
        
        input:
            start X
            start Y
            stop X
            stop Y
            
            pixelsize (effective)
        
        output:
            current X
            currnt Y
            status
            
        buttons:
            Start scan/Stop scan
            Homing
        
        '''
        
        self.labelStartX = QtWidgets.QLabel('Start Pos. (X):')
        self.labelStartY = QtWidgets.QLabel('Start Pos. (Y):')
        self.labelCurrentX = QtWidgets.QLabel('Current Pos. (X): 0 µm')
        self.labelCurrentY = QtWidgets.QLabel('Current Pos. (Y): 0 µm')

        self.labelStopX = QtWidgets.QLabel('Stop Pos. (X):')
        self.labelStopY = QtWidgets.QLabel('Stop Pos. (Y):')
        self.labelPixelsize = QtWidgets.QLabel('Pixelsize:')
        
        self.editStartX = QtWidgets.QLineEdit('0.0')
        self.editStartY = QtWidgets.QLineEdit('0.0')
        self.editStopX = QtWidgets.QLineEdit('0.0')
        self.editStopY = QtWidgets.QLineEdit('0.0')
        self.editPixelsize = QtWidgets.QLineEdit('0.0')
        
        self.btnStart = guitools.BetterPushButton('Start Scan')
        self.btnHome = guitools.BetterPushButton('Home')

        self.labelCurrentX = QtWidgets.QLabel('Current Pos. (X):')
        self.labelCurrentY = QtWidgets.QLabel('Current Pos. (Y):')

        # setup buttons 
        self.btnStart.setCheckable(True)
        self.btnStart.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                      QtWidgets.QSizePolicy.Expanding)

        self.btnHome.setCheckable(True)
        self.btnHome.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                      QtWidgets.QSizePolicy.Expanding)

        # Add elements to GridLayout
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        # order: Xstart Ystart, Xsize, Ysize
        grid.addWidget(self.labelStartX, 0, 0, 1, 1)
        grid.addWidget(self.labelStartY, 1, 0, 1, 1)
        grid.addWidget(self.labelStopX, 2, 0, 1, 1)
        grid.addWidget(self.labelStopY, 3, 0, 1, 1)
        grid.addWidget(self.labelPixelsize, 4, 0, 1, 1)
        grid.addWidget(self.editStartX, 0, 1, 1, 1)
        grid.addWidget(self.editStartY, 1, 1, 1, 1)
        grid.addWidget(self.editStopX, 2, 1, 1, 1)
        grid.addWidget(self.editStopY, 3, 1, 1, 1)
        grid.addWidget(self.editPixelsize, 4, 1, 1, 1)
        
        
        grid.addWidget(self.labelCurrentX, 0, 2, 1, 1)
        grid.addWidget(self.labelCurrentY, 1, 2, 1, 1)
        
        grid.addWidget(self.btnStart, 4, 2, 1, 1)
        grid.addWidget(self.btnHome, 3, 2, 1, 1)

        # Connect signals
        #self.showCheck.toggled.connect(self.sigShowToggled)

        self.layer = None

    def updateCurrentX(self, position):
        self.labelCurrentX.setText(f'Current Pos. (X) {position} [µm]')
    
    def updateCurrentY(self, position):
        self.labelCurrentX.setText(f'Current Pos. (Y) {position} [µm]')
        
    def updateRotationSpeed(self, speed):
        self.labelRotationSpeed.setText(f'Speed Rotation {speed} [stp\s]')

    def getCoordinates(self):
        x1=self.editStartX.text()
        x2=self.editStopX.text()
        y1=self.editStartY.text()
        y2=self.editStopY.text()
        return (x1,x2,y1,y2)

    def getImage(self):
        if self.layer is not None:
            return self.img.image

    def setImage(self, im):
        if self.layer is None or self.layer.name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False, name="SquidStageScan", blending='additive')
        self.layer.data = im


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
