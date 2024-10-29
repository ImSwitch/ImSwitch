from typing import List, Union

from imswitch.imcommon.model import APIExport
from imswitch.imcontrol.model import configfiletools
from imswitch.imcontrol.view import guitools
from ..basecontrollers import ImConWidgetController


class ShutterController(ImConWidgetController):
    """ Linked to ShutterWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ShutterModules = {}
        self.stateBeforeScan = {}

        self.settingAttr = False

        # Set up Shutters
        for sName, _ in self._master.shuttersManager:
            self._widget.addShutter(sName)
            self.setSharedAttr(sName, _enabledAttr, self._widget.isShutterActive(sName))

        # Connect CommunicationChannel signals
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged)
        self._commChannel.sigScanStarting.connect(lambda: self.scanChanged(True))
        self._commChannel.sigScanBuilt.connect(self.scanBuilt)
        self._commChannel.sigScanEnded.connect(lambda: self.scanChanged(False))

        # Connect ShutterWidget signals
        self._widget.sigStateChanged.connect(self.toggleShutter)

    def closeEvent(self):
        self._master.shuttersManager.execOnAll(lambda l: l.setScanModeActive(False))

    def toggleShutter(self, shutterName, enabled):
        """ Enable or disable shutter (on/off)."""
        self._master.shuttersManager[shutterName].setEnabled(enabled)
        self.setSharedAttr(shutterName, _enabledAttr, enabled)

    def scanChanged(self, isScanning):
        """ Handles what happens when a scan is started/stopped. """
        for sName, _ in self._master.shuttersManager:
            self._widget.setShutterEditable(sName, not isScanning)
        self._master.shuttersManager.execOnAll(lambda l: l.setScanModeActive(isScanning))
        
        if isScanning:
            # Si un scan commence, sauvegarde l'état actuel du shutter et ouvre le shutter              
            if sName not in self.stateBeforeScan:
                self.stateBeforeScan[sName] = self._widget.isShutterActive(sName)
            self._widget.setShutterActive(sName, True)
        else:
            # Si le scan est terminé, restaure l'état précédent
            if sName in self.stateBeforeScan:
                self._widget.setShutterActive(sName,self.stateBeforeScan[sName])
                del self.stateBeforeScan[sName]
        
    def scanBuilt(self, deviceList):
        for lName, _ in self._master.shuttersManager:
            if lName not in deviceList:
                self._widget.setShutterEditable(lName, True)

    def attrChanged(self, key, value):
        if self.settingAttr or len(key) != 3 or key[0] != _attrCategory:
            return

        shutterName = key[1]
        if key[2] == _enabledAttr:
            self.setShutterActive(shutterName, value)

    def setSharedAttr(self, shutterName, attr, value):
        self.settingAttr = True
        try:
            self._commChannel.sharedAttrs[(_attrCategory, shutterName, attr)] = value
        finally:
            self.settingAttr = False

    @APIExport()
    def getShutterNames(self) -> List[str]:
        """ Returns the device names of all shutters. These device names can be
        passed to other shutter-related functions. """
        return self._master.shuttersManager.getAllDeviceNames()

    @APIExport(runOnUIThread=True)
    def setShutterActive(self, shutterName: str, active: bool) -> None:
        """ Sets whether the specified shutter is powered on. """
        self._widget.setShutterActive(shutterName, active)

    @APIExport(runOnUIThread=True)
    def sendTrigger(self, triggerId: int):
        """ Sends a trigger puls through external device """
        #TODo: Very special case, try to move in seperate manager 
        self._master.rs232sManager["ESP32"]._esp32.sendTrigger(triggerId)


_attrCategory = 'Shutter'
_enabledAttr = 'Enabled'
