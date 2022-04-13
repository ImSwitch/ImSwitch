import pyqtgraph as pg
from qtpy import QtCore, QtWidgets

from imswitch.imcommon.view.guitools import pyqtgraphtools
from imswitch.imcontrol.view import guitools
from .basewidgets import Widget


class HoliSheetWidget(Widget):
    """ Displays the HoliSheet transform of the image. """

    sigShowToggled = QtCore.Signal(bool)  # (enabled)
    sigPosToggled = QtCore.Signal(bool)  # (enabled)
    sigPosChanged = QtCore.Signal(float)  # (pos)
    sigUpdateRateChanged = QtCore.Signal(float)  # (rate)
    sigResized = QtCore.Signal()
    sigValueChanged = QtCore.Signal(float)  # (value)


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.showCheck = QtWidgets.QCheckBox('Show HoliSheet')
        self.showCheck.setCheckable(True)
        self.posCheck = guitools.BetterPushButton('Period (pix)')
        self.posCheck.setCheckable(True)
        self.linePos = QtWidgets.QLineEdit('4')
        self.lineRate = QtWidgets.QLineEdit('0')
        self.labelRate = QtWidgets.QLabel('Update rate')

        valueDecimals = 1
        valueRange = (0,100)
        tickInterval = 5
        singleStep = 1
        self.slider = guitools.FloatSlider(QtCore.Qt.Horizontal, self, allowScrollChanges=False,
                                           decimals=valueDecimals)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        valueRangeMin, valueRangeMax = valueRange

        self.slider.setMinimum(valueRangeMin)
        self.slider.setMaximum(valueRangeMax)
        self.slider.setTickInterval(tickInterval)
        self.slider.setSingleStep(singleStep)
        self.slider.setValue(0)

        # Vertical and horizontal lines
        self.vline = pg.InfiniteLine()
        self.hline = pg.InfiniteLine()
        self.rvline = pg.InfiniteLine()
        self.lvline = pg.InfiniteLine()
        self.uhline = pg.InfiniteLine()
        self.dhline = pg.InfiniteLine()

        # Viewbox
        self.cwidget = pg.GraphicsLayoutWidget()
        self.vb = self.cwidget.addViewBox(row=1, col=1)
        self.vb.setMouseMode(pg.ViewBox.RectMode)
        self.img = pg.ImageItem(axisOrder='row-major')
        self.img.setTransform(self.img.transform().translate(-0.5, -0.5))
        self.vb.addItem(self.img)
        self.vb.setAspectLocked(True)
        self.hist = pg.HistogramLUTItem(image=self.img)
        self.hist.vb.setLimits(yMin=0, yMax=66000)
        self.hist.gradient.loadPreset('greyclip')
        for tick in self.hist.gradient.ticks:
            tick.hide()
        self.cwidget.addItem(self.hist, row=1, col=2)

        # Add lines to viewbox
        self.vb.addItem(self.vline)
        self.vb.addItem(self.hline)
        self.vb.addItem(self.lvline)
        self.vb.addItem(self.rvline)
        self.vb.addItem(self.uhline)
        self.vb.addItem(self.dhline)

        # Add elements to GridLayout
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.cwidget, 0, 0, 1, 6)
        grid.addWidget(self.showCheck, 1, 0, 1, 1)
        grid.addWidget(self.slider, 1, 1, 1, 1)
        grid.addWidget(self.posCheck, 2, 0, 1, 1)
        grid.addWidget(self.linePos, 2, 1, 1, 1)
        grid.addWidget(self.labelRate, 2, 2, 1, 1)
        grid.addWidget(self.lineRate, 2, 3, 1, 1)

        # grid.setRowMinimumHeight(0, 300)

        # Connect signals
        self.showCheck.toggled.connect(self.sigShowToggled)
        self.posCheck.toggled.connect(self.sigPosToggled)
        self.slider.valueChanged.connect(
            lambda value: self.sigValueChanged.emit(value)
        )
        self.linePos.textChanged.connect(
            lambda: self.sigPosChanged.emit(self.getPos())
        )
        self.lineRate.textChanged.connect(
            lambda: self.sigUpdateRateChanged.emit(self.getUpdateRate())
        )
        self.vb.sigResized.connect(self.sigResized)

    def getShowHoliSheetChecked(self):
        return self.showCheck.isChecked()

    def getShowPosChecked(self):
        return self.posCheck.isChecked()

    def getPos(self):
        return float(self.linePos.text())

    def getUpdateRate(self):
        return float(self.lineRate.text())

    def getImage(self):
        return self.img.image

    def setImage(self, im):
        self.img.setImage(im, autoLevels=False)

    def updateImageLimits(self, imgWidth, imgHeight):
        pyqtgraphtools.setPGBestImageLimits(self.vb, imgWidth, imgHeight)

    def getImageDisplayLevels(self):
        return self.hist.getLevels()

    def setImageDisplayLevels(self, minimum, maximum):
        self.hist.setLevels(minimum, maximum)
        self.hist.vb.autoRange()

    def setPosLinesVisible(self, visible):
        self.vline.setVisible(visible)
        self.hline.setVisible(visible)
        self.rvline.setVisible(visible)
        self.lvline.setVisible(visible)
        self.uhline.setVisible(visible)
        self.dhline.setVisible(visible)

    def updatePosLines(self, pos, imgWidth, imgHeight):
        self.vline.setValue(0.5 * imgWidth)
        self.hline.setAngle(0)
        self.hline.setValue(0.5 * imgHeight)
        self.rvline.setValue((0.5 + pos) * imgWidth)
        self.lvline.setValue((0.5 - pos) * imgWidth)
        self.dhline.setAngle(0)
        self.dhline.setValue((0.5 - pos) * imgHeight)
        self.uhline.setAngle(0)
        self.uhline.setValue((0.5 + pos) * imgHeight)


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
