import numpy as np

from .basecontrollers import LiveUpdatedController


class AlignXYController(LiveUpdatedController):
    """ Linked to AlignWidgetXY. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.axis = 0
        self.addROI()

        # Connect CommunicationChannel signals
        self._commChannel.updateImage.connect(self.update)

        # Connect AlignWidgetXY signals
        self._widget.sigShowROIToggled.connect(self.toggleROI)
        self._widget.sigAxisChanged.connect(self.setAxis)

    def update(self, im, init):
        """ Update with new detector frame. """
        if self.active:
            value = np.mean(
                self._commChannel.getROIdata(im, self._widget.getROIGraphicsItem()),
                self.axis
            )
            self._widget.updateGraph(value)

    def addROI(self):
        """ Adds the ROI to ImageWidget viewbox through the CommunicationChannel. """
        self._commChannel.addItemTovb.emit(self._widget.getROIGraphicsItem())

    def toggleROI(self, show):
        """ Show or hide ROI."""
        if show:
            ROIsize = (64, 64)
            ROIcenter = self._commChannel.getCenterROI()

            ROIpos = (ROIcenter[0] - 0.5 * ROIsize[0],
                      ROIcenter[1] - 0.5 * ROIsize[1])

            self._widget.showROI(ROIpos, ROIsize)
        else:
            self._widget.hideROI()

        self.active = show
        self._widget.updateDisplayState(show)

    def setAxis(self, axis):
        """ Setter for the axis (X or Y). """
        self.axis = axis