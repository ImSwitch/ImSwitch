import datetime
import json
import os
import traceback
from urllib.parse import quote

from imswitch.imcommon.model import APIExport, dirtools, initLogger

from .basecontrollers import SetupModeMixin


class SetupModeController:
    """Backend for saving and applying named imcontrol setup modes.

    A setup mode is a JSON file containing state snapshots from controllers
    that implement SetupModeMixin. This controller intentionally does not know
    details of lasers, scans, detectors, etc.; each component controller owns
    its own serialization and restore behavior.
    """

    schemaVersion = 1
    applyOrder = [
        'Settings',
        'Scan',
        'SLMs',
        'SLM',
        'LeicaStand',
        'FlipMirror',
        'Laser',
    ]

    def __init__(self, controllers, setupInfo=None):
        self._controllers = controllers
        self._setupInfo = setupInfo
        self._logger = initLogger(self)

        self._modeDir = os.path.join(dirtools.UserFileDirs.Root, 'imcontrol_setup_modes')
        os.makedirs(self._modeDir, exist_ok=True)

    @APIExport()
    def getSetupModeStorageDir(self):
        """Return the directory where setup mode JSON files are stored."""
        return self._modeDir

    @APIExport()
    def getSetupModeComponents(self):
        """Return component names that currently support setup modes."""
        return sorted(self._getModeAwareControllers().keys())

    @APIExport()
    def listSetupModes(self):
        """Return names of all saved setup modes."""
        modeNames = []

        for fileName in os.listdir(self._modeDir):
            if not fileName.endswith('.json'):
                continue

            path = os.path.join(self._modeDir, fileName)
            try:
                mode = self._readModeFile(path)
            except Exception:
                self._logger.error(f'Failed to read setup mode file: {path}')
                self._logger.error(traceback.format_exc())
                continue

            name = mode.get('name')
            if name:
                modeNames.append(name)

        return sorted(modeNames)

    @APIExport()
    def getSetupMode(self, name):
        """Return a saved setup mode by name."""
        return self._loadModeByName(name)

    @APIExport()
    def snapshotSetupModeState(self, componentNames=None):
        """Snapshot selected setup-mode components without saving them."""
        modeAwareControllers = self._getModeAwareControllers()
        componentNames = self._normalizeComponentNames(componentNames, modeAwareControllers)
        return self._snapshotComponents(componentNames, modeAwareControllers)

    @APIExport()
    def saveSetupMode(self, name, componentNames=None, description=None, shortcut=None):
        """Snapshot selected setup-mode components and save them as name.

        Args:
            name: Mode name.
            componentNames: Optional iterable of widget/component keys. If
                omitted, all currently supported setup-mode components are
                saved.
            description: Optional user description. If omitted while
                overwriting an existing mode, the previous description is
                preserved.
            shortcut: Optional shortcut text. If omitted while overwriting an
                existing mode, the previous shortcut is preserved. Pass an
                empty string to clear the shortcut.

        Returns:
            dict with keys "mode" and "warnings".
        """
        modeName = self._validateModeName(name)
        modeAwareControllers = self._getModeAwareControllers()
        componentNames = self._normalizeComponentNames(componentNames, modeAwareControllers)
        snapshot = self._snapshotComponents(componentNames, modeAwareControllers)

        now = self._nowIso()
        createdAt = now
        existingMode = None
        try:
            existingMode = self._loadModeByName(modeName)
            createdAt = existingMode.get('createdAt', now)
        except FileNotFoundError:
            pass

        if description is None and existingMode is not None:
            description = existingMode.get('description', '')
        if shortcut is None and existingMode is not None:
            shortcut = existingMode.get('shortcut')

        mode = {
            'schemaVersion': self.schemaVersion,
            'name': modeName,
            'description': description or '',
            'shortcut': self._normalizeShortcut(shortcut),
            'createdAt': createdAt,
            'updatedAt': now,
            'includedComponents': snapshot['includedComponents'],
            'state': snapshot['state'],
        }

        self._writeMode(mode)
        return {'mode': mode, 'warnings': snapshot['warnings']}

    @APIExport()
    def updateSetupModeMetadata(self, name, description=None, shortcut=None):
        """Update user-editable metadata for a saved setup mode."""
        mode = self._loadModeByName(name)

        if description is not None:
            mode['description'] = description or ''
        if shortcut is not None:
            mode['shortcut'] = self._normalizeShortcut(shortcut)

        mode['updatedAt'] = self._nowIso()
        self._writeMode(mode)
        return mode

    @APIExport()
    def renameSetupMode(self, name, newName):
        """Rename a saved setup mode and return the updated mode."""
        mode = self._loadModeByName(name)
        newModeName = self._validateModeName(newName)
        oldPath = self._modePathForName(name)
        newPath = self._modePathForName(newModeName)

        if os.path.exists(newPath):
            raise FileExistsError(f'Setup mode "{newModeName}" already exists')

        mode['name'] = newModeName
        mode['updatedAt'] = self._nowIso()
        self._writeMode(mode)

        if os.path.exists(oldPath):
            os.remove(oldPath)

        return mode

    @APIExport()
    def duplicateSetupMode(self, name, newName, description=None, shortcut=''):
        """Duplicate a saved setup mode and return the new mode."""
        sourceMode = self._loadModeByName(name)
        newModeName = self._validateModeName(newName)

        if os.path.exists(self._modePathForName(newModeName)):
            raise FileExistsError(f'Setup mode "{newModeName}" already exists')

        now = self._nowIso()
        mode = dict(sourceMode)
        mode['name'] = newModeName
        mode['description'] = (
            sourceMode.get('description', '') if description is None else description or ''
        )
        mode['shortcut'] = self._normalizeShortcut(shortcut)
        mode['createdAt'] = now
        mode['updatedAt'] = now

        self._writeMode(mode)
        return mode

    @APIExport()
    def loadSetupMode(self, name, componentNames=None):
        """Apply a saved setup mode.

        Args:
            name: Saved mode name.
            componentNames: Optional iterable of widget/component keys. If
                omitted, the mode's saved component list is applied.

        Returns:
            list of warning strings.
        """
        mode = self._loadModeByName(name)
        modeAwareControllers = self._getModeAwareControllers()
        modeState = mode.get('state', {})

        if componentNames is None:
            componentNames = mode.get('includedComponents') or list(modeState.keys())
        else:
            componentNames = self._normalizeComponentNames(componentNames, modeAwareControllers)

        componentNames = self._orderedComponentNames(componentNames)
        warnings = []

        for componentName in componentNames:
            if componentName not in modeState:
                warnings.append(f'Setup mode "{mode["name"]}" has no state for "{componentName}".')
                continue

            controller = modeAwareControllers.get(componentName)
            if controller is None:
                warnings.append(f'Setup mode component "{componentName}" is not available.')
                continue

            try:
                componentWarnings = controller.applySetupModeState(modeState[componentName])
            except Exception as e:
                self._logger.error(f'Failed to apply setup mode component: {componentName}')
                self._logger.error(traceback.format_exc())
                warnings.append(f'Failed to apply "{componentName}": {e}')
                continue

            if componentWarnings:
                warnings.extend([f'{componentName}: {warning}' for warning in componentWarnings])

        return warnings

    @APIExport()
    def deleteSetupMode(self, name):
        """Delete a saved setup mode. Returns True if a file was removed."""
        path = self._modePathForName(name)
        if not os.path.exists(path):
            return False

        os.remove(path)
        return True

    def _getModeAwareControllers(self):
        modeAwareControllers = {}

        for componentName, controller in self._controllers.items():
            if isinstance(controller, SetupModeMixin):
                modeAwareControllers[componentName] = controller

        return modeAwareControllers

    def _snapshotComponents(self, componentNames, modeAwareControllers):
        warnings = []
        includedComponents = []
        state = {}

        for componentName in componentNames:
            controller = modeAwareControllers.get(componentName)
            if controller is None:
                warnings.append(f'Setup mode component "{componentName}" is not available.')
                continue

            try:
                componentState = controller.getSetupModeState()
                self._assertJSONSerializable(componentState, componentName)
            except Exception as e:
                self._logger.error(f'Failed to snapshot setup mode component: {componentName}')
                self._logger.error(traceback.format_exc())
                warnings.append(f'Failed to snapshot "{componentName}": {e}')
                continue

            state[componentName] = componentState
            includedComponents.append(componentName)

        return {
            'includedComponents': includedComponents,
            'state': state,
            'warnings': warnings,
        }

    def _normalizeComponentNames(self, componentNames, modeAwareControllers):
        if componentNames is None:
            return sorted(modeAwareControllers.keys())

        if isinstance(componentNames, str):
            return [componentNames]

        try:
            return list(componentNames)
        except TypeError:
            raise TypeError('componentNames must be None, a string, or an iterable of strings')

    def _orderedComponentNames(self, componentNames):
        componentNames = list(componentNames)
        order = {name: index for index, name in enumerate(self.applyOrder)}
        return sorted(
            componentNames,
            key=lambda name: (order.get(name, len(order)), componentNames.index(name))
        )

    def _validateModeName(self, name):
        if not isinstance(name, str):
            raise TypeError('Setup mode name must be a string')

        modeName = name.strip()
        if not modeName:
            raise ValueError('Setup mode name must not be empty')

        return modeName

    def _normalizeShortcut(self, shortcut):
        if shortcut is None:
            return None
        if not isinstance(shortcut, str):
            raise TypeError('Setup mode shortcut must be a string or None')

        shortcut = shortcut.strip()
        return shortcut if shortcut else None

    def _modePathForName(self, name):
        modeName = self._validateModeName(name)
        safeFileName = quote(modeName, safe='') + '.json'
        return os.path.join(self._modeDir, safeFileName)

    def _loadModeByName(self, name):
        path = self._modePathForName(name)
        if not os.path.exists(path):
            raise FileNotFoundError(f'Setup mode "{name}" does not exist')

        return self._readModeFile(path)

    def _readModeFile(self, path):
        with open(path, 'r', encoding='utf-8') as file:
            mode = json.load(file)

        schemaVersion = mode.get('schemaVersion')
        if schemaVersion != self.schemaVersion:
            raise ValueError(
                f'Unsupported setup mode schema version "{schemaVersion}" in {path}'
            )

        if not mode.get('name'):
            raise ValueError(f'Setup mode file has no name: {path}')

        if not isinstance(mode.get('state', {}), dict):
            raise ValueError(f'Setup mode state must be a dict: {path}')

        return mode

    def _writeMode(self, mode):
        path = self._modePathForName(mode['name'])
        tmpPath = path + '.tmp'

        with open(tmpPath, 'w', encoding='utf-8') as file:
            json.dump(mode, file, indent=2, sort_keys=True)
            file.write('\n')

        os.replace(tmpPath, path)

    def _assertJSONSerializable(self, state, componentName):
        try:
            json.dumps(state)
        except TypeError as e:
            raise TypeError(
                f'Setup mode state for "{componentName}" is not JSON-serializable: {e}'
            )

    def _nowIso(self):
        return datetime.datetime.now().astimezone().isoformat(timespec='seconds')


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
