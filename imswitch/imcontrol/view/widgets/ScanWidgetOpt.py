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
        # Treat parameters as polarization rotation parameters.
        currentRow = 0
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

        self.grid.addWidget(self.scanPar['RotStepsLabel'], currentRow, 0)
        self.grid.addWidget(self.scanPar['RotStepsEdit'], currentRow, 1)
        self.grid.addWidget(self.scanPar['RotStepsUnit'], currentRow, 2)

        currentRow += 1

        self.grid.addWidget(self.scanPar['LiveReconButton'], currentRow, 0)
        self.grid.addWidget(self.scanPar['SaveOptButton'], currentRow, 1)
        self.grid.addWidget(self.scanPar['StartButton'], currentRow, 5)
        self.grid.addWidget(self.scanPar['StopButton'], currentRow, 6)

        self.grid.addItem(QtWidgets.QSpacerItem(10, 10,
                          QtWidgets.QSizePolicy.Minimum,
                          QtWidgets.QSizePolicy.Expanding),
                          4, 0, 1, -1)

    def getRotationSteps(self):
        """ Returns the user-input number fo rotation steps. """
        return int(self.scanPar['RotStepsEdit'].text())

    def setRotStepEnable(self, enabled):
        """ For inactivating during scanning when ActivateButton pressed
        and waiting for a scan. When scan finishes, enable again. """
        self.scanPar['RotStepsEdit'].setEnabled(enabled)

    def setImage(self, im, colormap="gray", name="",
                 pixelsize=(1, 1, 1), translation=(0, 0, 0)):
        if len(im.shape) == 2:
            translation = (translation[0], translation[1])
        if self.layer is None or name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False,
                                               colormap=colormap,
                                               scale=pixelsize,
                                               translate=translation,
                                               name=name, blending='additive')
        self.layer.data = im
        self.layer.contrast_limits = (np.min(im), np.max(im))


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
