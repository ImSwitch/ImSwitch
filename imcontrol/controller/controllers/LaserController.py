from .basecontrollers import ImConWidgetController


class LaserController(ImConWidgetController):
    """ Linked to LaserWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.aotfLasers = {}

        for lName, lManager in self._master.lasersManager:
            self._widget.addLaser(
                lName, lManager.valueUnits, lManager.wavelength,
                (lManager.valueRangeMin, lManager.valueRangeMax) if not lManager.isBinary else None
            )

            if not lManager.isDigital:
                self.aotfLasers[lName] = False
            elif not lManager.isBinary:
                self.valueChanged(lName, lManager.valueRangeMin)

            self.setSharedAttr(lName, 'DigMod', self._widget.isDigModActive())
            self.setSharedAttr(lName, 'Enabled', self._widget.isLaserActive(lName))
            self.setSharedAttr(lName, 'Value',
                               self._widget.getValue(lName) if not self._widget.isDigModActive()
                               else self._widget.getDigValue(lName))

        # Connect LaserWidget signals
        self._widget.sigEnableChanged.connect(self.toggleLaser)
        self._widget.sigValueChanged.connect(self.valueChanged)

        self._widget.sigDigitalModToggled.connect(
            lambda digMod: self.GlobalDigitalMod(
                digMod, [laser.name for _, laser in self._master.lasersManager]
            )
        )
        self._widget.sigDigitalValueChanged.connect(
            lambda laserName: self.updateDigitalPowers([laserName])
        )

    def closeEvent(self):
        self._master.lasersManager.execOnAll(lambda l: l.setDigitalMod(False, 0))
        self._master.lasersManager.execOnAll(lambda l: l.setValue(0))

    def toggleLaser(self, laserName, enabled):
        """ Enable or disable laser (on/off)."""
        self._master.lasersManager[laserName].setEnabled(enabled)
        self.setSharedAttr(laserName, 'Enabled', enabled)

    def valueChanged(self, laserName, magnitude):
        """ Change magnitude. """
        if laserName not in self.aotfLasers.keys() or not self.aotfLasers[laserName]:
            self._master.lasersManager[laserName].setValue(magnitude)
            self._widget.setValue(laserName, magnitude)

        self.setSharedAttr(laserName, 'Value', magnitude)

    def updateDigitalPowers(self, laserNames):
        """ Update the powers if the digital mod is on. """
        if self._widget.isDigModActive():
            for laserName in laserNames:
                value = self._widget.getDigValue(laserName)
                self._master.lasersManager[laserName].setValue(value)
                self.setSharedAttr(laserName, 'Value', value)

    def GlobalDigitalMod(self, digMod, laserNames):
        """ Start/stop digital modulation. """
        for laserName in laserNames:
            laserManager = self._master.lasersManager[laserName]

            if laserManager.isBinary:
                continue

            value = self._widget.getDigValue(laserName)
            if laserManager.isDigital:
                laserManager.setDigitalMod(digMod, value)
            else:
                laserManager.setValue(value)
                self._widget.setLaserActive(laserName, False)
                self._widget.setLaserActivatable(laserName, not digMod)
                self.aotfLasers[laserName] = digMod
                laserManager.setEnabled(False)  # TODO: Correct?
            self._widget.setLaserEditable(laserName, not digMod)

            self.setSharedAttr(laserName, 'DigMod', digMod)
            if not digMod:
                self.valueChanged(laserName, self._widget.getValue(laserName))
            else:
                self.setSharedAttr(laserName, 'Value', value)

    def setSharedAttr(self, laserName, attr, value):
        self._commChannel.sharedAttrs[('Lasers', laserName, attr)] = value