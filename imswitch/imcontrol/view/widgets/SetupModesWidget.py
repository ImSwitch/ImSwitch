from qtpy import QtCore, QtGui, QtWidgets

from imswitch.imcontrol.view.guitools import BetterPushButton
from .basewidgets import Widget


class SetupModesWidget(Widget):
    """Compact widget for saving and applying named setup modes."""

    _transparentToolButtonStyle = """
        QToolButton {
            border: none;
            background: transparent;
        }
        QToolButton:hover {
            background: transparent;
        }
        QToolButton:pressed {
            background: transparent;
        }
    """

    inspectDialogFontPointSize = 10

    sigUpdateMode = QtCore.Signal()
    sigSaveAsMode = QtCore.Signal()
    sigModeSelected = QtCore.Signal(str)
    sigReloadMode = QtCore.Signal()
    sigInspectModes = QtCore.Signal()
    sigRenameMode = QtCore.Signal()
    sigDuplicateMode = QtCore.Signal()
    sigSetShortcut = QtCore.Signal()
    sigSafetySettings = QtCore.Signal()
    sigDeleteMode = QtCore.Signal()
    sigRevealFolder = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._modeSummaries = {}
        self._backendAvailable = False

        self.setMinimumWidth(260)

        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(6, 6, 6, 6)
        mainLayout.setSpacing(6)

        title = QtWidgets.QLabel("General Setup Mode")
        title.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        font = title.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 4)
        title.setFont(font)
        title.setContentsMargins(0, 6, 0, 2)

        self.modeWarningButton = QtWidgets.QToolButton()
        self.modeWarningButton.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxWarning)
        )
        self.modeWarningButton.setStyleSheet(self._transparentToolButtonStyle)
        self.modeWarningButton.setAutoRaise(True)
        self.modeWarningButton.setFixedSize(20, 20)
        self.modeWarningButton.setToolTip(
            "Selecting a mode immediately applies saved hardware settings."
        )

        titleLayout = QtWidgets.QHBoxLayout()
        titleLayout.setContentsMargins(0, 0, 0, 0)
        titleLayout.addWidget(title)
        titleLayout.addWidget(self.modeWarningButton)
        titleLayout.addStretch(1)

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator.setMaximumHeight(12)

        controlsWidget = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout(controlsWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(4)
        layout.setVerticalSpacing(0)

        modeLabel = QtWidgets.QLabel("Mode:")
        self.modeCombo = QtWidgets.QComboBox()
        self.modeCombo.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        )
        self.modeCombo.view().setMouseTracking(True)
        self.modeCombo.wheelEvent = lambda event: None

        self.infoButton = QtWidgets.QToolButton()
        self.infoButton.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxInformation)
        )
        self.infoButton.setAutoRaise(True)
        self.infoButton.setFixedSize(18, 18)
        self.infoButton.setToolTip("Open setup mode inspector")
        self.infoButton.setStyleSheet(self._transparentToolButtonStyle)
        self.reloadButton = QtWidgets.QToolButton()
        self.reloadButton.setIcon(
            self.style().standardIcon(
                getattr(QtWidgets.QStyle, "SP_BrowserReload", QtWidgets.QStyle.SP_ArrowRight)
            )
        )
        self.reloadButton.setAutoRaise(True)
        self.reloadButton.setFixedSize(22, 22)
        self.reloadButton.setToolTip("Reload selected mode")
        self.reloadButton.setStyleSheet(self._transparentToolButtonStyle)
        self.updateButton = BetterPushButton("Update Mode")
        self.moreButton = QtWidgets.QToolButton()
        self.moreButton.setText("More")
        self.moreButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)

        self.moreMenu = QtWidgets.QMenu(self.moreButton)
        self.saveAsAction = self.moreMenu.addAction("Save as...")
        self.moreMenu.addSeparator()
        self.renameAction = self.moreMenu.addAction("Rename mode...")
        self.duplicateAction = self.moreMenu.addAction("Duplicate mode...")
        self.shortcutAction = self.moreMenu.addAction("Set shortcut...")
        self.moreMenu.addSeparator()
        self.safetySettingsAction = self.moreMenu.addAction("Safety settings...")
        self.revealFolderAction = self.moreMenu.addAction("Open modes folder")
        self.moreMenu.addSeparator()
        self.deleteAction = self.moreMenu.addAction("Delete mode")
        self.moreButton.setMenu(self.moreMenu)

        layout.addWidget(modeLabel, 0, 0)
        layout.addWidget(self.modeCombo, 0, 1)
        layout.addWidget(self.infoButton, 0, 2)
        layout.addWidget(self.reloadButton, 0, 3)
        layout.addWidget(self.updateButton, 0, 4)
        layout.addWidget(self.moreButton, 0, 5)
        layout.setColumnStretch(1, 1)

        mainLayout.addLayout(titleLayout)
        mainLayout.addWidget(separator)
        mainLayout.addWidget(controlsWidget)
        mainLayout.addStretch(1)

        self.modeCombo.currentIndexChanged.connect(self._onModeIndexChanged)
        self.modeCombo.activated.connect(self._onModeActivated)
        self.infoButton.clicked.connect(self.sigInspectModes)
        self.reloadButton.clicked.connect(self.sigReloadMode)
        self.updateButton.clicked.connect(self.sigUpdateMode)
        self.saveAsAction.triggered.connect(self.sigSaveAsMode)
        self.renameAction.triggered.connect(self.sigRenameMode)
        self.duplicateAction.triggered.connect(self.sigDuplicateMode)
        self.shortcutAction.triggered.connect(self.sigSetShortcut)
        self.safetySettingsAction.triggered.connect(self.sigSafetySettings)
        self.deleteAction.triggered.connect(self.sigDeleteMode)
        self.revealFolderAction.triggered.connect(self.sigRevealFolder)

        self.setBackendAvailable(False)
        self.setModes([])

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        self.setMaximumHeight(105)

    def setBackendAvailable(self, available):
        self._backendAvailable = bool(available)
        self.saveAsAction.setEnabled(self._backendAvailable)
        self.revealFolderAction.setEnabled(self._backendAvailable)
        self._updateModeControls()

    def setModes(self, modeSummaries, selectedName=None):
        self._modeSummaries = {
            summary["name"]: summary for summary in modeSummaries
            if summary.get("name")
        }

        self.modeCombo.blockSignals(True)
        self.modeCombo.clear()

        if modeSummaries:
            self.modeCombo.addItem("", None)
            for summary in modeSummaries:
                self.modeCombo.addItem(summary.get("displayName", summary["name"]), summary["name"])
                self.modeCombo.setItemData(
                    self.modeCombo.count() - 1,
                    self._modeTooltipText(summary),
                    QtCore.Qt.ToolTipRole
                )
        else:
            self.modeCombo.addItem("No saved modes", None)

        if selectedName:
            index = self.modeCombo.findData(selectedName)
            if index >= 0:
                self.modeCombo.setCurrentIndex(index)

        self.modeCombo.blockSignals(False)
        self._updateInfoButton()
        self._updateModeControls()

    def getSelectedModeName(self):
        return self.modeCombo.currentData()

    def showInspectModesDialog(self, modeDetails, selectedName=None):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Inspect setup modes")
        dialog.resize(720, 420)
        dialogFont = self._applyInspectDialogFont(dialog)

        mainLayout = QtWidgets.QHBoxLayout(dialog)

        modeList = QtWidgets.QListWidget()
        modeList.setMinimumWidth(210)
        for details in modeDetails:
            item = QtWidgets.QListWidgetItem(details.get("displayName") or details["name"])
            item.setData(QtCore.Qt.UserRole, details["name"])
            modeList.addItem(item)
        mainLayout.addWidget(modeList, 0)

        detailWidget = QtWidgets.QWidget()
        detailLayout = QtWidgets.QVBoxLayout(detailWidget)
        detailLayout.setContentsMargins(6, 0, 0, 0)

        nameLabel = QtWidgets.QLabel()
        nameFont = QtGui.QFont(dialogFont)
        nameFont.setBold(True)
        nameLabel.setFont(nameFont)
        detailLayout.addWidget(nameLabel)

        form = QtWidgets.QFormLayout()
        shortcutLabel = QtWidgets.QLabel()
        updatedLabel = QtWidgets.QLabel()
        createdLabel = QtWidgets.QLabel()
        componentsLabel = QtWidgets.QLabel()
        componentsLabel.setWordWrap(True)
        form.addRow("Shortcut:", shortcutLabel)
        form.addRow("Updated:", updatedLabel)
        form.addRow("Created:", createdLabel)
        form.addRow("Includes:", componentsLabel)
        detailLayout.addLayout(form)

        descriptionLabel = QtWidgets.QLabel("Description")
        descriptionFont = QtGui.QFont(dialogFont)
        descriptionFont.setBold(True)
        descriptionLabel.setFont(descriptionFont)

        descriptionEdit = QtWidgets.QPlainTextEdit()
        descriptionEdit.setReadOnly(True)
        descriptionEdit.setMaximumHeight(85)
        descriptionEdit.setPlaceholderText("No description")
        self._applyPlainTextEditFont(descriptionEdit, dialogFont)
        
        detailLayout.addWidget(descriptionLabel)
        detailLayout.addWidget(descriptionEdit)
        
        savedStateLabel = QtWidgets.QLabel("Saved state summary")
        savedStateFont = QtGui.QFont(dialogFont)
        savedStateFont.setBold(True)
        savedStateLabel.setFont(savedStateFont)

        stateSummary = QtWidgets.QPlainTextEdit()
        stateSummary.setReadOnly(True)
        self._applyPlainTextEditFont(stateSummary, dialogFont)

        detailLayout.addWidget(savedStateLabel)
        detailLayout.addWidget(stateSummary, 1)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        buttonBox.rejected.connect(dialog.reject)
        detailLayout.addWidget(buttonBox)

        mainLayout.addWidget(detailWidget, 1)

        detailsByName = {details["name"]: details for details in modeDetails}

        def updateDetails(index):
            item = modeList.item(index)
            if item is None:
                nameLabel.setText("No setup modes")
                shortcutLabel.setText("")
                updatedLabel.setText("")
                createdLabel.setText("")
                componentsLabel.setText("")
                descriptionEdit.setPlainText("")
                stateSummary.setPlainText("")
                return

            details = detailsByName.get(item.data(QtCore.Qt.UserRole), {})
            nameLabel.setText(details.get("name", ""))
            shortcutLabel.setText(details.get("shortcut") or "None")
            updatedLabel.setText(details.get("updatedAt") or "Unknown")
            createdLabel.setText(details.get("createdAt") or "Unknown")
            componentsLabel.setText(", ".join(details.get("includedComponents") or []))
            descriptionEdit.setPlainText(details.get("description") or "")
            stateSummary.setPlainText("\n".join(details.get("stateSummary") or []))

        modeList.currentRowChanged.connect(updateDetails)

        selectedRow = 0
        if selectedName:
            for row in range(modeList.count()):
                if modeList.item(row).data(QtCore.Qt.UserRole) == selectedName:
                    selectedRow = row
                    break

        if modeList.count() > 0:
            modeList.setCurrentRow(selectedRow)
        else:
            updateDetails(-1)

        self._execDialog(dialog)

    def _modeTooltipText(self, summary):
        lines = []

        description = summary.get("description")
        if description:
            lines.append(description)

        shortcut = summary.get("shortcut")
        if shortcut:
            lines.append(f"Shortcut: {shortcut}")

        components = summary.get("includedComponents") or []
        if components:
            lines.append("Includes: " + ", ".join(components))

        return "\n\n".join(lines)

    def _applyInspectDialogFont(self, dialog):
        font = QtGui.QFont(dialog.font())
        font.setPointSize(self.inspectDialogFontPointSize)
        dialog.setFont(font)
        dialog.setStyleSheet(
            f"QDialog QWidget {{ font-size: {self.inspectDialogFontPointSize}pt; }}"
        )
        return font

    def _applyPlainTextEditFont(self, edit, font):
        edit.setFont(font)
        edit.document().setDefaultFont(font)

    def showSaveModeDialog(
            self, defaultName, defaultDescription, defaultShortcut,
            components, selectedComponents):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Save setup mode")

        layout = QtWidgets.QVBoxLayout(dialog)
        form = QtWidgets.QFormLayout()

        nameEdit = QtWidgets.QLineEdit(defaultName or "")
        descriptionEdit = QtWidgets.QPlainTextEdit(defaultDescription or "")
        descriptionEdit.setFixedHeight(70)

        shortcutRow = QtWidgets.QWidget()
        shortcutLayout = QtWidgets.QHBoxLayout(shortcutRow)
        shortcutLayout.setContentsMargins(0, 0, 0, 0)
        shortcutEdit = self._makeShortcutEditor(defaultShortcut)
        clearShortcutButton = BetterPushButton("Clear")
        clearShortcutButton.clicked.connect(lambda: self._clearShortcutEditor(shortcutEdit))
        shortcutLayout.addWidget(shortcutEdit, 1)
        shortcutLayout.addWidget(clearShortcutButton)

        form.addRow("Name:", nameEdit)
        form.addRow("Description:", descriptionEdit)
        form.addRow("Shortcut:", shortcutRow)
        layout.addLayout(form)

        includeGroup = QtWidgets.QGroupBox("Include in snapshot")
        includeLayout = QtWidgets.QGridLayout(includeGroup)
        includeLayout.setContentsMargins(6, 6, 6, 6)
        includeLayout.setHorizontalSpacing(10)
        includeLayout.setVerticalSpacing(3)

        selectedComponents = set(selectedComponents or [])
        componentChecks = {}
        for index, component in enumerate(components):
            check = QtWidgets.QCheckBox(component)
            check.setChecked(component in selectedComponents)
            componentChecks[component] = check
            includeLayout.addWidget(check, index // 2, index % 2)

        layout.addWidget(includeGroup)

        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel
        )
        layout.addWidget(buttonBox)

        def acceptIfValid():
            if not nameEdit.text().strip():
                QtWidgets.QMessageBox.warning(dialog, "Save setup mode", "Mode name is required.")
                return

            included = [
                component for component, check in componentChecks.items()
                if check.isChecked()
            ]
            if not included:
                QtWidgets.QMessageBox.warning(
                    dialog, "Save setup mode", "Select at least one component."
                )
                return

            dialog.accept()

        buttonBox.accepted.connect(acceptIfValid)
        buttonBox.rejected.connect(dialog.reject)

        if self._execDialog(dialog) != QtWidgets.QDialog.Accepted:
            return None

        return {
            "name": nameEdit.text().strip(),
            "description": descriptionEdit.toPlainText().strip(),
            "shortcut": self._shortcutEditorText(shortcutEdit),
            "components": [
                component for component, check in componentChecks.items()
                if check.isChecked()
            ],
        }

    def showUpdateModeDialog(self, modeName, summaries, warnings):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Update setup mode")

        layout = QtWidgets.QVBoxLayout(dialog)
        layout.addWidget(QtWidgets.QLabel(f'Update "{modeName}" with current hardware state?'))

        summaryList = QtWidgets.QListWidget()
        summaryList.setMinimumWidth(420)
        summaryList.setMaximumHeight(220)
        for summary in summaries:
            summaryList.addItem(summary)
        layout.addWidget(summaryList)

        if warnings:
            warningLabel = QtWidgets.QLabel("Snapshot warnings:\n" + "\n".join(warnings))
            warningLabel.setWordWrap(True)
            layout.addWidget(warningLabel)

        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel
        )
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)

        return self._execDialog(dialog) == QtWidgets.QDialog.Accepted

    def showShortcutDialog(self, modeName, currentShortcut):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Set setup mode shortcut")

        layout = QtWidgets.QVBoxLayout(dialog)
        layout.addWidget(QtWidgets.QLabel(modeName))

        row = QtWidgets.QWidget()
        rowLayout = QtWidgets.QHBoxLayout(row)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        shortcutEdit = self._makeShortcutEditor(currentShortcut)
        clearButton = BetterPushButton("Clear")
        clearButton.clicked.connect(lambda: self._clearShortcutEditor(shortcutEdit))
        rowLayout.addWidget(shortcutEdit, 1)
        rowLayout.addWidget(clearButton)
        layout.addWidget(row)

        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)

        if self._execDialog(dialog) != QtWidgets.QDialog.Accepted:
            return None

        return self._shortcutEditorText(shortcutEdit)

    def showSafetySettingsDialog(self, settings):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Setup mode safety")

        layout = QtWidgets.QVBoxLayout(dialog)

        warnCheck = QtWidgets.QCheckBox("Warn above laser power threshold")
        warnCheck.setChecked(bool(settings.get("warnAboveLaserPowerThreshold", True)))
        layout.addWidget(warnCheck)

        thresholdSpin = QtWidgets.QDoubleSpinBox()
        thresholdSpin.setRange(0.0, 1000000.0)
        thresholdSpin.setDecimals(3)
        thresholdSpin.setSuffix(" mW")
        try:
            thresholdValue = float(settings.get("laserPowerThresholdMw", 50.0))
        except (TypeError, ValueError):
            thresholdValue = 50.0
        thresholdSpin.setValue(thresholdValue)

        form = QtWidgets.QFormLayout()
        form.addRow("Threshold:", thresholdSpin)
        layout.addLayout(form)

        shortcutCheck = QtWidgets.QCheckBox("Confirm shortcut applies when warning is triggered")
        shortcutCheck.setChecked(bool(settings.get("confirmHighPowerShortcutApply", True)))
        layout.addWidget(shortcutCheck)

        suppressedCount = len(settings.get("suppressedWarnings", []) or [])
        clearSuppressedCheck = QtWidgets.QCheckBox(
            f"Show hidden warnings again ({suppressedCount} hidden)"
        )
        clearSuppressedCheck.setEnabled(suppressedCount > 0)
        layout.addWidget(clearSuppressedCheck)

        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)

        if self._execDialog(dialog) != QtWidgets.QDialog.Accepted:
            return None

        return {
            "warnAboveLaserPowerThreshold": warnCheck.isChecked(),
            "laserPowerThresholdMw": thresholdSpin.value(),
            "confirmHighPowerShortcutApply": shortcutCheck.isChecked(),
            "clearSuppressedWarnings": clearSuppressedCheck.isChecked(),
        }

    def showNameDialog(self, title, label, suggested=""):
        result, okClicked = QtWidgets.QInputDialog.getText(
            self, title, label,
            flags=QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint,
            text=suggested or ""
        )
        return result.strip() if okClicked and result.strip() else None

    def askOverwriteMode(self, modeName):
        return self._askQuestion(
            "Overwrite setup mode",
            f'Setup mode "{modeName}" already exists. Overwrite it?'
        )

    def askDeleteMode(self, modeName):
        return self._askQuestion(
            "Delete setup mode",
            f'Delete setup mode "{modeName}"?'
        )

    def askShortcutConflict(self, shortcut, otherModeName):
        return self._askQuestion(
            "Shortcut already used",
            f'Shortcut "{shortcut}" is already assigned to "{otherModeName}". Replace it?'
        )

    def confirmHighPowerApply(self, modeName, laserEntries, thresholdMw):
        details = "\n".join(
            f'- {entry["laserName"]}: {entry["value"]:.3g} {entry["units"]}'
            for entry in laserEntries
        )

        box = QtWidgets.QMessageBox(self)
        box.setIcon(QtWidgets.QMessageBox.Warning)
        box.setWindowTitle("Laser power warning")
        box.setText(
            f'Setup mode "{modeName}" turns on laser power above {thresholdMw:.3g} mW.'
        )
        box.setInformativeText(details)

        applyButton = box.addButton("Apply", QtWidgets.QMessageBox.AcceptRole)
        cancelButton = box.addButton(QtWidgets.QMessageBox.Cancel)
        box.setDefaultButton(cancelButton)
        self._execDialog(box)
        return box.clickedButton() == applyButton

    def showWarnings(self, title, warnings, allowSuppress=False):
        if not warnings:
            return False

        box = QtWidgets.QMessageBox(self)
        box.setIcon(QtWidgets.QMessageBox.Warning)
        box.setWindowTitle(title)
        box.setText(title)
        box.setInformativeText("\n".join(warnings))
        box.addButton(QtWidgets.QMessageBox.Ok)

        suppressCheck = None
        if allowSuppress:
            suppressCheck = QtWidgets.QCheckBox("Don't show these warnings again")
            if hasattr(box, "setCheckBox"):
                box.setCheckBox(suppressCheck)

        if allowSuppress and suppressCheck is not None and not hasattr(box, "setCheckBox"):
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle(title)
            layout = QtWidgets.QVBoxLayout(dialog)
            label = QtWidgets.QLabel("\n".join(warnings))
            label.setWordWrap(True)
            layout.addWidget(label)
            layout.addWidget(suppressCheck)
            buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
            buttonBox.accepted.connect(dialog.accept)
            layout.addWidget(buttonBox)
            self._execDialog(dialog)
            return suppressCheck.isChecked()

        self._execDialog(box)
        return bool(suppressCheck is not None and suppressCheck.isChecked())

    def showError(self, title, message):
        QtWidgets.QMessageBox.critical(self, title, message)

    def showInformation(self, title, message):
        QtWidgets.QMessageBox.information(self, title, message)

    def _onModeIndexChanged(self, _index):
        self._updateInfoButton()
        self._updateModeControls()

    def _onModeActivated(self, _index):
        modeName = self.getSelectedModeName()
        if modeName:
            self.sigModeSelected.emit(modeName)

    def _updateInfoButton(self):
        self.infoButton.setToolTip("Open setup mode inspector")
        self.infoButton.setEnabled(self._backendAvailable and bool(self._modeSummaries))

    def _updateModeControls(self):
        hasMode = self.getSelectedModeName() is not None
        hasModes = bool(self._modeSummaries)
        hasUsableMode = self._backendAvailable and hasMode
        self.modeCombo.setEnabled(self._backendAvailable and hasModes)
        self.reloadButton.setEnabled(hasUsableMode)
        self.updateButton.setEnabled(hasUsableMode)
        self.moreButton.setEnabled(self._backendAvailable)
        self.renameAction.setEnabled(hasUsableMode)
        self.duplicateAction.setEnabled(hasUsableMode)
        self.shortcutAction.setEnabled(hasUsableMode)
        self.deleteAction.setEnabled(hasUsableMode)

    def _makeShortcutEditor(self, shortcut):
        if hasattr(QtWidgets, "QKeySequenceEdit"):
            editor = QtWidgets.QKeySequenceEdit()
            if shortcut:
                editor.setKeySequence(QtGui.QKeySequence(shortcut))
        else:
            editor = QtWidgets.QLineEdit(shortcut or "")
            editor.setPlaceholderText("F3")
        return editor

    def _clearShortcutEditor(self, editor):
        if hasattr(QtWidgets, "QKeySequenceEdit") and isinstance(editor, QtWidgets.QKeySequenceEdit):
            editor.setKeySequence(QtGui.QKeySequence())
        else:
            editor.clear()

    def _shortcutEditorText(self, editor):
        if hasattr(QtWidgets, "QKeySequenceEdit") and isinstance(editor, QtWidgets.QKeySequenceEdit):
            sequence = editor.keySequence()
            try:
                return sequence.toString(QtGui.QKeySequence.NativeText).strip()
            except TypeError:
                return sequence.toString().strip()

        return editor.text().strip()

    def _askQuestion(self, title, question):
        result = QtWidgets.QMessageBox.question(
            self, title, question,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        return result == QtWidgets.QMessageBox.Yes

    def _execDialog(self, dialog):
        if hasattr(dialog, "exec_"):
            return dialog.exec_()
        return dialog.exec()


# Copyright (C) 2026 ImSwitch developers
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
