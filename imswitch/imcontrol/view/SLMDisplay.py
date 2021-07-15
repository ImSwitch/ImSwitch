import numpy as np
import skimage
import skimage.transform
from qtpy import QtCore, QtGui, QtWidgets


class SLMDisplay(QtWidgets.QLabel):
    """ Full-screen SLM display. """

    def __init__(self, monitor):
        super().__init__()
        self.setWindowTitle('SLM display')
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setWindowState(QtCore.Qt.WindowFullScreen)

        self.monitor, self.imgWidth, self.imgHeight = self.setMonitor(monitor)
        self.imgArr = np.zeros((2, 2))

    def setMonitor(self, monitor):
        app = QtWidgets.QApplication.instance()
        screens = app.screens()

        tryMonitor = monitor

        if len(screens) < 1:
            raise RuntimeError('No monitors available, cannot set monitor for SLM')

        while tryMonitor > len(screens) - 1:
            tryMonitor -= 1  # Try other monitor

        screenGeom = screens[tryMonitor].geometry()
        self.move(screenGeom.left(), screenGeom.top())
        return tryMonitor, screenGeom.width(), screenGeom.height()
        
    def updateImage(self, imgArr):
        self.imgArr = imgArr

        if not self.isVisible():
            return

        imgScaled = skimage.img_as_ubyte(
            skimage.transform.resize(self.imgArr, (self.imgHeight, self.imgWidth), order=0)
        )

        qimage = QtGui.QImage(
            imgScaled, imgScaled.shape[1], imgScaled.shape[0], imgScaled.shape[1] * 3,
            QtGui.QImage.Format_RGB888
        )

        qpixmap = QtGui.QPixmap(qimage)
        self.setPixmap(qpixmap)

    def setVisible(self, visible):
        super().setVisible(visible)

        if visible:
            self.updateImage(self.imgArr)


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
