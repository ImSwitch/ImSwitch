from typing import List, Union

import os
import ctypes
import importlib

from collections import deque
from datetime import datetime
from tkinter import Tk
from inspect import signature
from tkinter.filedialog import askopenfilename
from scipy.optimize import least_squares
import scipy.ndimage as ndi
import pyqtgraph as pg
import numpy as np

from imswitch.imcommon.model import APIExport
from imswitch.imcontrol.model import configfiletools
from imswitch.imcommon.model import dirtools
from imswitch.imcontrol.view import guitools
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import initLogger

_etstedDir = os.path.join(dirtools.UserFileDirs.Root, 'imcontrol_etsted')
_logsDir = os.path.join(dirtools.UserFileDirs.Root, 'recordings', 'logs_etsted')


# HIGH-RES TIMING FUNCTIONS FROM https://stackoverflow.com/questions/38319606/how-can-i-get-millisecond-and-microsecond-resolution-timestamps-in-python/38319607#38319607
def micros():
    "return a timestamp in microseconds (us)"
    tics = ctypes.c_int64()
    freq = ctypes.c_int64()

    #get ticks on the internal ~2MHz QPC clock
    ctypes.windll.Kernel32.QueryPerformanceCounter(ctypes.byref(tics)) 
    #get the actual freq. of the internal ~2MHz QPC clock
    ctypes.windll.Kernel32.QueryPerformanceFrequency(ctypes.byref(freq))  
    
    t_us = tics.value*1e6/freq.value
    return t_us
    
def millis():
    "return a timestamp in milliseconds (ms)"
    tics = ctypes.c_int64()
    freq = ctypes.c_int64()

    #get ticks on the internal ~2MHz QPC clock
    ctypes.windll.Kernel32.QueryPerformanceCounter(ctypes.byref(tics)) 
    #get the actual freq. of the internal ~2MHz QPC clock 
    ctypes.windll.Kernel32.QueryPerformanceFrequency(ctypes.byref(freq)) 
    
    t_ms = tics.value*1e3/freq.value
    return t_ms


class EtSTEDController(ImConWidgetController):
    """ Linked to EtSTEDWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        self.__logger.debug('Initializing')

        self.analysisDir = os.path.join(_etstedDir, 'analysis_pipelines')

        # detectors for fast (widefield) and slow (sted) imaging, and laser for fast
        self.detectorFast = self._setupInfo.etSTED.detectorFast
        self.detectorSlow = self._setupInfo.etSTED.detectorSlow
        self.laserFast = self._setupInfo.etSTED.laserFast

        # create a helper controller for the coordinate transform pop-out widget
        self.__coordTransformHelper = EtSTEDCoordTransformHelper(self, self._widget.coordTransformWidget, _logsDir)

        # Initiate coordinate transform coeffs
        self.__transformCoeffs = np.ones(20)

        # Connect EtSTEDWidget and communication channel signals
        self._widget.initiateButton.clicked.connect(self.initiate)
        self._widget.loadPipelineButton.clicked.connect(self.loadPipeline)
        self._widget.recordBinaryMaskButton.clicked.connect(self.initiateBinaryMask)
        self._widget.loadScanParametersButton.clicked.connect(self.setScanParameters)
        self._widget.setUpdatePeriodButton.clicked.connect(self.setUpdatePeriod)
        self._widget.setBusyFalseButton.clicked.connect(self.setBusyFalse)
        self._commChannel.sendScanParameters.connect(lambda analogParams, digitalParams: self.assignScanParameters(analogParams, digitalParams))

        # create scatter plot item for sending to the viewbox in the help widget while analysis is running
        self.__scatterPlot = pg.ScatterPlotItem()
        self.addScatter()

        # initiate log for each detected event
        self.__detLog = {
            "pipeline_start": "",
            "pipeline_end": "",
            "coord_transf_start": "",
            "fastscan_x_center": 0,
            "fastscan_y_center": 0,
            "slowscan_x_center": 0,
            "slowscan_y_center": 0
        }

        # initiate flags and params
        self.__running = False
        self.__validating = False
        self.__busy = False
        self.__visualizeMode = False
        self.__validateMode = False
        self.__bkg = None
        self.__prevFrames = deque(maxlen=10)
        self.__prevAnaFrames = deque(maxlen=10)
        self.__binary_mask = None
        self.__binary_stack = None
        self.__binary_frames = 10
        self.__init_frames = 5
        self.__validationFrames = 0
        self.__frame = 0
        self.__imgstack = []

        self.t_call = 0


    def initiate(self):
        pass

    def loadPipeline(self):
        pass

    def initiateBinaryMask(self):
        pass

    def setScanParameters(self):
        pass

    def setUpdatePeriod(self):
        pass

    def setBusyFalse(self):
        pass

    def assignScanParameters(self, analogParams, digitalParams):
        pass

    def addScatter(self):
        pass

    def closeEvent(self):
        pass


class EtSTEDCoordTransformHelper():
    """ Coordinate transform help widget controller. """
    def __init__(self, etSTEDController, coordTransformWidget, saveFolder, *args, **kwargs):
        
        etSTEDController._widget.coordTransfCalibButton.clicked.connect(self.calibrationLaunch)


    def calibrationLaunch(self):
        pass

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
