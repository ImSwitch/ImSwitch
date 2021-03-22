import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

from .guitools import BetterPushButton
from .DataEditDialog import DataEditDialog


class DataFrame(QtWidgets.QFrame):
    """Frame for showing and examining the raw data"""

    # Signals
    sigShowMeanClicked = QtCore.Signal()
    sigAdjustDataClicked = QtCore.Signal()
    sigUnloadDataClicked = QtCore.Signal()
    sigFrameNumberChanged = QtCore.Signal(int)
    sigFrameSliderChanged = QtCore.Signal(int)

    # Methods
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Image Widget
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
        self.showMeanBtn.clicked.connect(self.sigShowMeanClicked)

        self.adjustDataBtn = BetterPushButton()
        self.adjustDataBtn.setText('Adjust/compl. data')
        self.adjustDataBtn.clicked.connect(self.sigAdjustDataClicked)

        self.unloadDataBtn = BetterPushButton()
        self.unloadDataBtn.setText('Unload data')
        self.unloadDataBtn.clicked.connect(self.sigUnloadDataClicked)

        frameLabel = QtWidgets.QLabel('Frame # ')
        self.frameNum = QtWidgets.QLineEdit('0')
        self.frameNum.textChanged.connect(lambda x: (x.isdigit() and
                                                     self.setCurrentFrame(int(x)) and
                                                     self.sigFrameNumberChanged.emit(int(x))))
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
        self.slider.valueChanged[int].connect(self.setCurrentFrame)
        self.slider.valueChanged[int].connect(self.sigFrameSliderChanged)

        self.patternScatter = pg.ScatterPlotItem()
        self.patternScatter.setData(
            pos=[[0, 0], [10, 10], [20, 20], [30, 30], [40, 40]],
            pen=pg.mkPen(color=(255, 0, 0), width=0.5,
                         style=QtCore.Qt.SolidLine, antialias=True),
            brush=pg.mkBrush(color=(255, 0, 0), antialias=True), size=1,
            pxMode=False)

        self.editWdw = DataEditDialog(self)

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
        layout.addWidget(self.adjustDataBtn, 2, 0)
        layout.addWidget(self.unloadDataBtn, 2, 1)
        layout.addWidget(imageWidget, 3, 0, 1, 4)

        self._showPattern = False

    def setShowPattern(self, value):
        self._showPattern = value

        if value:
            print('Showing pattern')
            self.imgVb.addItem(self.patternScatter)
        else:
            print('Hiding pattern')
            self.imgVb.removeItem(self.patternScatter)

    def showEditWindow(self):
        self.editWdw.show()

    def setImage(self, im, autoLevels):
        self.img.setImage(im, autoLevels)

    def setPatternGridData(self, x, y):
        self.patternScatter.setData(x, y)

    def setCurrentFrame(self, value):
        self.frameNum.setText(str(value))
        self.slider.setValue(value)

    def setNumFrames(self, value):
        self.numFrames.setText(str(value))
        self.slider.setMaximum(value - 1 if value > 0 else 0)

    def setDataName(self, value):
        self.dataName.setText(value)


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
