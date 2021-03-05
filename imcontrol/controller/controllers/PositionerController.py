from .basecontrollers import ImConWidgetController


class PositionerController(ImConWidgetController):
    """ Linked to PositionerWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for pName, pManager in self._master.positionersManager:
            self._widget.addPositioner(pName)
            self.setSharedAttr(pName, 'Position', pManager.position)

        # Connect CommunicationChannel signals
        self._commChannel.sigMoveZStage.connect(lambda step: self.move('Z', step))

        # Connect PositionerWidget signals
        self._widget.sigStepUpClicked.connect(
            lambda positionerName: self.move(positionerName, self._widget.getStepSize(positionerName))
        )
        self._widget.sigStepDownClicked.connect(
            lambda positionerName: self.move(positionerName, -self._widget.getStepSize(positionerName))
        )

    def closeEvent(self):
        self._master.positionersManager.execOnAll(lambda p: p.setPosition(0))

    def getPos(self):
        return self._master.positionersManager.execOnAll(lambda p: p.position)

    def move(self, positionerName, dist):
        """ Moves the piezzos in x y or z (axis) by dist micrometers. """
        newPos = self._master.positionersManager[positionerName].move(dist)
        self._widget.updatePosition(positionerName, newPos)
        self.setSharedAttr(positionerName, 'Position', newPos)

    def setSharedAttr(self, positionerName, attr, value):
        self._commChannel.sharedAttrs[('Positioners', positionerName, attr)] = value