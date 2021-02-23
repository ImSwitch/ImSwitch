from .basecontrollers import ImConWidgetController


class AlignmentLineController(ImConWidgetController):
    """ Linked to AlignmentLineWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addLine()

        # Connect AlignmentLineWidget signals
        self._widget.sigAlignmentLineMakeClicked.connect(self.updateLine)
        self._widget.sigAlignmentCheckToggled.connect(self.show)

    def addLine(self):
        """ Adds alignmentLine to ImageWidget viewbox through the CommunicationChannel. """
        self._commChannel.sigAddItemToVb.emit(self._widget.alignmentLine)

    def updateLine(self):
        """ Updates line with new parameters. """
        self._widget.setLineAngle(self._widget.getAngleInput())

    def show(self, enabled):
        """ Shows or hides line. """
        if enabled:
            self._widget.alignmentLine.show()
        else:
            self._widget.alignmentLine.hide()