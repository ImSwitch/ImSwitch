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
        self._shouldResetView = False

        self._widget.setLayers(self._master.detectorsManager.getAllDetectorNames())

        # Connect CommunicationChannel signals
        self._commChannel.sigUpdateImage.connect(self.update)
        self._commChannel.sigAdjustFrame.connect(self.adjustFrame)
        self._commChannel.sigGridToggled.connect(self.gridToggle)
        self._commChannel.sigCrosshairToggled.connect(self.crosshairToggle)
        self._commChannel.sigAddItemToVb.connect(self.addItemToVb)
        self._commChannel.sigRemoveItemFromVb.connect(self.removeItemFromVb)

    def autoLevels(self, detectorNames=None, im=None):
        """ Set histogram levels automatically with current detector image."""
        if detectorNames is None:
            detectorNames = self._master.detectorsManager.getAllDetectorNames()

        for detectorName in detectorNames:
            if im is None:
                im = self._widget.getImage(detectorName)

            self._widget.setImageDisplayLevels(detectorName, *guitools.bestLevels(im))

    def addItemToVb(self, item):
        """ Add item from communication channel to viewbox."""
        item.hide()
        self._widget.addItem(item)

    def removeItemFromVb(self, item):
        """ Remove item from communication channel to viewbox."""
        self._widget.removeItem(item)

    def update(self, detectorName, im, init, isCurrentDetector):
        """ Update new image in the viewbox. """
        if not init:
            self.autoLevels([detectorName], im)

        self._widget.setImage(detectorName, im)

        if not init or self._shouldResetView:
            self.adjustFrame(self._lastWidth, self._lastHeight, instantResetView=True)

    def adjustFrame(self, width, height, instantResetView=False):
        """ Adjusts the viewbox to a new width and height. """
        self._widget.updateGrid([width, height])
        if instantResetView:
            self._widget.resetView()
        else:
            self._shouldResetView = True

        self._lastWidth = width
        self._lastHeight = height

    def getROIdata(self, image, roi):
        """ Returns the cropped image within the ROI. """
        return roi.getArrayRegion(image, self._widget.img)

    def getCenterROI(self):
        """ Returns center of viewbox to center a ROI. """
        return self._widget.getCenterROI()

    def gridToggle(self, enabled):
        """ Shows or hides grid. """
        self._widget.setGridVisible(enabled)

    def crosshairToggle(self, enabled):
        """ Shows or hides crosshair. """
        self._widget.setCrosshairVisible(enabled)
