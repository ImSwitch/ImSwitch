from imswitch.imcommon.model import APIExport
from ..basecontrollers import ImConWidgetController


class ViewController(ImConWidgetController):
    """ Linked to ViewWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._acqHandle = None

        self._widget.setViewToolsEnabled(False)

        # Connect ViewWidget signals
        self._widget.sigGridToggled.connect(self.gridToggle)
        self._widget.sigCrosshairToggled.connect(self.crosshairToggle)

        # Connect CommunicationChannel signals
        self._commChannel.sigLiveViewUpdateRequested.connect(self.toggleLive)

        # The live view handling depends on the current acquisition engine loaded
        # in the configuration. If the acquisition engine is PycroManager, then 
        # we will handle the live acquisition via liveViewPycroManager. Otherwise,
        # we will handle it via the original liveview method.
        if self._master.pycroManagerAcquisition is not None:
            self._widget.sigLiveviewToggled.connect(self.liveViewPycroManager)
        else:
            self._widget.sigLiveviewToggled.connect(self.liveview)

    def toggleLive(self, enabled):
        """ If live acquisition is already started, stop it. Otherwise, resume.
        """
        if self._acqHandle is not None:
            self.liveview(enabled)

    def liveview(self, enabled):
        """ Start liveview and activate detector acquisition. """
        if enabled and self._acqHandle is None:
            self._acqHandle = self._master.detectorsManager.startAcquisition(liveView=True)
            self._widget.setViewToolsEnabled(True)
        elif not enabled and self._acqHandle is not None:
            self._master.detectorsManager.stopAcquisition(self._acqHandle, liveView=True)
            self._acqHandle = None
    
    def liveViewPycroManager(self, enabled : bool) -> None:
        if enabled:
            self._commChannel.sigLiveAcquisitionStarted.emit()
        else:
            self._commChannel.sigLiveAcquisitionStopped.emit()

    def gridToggle(self, enabled):
        """ Connect with grid toggle from Image Widget through communication channel. """
        self._commChannel.sigGridToggled.emit(enabled)

    def crosshairToggle(self, enabled):
        """ Connect with crosshair toggle from Image Widget through communication channel. """
        self._commChannel.sigCrosshairToggled.emit(enabled)

    def closeEvent(self):
        if self._acqHandle is not None:
            self._master.detectorsManager.stopAcquisition(self._acqHandle, liveView=True)

    def get_image(self, detectorName):
        if detectorName is None:
            return self._master.detectorsManager.execOnCurrent(lambda c: c.getLatestFrame())
        else:
            return self._master.detectorsManager[detectorName].getLatestFrame()

    @APIExport(runOnUIThread=True)
    def setLiveViewActive(self, active: bool) -> None:
        """ Sets whether the LiveView is active and updating. """
        self._widget.setLiveViewActive(active)

    @APIExport(runOnUIThread=True)
    def setLiveViewGridVisible(self, visible: bool) -> None:
        """ Sets whether the LiveView grid is visible. """
        self._widget.setLiveViewGridVisible(visible)

    @APIExport(runOnUIThread=True)
    def setLiveViewCrosshairVisible(self, visible: bool) -> None:
        """ Sets whether the LiveView crosshair is visible. """
        self._widget.setLiveViewCrosshairVisible(visible)


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
