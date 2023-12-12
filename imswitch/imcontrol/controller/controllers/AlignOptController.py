import os
from PyQt5.QtCore import pyqtSlot
from PyQt5 import QtWidgets

# import matplotlib.pyplot as plt
from functools import partial
import numpy as np
import pdb
import pyqtgraph as pg

from imswitch.imcommon.model import dirtools, initLogger
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.framework import Signal


class AlignOptController(ImConWidgetController):
    """ OPT scan controller.
    """
    sigImageReceived = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__logger = initLogger(self, tryInheritParent=True)
        self.optStack = np.ones((1, 1, 1))
        self.counterProj = np.ones((1, 1, 1))

        # Set up rotator in widget
        self._widget.initControls()
        self.isOptRunning = False

        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]

        # get rotators
        self.getRotators()
        self.__motor_steps = self._master.rotatorsManager[self.__rotators[0]]._motor._steps_per_turn
        self.__logger.debug(f'Your rotators {self.__rotators} with {self.__motor_steps} steps per revolution.')

        # Connect widget signals
        self._widget.scanPar['StartButton'].clicked.connect(self.getProj)
        self._widget.scanPar['PlotHorCuts'].clicked.connect(self.plotHorCuts)

    def processAlign(self, name):
        # subsample stack
        self.cor = AlignCOR(name, self.allFrames)
        self.cor.merge()
        self._widget.plotCounterProj(self.cor.merged)
        # self.sigImageReceived.disconnect()

    def plotHorCuts(self):
        # query the line indeces to get hor cuts.
        self.horIdxList = self.getHorCutIdxs()
        # process the hor cuts
        self.cor.processHorCuts(self.horIdxList)

        # plotting
        self._widget.plotHorCuts.addLegend()
        for i, px in enumerate(self.horIdxList):
            self._logger.info(f'plotting {i}, {px}')
            self._widget.plotHorCuts.plot(self.cor.horCuts[i][0], label=f'single {px}',
                                          pen=pg.mkPen('r'))
            self._widget.plotHorCuts.plot(self.cor.horCuts[i][1], label=f'merge {px}',
                                          pen=pg.mkPen('b'))

    def emitScanSignal(self, signal, *args):
        signal.emit(*args)

    def saveScanParamsToFile(self, filePath: str) -> None:
        """ Saves the set scanning parameters to the specified file. """
        self.getParameters()

    def loadScanParamsFromFile(self, filePath: str) -> None:
        """ Loads scanning parameters from the specified file. """
        self.setParameters()

    def enableWidgetInterface(self, enableBool):
        self._widget.enableInterface(enableBool)

    def getHorCutIdxs(self):
        return [int(k) for k in self._widget.getHorCutsIdxList().split()]

    def getRotationSteps(self):
        """ Get the total rotation steps. """
        return self._widget.getRotationSteps()

    def getRotators(self):
        """ Get a list of all rotators."""
        self.__rotators = self._master.rotatorsManager.getAllDeviceNames()

    def getProj(self):
        """ Reset and initiate Opt 0 and 180 degrees. """
        self.sigImageReceived.connect(self.processAlign)
        self._widget.scanPar['StartButton'].setEnabled(False)
        self._widget.scanPar['StopButton'].setEnabled(True)
        self._widget.scanPar['StartButton'].setText('Running')
        self._widget.scanPar['StopButton'].setText('Stop')
        self._widget.scanPar['StopButton'].setStyleSheet("background-color: red")
        self._widget.scanPar['StartButton'].setStyleSheet("background-color: green")

        # equidistant steps for the OPT scan in absolute values.
        curPos = self._master.rotatorsManager[self.__rotators[0]]._motor.current_pos[0]
        counterPos = (curPos + self.__motor_steps//2) % self.__motor_steps
        self.opt_steps = [curPos, counterPos]
        self.__logger.debug(f'OPT steps: {self.opt_steps}')
        self.allFrames = []
        # run OPT
        self.scanRecordOpt()

    def stopOpt(self):
        """Stop OPT acquisition and enable buttons
        """
        self.isOptRunning = False
        self.sigImageReceived.disconnect()
        self._master.rotatorsManager[self.__rotators[0]]._motor.opt_step_done.disconnect()
        self._widget.scanPar['StartButton'].setEnabled(True)
        self._widget.scanPar['StopButton'].setEnabled(False)
        self._widget.scanPar['StartButton'].setText("Start")
        self._widget.scanPar['StopButton'].setText("Stopped")
        self._widget.scanPar['StopButton'].setStyleSheet("background-color: green")
        self._widget.scanPar['StartButton'].setStyleSheet("background-color: red")
        self._logger.info("OPT stopped.")

    def scanRecordOpt(self):
        """Initiaate OPT with step 0 and setting flags.
        """
        if not self.isOptRunning:
            self.isOptRunning = True
            self.__currentStep = 0

            self._master.rotatorsManager[self.__rotators[0]]._motor.opt_step_done.connect(self.post_step)
            self.moveAbsRotator(self.__rotators[0], self.opt_steps[self.__currentStep])

    def post_step(self):
        """Acquire image after motor step is done, stop OPT in case of last step,
        otherwise move motor again.
        """
        frame = self.detector.getLatestFrame()
        if frame.shape[0] != 0:
            self.allFrames.append(frame)

        self.__currentStep += 1
        # TODO: fix display after every step
        # self.sigImageReceived.emit('OPT stack')
        if self.__currentStep > len(self.opt_steps)-1:
            self.optStack = np.array(self.allFrames)
            self.sigImageReceived.emit('mirror1-disp2')
            self.__logger.info(f'collected {len(self.optStack)} images')
            self.stopOpt()
        else:
            self.__logger.debug(f'post_step func, step{self.__currentStep}')
            self.moveAbsRotator(self.__rotators[0], self.opt_steps[self.__currentStep])

    def exec_plotHorCuts(self):
        pdb.set_trace()
        if self.cor.horCuts == []:
            print('empty list')
            return

    def exec_plotCounterProj(self):
        if self.cor.merged is None:
            self._logger.debug('No image to plot')
        self._widget.plotCounterProj(self.cor.merge)

    @pyqtSlot()
    def moveAbsRotator(self, name, dist):
        """ Move a specific rotator to a certain position. """
        self.__logger.debug(f'Scancontroller, dist to move: {dist}')
        self._master.rotatorsManager[name].move_abs_steps(dist)
        self.__logger.debug('Scancontroller, after move.')


class AlignCOR():
    def __init__(self, name, img_stack):
        self.name = name
        if len(img_stack) != 2:
            raise IndexError('AlignCOR expects stack of two images')
        self.img_stack = img_stack
        # mirror first of the images
        self.img_stack[0] = self.img_stack[0][:, ::-1]
        self.horCuts = []
        self.merged = None

    def merge(self):
        self.merged = np.array(self.img_stack).mean(axis=0).astype(np.int16)

    def processHorCuts(self, idx_list):
        self.horCuts = []
        for i in idx_list:
            try:
                # append tuple of first from stack and merged one at given idx
                self.horCuts.append((self.img_stack[0][i], self.merged[i]))
            except IndexError:
                # TODO: this has to update the valid idx list too
                print('Index out of range')

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
