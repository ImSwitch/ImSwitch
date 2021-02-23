from .basecontrollers import ImConWidgetController


class ViewController(ImConWidgetController):
    """ Linked to ViewWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            self._master.detectorsManager.startAcquisition()
            self._widget.setViewToolsEnabled(True)
        else:
            self._master.detectorsManager.stopAcquisition()

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
        self._master.detectorsManager.stopAcquisition()