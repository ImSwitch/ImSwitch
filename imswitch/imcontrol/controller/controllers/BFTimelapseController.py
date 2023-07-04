import os
import time
import importlib
import enum
import h5py
import csv

from collections import deque
from datetime import datetime
from inspect import signature
import pyqtgraph as pg
import numpy as np
from tkinter.filedialog import askopenfilename

from imswitch.imcommon.model import dirtools
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import initLogger
from imswitch.imcommon.framework import Thread, Timer


class BFTimelapseController(ImConWidgetController):
    """ Linked to BFTimelapseWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._widget.setDetectorList(
            self._master.detectorsManager.execOnAll(lambda c: c.name,
                                                    condition=lambda c: c.forAcquisition)
        )

        # Connect BFTimelapseWidget signals
        self._widget.initiateButton.clicked.connect(self.initiate)

        # initiate flags and params
        self.__running = False
        self.__timerThread = TimerThread(self)


    def __del__(self):
        self.__timerThread.quit()
        self.__timerThread.wait()
        if hasattr(super(), '__del__'):
            super().__del__()

    def initiate(self):
        """ Initiate or stop an bftimelapse experiment. """
        if not self.__running:
            #detectorIdx = self._widget.detectorsPar.currentIndex()
            #self.detector = self._widget.detectors[detectorIdx]
            self.interval = int(self._widget.interval_edit.text())*1000  # in milliseconds
            # start timer that when timeouts: turns on wf lamp, takes image, and sleeps for the time set in widget GUI
            self.__timerThread.timer.start(self.interval)
            self._widget.initiateButton.setText('Stop')
            self.__running = True
        else:
            # stop thread loop
            self.__timerThread.timer.stop()
            self._widget.initiateButton.setText('Initiate')
            self.__running = False

    def closeEvent(self):
        pass


class TimerThread(Thread):
    def __init__(self, controller, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._controller = controller
        self.timer = Timer()
        self.timer.timeout.connect(self.timerLoopEnded)

    def timerLoopEnded(self):
        """ Snap a BFTimelapse image through communication channel -> recordingWidget, after turning on WF lamp in Leica stand. Turn off lamp after. """
        #TODO START WF LAMP
        #time.sleep(0.1)
        self._controller._commChannel.sigSnapImg.emit()
        #time.sleep(0.1)
        #TODO STOP WF LAMP




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
