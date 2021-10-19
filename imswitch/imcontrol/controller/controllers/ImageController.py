from imswitch.imcontrol.view import guitools
from ..basecontrollers import LiveUpdatedController
import numpy as np

class ImageController(LiveUpdatedController):
    """ Linked to ImageWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self._master.detectorsManager.hasDevices():
            return

        self._lastShape = self._master.detectorsManager.execOnCurrent(lambda c: c.shape)
        self._shouldResetView = False

        self._widget.setLiveViewLayers(
            self._master.detectorsManager.getAllDeviceNames(lambda c: c.forAcquisition)
        )

        # Connect CommunicationChannel signals
        self._commChannel.sigUpdateImage.connect(self.update)
        self._commChannel.sigAdjustFrame.connect(self.adjustFrame)
        self._commChannel.sigGridToggled.connect(self.gridToggle)
        self._commChannel.sigCrosshairToggled.connect(self.crosshairToggle)
        self._commChannel.sigAddItemToVb.connect(self.addItemToVb)
        self._commChannel.sigRemoveItemFromVb.connect(self.removeItemFromVb)
        self._commChannel.sigMemorySnapAvailable.connect(self.memorySnapAvailable)

    def autoLevels(self, detectorNames=None, im=None):
        """ Set histogram levels automatically with current detector image."""
        if detectorNames is None:
            detectorNames = self._master.detectorsManager.getAllDeviceNames(
                lambda c: c.forAcquisition
            )

        for detectorName in detectorNames:
            if im is None:
                im = self._widget.getImage(detectorName)

            # self._widget.setImageDisplayLevels(detectorName, *guitools.bestLevels(im))
            self._widget.setImageDisplayLevels(detectorName, *guitools.minmaxLevels(im))

    def addItemToVb(self, item):
        """ Add item from communication channel to viewbox."""
        item.hide()
        self._widget.addItem(item)

    def removeItemFromVb(self, item):
        """ Remove item from communication channel to viewbox."""
        self._widget.removeItem(item)

    def update(self, detectorName, im, init, isCurrentDetector):
        """ Update new image in the viewbox. """
        if np.prod(im.shape)>1: # TODO: This seems weird!
            print(np.shape(im))
            if not init:
                self.autoLevels([detectorName], im)

            self._widget.setImage(detectorName, im)

            if not init or self._shouldResetView:
                self.adjustFrame(instantResetView=True)

    def adjustFrame(self, shape=None, instantResetView=False):
        """ Adjusts the viewbox to a new width and height. """

        if shape is None:
            shape = self._lastShape

        self._widget.updateGrid(shape)
        if instantResetView:
            self._widget.resetView()
            self._shouldResetView = False
        else:
            self._shouldResetView = True

        self._lastShape = shape

    def getCenterViewbox(self):
        """ Returns center of viewbox to center a ROI. """
        return self._widget.getCenterViewbox()

    def gridToggle(self, enabled):
        """ Shows or hides grid. """
        self._widget.setGridVisible(enabled)

    def crosshairToggle(self, enabled):
        """ Shows or hides crosshair. """
        self._widget.setCrosshairVisible(enabled)

    def memorySnapAvailable(self, name, image, _, __):
        """ Adds captured image to widget. """
        self._widget.addStaticLayer(name, image)
        if self._shouldResetView:
            self.adjustFrame(image.shape, instantResetView=True)


# Copyright (C) 2020, 2021 TestaLab
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
