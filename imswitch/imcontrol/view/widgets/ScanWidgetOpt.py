from qtpy import QtCore, QtWidgets
import numpy as np

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import NapariHybridWidget


class ScanWidgetOpt(NapariHybridWidget):
    """ Widget controlling OPT experiments where a rotation stage is triggered
    """

    sigRotStepDone = QtCore.Signal()
    sigRunScanClicked = QtCore.Signal()
    sigScanDone = QtCore.Signal()

    def __post_init__(self, *args, **kwargs):
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        self.scanPar = {}
        self.enabled = True
        self.layer = None

    def initControls(self):
        # populate widget
        self.widgetLayout()

    def getRotationSteps(self):
        """ Returns the user-input number fo rotation steps. """
        return int(self.scanPar['RotStepsEdit'].text())

    def getHotStd(self):
        """ Returns the user-input STD cutoff for the hot pixel correction. """
        return float(self.scanPar['HotPixelsStdEdit'].text())

    def getAverages(self):
        """ Returns the user-input number of averages for the hot pixel correction. """
        return int(self.scanPar['AveragesEdit'].text())

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

    def setRotStepEnable(self, enabled):
        """ For inactivating during scanning when ActivateButton pressed
        and waiting for a scan. When scan finishes, enable again. """
        self.scanPar['RotStepsEdit'].setEnabled(enabled)

    def setImage(self, im, colormap="gray", name="",
                 pixelsize=(1, 1, 1), translation=(0, 0, 0)):
        if len(im.shape) == 2:
            print('2D image supposedly', im.shape)
            translation = (translation[0], translation[1])
        if self.layer is None or name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False,
                                               colormap=colormap,
                                               scale=pixelsize,
                                               translate=translation,
                                               name=name, blending='additive')
        self.layer.data = im
        self.layer.contrast_limits = (np.min(im), np.max(im))

    def widgetLayout(self):
        self.scanPar['GetHotPixels'] = guitools.BetterPushButton('Acquire')

        self.scanPar['HotPixelsStdEdit'] = QtWidgets.QLineEdit('5')
        self.scanPar['HotPixelsStdEdit'].setToolTip('Hot pixel is defined with Int. higher than mean + STD.')
        self.scanPar['HotPixelsStdLabel'] = QtWidgets.QLabel('STD cutoff')

        self.scanPar['AveragesEdit'] = QtWidgets.QLineEdit('30')
        self.scanPar['AveragesEdit'].setToolTip('Average N frames for Hot pixels aquistion.')
        self.scanPar['AveragesLabel'] = QtWidgets.QLabel('Averages')

        self.scanPar['HotPixelCount'] = QtWidgets.QLabel(f'Count: {0:d}')
        self.scanPar['HotPixelMean'] = QtWidgets.QLabel(f'Hot mean: {0:.2f}')
        self.scanPar['NonHotPixelMean'] = QtWidgets.QLabel(f'Non-hot mean: {0:.2f}')

        # darkfield
        self.scanPar['GetDark'] = guitools.BetterPushButton('Acquire')
        self.scanPar['DarkMean'] = QtWidgets.QLabel(f'Dark mean: {0:.2f} cts')
        self.scanPar['DarkStd'] = QtWidgets.QLabel(f'Dark STD: {0:.2f} cts')

        # brightfield
        self.scanPar['GetFlat'] = guitools.BetterPushButton('Acquire')
        self.scanPar['FlatMean'] = QtWidgets.QLabel(f'Flat mean: {0:.2f} cts')
        self.scanPar['FlatStd'] = QtWidgets.QLabel(f'Flat STD: {0:.2f} cts')

        # OPT
        self.scanPar['RotStepsLabel'] = QtWidgets.QLabel('Rot. steps')
        self.scanPar['RotStepsEdit'] = QtWidgets.QLineEdit('200')
        self.scanPar['RotStepsUnit'] = QtWidgets.QLabel(' steps')

        self.scanPar['LiveReconButton'] = QtWidgets.QCheckBox(
                                                'Live reconstruction')
        self.scanPar['LiveReconButton'].setCheckable(True)
        self.scanPar['SaveOptButton'] = QtWidgets.QCheckBox('Save OPT')
        self.scanPar['SaveOptButton'].setCheckable(True)

        self.scanPar['StartButton'] = guitools.BetterPushButton('Start')
        self.scanPar['StopButton'] = guitools.BetterPushButton('Stop')

        currentRow = 0
        # corrections
        self.grid.addWidget(QtWidgets.QLabel('<strong>Corrections:</strong>'),
                            currentRow, 0)
        self.grid.addWidget(self.scanPar['AveragesEdit'], currentRow, 1)
        self.grid.addWidget(self.scanPar['AveragesLabel'], currentRow, 2)

        currentRow += 1

        self.grid.addWidget(QtWidgets.QLabel('<strong> Hot Pixels:</strong>'),
                            currentRow, 0)
        self.grid.addWidget(self.scanPar['HotPixelsStdLabel'], currentRow, 1)
        self.grid.addWidget(self.scanPar['HotPixelsStdEdit'], currentRow, 2)

        currentRow += 1

        self.grid.addWidget(self.scanPar['GetHotPixels'], currentRow, 0)
        self.grid.addWidget(self.scanPar['HotPixelCount'], currentRow, 1)
        self.grid.addWidget(self.scanPar['HotPixelMean'], currentRow, 2)
        self.grid.addWidget(self.scanPar['NonHotPixelMean'], currentRow, 3)

        currentRow += 1
        # dark field correction
        self.grid.addWidget(QtWidgets.QLabel('<strong> Dark-field:</strong>'),
                            currentRow, 0)

        currentRow += 1
        self.grid.addWidget(self.scanPar['GetDark'], currentRow, 0)
        self.grid.addWidget(self.scanPar['DarkMean'], currentRow, 1)
        self.grid.addWidget(self.scanPar['DarkStd'], currentRow, 2)

        currentRow += 1
        # bright field correction
        self.grid.addWidget(QtWidgets.QLabel('<strong> Bright-field:</strong>'),
                            currentRow, 0)

        currentRow += 1
        self.grid.addWidget(self.scanPar['GetFlat'], currentRow, 0)
        self.grid.addWidget(self.scanPar['FlatMean'], currentRow, 1)
        self.grid.addWidget(self.scanPar['FlatStd'], currentRow, 2)

        # OPT settings
        currentRow += 1

        self.grid.addWidget(self.scanPar['RotStepsLabel'], currentRow, 0)
        self.grid.addWidget(self.scanPar['RotStepsEdit'], currentRow, 1)
        self.grid.addWidget(self.scanPar['RotStepsUnit'], currentRow, 2)

        currentRow += 1

        self.grid.addWidget(self.scanPar['LiveReconButton'], currentRow, 0)
        self.grid.addWidget(self.scanPar['SaveOptButton'], currentRow, 1)
        self.grid.addWidget(self.scanPar['StartButton'], currentRow, 2)
        self.grid.addWidget(self.scanPar['StopButton'], currentRow, 3)

        # self.grid.addItem(QtWidgets.QSpacerItem(10, 10,
        #                   QtWidgets.QSizePolicy.Minimum,
        #                   QtWidgets.QSizePolicy.Expanding),
        #                   currentRow+1, 0, 1, -1)


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
