from .basecontrollers import LiveUpdatedController
from imcontrol.view import guitools as guitools


class ImageController(LiveUpdatedController):
    """ Linked to ImageWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self._master.detectorsManager.hasDetectors():
            return

        self._lastWidth, self._lastHeight = self._master.detectorsManager.execOnCurrent(
            lambda c: c.shape
        )
        self._savedLevels = {}

        # Connect CommunicationChannel signals
        self._commChannel.sigUpdateImage.connect(self.update)
        self._commChannel.sigAcquisitionStopped.connect(self.acquisitionStopped)
        self._commChannel.sigAdjustFrame.connect(self.adjustFrame)
        self._commChannel.sigGridToggled.connect(self.gridToggle)
        self._commChannel.sigCrosshairToggled.connect(self.crosshairToggle)
        self._commChannel.sigAddItemToVb.connect(self.addItemTovb)
        self._commChannel.sigRemoveItemFromVb.connect(self.removeItemFromvb)
        self._commChannel.sigDetectorSwitched.connect(self.restoreSavedLevels)

        # Connect ImageWidget signals
        self._widget.sigResized.connect(lambda: self.adjustFrame(self._lastWidth, self._lastHeight))
        self._widget.sigLevelsChanged.connect(self.updateSavedLevels)
        self._widget.sigUpdateLevelsClicked.connect(self.autoLevels)

    def autoLevels(self, im=None):
        """ Set histogram levels automatically with current detector image."""
        if im is None:
            im = self._widget.img.image

        self._widget.hist.setLevels(*guitools.bestLevels(im))
        self._widget.hist.vb.setYRange(im.min(), im.max())

    def addItemTovb(self, item):
        """ Add item from communication channel to viewbox."""
        self._widget.vb.addItem(item)
        item.hide()

    def removeItemFromvb(self, item):
        """ Remove item from communication channel to viewbox."""
        self._widget.vb.removeItem(item)

    def update(self, im, init):
        """ Update new image in the viewbox. """
        if not init:
            self._widget.img.setOnlyRenderVisible(True, render=False)
            self._widget.levelsButton.setEnabled(True)
            self.autoLevels(im)

        self._widget.img.setImage(im.reshape(im.shape[1], im.shape[0]),
                                  autoLevels=False, autoDownsample=False)

        if not init:
            self.adjustFrame(self._lastWidth, self._lastHeight)

    def acquisitionStopped(self):
        """ Disable the onlyRenderVisible optimization for a smoother experience. """
        self._widget.img.setOnlyRenderVisible(False, render=True)

    def adjustFrame(self, width, height):
        """ Adjusts the viewbox to a new width and height. """
        self._widget.grid.update([width, height])
        guitools.setBestImageLimits(self._widget.vb, width, height)
        self._widget.img.render()

        self._lastWidth = width
        self._lastHeight = height

    def getROIdata(self, image, roi):
        """ Returns the cropped image within the ROI. """
        return roi.getArrayRegion(image, self._widget.img)

    def getCenterROI(self):
        """ Returns center of viewbox to center a ROI. """
        return (int(self._widget.vb.viewRect().center().x()),
                int(self._widget.vb.viewRect().center().y()))

    def gridToggle(self, enabled):
        """ Shows or hides grid. """
        self._widget.grid.setVisible(enabled)

    def crosshairToggle(self, enabled):
        """ Shows or hides crosshair. """
        self._widget.crosshair.setVisible(enabled)

    def updateSavedLevels(self):
        detectorName = self._master.detectorsManager.getCurrentDetectorName()
        self._savedLevels[detectorName] = self._widget.hist.getLevels()

    def restoreSavedLevels(self, newDetectorName):
        """ Updates image levels from saved levels for detector that is switched to. """
        if newDetectorName in self._savedLevels:
            self._widget.hist.setLevels(*self._savedLevels[newDetectorName])
    

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
