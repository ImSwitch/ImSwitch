import numpy as np
import pyqtgraph as pg
import pyqtgraph.ptime as ptime
from qtpy import QtCore, QtGui, QtWidgets


def setBestImageLimits(viewBox, width, height):
    viewBox.setAspectLocked()
    viewBox.setLimits(xMin=None, xMax=None, yMin=None, yMax=None)

    viewBox.setRange(xRange=(-0.5, width - 0.5), yRange=(-0.5, height - 0.5), padding=0)
    viewBounds = viewBox.viewRange()
    viewBox.setLimits(xMin=viewBounds[0][0], xMax=viewBounds[0][1],
                      yMin=viewBounds[1][0], yMax=viewBounds[1][1])


class Grid:
    def __init__(self, viewBox):
        self.showed = False
        self.vb = viewBox
        self.shape = None
        pen = QtGui.QPen(QtCore.Qt.yellow, 2, QtCore.Qt.DotLine)
        pen2 = QtGui.QPen(QtCore.Qt.yellow, 2.5, QtCore.Qt.SolidLine)

        self.yline1 = pg.InfiniteLine(pen=pen)
        self.yline2 = pg.InfiniteLine(pen=pen)
        self.yline3 = pg.InfiniteLine(pen=pen2)
        self.yline4 = pg.InfiniteLine(pen=pen)
        self.yline5 = pg.InfiniteLine(pen=pen)
        self.xline1 = pg.InfiniteLine(pen=pen, angle=0)
        self.xline2 = pg.InfiniteLine(pen=pen2, angle=0)
        self.xline3 = pg.InfiniteLine(pen=pen2, angle=0)
        self.xline4 = pg.InfiniteLine(pen=pen2, angle=0)
        self.xline5 = pg.InfiniteLine(pen=pen, angle=0)
        self.vb.addItem(self.xline1)
        self.vb.addItem(self.xline2)
        self.vb.addItem(self.xline3)
        self.vb.addItem(self.xline4)
        self.vb.addItem(self.xline5)
        self.vb.addItem(self.yline1)
        self.vb.addItem(self.yline2)
        self.vb.addItem(self.yline3)
        self.vb.addItem(self.yline4)
        self.vb.addItem(self.yline5)
        self.hide()

    def update(self, shape):
        self.yline1.setPos(0.25 * shape[0])
        self.yline2.setPos(0.375 * shape[0])
        self.yline3.setPos(0.50 * shape[0])
        self.yline4.setPos(0.625 * shape[0])
        self.yline5.setPos(0.75 * shape[0])
        self.xline1.setPos(0.25 * shape[1])
        self.xline2.setPos(0.375 * shape[1])
        self.xline3.setPos(0.50 * shape[1])
        self.xline4.setPos(0.625 * shape[1])
        self.xline5.setPos(0.75 * shape[1])

    def toggle(self):
        if self.showed:
            self.hide()
        else:
            self.show()

    def show(self):
        self.setVisible(True)

    def hide(self):
        self.setVisible(False)

    def setVisible(self, visible):
        self.yline1.setVisible(visible)
        self.yline2.setVisible(visible)
        self.yline3.setVisible(visible)
        self.yline4.setVisible(visible)
        self.yline5.setVisible(visible)
        self.xline1.setVisible(visible)
        self.xline2.setVisible(visible)
        self.xline3.setVisible(visible)
        self.xline4.setVisible(visible)
        self.xline5.setVisible(visible)
        self.showed = visible


class TwoColorGrid:
    def __init__(self, viewBox, shape=(512, 512)):
        self.showed = False
        self.vb = viewBox
        self.shape = shape

        pen = QtGui.QPen(QtCore.Qt.yellow, 1, QtCore.Qt.SolidLine)
        pen2 = QtGui.QPen(QtCore.Qt.yellow, 0.75, QtCore.Qt.DotLine)

        self.rectT = QtWidgets.QGraphicsRectItem(192, 118, 128, 128)
        self.rectT.setPen(pen)
        self.rectR = QtWidgets.QGraphicsRectItem(192, 266, 128, 128)
        self.rectR.setPen(pen)
        self.yLine = pg.InfiniteLine(pos=0.5 * self.shape[0], pen=pen2)
        self.xLine = pg.InfiniteLine(pos=0.5 * self.shape[1], pen=pen2, angle=0)
        self.xLineT = pg.InfiniteLine(pos=182, pen=pen2, angle=0)
        self.xLineR = pg.InfiniteLine(pos=330, pen=pen2, angle=0)

    def toggle(self):
        if self.showed:
            self.hide()
        else:
            self.show()

    def show(self):
        self.setVisible(True)

    def hide(self):
        self.setVisible(False)

    def setVisible(self, visible):
        func = self.vb.addItem if visible else self.vb.removeItem
        func(self.rectT)
        func(self.rectR)
        func(self.yLine)
        func(self.xLine)
        func(self.xLineR)
        func(self.xLineT)
        self.showed = visible


