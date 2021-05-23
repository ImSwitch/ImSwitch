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

            self.setSharedAttr(lName, _enabledAttr, self._widget.isLaserActive(lName))
            self.setSharedAttr(lName, _valueAttr, self._widget.getValue(lName))

        # Connect CommunicationChannel signals
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged)
        self._commChannel.sigScanStarted.connect(lambda: self.scanChanged(True))
        self._commChannel.sigScanEnded.connect(lambda: self.scanChanged(False))

        # Connect LaserWidget signals
        self._widget.sigEnableChanged.connect(self.toggleLaser)
        self._widget.sigValueChanged.connect(self.valueChanged)

    def closeEvent(self):
        self._master.lasersManager.execOnAll(lambda l: l.setScanModeActive(False))
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

    def scanChanged(self, isScanning):
        self._master.lasersManager.execOnAll(lambda l: l.setScanModeActive(isScanning))

    def attrChanged(self, key, value):
        if self.settingAttr or len(key) != 3 or key[0] != _attrCategory:
            return

        laserName = key[1]
        if key[2] == _enabledAttr:
            self.setLaserActive(laserName, value)
        elif key[2] == _valueAttr:
            self.setLaserValue(laserName, value)

    def setSharedAttr(self, laserName, attr, value):
        self.settingAttr = True
        try:
            self._commChannel.sharedAttrs[(_attrCategory, laserName, attr)] = value
        finally:
            self.settingAttr = False

    @APIExport
    def getLaserNames(self):
        """ Returns the device names of all lasers. These device names can be
        passed to other laser-related functions. """
        return self._master.lasersManager.getAllDeviceNames()

    @APIExport
    def setLaserActive(self, laserName, active):
        """ Sets whether the specified laser is powered on. """
        self._widget.setLaserActive(laserName, active)

    @APIExport
    def setLaserValue(self, laserName, value):
        """ Sets the value of the specified laser, in the units that the laser
        uses. """
        self._widget.setValue(laserName, value)


_attrCategory = 'Laser'
_enabledAttr = 'Enabled'
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
