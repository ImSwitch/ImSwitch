from .basecontrollers import ImConWidgetController


class ViewController(ImConWidgetController):
    """ Linked to ViewWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._acqHandle = None

        self._widget.setDetectorList(self._master.detectorsManager.execOnAll(lambda c: c.model))
        self._widget.setViewToolsEnabled(False)

        # Connect ViewWidget signals
        self._widget.sigGridToggled.connect(self.gridToggle)
        self._widget.sigCrosshairToggled.connect(self.crosshairToggle)
        self._widget.sigLiveviewToggled.connect(self.liveview)
        self._widget.sigDetectorChanged.connect(self.detectorSwitch)
        self._widget.sigNextDetectorClicked.connect(self.detectorNext)

    def liveview(self, enabled):
        """ Start liveview and activate detector acquisition. """
        if enabled:
            self._acqHandle = self._master.detectorsManager.startAcquisition(liveView=True)
            self._widget.setViewToolsEnabled(True)
        else:
            self._master.detectorsManager.stopAcquisition(self._acqHandle, liveView=True)
            self._acqHandle = None

    def gridToggle(self, enabled):
        """ Connect with grid toggle from Image Widget through communication channel. """
        self._commChannel.sigGridToggled.emit(enabled)

    def crosshairToggle(self, enabled):
        """ Connect with crosshair toggle from Image Widget through communication channel. """
        self._commChannel.sigCrosshairToggled.emit(enabled)

    def detectorSwitch(self, detectorName):
        """ Changes the current detector to the selected detector. """
        self._master.detectorsManager.setCurrentDetector(detectorName)

    def detectorNext(self):
        """ Changes the current detector to the next detector. """
        self._widget.selectNextDetector()

    def closeEvent(self):
        if self._acqHandle is not None:
            self._master.detectorsManager.stopAcquisition(self._acqHandle, liveView=True)

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