class Crosshair:
    def __init__(self, viewBox):
        self.showed = False

        self.vLine = pg.InfiniteLine(pos=0, angle=90, movable=False)
        self.hLine = pg.InfiniteLine(pos=0, angle=0, movable=False)
        self.vb = viewBox
        self.vb.addItem(self.vLine, ignoreBounds=False)
        self.vb.addItem(self.hLine, ignoreBounds=False)
        self.hide()

    def mouseMoved(self, pos):
        if self.vb.sceneBoundingRect().contains(pos):
            mousePoint = self.vb.mapSceneToView(pos)
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())

    def mouseClicked(self):
        try:
            self.vb.scene().sigMouseMoved.disconnect(self.mouseMoved)
        except:
            pass

    def toggle(self):
        if self.showed:
            self.hide()
        else:
            self.show()

    def show(self):
        self.vb.scene().sigMouseClicked.connect(self.mouseClicked)
        self.vb.scene().sigMouseMoved.connect(self.mouseMoved)
        self.vLine.show()
        self.hLine.show()
        self.showed = True

    def hide(self):
        self.vLine.hide()
        self.hLine.hide()
        self.showed = False

    def setVisible(self, visible):
        if visible:
            self.show()
        else:
            self.hide()


class ROI(pg.ROI):
    def __init__(self, shape, pos, handlePos, handleCenter, color, *args,
                 **kwargs):
        self.mainShape = shape

        pg.ROI.__init__(self, pos, size=shape, pen=color, *args, **kwargs)
        self.addScaleHandle(handlePos, handleCenter, lockAspect=True)

        self.label = pg.TextItem()
        self.label.setPos(self.pos()[0] + self.size()[0],
                          self.pos()[1] + self.size()[1])
        self.label.setText('{}x{}'.format(shape[0], shape[1]))

        self.sigRegionChanged.connect(self.updateText)

    def updateText(self):
        self.label.setPos(self.pos()[0] + self.size()[0],
                          self.pos()[1] + self.size()[1])
        size = np.round(self.size()).astype(np.int)
        self.label.setText('{}x{}'.format(size[0], size[1]))

    def hide(self, *args, **kwargs):
        super().hide(*args, **kwargs)
        self.label.hide()

    def show(self, *args, **kwargs):
        super().show(*args, **kwargs)
        self.label.show()


class cropROI(pg.ROI):
    def __init__(self, shape, vb, *args, **kwargs):
        self.mainShape = shape

        pg.ROI.__init__(self, pos=(shape[0], shape[1]), size=(128, 128),
                        scaleSnap=True, translateSnap=True, movable=False,
                        pen='y', *args, **kwargs)
        self.addScaleHandle((0, 1), (1, 0))


class SumpixelsGraph(pg.GraphicsLayoutWidget):
    """The graph window class"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle('Average of area')
        self.setAntialiasing(True)

        self.npoints = 400
        self.data = np.zeros(self.npoints)
        self.ptr = 0

        # Graph without a fixed range
        self.statistics = pg.LabelItem(justify='right')
        self.addItem(self.statistics)
        self.statistics.setText('---')
        self.plot = self.addPlot(row=1, col=0)
        self.plot.setLabels(bottom=('Time', 's'), left=('Intensity', 'au'))
        self.plot.showGrid(x=True, y=True)
        self.sumCurve = self.plot.plot(pen='y')

        self.time = np.zeros(self.npoints)
        self.startTime = ptime.time()

    def resetData(self):
        """Set all data points to zero, useful if going from very large values
        to very small values"""
        self.data = np.zeros(self.npoints)
        self.time = np.zeros(self.npoints)
        self.startTime = ptime.time()
        self.ptr = 0

    def updateGraph(self, value):
        """ Update the data displayed in the graphs
        """
        if self.ptr < self.npoints:
            self.data[self.ptr] = value
            self.time[self.ptr] = ptime.time() - self.startTime
            self.sumCurve.setData(self.time[1:self.ptr + 1],
                                  self.data[1:self.ptr + 1])

        else:
            self.data[:-1] = self.data[1:]
            self.data[-1] = value
            self.time[:-1] = self.time[1:]
            self.time[-1] = ptime.time() - self.startTime

            self.sumCurve.setData(self.time, self.data)

        self.ptr += 1


class ProjectionGraph(pg.GraphicsLayoutWidget):
    """The graph window class"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle('Average of area')
        self.setAntialiasing(True)

        self.npoints = 400
        self.data = np.zeros(self.npoints)
        self.ptr = 0

        # Graph without a fixed range
        self.statistics = pg.LabelItem(justify='right')
        self.addItem(self.statistics)
        self.statistics.setText('---')
        self.plot = self.addPlot(row=1, col=0)
        self.plot.setLabels(bottom=('Time', 's'),
                            left=('Intensity', 'au'))
        self.plot.showGrid(x=True, y=True)
        self.sumCurve = self.plot.plot(pen='y')

        self.startTime = ptime.time()

    def updateGraph(self, values):
        """ Update the data displayed in the graphs
        """
        self.data = values
        self.sumCurve.setData(np.arange(len(self.data)), self.data)


# Copyright (C) 2017 Federico Barabas
# This file is part of Tormenta.
#
# Tormenta is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tormenta is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
