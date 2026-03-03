import sys

import numpy as np
import skimage
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QLabel, QApplication
from cupy import asfortranarray
from matplotlib import pyplot as plt
from qtpy import QtCore, QtGui

from imswitch.imcommon.framework import SignalInterface
from imswitch.imcommon.model import initLogger


class HamamatsuSLMdviManager(SignalInterface):
    """Manager for communication with Hamamatsu SLM with dvi connection"""
    
    requires_device_connection: bool = False

    def __init__(self, slmInfo, slmName, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        self.slmName = slmName
        self.slmInfo = slmInfo
        self.width = slmInfo.width
        self.height = slmInfo.height
        self.__logger.debug(self.slmInfo)
        self.pixel_size = slmInfo.pixelSize

        self.preferredMonitor = slmInfo.monitorIdx

        if slmInfo.managerProperties is not None:
            self.mockermode = slmInfo.managerProperties.get("mockermode", False)

        if self.mockermode:
            self.__logger.info(
                f"SLM Manager {self.slmName} running in MOCKER MODE. No actual connection to SLM will be made.")

        # prepare the qwidget

        self.SLMQLabel = QLabel()
        self.imgArr = np.random.randint(1, 250, size=(self.width, self.height), dtype=np.uint8)

        self.init_slm_window()

    @property
    def requires_device_connection(self):
        return False

    def init_slm_window(self):
        """Init SLM QLabel as fullscreen wundow and show a random pattern on specified screen"""

        app = QApplication.instance()

        screens = list(app.screens())

        if self.preferredMonitor >= len(screens):
            raise RuntimeError(f"Preferred monitor {self.preferredMonitor} is not available")

        screen = screens[self.preferredMonitor]
        geo = screen.geometry()

        self.width = geo.width()
        self.height = geo.height()

        self.__logger.debug(f"Screen geometry: {self.width}x{self.height}")

        self.SLMQLabel.setWindowFlags(QtCore.Qt.Window)
        self.SLMQLabel.setWindowTitle("SLM display")

        self.SLMQLabel.setGeometry(geo)
        self.SLMQLabel.move(geo.topLeft())

        self.SLMQLabel.setScaledContents(False)
        self.SLMQLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.SLMQLabel.showFullScreen()

    def upload_pattern(self, pattern, slot_no=0):
        """ Upload pattern to SLM """

        if self.mockermode:
            self.__logger.info("Mocker mode - not uploading pattern to device.")
            return

        pix = self._array_to_qpixmap(pattern)
        self.SLMQLabel.setPixmap(pix)

    def finalize(self):
        pass

    def connect_to_device(self):
        pass

    def close_device(self):
        pass


    def _array_to_qpixmap(self, arr2d: np.ndarray) -> QtGui.QPixmap:
        """
        Converts a numpy array to RGB888 QPixmap.
        """
        array = np.ascontiguousarray(arr2d, dtype=np.uint8)

        w, h = array.shape

        if h != self.height or w != self.width:
            self.__logger.warning(f"Pattern shape {array.shape} does not match SLM {self.width} x {self.height} shape")

            array = skimage.transform.resize(array, (self.height, self.width), order=0, preserve_range=True)

            h = self.height
            w = self.width

        rgb = np.repeat(array[:, :, None], 3, axis=2)

        rgb = np.ascontiguousarray(rgb)

        qimg = QtGui.QImage(rgb.data, w, h, w * 3, QtGui.QImage.Format_RGB888).copy()

        return QtGui.QPixmap.fromImage(qimg)








