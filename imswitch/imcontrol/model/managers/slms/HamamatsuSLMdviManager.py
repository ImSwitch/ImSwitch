import numpy as np
import skimage
from PyQt5.QtWidgets import QLabel
from qtpy import QtCore, QtGui

from imswitch.imcommon.framework import SignalInterface
from imswitch.imcommon.model import initLogger


class HamamatsuSLMdviManager(SignalInterface):
    """Manager for communication with Hamamatsu SLM with dvi connection"""

    def __init__(self, slmInfo, slmName, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        self.slmName = slmName
        self.slmInfo = slmInfo
        self.width = slmInfo.width
        self.height = slmInfo.height
        self.pixel_size = slmInfo.pixelSize

        self.preferredMonitor = slmInfo.monitorIdx

        if slmInfo.managerProperties is not None:
            self.mockermode = slmInfo.managerProperties.get("mockermode", False)

        if self.mockermode:
            self.__logger.info(
                f"SLM Manager {self.slmName} running in MOCKER MODE. No actual connection to SLM will be made.")
            self.dll = None

        # prepare the qwidget

        self.SLMQwindow = QLabel()
        self.imgArr = np.zeros((2, 2))

        self.setup_qlabel_as_display_output()


    def setup_qlabel_as_display_output(self):

        self.SLMQwindow.monitor = self.preferredMonitor
        self.SLMQwindow.setWindowTitle('SLM display')
        self.SLMQwindow.setWindowFlags(QtCore.Qt.Window)
        self.SLMQwindow.setWindowState(QtCore.Qt.WindowFullScreen)

        self.SLMQwindow.hasShownMonitorWarning = False

    def upload_pattern(self, pattern, slot_no=0):
        """ Upload pattern to SLM """

        if self.mockermode:
            self.__logger.info("Mocker mode - not uploading pattern to device.")
            return

        imgScaled = skimage.img_as_ubyte(
            skimage.transform.resize(pattern, (self.height, self.width), order=0)
        )

        qimage = QtGui.QImage(
            imgScaled, imgScaled.shape[1], imgScaled.shape[0], imgScaled.shape[1] * 3,
            QtGui.QImage.Format_RGB888
        )

        qpixmap = QtGui.QPixmap(qimage)
        self.SLMQwindow.setPixmap(qpixmap)




