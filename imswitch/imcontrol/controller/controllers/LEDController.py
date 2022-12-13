from typing import List, Union

from imswitch.imcommon.model import APIExport
from imswitch.imcontrol.model import configfiletools
from imswitch.imcontrol.view import guitools
from ..basecontrollers import ImConWidgetController


class LEDController(ImConWidgetController):
    """ Linked to LEDWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settingAttr = False
        self.presetBeforeScan = None

        # Set up LEDs
        for lName, lManager in self._master.LEDsManager:
            self._widget.addLED(
                lName, lManager.valueUnits, lManager.valueDecimals,
                (lManager.valueRangeMin, lManager.valueRangeMax) if not lManager.isBinary else None,
                lManager.valueRangeStep if lManager.valueRangeStep is not None else None,
            )
            if not lManager.isBinary:
                self.valueChanged(lName, lManager.valueRangeMin)

            self.setSharedAttr(lName, _enabledAttr, self._widget.isLEDActive(lName))
            self.setSharedAttr(lName, _valueAttr, self._widget.getValue(lName))

        # Load presets
        for ledPresetName in self._setupInfo.ledPresets:
            self._widget.addPreset(ledPresetName)

        self._widget.setCurrentPreset(None)  # Unselect
        self._widget.setScanDefaultPreset(self._setupInfo.defaultLEDPresetForScan)

        # Connect CommunicationChannel signals
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged)
        self._commChannel.sigScanStarting.connect(lambda: self.scanChanged(True))
        self._commChannel.sigScanBuilt.connect(self.scanBuilt)
        self._commChannel.sigScanEnded.connect(lambda: self.scanChanged(False))

        # Connect LEDWidget signals
        self._widget.sigEnableChanged.connect(self.toggleLED)
        self._widget.sigValueChanged.connect(self.valueChanged)

        self._widget.sigPresetSelected.connect(self.presetSelected)
        self._widget.sigLoadPresetClicked.connect(self.loadPreset)
        self._widget.sigSavePresetClicked.connect(self.savePreset)
        self._widget.sigSavePresetAsClicked.connect(self.savePresetAs)
        self._widget.sigDeletePresetClicked.connect(self.deletePreset)
        self._widget.sigPresetScanDefaultToggled.connect(self.presetScanDefaultToggled)

    def closeEvent(self):
        self._master.LEDsManager.execOnAll(lambda l: l.setScanModeActive(False))
        self._master.LEDsManager.execOnAll(lambda l: l.setValue(0))

    def toggleLED(self, ledName, enabled):
        """ Enable or disable LED (on/off)."""
        self._master.LEDsManager[ledName].setEnabled(enabled)
        self.setSharedAttr(ledName, _enabledAttr, enabled)

    def valueChanged(self, ledName, magnitude):
        """ Change magnitude. """
        self._master.LEDsManager[ledName].setValue(magnitude)
        self._widget.setValue(ledName, magnitude)
        self.setSharedAttr(ledName, _valueAttr, magnitude)

    def presetSelected(self, presetName):
        """ Handles what happens when a preset is selected in the preset list.
        """
        if presetName:
            self._widget.setCurrentPreset(presetName)

        self._widget.setScanDefaultPresetActive(
            self._setupInfo.defaultLEDPresetForScan == presetName
        )

    def loadPreset(self):
        """ Handles what happens when the user requests the selected preset to
        be loaded. """
        presetToLoad = self._widget.getCurrentPreset()
        if not presetToLoad:
            return

        if presetToLoad not in self._setupInfo.ledPresets:
            return

        # Load values
        self.applyPreset(self._setupInfo.ledPresets[presetToLoad])

    def savePreset(self, name=None):
        """ Saves current values to a preset. If the name parameter is None,
        the values will be saved to the currently selected preset. """

        if not name:
            name = self._widget.getCurrentPreset()
            if not name:
                return

        # Add in GUI
        if name not in self._setupInfo.ledPresets:
            self._widget.addPreset(name)

        # Set in setup info
        self._setupInfo.setLEDPreset(name, self.makePreset())
        configfiletools.saveSetupInfo(configfiletools.loadOptions()[0], self._setupInfo)

        # Update selected preset in GUI
        self._widget.setCurrentPreset(name)

    def savePresetAs(self):
        """ Handles what happens when the user requests the current LED
        values to be saved as a new preset. """

        name = guitools.askForTextInput(self._widget, 'Add LED preset',
                                        'Enter a name for this preset:')

        if not name:  # No name provided
            return

        add = True
        if name in self._setupInfo.ledPresets:
            add = guitools.askYesNoQuestion(
                self._widget,
                'LED preset already exists',
                f'A preset with the name "{name}" already exists. Do you want to overwrite it"?'
            )

        if add:
            self.savePreset(name)

    def deletePreset(self):
        """ Handles what happens when the user requests the selected preset to
        be deleted. """

        presetToDelete = self._widget.getCurrentPreset()
        if not presetToDelete:
            return

        confirmationResult = guitools.askYesNoQuestion(
            self._widget,
            'Delete LED preset?',
            f'Are you sure you want to delete the preset "{presetToDelete}"?'
        )

        if confirmationResult:
            # Remove in GUI
            self._widget.removePreset(presetToDelete)

            # Remove from setup info
            self._setupInfo.removeLEDPreset(presetToDelete)
            configfiletools.saveSetupInfo(configfiletools.loadOptions()[0], self._setupInfo)

    def presetScanDefaultToggled(self):
        """ Handles what happens when the user requests the "default for
        scanning" state of the selected preset to be toggled. """

        currentPresetName = self._widget.getCurrentPreset()
        if not currentPresetName:
            return

        enabling = self._setupInfo.defaultLEDPresetForScan != currentPresetName

        # Set in setup info
        self._setupInfo.setDefaultLEDPresetForScan(currentPresetName if enabling else None)
        configfiletools.saveSetupInfo(configfiletools.loadOptions()[0], self._setupInfo)

        # Update in GUI
        self._widget.setScanDefaultPreset(currentPresetName if enabling else None)
        self._widget.setScanDefaultPresetActive(enabling)

    def makePreset(self):
        """ Returns a preset object corresponding to the current LED values.
        """
        return {lName: guitools.LEDPresetInfo(value=self._widget.getValue(lName))
                for lName, lManager in self._master.LEDsManager if not lManager.isBinary}

    def applyPreset(self, ledPreset):
        """ Loads a preset object into the current values. """
        for ledName, ledPresetInfo in ledPreset.items():
            self.setLEDValue(ledName, ledPresetInfo.value)

    def scanChanged(self, isScanning):
        """ Handles what happens when a scan is started/stopped. """
        for lName, _ in self._master.LEDsManager:
            self._widget.setLEDEditable(lName, not isScanning)
        self._master.LEDsManager.execOnAll(lambda l: l.setScanModeActive(isScanning))

        defaultScanPresetName = self._setupInfo.defaultLEDPresetForScan
        if defaultScanPresetName in self._setupInfo.ledPresets:
            if isScanning and self.presetBeforeScan is None:
                # Scan started, save current values and apply default scan preset
                self.presetBeforeScan = self.makePreset()
                self.applyPreset(self._setupInfo.ledPresets[defaultScanPresetName])
            elif self.presetBeforeScan is not None:
                # Scan finished, restore the values that were set before the scan started
                self.applyPreset(self.presetBeforeScan)
                self.presetBeforeScan = None

    def scanBuilt(self, deviceList):
        for lName, _ in self._master.LEDsManager:
            if lName not in deviceList:
                self._widget.setLEDEditable(lName, True)

    def attrChanged(self, key, value):
        if self.settingAttr or len(key) != 3 or key[0] != _attrCategory:
            return

        ledName = key[1]
        if key[2] == _enabledAttr:
            self.setLEDActive(ledName, value)
        elif key[2] == _valueAttr:
            self.setLEDValue(ledName, value)

    def setSharedAttr(self, ledName, attr, value):
        self.settingAttr = True
        try:
            self._commChannel.sharedAttrs[(_attrCategory, ledName, attr)] = value
        finally:
            self.settingAttr = False

    @APIExport()
    def getLEDNames(self) -> List[str]:
        """ Returns the device names of all LEDs. These device names can be
        passed to other LED-related functions. """
        return self._master.LEDsManager.getAllDeviceNames()

    @APIExport(runOnUIThread=True)
    def setLEDActive(self, ledName: str, active: bool) -> None:
        """ Sets whether the specified LED is powered on. """
        self._widget.setLEDActive(ledName, active)

    @APIExport(runOnUIThread=True)
    def setLEDValue(self, ledName: str, value: Union[int, float]) -> None:
        """ Sets the value of the specified LED, in the units that the LED
        uses. """
        self._widget.setValue(ledName, value)

    @APIExport()
    def changeScanPower(self, ledName, ledValue):
        defaultPreset = self._setupInfo.ledPresets[self._setupInfo.defaultLEDPresetForScan]
        defaultPreset[ledName] = guitools.LEDPresetInfo(value=ledValue)



_attrCategory = 'LED'
_enabledAttr = 'Enabled'
_valueAttr = 'Value'


# Copyright (C) 2020-2021 ImSwitch developers
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
