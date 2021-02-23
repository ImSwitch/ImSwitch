import numpy as np

from .basecontrollers import LiveUpdatedController


class AlignAverageController(LiveUpdatedController):
    """ Linked to AlignWidgetAverage."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addROI()

        # Connect CommunicationChannel signals
        self._commChannel.updateImage.connect(self.update)

        # Connect AlignWidgetAverage signals
        self._widget.sigShowROIToggled.connect(self.toggleROI)

    def update(self, im, init):
        """ Update with new detector frame. """
        if self.active:
            value = np.mean(
                self._commChannel.getROIdata(im, self._widget.getROIGraphicsItem())
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