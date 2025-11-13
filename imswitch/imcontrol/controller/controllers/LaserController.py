from typing import List, Union

from imswitch.imcommon.model import APIExport
from imswitch.imcontrol.model import configfiletools
from imswitch.imcontrol.view import guitools
from ..basecontrollers import ImConWidgetController


class LaserController(ImConWidgetController):
    """ Linked to LaserWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settingAttr = False
        self.presetBeforeScan = None
        self.is_scanning = False

        # Set up lasers
        for lName, lManager in self._master.lasersManager:
            self._widget.addLaser(
                lName, lManager.valueUnits, lManager.valueDecimals, lManager.wavelength,
                (lManager.valueRangeMin, lManager.valueRangeMax) if not lManager.isBinary else None,
                lManager.valueRangeStep if lManager.valueRangeStep is not None else None,
                (lManager.freqRangeMin, lManager.freqRangeMax, lManager.freqRangeInit) if lManager.isModulated else (0, 0, 0)
            )
            if not lManager.isBinary:
                self.valueChanged(lName, lManager.valueRangeMin)

            self.setSharedAttr(lName, _enabledAttr, self._widget.isLaserActive(lName))
            self.setSharedAttr(lName, _valueAttr, self._widget.getValue(lName))

        # Load presets
        for laserPresetName in self._setupInfo.laserPresets:
            self._widget.addPreset(laserPresetName)

        self._widget.setCurrentPreset(None)  # Unselect
        self._widget.setScanDefaultPreset(self._setupInfo.defaultLaserPresetForScan)

        # Connect CommunicationChannel signals
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged)
        self._commChannel.sigScanStarting.connect(lambda: self.scanChanged(True))
        self._commChannel.sigScanBuilt.connect(self.scanBuilt)
        self._commChannel.sigScanEnded.connect(lambda: self.scanChanged(False))

        # Connect LaserWidget signals
        self._widget.sigEnableChanged.connect(self.toggleLaser)
        self._widget.sigValueChanged.connect(self.valueChanged)

        self._widget.sigModEnabledChanged.connect(self.toggleModulation)
        self._widget.sigFreqChanged.connect(self.frequencyChanged)
        self._widget.sigDutyCycleChanged.connect(self.dutyCycleChanged)

        self._widget.sigPresetSelected.connect(self.presetSelected)
        self._widget.sigLoadPresetClicked.connect(self.loadPreset)
        self._widget.sigSavePresetClicked.connect(self.savePreset)
        self._widget.sigSavePresetAsClicked.connect(self.savePresetAs)
        self._widget.sigDeletePresetClicked.connect(self.deletePreset)
        self._widget.sigPresetScanDefaultToggled.connect(self.presetScanDefaultToggled)

    def closeEvent(self):
        self._master.lasersManager.execOnAll(lambda l: l.setScanModeActive(False))
        self._master.lasersManager.execOnAll(lambda l: l.setValue(0))

    def toggleLaser(self, laserName, enabled):
        """ Enable or disable laser (on/off)."""
        self._master.lasersManager[laserName].setEnabled(enabled)
        self.setSharedAttr(laserName, _enabledAttr, enabled)

    def valueChanged(self, laserName, magnitude):
        """ Change magnitude. """
        enabled = self._widget.isLaserActive(laserName)
        self._master.lasersManager[laserName].setValue(magnitude, enabled, self.is_scanning)
        self._widget.setValue(laserName, magnitude)
        self.setSharedAttr(laserName, _valueAttr, magnitude)
    
    def toggleModulation(self, laserName, enabled):
        """ Enable or disable laser modulation (on/off). """
        self._master.lasersManager[laserName].setModulationEnabled(enabled)
        self.setSharedAttr(laserName, _freqEnAttr, enabled)

    def frequencyChanged(self, laserName, frequency):
        """ Change modulation frequency. """
        self._master.lasersManager[laserName].setModulationFrequency(frequency)
        self._widget.setModulationFrequency(laserName, frequency)
        self.setSharedAttr(laserName, _freqAttr, frequency)
    
    def dutyCycleChanged(self, laserName, dutyCycle):
        """ Change modulation duty cycle. """
        self._master.lasersManager[laserName].setModulationDutyCycle(dutyCycle)
        self._widget.setModulationDutyCycle(laserName, dutyCycle)
        self.setSharedAttr(laserName, _dcAttr, dutyCycle)

    def presetSelected(self, presetName):
        """ Handles what happens when a preset is selected in the preset list.
        """
        if presetName:
            self._widget.setCurrentPreset(presetName)

        self._widget.setScanDefaultPresetActive(
            self._setupInfo.defaultLaserPresetForScan == presetName
        )

    def loadPreset(self):
        """ Handles what happens when the user requests the selected preset to
        be loaded. """
        presetToLoad = self._widget.getCurrentPreset()
        if not presetToLoad:
            return

        if presetToLoad not in self._setupInfo.laserPresets:
            return

        # Load values
        self.applyPreset(self._setupInfo.laserPresets[presetToLoad])

    def savePreset(self, name=None):
        """ Saves current values to a preset. If the name parameter is None,
        the values will be saved to the currently selected preset. """

        if not name:
            name = self._widget.getCurrentPreset()
            if not name:
                return

        # Add in GUI
        if name not in self._setupInfo.laserPresets:
            self._widget.addPreset(name)

        # Set in setup info
        self._setupInfo.setLaserPreset(name, self.makePreset())
        configfiletools.saveSetupInfo(configfiletools.loadOptions()[0], self._setupInfo)

        # Update selected preset in GUI
        self._widget.setCurrentPreset(name)

    def savePresetAs(self):
        """ Handles what happens when the user requests the current laser
        values to be saved as a new preset. """

        name = guitools.askForTextInput(self._widget, 'Add laser preset',
                                        'Enter a name for this preset:')

        if not name:  # No name provided
            return

        add = True
        if name in self._setupInfo.laserPresets:
            add = guitools.askYesNoQuestion(
                self._widget,
                'Laser preset already exists',
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
            'Delete laser preset?',
            f'Are you sure you want to delete the preset "{presetToDelete}"?'
        )

        if confirmationResult:
            # Remove in GUI
            self._widget.removePreset(presetToDelete)

            # Remove from setup info
            self._setupInfo.removeLaserPreset(presetToDelete)
            configfiletools.saveSetupInfo(configfiletools.loadOptions()[0], self._setupInfo)

    def presetScanDefaultToggled(self):
        """ Handles what happens when the user requests the "default for
        scanning" state of the selected preset to be toggled. """

        currentPresetName = self._widget.getCurrentPreset()
        if not currentPresetName:
            return

        enabling = self._setupInfo.defaultLaserPresetForScan != currentPresetName

        # Set in setup info
        self._setupInfo.setDefaultLaserPresetForScan(currentPresetName if enabling else None)
        configfiletools.saveSetupInfo(configfiletools.loadOptions()[0], self._setupInfo)

        # Update in GUI
        self._widget.setScanDefaultPreset(currentPresetName if enabling else None)
        self._widget.setScanDefaultPresetActive(enabling)

    def makePreset(self):
        """ Returns a preset object corresponding to the current laser values.
        """
        return {lName: guitools.LaserPresetInfo(value=self._widget.getValue(lName))
                for lName, lManager in self._master.lasersManager if not lManager.isBinary}

    def applyPreset(self, laserPreset):
        """ Loads a preset object into the current values. """
        for laserName, laserPresetInfo in laserPreset.items():
            self.setLaserValue(laserName, laserPresetInfo.value)

    def scanChanged(self, isScanning):
        """ Handles what happens when a scan is started/stopped. """

        self.is_scanning = isScanning

        for lName, _ in self._master.lasersManager:
            enabled = self._widget.isLaserActive(lName)
            self._widget.setLaserEditable(lName, not isScanning)
            self._master.lasersManager[lName].setScanModeActive(isScanning, enabled)
        #self._master.lasersManager.execOnAll(lambda l: l.setScanModeActive(isScanning))

        defaultScanPresetName = self._setupInfo.defaultLaserPresetForScan
        if defaultScanPresetName in self._setupInfo.laserPresets:
            if isScanning and self.presetBeforeScan is None:
                # Scan started, save current values and apply default scan preset
                self.presetBeforeScan = self.makePreset()
                self.applyPreset(self._setupInfo.laserPresets[defaultScanPresetName])
            elif self.presetBeforeScan is not None:
                # Scan finished, restore the values that were set before the scan started
                self.applyPreset(self.presetBeforeScan)
                self.presetBeforeScan = None

    def scanBuilt(self, deviceList):
        for lName, _ in self._master.lasersManager:
            if lName not in deviceList:
                self._widget.setLaserEditable(lName, True)

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

    @APIExport()
    def getLaserNames(self) -> List[str]:
        """ Returns the device names of all lasers. These device names can be
        passed to other laser-related functions. """
        return self._master.lasersManager.getAllDeviceNames()

    @APIExport(runOnUIThread=True)
    def setLaserActive(self, laserName: str, active: bool) -> None:
        """ Sets whether the specified laser is powered on. """
        self._widget.setLaserActive(laserName, active)

    @APIExport(runOnUIThread=True)
    def setLaserValue(self, laserName: str, value: Union[int, float]) -> None:
        """ Sets the value of the specified laser, in the units that the laser
        uses. """
        self._widget.setValue(laserName, value)

    @APIExport()
    def changeScanPower(self, laserName, laserValue):
        defaultPreset = self._setupInfo.laserPresets[self._setupInfo.defaultLaserPresetForScan]
        defaultPreset[laserName] = guitools.LaserPresetInfo(value=laserValue)

    @APIExport(runOnUIThread=True)
    def sendTrigger(self, triggerId: int):
        """ Sends a trigger puls through external device """
        #TODo: Very special case, try to move in seperate manager 
        self._master.rs232sManager["ESP32"]._esp32.sendTrigger(triggerId)

    @APIExport(runOnUIThread=True)
    def post_json(self, path: str, payload: dict) -> str:
        """ Sends the specified command to the RS232 device and returns a
        string encoded from the received bytes. """
        return self._master.rs232sManager["ESP32"]._esp32.post_json(path, payload=payload, headers=None, timeout=1)

    @APIExport(runOnUIThread=True)
    def send_serial(self, payload: str) -> str:
        """ Sends the specified command to the RS232 device and returns a
        string encoded from the received bytes. """
        self._master.rs232sManager["ESP32"]._esp32.writeSerial(payload)
        #self.__logger.debug(payload)
        returnmessage = self._master.rs232sManager["ESP32"]._esp32.readSerial(is_blocking=True, timeout=1)

        return returnmessage




_attrCategory = 'Laser'
_enabledAttr = 'Enabled'
_valueAttr = 'Value'
_freqEnAttr = "ModulationEnabled"
_freqAttr = "Frequency"
_dcAttr = "DutyCycle"


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
