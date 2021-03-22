import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

from .guitools import BetterPushButton


class DataEditDialog(QtWidgets.QDialog):
    """For future data editing window, for example to remove rearrange frames
    or devide into seperate datasets"""

    sigImageSliceChanged = QtCore.Signal(int)
    sigShowMeanClicked = QtCore.Signal()
    sigSetDarkFrameClicked = QtCore.Signal()

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.setWindowTitle('Data Edit/Complement')

        # Data view Widget
        imageWidget = pg.GraphicsLayoutWidget()
        self.imgVb = imageWidget.addViewBox(row=0, col=0)
        self.imgVb.setMouseMode(pg.ViewBox.PanMode)
        self.img = pg.ImageItem(axisOrder='row-major')
        self.img.translate(-0.5, -0.5)
        self.imgVb.addItem(self.img)
        self.imgVb.setAspectLocked(True)
        self.imgHist = pg.HistogramLUTItem(image=self.img)
        imageWidget.addItem(self.imgHist, row=0, col=1)

        self.showMeanBtn = BetterPushButton()
        self.showMeanBtn.setText('Show mean image')
        self.showMeanBtn.pressed.connect(self.sigShowMeanClicked)

        frameLabel = QtWidgets.QLabel('Frame # ')
        self.frameNum = QtWidgets.QLineEdit('0')
        self.frameNum.textChanged.connect(self.frameNumberChanged)
        self.frameNum.setFixedWidth(45)

        dataNameLabel = QtWidgets.QLabel('File name:')
        self.dataName = QtWidgets.QLabel('')
        numFramesLabel = QtWidgets.QLabel('Nr of frames:')
        self.numFrames = QtWidgets.QLabel('')

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self.slider.setTickInterval(5)
        self.slider.setSingleStep(1)
        self.slider.valueChanged[int].connect(self.sliderMoved)

        self.actionBtns = DataEditActions()
        self.actionBtns.sigSetDarkFrame.connect(self.sigSetDarkFrameClicked)

        # Dark frame view widget
        dfWidget = pg.GraphicsLayoutWidget()
        self.dfVb = dfWidget.addViewBox(row=0, col=0)
        self.dfVb.setMouseMode(pg.ViewBox.PanMode)
        self.df = pg.ImageItem(axisOrder='row-major')
        self.df.translate(-0.5, -0.5)
        self.dfVb.addItem(self.df)
        self.dfVb.setAspectLocked(True)
        self.dfHist = pg.HistogramLUTItem(image=self.df)
        dfWidget.addItem(self.dfHist, row=0, col=1)

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        layout.addWidget(dataNameLabel, 0, 0)
        layout.addWidget(self.dataName, 0, 1)
        layout.addWidget(numFramesLabel, 0, 2)
        layout.addWidget(self.numFrames, 0, 3)
        layout.addWidget(self.showMeanBtn, 1, 0)
        layout.addWidget(self.slider, 1, 1)
        layout.addWidget(frameLabel, 1, 2)
        layout.addWidget(self.frameNum, 1, 3)
        layout.addWidget(imageWidget, 2, 0, 1, 4)
        layout.addWidget(self.actionBtns, 0, 4)
        layout.addWidget(dfWidget, 0, 5, 3, 1)

    def sliderMoved(self):
        frameNumber = self.slider.value()
        self.frameNum.setText(str(frameNumber))
        self.sigImageSliceChanged.emit(frameNumber)

    def frameNumberChanged(self):
        try:
            frameNumber = int(self.frameNum.text())
        except TypeError:
            print('ERROR: Input must be an integer value')
            return

        self.slider.setValue(frameNumber)
        self.sigImageSliceChanged.emit(frameNumber)

    def setImage(self, image, autoLevels):
        self.img.setImage(image, autoLevels=autoLevels)

    def updateDataProperties(self, dataName, numFrames):
        self.dataName.setText(dataName)
        self.numFrames.setText(str(numFrames))
        self.slider.setMaximum(numFrames - 1)


class DataEditActions(QtWidgets.QFrame):
    sigSetDarkFrame = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        setDarkFrameBtn = BetterPushButton('Set Dark/Offset frame')
        setDarkFrameBtn.clicked.connect(self.sigSetDarkFrame)

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        layout.addWidget(setDarkFrameBtn, 0, 0)


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
