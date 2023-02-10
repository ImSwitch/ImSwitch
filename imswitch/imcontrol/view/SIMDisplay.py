import numpy as np
import skimage
import skimage.transform
from qtpy import QtCore, QtGui, QtWidgets


class SIMDisplay(QtWidgets.QLabel):
    """ Full-screen SIM display. """

    sigClosed = QtCore.Signal()

    def __init__(self, parent, preferredMonitor):
        super().__init__()

        self._parent = parent

        self.setWindowTitle('SIM display')
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowState(QtCore.Qt.WindowFullScreen)

        self.setMonitor(preferredMonitor)
        self.imgArr = np.zeros((2, 2))
        self.hasShownMonitorWarning = False

    def setMonitor(self, monitor, updateImage=False):
        app = QtWidgets.QApplication.instance()
        screens = app.screens()

        self.preferredMonitor = monitor
        tryMonitor = monitor

        if len(screens) < 1:
            raise RuntimeError('No monitors available, cannot set monitor for SIM')

        while tryMonitor > len(screens) - 1:
            tryMonitor -= 1  # Try other monitor

        screenGeom = screens[tryMonitor].geometry()
        self.setGeometry(screenGeom)

        self.monitor = tryMonitor
        self.monitorName = screens[tryMonitor].name()
        self.imgWidth = screenGeom.width()
        self.imgHeight = screenGeom.height()

        if updateImage:
            self.updateImage(self.imgArr)

    def updateImage(self, imgArr, isFlip=True):
        if len(imgArr.shape)<3:
            imgArr=np.stack((imgArr,imgArr,imgArr), 2)
        self.imgArr = np.transpose(imgArr, (1,0,2))
        if isFlip:
            self.imgArr = np.flip(self.imgArr,0)
        if not self.isVisible():
            return
        # todo: This operation is expensive! -> skimage.transform.resize( do that outside the thread!!
        #imgScaled = skimage.img_as_ubyte(
        #    skimage.transform.resize(self.imgArr, (self.imgHeight, self.imgWidth), order=0)
        #)
        imgScaled = self.imgArr.copy()
        qimage = QtGui.QImage(
            imgScaled, imgScaled.shape[1], imgScaled.shape[0], QtGui.QImage.Format_RGB888
        )
        qpixmap = QtGui.QPixmap(qimage)
        self.setPixmap(qpixmap)
        
    def setVisible(self, visible):
        super().setVisible(visible)

        if visible:
            # Update monitor to display on (in case the user has (dis)connected a monitor)
            self.setMonitor(self.preferredMonitor)

            # Show warning if SIM display is shown over ImSwitch
            parentMonitorName = self._parent.screen().name()
            if (not self.hasShownMonitorWarning and
                    parentMonitorName and parentMonitorName == self.monitorName):
                QtWidgets.QMessageBox.information(
                    self, 'SIM display information',
                    f'The SIM display will be displayed over ImSwitch, since it is configured to be'
                    f' displayed on screen {self.monitor}, which is the same screen that ImSwitch'
                    f' currently is displayed on. You can close the SIM display by pressing the'
                    f' escape key on your keyboard.'
                )
                self.hasShownMonitorWarning = True

            # Focus window
            self.activateWindow()

            # Update image
            self.updateImage(self.imgArr)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        self.sigClosed.emit()


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
