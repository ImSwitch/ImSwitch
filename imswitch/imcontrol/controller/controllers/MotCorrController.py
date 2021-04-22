from .basecontrollers import ImConWidgetController


class MotCorrController(ImConWidgetController):
    """ Linked to MotCorrWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        return

        # TODO: BELOW IS JUST COPIED FROM LASERCONTROLLER
        self.aotfLasers = {}
        for laserName, laserManager in self._master.lasersManager:
            if not laserManager.isDigital:
                self.aotfLasers[laserName] = False

        # Connect LaserWidget signals
        for laserModule in self._widget.laserModules.values():
            if not self._master.lasersManager[laserModule.laser].isBinary:
                if self._master.lasersManager[laserModule.laser].isDigital:
                    self.changeEdit(laserModule.laser)

                laserModule.slider.valueChanged[int].connect(
                    lambda _, laser=laserModule.laser: self.changeSlider(laser))
                laserModule.setPointEdit.returnPressed.connect(
                    lambda laser=laserModule.laser: self.changeEdit(laser))

            laserModule.enableButton.toggled.connect(
                lambda _, laser=laserModule.laser: self.toggleLaser(laser))

        for digModuleLaser in self._widget.digModule.powers.keys():
            self._widget.digModule.powers[digModuleLaser].textChanged.connect(
                lambda _, laser=digModuleLaser: self.updateDigitalPowers([laser])
            )

        self._widget.digModule.DigitalControlButton.clicked.connect(
            lambda: self.GlobalDigitalMod(list(self._widget.digModule.powers.keys()))
        )
        self._widget.digModule.updateDigPowersButton.clicked.connect(
            lambda: self.updateDigitalPowers(list(self._widget.digModule.powers.keys()))
        )

    def closeEvent(self):
        self._master.lasersManager.execOnAll(lambda l: l.setDigitalMod(False, 0))
        self._master.lasersManager.execOnAll(lambda l: l.setValue(0))

    def toggleLaser(self, laserName):
        """ Enable or disable laser (on/off)."""
        self._master.lasersManager[laserName].setEnabled(
            self._widget.laserModules[laserName].enableButton.isChecked()
        )

    def changeSlider(self, laserName):
        """ Change power with slider magnitude. """
        magnitude = self._widget.laserModules[laserName].slider.value()
        if laserName not in self.aotfLasers.keys() or not self.aotfLasers[laserName]:
            self._master.lasersManager[laserName].setValue(magnitude)
            self._widget.laserModules[laserName].setPointEdit.setText(str(magnitude))

    def changeEdit(self, laserName):
        """ Change power with edit magnitude. """
        magnitude = float(self._widget.laserModules[laserName].setPointEdit.text())
        if laserName not in self.aotfLasers.keys() or not self.aotfLasers[laserName]:
            self._master.lasersManager[laserName].setValue(magnitude)
            self._widget.laserModules[laserName].slider.setValue(magnitude)

    def updateDigitalPowers(self, laserNames):
        """ Update the powers if the digital mod is on. """
        if self._widget.digModule.DigitalControlButton.isChecked():
            for laserName in laserNames:
                self._master.lasersManager[laserName].setValue(
                    float(self._widget.digModule.powers[laserName].text())
                )

    def GlobalDigitalMod(self, laserNames):
        """ Start digital modulation. """
        digMod = self._widget.digModule.DigitalControlButton.isChecked()
        for laserName in laserNames:
            laserModule = self._widget.laserModules[laserName]
            laserManager = self._master.lasersManager[laserName]

            if laserManager.isBinary:
                continue

            value = float(self._widget.digModule.powers[laserName].text())
            if laserManager.isDigital:
                laserManager.setDigitalMod(digMod, value)
            else:
                laserManager.setValue(value)
                laserModule.enableButton.setChecked(False)
                laserModule.enableButton.setEnabled(not digMod)
                self.aotfLasers[laserName] = digMod
                laserManager.setEnabled(False)  # TODO: Correct?

            laserModule.setPointEdit.setEnabled(not digMod)
            laserModule.slider.setEnabled(not digMod)

            if not digMod:
                self.changeEdit(laserName)

    def setDigitalButton(self, b):
        self._widget.digModule.DigitalControlButton.setChecked(b)
        self.GlobalDigitalMod(
            [laser.name for laser in self._master.lasersManager if laser.isDigital]
        )


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
