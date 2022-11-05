import json
import os

import numpy as np
import time
import tifffile as tif
import threading
from datetime import datetime
import cv2

from imswitch.imcommon.model import dirtools, initLogger, APIExport
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex, Timer
import time

from ..basecontrollers import LiveUpdatedController

#import NanoImagingPack as nip

class PixelCalibrationController(LiveUpdatedController):
    """Linked to PixelCalibrationWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self)

        # Connect PixelCalibrationWidget signals
        #self._widget.PixelCalibrationLabelInfo.clicked.connect()
        self._widget.PixelCalibrationSnapPreviewButton.clicked.connect(self.snapPreview)
        self._widget.PixelCalibrationUndoButton.clicked.connect(self.undoSelection)
        self._widget.PixelCalibrationCalibrateButton.clicked.connect(self.startPixelCalibration)
        self.pixelSize=0
        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]


    def undoSelection(self):
        # recover the previous selection
        self._widget.canvas.undoSelection()
        
    def snapPreview(self):
        self._logger.info("Snap preview...")
        self.previewImage = self.detector.getLatestFrame()
        self._widget.canvas.setImage(self.previewImage)
        
    def startPixelCalibration(self):
        # initilaze setup
        # this is not a thread!
        self.pixelSize = self._widget.getPixelSize()
        self._widget.setInformationLabel(str(self.pixelSize)+" µm")

    


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
