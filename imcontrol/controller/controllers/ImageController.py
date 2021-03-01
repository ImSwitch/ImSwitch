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

        self._widget.setLayers(self._master.detectorsManager.getAllDetectorNames())

        # Connect CommunicationChannel signals
        self._commChannel.sigUpdateImage.connect(self.update)
        self._commChannel.sigAdjustFrame.connect(self.adjustFrame)
        self._commChannel.sigGridToggled.connect(self.gridToggle)
        self._commChannel.sigCrosshairToggled.connect(self.crosshairToggle)
        self._commChannel.sigAddItemToVb.connect(self.addItemTovb)
        self._commChannel.sigRemoveItemFromVb.connect(self.removeItemFromvb)
        self._commChannel.sigDetectorSwitched.connect(self.detectorSwitched)

        self.detectorSwitched(self._master.detectorsManager.getCurrentDetectorName())

    def autoLevels(self, detectorNames=None, im=None):
        """ Set histogram levels automatically with current detector image."""
        if detectorNames is None:
            detectorNames = self._master.detectorsManager.getAllDetectorNames()

        for detectorName in detectorNames:
            if im is None:
                im = self._widget.getImage(detectorName)

            self._widget.setImageDisplayLevels(detectorName, *guitools.bestLevels(im))

    def addItemTovb(self, item):
        """ Add item from communication channel to viewbox."""
        # TODO: self._widget.vb.addItem(item)
        item.hide()

    def removeItemFromvb(self, item):
        """ Remove item from communication channel to viewbox."""
        # TODO: self._widget.vb.removeItem(item)
        pass

    def update(self, detectorName, im, init, isCurrentDetector):
        """ Update new image in the viewbox. """
        if not init:
            self.autoLevels([detectorName], im)

        self._widget.setImage(detectorName, im)

        if not init:
            self.adjustFrame(self._lastWidth, self._lastHeight)

    def detectorSwitched(self, newDetectorName):
        pass
        # self._widget.setLayers([newDetectorName])

    def adjustFrame(self, width, height):
        """ Adjusts the viewbox to a new width and height. """
        # TODO: self._widget.grid.update([width, height])
        self._widget.resetView()

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
