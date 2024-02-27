from qtpy import QtCore, QtWidgets
import numpy as np
import pyqtgraph as pg
import time

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import NapariHybridWidget


class ScanWidgetOpt(NapariHybridWidget):
    """ Widget controlling OPT experiments where a rotation stage is triggered
    """

    sigRotStepDone = QtCore.Signal()
    sigRunScanClicked = QtCore.Signal()
    # sigSetImage = QtCore.Signal()

    def __post_init__(self, *args, **kwargs):
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        self.scanPar = {}
        self.enabled = True
        self.layer = None

    def initControls(self):
        # populate widget
        self.widgetLayout()

    def getRotatorIdx(self):
        """Returns currently selected rotator for the OPT
        """
        return self.scanPar['Rotator'].currentIndex()

    def getOptSteps(self) -> int:
        """ Returns the user-input number of OPTsteps. """
        return self.scanPar['OptStepsEdit'].value()

    def setOptSteps(self, value: int) -> None:
        """ Setter for number for OPT steps. """
        self.scanPar['OptStepsEdit'].setValue(value)

    def getHotStd(self) -> float:
        """ Returns the user-input STD cutoff for the hot pixel correction. """
        return self.scanPar['HotPixelsStdEdit'].value()

    def getAverages(self) -> int:
        """ Returns the user-input number of averages for the
        hot pixel correction.
        """
        return self.scanPar['AveragesEdit'].value()

    def getLiveReconIdx(self) -> int:
        return self.scanPar['LiveReconIdxEdit'].value()

    def setLiveReconIdx(self, value: int) -> None:
        self.scanPar['LiveReconIdxEdit'].setValue(int(value))

    def updateHotPixelCount(self, count):
        self.scanPar['HotPixelCount'].setText(f'Count: {count:d}')

    def updateHotPixelMean(self, value):
        self.scanPar['HotPixelMean'].setText(f'Hot mean: {value:.3f}')

    def updateNonHotPixelMean(self, value):
        self.scanPar['NonHotPixelMean'].setText(f'Non-hot mean: {value:.3f}')

    def updateDarkMean(self, value):
        self.scanPar['DarkMean'].setText(f'Dark mean: {value:.2f}')

    def updateDarkStd(self, value):
        self.scanPar['DarkStd'].setText(f'Dark STD: {value:.2f}')

    def updateFlatMean(self, value):
        self.scanPar['FlatMean'].setText(f'Flat mean: {value:.2f}')

    def updateFlatStd(self, value):
        self.scanPar['FlatStd'].setText(f'Flat STD: {value:.2f}')

    def updateCurrentStep(self, value='-'):
        self.scanPar['CurrentStepLabel'].setText(
            f'Current Step: {value}/{self.getOptSteps()}'
        )

    def updateCurrentReconStep(self, value='-'):
        self.scanPar['CurrentReconStepLabel'].setText(
            f'Current Recon: {value}/{self.getOptSteps()}'
        )

    def setRotStepEnable(self, enabled):
        """ For inactivating during scanning when ActivateButton pressed
        and waiting for a scan. When scan finishes, enable again. """
        self.scanPar['OptStepsEdit'].setEnabled(enabled)

    def setImage(self, im, colormap="gray", name="",
                 pixelsize=(1, 20, 20), translation=(0, 0, 0), step=0):
        print('IN THE setImage')
        if len(im.shape) == 2:
            print('2D image supposedly', im.shape)
            translation = (translation[0], translation[1])

        print(self.layer, self.viewer.layers, name)
        if self.layer is None or name not in self.viewer.layers:
            print('im', im.shape)
            self.layer = self.viewer.add_image(im, rgb=False,
                                               colormap=colormap,
                                               scale=pixelsize,
                                               translate=translation,
                                               name=name,
                                               blending='translucent')
        try:
            print('try setImage', step, im.shape, (step+1, im.shape[1], im.shape[2]))
            self.viewer.dims.current_step = (step, im.shape[1], im.shape[2])
        except Exception as e:
            print('Except from dims', e)
        self.layer.data = im
        self.layer.contrast_limits = (np.min(im), np.max(im))
        print('end of setImage', self.layer.data.shape)
        time.sleep(0.2)

    def widgetLayout(self):
        self.scanPar['GetHotPixels'] = guitools.BetterPushButton('Hot Pixels')

        self.scanPar['HotPixelsStdEdit'] = QtWidgets.QDoubleSpinBox()
        self.scanPar['HotPixelsStdEdit'].setRange(1, 100)  # step 1 by default
        self.scanPar['HotPixelsStdEdit'].setValue(5)
        self.scanPar['HotPixelsStdEdit'].setDecimals(1)
        self.scanPar['HotPixelsStdEdit'].setToolTip(
            'Hot pixel is identified as counts > mean + STD.',
            )
        self.scanPar['HotPixelsStdLabel'] = QtWidgets.QLabel('STD cutoff')

        self.scanPar['AveragesEdit'] = QtWidgets.QSpinBox()
        self.scanPar['AveragesEdit'].setRange(1, 1000)  # step is 1 by default
        self.scanPar['AveragesEdit'].setValue(30)
        self.scanPar['AveragesEdit'].setToolTip(
            'Average N frames for Hot pixels aquistion.',
            )
        self.scanPar['AveragesLabel'] = QtWidgets.QLabel('Averages')

        self.scanPar['HotPixelCount'] = QtWidgets.QLabel(f'Count: {0:d}')
        self.scanPar['HotPixelMean'] = QtWidgets.QLabel(f'Hot mean: {0:.2f}')
        self.scanPar['NonHotPixelMean'] = QtWidgets.QLabel(
            f'Non-hot mean: {0:.2f}',
            )

        # darkfield
        self.scanPar['GetDark'] = guitools.BetterPushButton('Dark-field')
        self.scanPar['DarkMean'] = QtWidgets.QLabel(f'Dark mean: {0:.2f}')
        self.scanPar['DarkStd'] = QtWidgets.QLabel(f'Dark STD: {0:.2f}')

        # brightfield
        self.scanPar['GetFlat'] = guitools.BetterPushButton('Bright-field')
        self.scanPar['FlatMean'] = QtWidgets.QLabel(f'Flat mean: {0:.2f}')
        self.scanPar['FlatStd'] = QtWidgets.QLabel(f'Flat STD: {0:.2f}')

        # OPT
        self.scanPar['RotStepsLabel'] = QtWidgets.QLabel('OPT rot. steps')
        self.scanPar['OptStepsEdit'] = QtWidgets.QSpinBox()
        self.scanPar['OptStepsEdit'].setRange(2, 10000)  # step is 1 by default
        self.scanPar['OptStepsEdit'].setValue(200)
        self.scanPar['OptStepsEdit'].setToolTip(
            'Steps taken per revolution of OPT scan',
            )
        self.scanPar['CurrentStepLabel'] = QtWidgets.QLabel(
            f'Current Step: -/{self.getOptSteps()}')

        self.scanPar['Rotator'] = QtWidgets.QComboBox()
        self.scanPar['RotatorLabel'] = QtWidgets.QLabel('Rotator')
        self.scanPar['StepsPerRevLabel'] = QtWidgets.QLabel(f'{0:d} steps/rev')

        self.scanPar['LiveReconButton'] = QtWidgets.QCheckBox(
            'Live reconstruction',
            )
        self.scanPar['LiveReconButton'].setCheckable(True)
        self.scanPar['LiveReconIdxEdit'] = QtWidgets.QSpinBox()
        self.scanPar['LiveReconIdxEdit'].setRange(0, 10000)  # step 1 by default
        self.scanPar['LiveReconIdxEdit'].setValue(200)
        self.scanPar['LiveReconIdxEdit'].setToolTip(
            'Line px of the camera to reconstruct live via FBP',
            )
        self.scanPar['LiveReconIdxLabel'] = QtWidgets.QLabel('Recon Idx')
        self.scanPar['CurrentReconStepLabel'] = QtWidgets.QLabel(
            f'Current Recon: -/{self.getOptSteps()}',
            )

        self.scanPar['MockOpt'] = QtWidgets.QCheckBox(
            'Demo experiment',
            )
        self.scanPar['MockOpt'].setCheckable(True)

        # Start and Stop buttons
        self.scanPar['StartButton'] = QtWidgets.QPushButton('Start')
        self.scanPar['StopButton'] = QtWidgets.QPushButton('Stop')
        self.scanPar['PlotReportButton'] = QtWidgets.QPushButton('Report')
        self.scanPar['SaveButton'] = QtWidgets.QCheckBox('Save')
        self.scanPar['SaveButton'].setCheckable(True)
        self.scanPar['noRamButton'] = QtWidgets.QCheckBox('no RAM')
        self.scanPar['noRamButton'].setCheckable(True)

        self.liveReconPlot = pg.ImageView()
        self.intensityPlot = pg.PlotWidget()

        # tab for plots
        self.tabs = QtWidgets.QTabWidget()
        self.tabRecon = QtWidgets.QWidget()
        self.grid2 = QtWidgets.QGridLayout()
        self.tabRecon.setLayout(self.grid2)
        self.grid2.addWidget(self.liveReconPlot, 0, 0)

        self.tabInt = QtWidgets.QWidget()
        self.grid3 = QtWidgets.QGridLayout()
        self.tabInt.setLayout(self.grid3)
        self.grid3.addWidget(self.intensityPlot)

        # Add tabs
        self.tabs.addTab(self.tabRecon, "Recon")
        self.tabs.addTab(self.tabInt, "Intensity")

        currentRow = 0
        # corrections
        self.grid.addWidget(QtWidgets.QLabel('<strong>Corrections:</strong>'),
                            currentRow, 0)
        self.grid.addWidget(self.scanPar['AveragesEdit'], currentRow, 1)
        self.grid.addWidget(self.scanPar['AveragesLabel'], currentRow, 2)

        currentRow += 1

        self.grid.addWidget(self.scanPar['GetHotPixels'], currentRow, 0)
        self.grid.addWidget(self.scanPar['HotPixelsStdEdit'], currentRow, 1)
        self.grid.addWidget(self.scanPar['HotPixelsStdLabel'], currentRow, 2)

        currentRow += 1

        self.grid.addWidget(self.scanPar['HotPixelCount'], currentRow, 0)
        self.grid.addWidget(self.scanPar['HotPixelMean'], currentRow, 1)
        self.grid.addWidget(self.scanPar['NonHotPixelMean'], currentRow, 2)

        currentRow += 1

        self.grid.addWidget(self.scanPar['GetDark'], currentRow, 0)
        self.grid.addWidget(self.scanPar['DarkMean'], currentRow, 1)
        self.grid.addWidget(self.scanPar['DarkStd'], currentRow, 2)

        currentRow += 1

        self.grid.addWidget(self.scanPar['GetFlat'], currentRow, 0)
        self.grid.addWidget(self.scanPar['FlatMean'], currentRow, 1)
        self.grid.addWidget(self.scanPar['FlatStd'], currentRow, 2)

        # OPT settings
        currentRow += 1
        self.grid.addWidget(self.scanPar['RotatorLabel'], currentRow, 0)
        self.grid.addWidget(self.scanPar['Rotator'], currentRow, 1)
        self.grid.addWidget(self.scanPar['StepsPerRevLabel'], currentRow, 2)

        currentRow += 1

        self.grid.addWidget(self.scanPar['RotStepsLabel'], currentRow, 0)
        self.grid.addWidget(self.scanPar['OptStepsEdit'], currentRow, 1)
        self.grid.addWidget(self.scanPar['MockOpt'], currentRow, 2)

        currentRow += 1

        self.grid.addWidget(self.scanPar['LiveReconButton'], currentRow, 0)
        self.grid.addWidget(self.scanPar['LiveReconIdxEdit'], currentRow, 1)
        self.grid.addWidget(self.scanPar['LiveReconIdxLabel'], currentRow, 2)

        currentRow += 1

        self.grid.addWidget(self.scanPar['CurrentStepLabel'], currentRow, 0)
        # self.grid.addWidget(self.scanPar['CurrentReconStepLabel'], currentRow, 1)
        self.grid.addWidget(self.scanPar['SaveButton'], currentRow, 1)
        self.grid.addWidget(self.scanPar['noRamButton'], currentRow, 2)
        currentRow += 1

        # Start and Stop buttons
        self.grid.addWidget(self.scanPar['StartButton'], currentRow, 0)
        self.grid.addWidget(self.scanPar['StopButton'], currentRow, 1)
        self.grid.addWidget(self.scanPar['PlotReportButton'], currentRow, 2)
        

        currentRow += 1
        self.grid.addWidget(self.tabs, currentRow, 0, 1, -1)
    
    def requestMockConfirmation(self):
        text = "Steps per/rev should be divisable by number of OPT steps. \
                You can continue by casting the steps on integers and risk \
                imprecise measured angles. Or cancel scan."
        return guitools.askYesNoQuestion(self, "Motor steps not integer values.", " ".join(text.split()))


# Copyright (C) 2020-2022 ImSwitch developers
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
