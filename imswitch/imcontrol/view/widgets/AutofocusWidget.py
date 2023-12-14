import numpy as np
import pyqtgraph as pg
from qtpy import QtWidgets

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget
from .basewidgets import NapariHybridWidget

class AutofocusWidget(NapariHybridWidget):
    """ Widget containing focus lock interface. """

    def __post_init__(self):
        #super().__init__(*args, **kwargs)

        # Focus lock
        self.focusButton = guitools.BetterPushButton('Autofocus')
        self.focusButton.setCheckable(True)
        self.focusButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                      QtWidgets.QSizePolicy.Expanding)

        self.zStepRangeEdit = QtWidgets.QLineEdit('100')
        self.zStepRangeLabel = QtWidgets.QLabel('Focus search range (mm)')
        self.zStepSizeEdit = QtWidgets.QLineEdit('10')
        self.zStepSizeLabel = QtWidgets.QLabel('Stepsize (mm)')
        self.zBackgroundDefocusEdit = QtWidgets.QLineEdit('0')
        self.zBackgroundDefocusLabel = QtWidgets.QLabel('Defocus Move (mm)')
        # self.focusDataBox = QtWidgets.QCheckBox('Save data')  # Connect to exportData
        #self.camDialogButton = guitools.BetterPushButton('Camera Dialog')


        # Focus lock graph
        self.AutofocusGraph = pg.GraphicsLayoutWidget()
        self.AutofocusGraph.setAntialiasing(True)
        self.focusPlot = self.AutofocusGraph.addPlot(row=1, col=0)
        self.focusPlot.setLabels(bottom=('Motion', 'mm'), left=('Contrast', 'A.U.'))
        self.focusPlot.showGrid(x=True, y=True)
        # update this (self.focusPlotCurve.setData(X,Y)) with update(focusSignal) function
        self.focusPlotCurve = self.focusPlot.plot(pen='y')

        # Webcam graph
        self.webcamGraph = pg.GraphicsLayoutWidget()
        self.camImg = pg.ImageItem(border='w')
        self.camImg.setImage(np.zeros((100, 100)))
        self.vb = self.webcamGraph.addViewBox(invertY=True, invertX=False)
        self.vb.setAspectLocked(True)
        self.vb.addItem(self.camImg)

        # PROCESS DATA THREAD - ADD SOMEWHERE ELSE, NOT HERE, AS IT HAS NO GRAPHICAL ELEMENTS!

        # GUI layout below
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.AutofocusGraph, 0, 0, 1, 9)
        grid.addWidget(self.webcamGraph, 0, 9, 4, 1)
        grid.addWidget(self.focusButton, 1, 5, 2, 1)
        grid.addWidget(self.zStepRangeLabel, 3, 4)
        grid.addWidget(self.zStepRangeEdit, 4, 4)
        grid.addWidget(self.zStepSizeLabel, 3, 5)
        grid.addWidget(self.zStepSizeEdit, 4, 5)
        grid.addWidget(self.zBackgroundDefocusLabel, 1, 6)
        grid.addWidget(self.zBackgroundDefocusEdit, 1, 7)
        self.layer = None
        
    def setImageNapari(self, im, colormap="gray", isRGB = False, name="", pixelsize=(1,1), translation=(0,0)):
        if len(im.shape) == 2:
            translation = (translation[0], translation[1])
        if self.layer is None or name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=isRGB, colormap=colormap, 
                                               scale=pixelsize,translate=translation,
                                               name=name, blending='additive')
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
