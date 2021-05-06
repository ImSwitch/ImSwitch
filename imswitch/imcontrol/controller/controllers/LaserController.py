from imswitch.imcommon.model import APIExport
from .basecontrollers import ImConWidgetController


class LaserController(ImConWidgetController):
    """ Linked to LaserWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settingAttr = False

        # Set up lasers
        for lName, lManager in self._master.lasersManager:
            self._widget.addLaser(
                lName, lManager.valueUnits, lManager.wavelength,
                (lManager.valueRangeMin, lManager.valueRangeMax) if not lManager.isBinary else None,
                lManager.valueRangeStep if lManager.valueRangeStep is not None else None
            )
            if not lManager.isBinary and lManager.isDigital:
                self.valueChanged(lName, lManager.valueRangeMin)

            self.setSharedAttr(lName, _digModAttr, self._widget.isDigModActive())
            self.setSharedAttr(lName, _enabledAttr, self._widget.isLaserActive(lName))
            self.setSharedAttr(lName, _valueAttr,
                               self._widget.getValue(lName) if not self._widget.isDigModActive()
                               else self._widget.getDigValue(lName))

        # Connect CommunicationChannel signals
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged)
        self._commChannel.sigScanStarted.connect(lambda: self.scanChanged(True))
        self._commChannel.sigScanEnded.connect(lambda: self.scanChanged(False))

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
        self.setSharedAttr(laserName, _enabledAttr, enabled)

    def valueChanged(self, laserName, magnitude):
        """ Change magnitude. """
        self._master.lasersManager[laserName].setValue(magnitude)
        self._widget.setValue(laserName, magnitude)
        self.setSharedAttr(laserName, _valueAttr, magnitude)


    def updateDigitalPowers(self, laserNames):
        """ Update the powers if the digital mod is on. """
        if self._widget.isDigModActive():
            for laserName in laserNames:
                value = self._widget.getDigValue(laserName)
                self._master.lasersManager[laserName].setValue(value)
                self.setSharedAttr(laserName, _valueAttr, value)

    def GlobalDigitalMod(self, digMod, laserNames):
        """ Start/stop digital modulation. """
        for laserName in laserNames:
            laserManager = self._master.lasersManager[laserName]
            value = self._widget.getDigValue(laserName)
            
            if laserManager.isDigital:
                laserManager.setDigitalMod(digMod, value)
            else:
                laserManager.setValue(value)
                self._widget.setLaserActive(laserName, False)
                self._widget.setLaserActivatable(laserName, not digMod)
                laserManager.setEnabled(False)
            self._widget.setLaserEditable(laserName, not digMod)

            self.setSharedAttr(laserName, _digModAttr, digMod)
            if not digMod:
                self.valueChanged(laserName, self._widget.getValue(laserName))
            else:
                self.setSharedAttr(laserName, _valueAttr, value)

    def attrChanged(self, key, value):
        if self.settingAttr or len(key) != 3 or key[0] != _attrCategory:
            return

        laserName = key[1]
        if key[2] == _enabledAttr:
            self.setLaserActive(laserName, value)
        elif key[2] == _digModAttr:
            self.setLaserDigModActive(value)
        elif key[2] == _valueAttr:
            self.setLaserValue(laserName, value)
            self.setLaserDigValue(laserName, value)

    def setSharedAttr(self, laserName, attr, value):
        self.settingAttr = True
        try:
            self._commChannel.sharedAttrs[(_attrCategory, laserName, attr)] = value
        finally:
            self.settingAttr = False

    def scanChanged(self, isScanning):
        for lName, lManager in self._master.lasersManager:
            if not lManager.isDigital and not lManager.isBinary:
                self._widget.digModule.setEditable(lName, not isScanning)

    @APIExport
    def getLaserNames(self):
        """ Returns the device names of all lasers. These device names can be
        passed to other laser-related functions. """
        return self._master.lasersManager.getAllDeviceNames()

    @APIExport
    def setLaserDigModActive(self, active):
        """ Sets whether the laser digital modulation mode is active. """
        self._widget.setDigModActive(active)

    @APIExport
    def setLaserActive(self, laserName, active):
        """ Sets whether the specified laser is powered on. """
        self._widget.setLaserActive(laserName, active)

    @APIExport
    def setLaserValue(self, laserName, value):
        """ Sets the value of the specified laser, in the units that the laser
        uses. """
        self._widget.setValue(laserName, value)

    @APIExport
    def setLaserDigValue(self, laserName, value):
        """ Sets the digital modulation value of the specified laser, in the
        units that the laser uses. """
        self._widget.setDigValue(laserName, value)


_attrCategory = 'Laser'
_enabledAttr = 'Enabled'
_digModAttr = 'DigMod'
_valueAttr = 'Value'


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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
