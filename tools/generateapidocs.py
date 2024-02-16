import inspect
import os

from imswitch import imcontrol, imreconstruct
from imswitch.imcommon import prepareApp
from imswitch.imcommon.controller import ModuleCommunicationChannel, MultiModuleWindowController
from imswitch.imcontrol.model import Options
from imswitch.imcontrol.view import ViewSetupInfo
from imswitch.imscripting.model.actions import _Actions


def writeDocs(cls, isClass=True, displayName=None):
    def fixIndent(docstring, indent):
        lines = docstring.splitlines()
        for i in range(len(lines)):
            lines[i] = f'{" " * indent}{lines[i].lstrip()}'
        return '\n'.join(lines)

    rst = ''
    indent = 0

    if not displayName:
        displayName = cls.__name__

    # Title
    title = displayName
    rst += f'{"*" * len(title)}\n'
    rst += f'{title}\n'
    rst += f'{"*" * len(title)}\n'
    rst += '\n'

    # Class
    if isClass:
        rst += f'.. class:: {displayName}\n'
        indent += 3
        if cls.__doc__:
            rst += '\n'
            rst += f'{fixIndent(cls.__doc__, indent)}\n'
        rst += '\n'

    # Attributes
    for attrName in dir(cls):
        if attrName.startswith('_'):
            continue  # Skip private members

        attr = getattr(cls, attrName)
        if callable(attr):
            # Method
            rst += f'{" " * indent}.. method:: {attr.__name__}{inspect.signature(attr)}\n'
            indent += 3
            if attr.__doc__:
                rst += '\n'
                rst += f'{fixIndent(attr.__doc__, indent)}\n'
            rst += '\n'
            indent -= 3

    # End class
    if isClass:
        indent -= 3

    # Write rst file
    with open(os.path.join(apiDocsDir, f'{cls.__name__}.rst'), 'w') as file:
        file.write(rst)


# Create and set working directory
docsDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../docs')
apiDocsDir = os.path.join(docsDir, 'api')
os.makedirs(apiDocsDir, exist_ok=True)

# Generate docs for modules
dummyApp = prepareApp()
dummyModuleCommChannel = ModuleCommunicationChannel()

modules = [imcontrol, imreconstruct]  # imscripting excluded
for modulePackage in modules:
    kwargs = {}
    if False and modulePackage == imcontrol:
        kwargs['overrideSetupInfo'] = ViewSetupInfo.from_json(
            """
            {
            }
            """
        )
        kwargs['overrideOptions'] = Options.from_json(
            """
            {
                "setupFileName": ""
            }
            """
        )

    _, mainController = modulePackage.getMainViewAndController(dummyModuleCommChannel, **kwargs)
    if not hasattr(mainController, 'api'):
        continue

    moduleId = modulePackage.__name__
    moduleId = moduleId[moduleId.rindex('.') + 1:]
    moduleId = f'api.{moduleId}'

    class API:
        pass

    API.__name__ = moduleId
    API.__doc__ = f""" These functions are available in the {moduleId} object. """

    for key, value in mainController.api._asdict().items():
        setattr(API, key, value)

    writeDocs(API)

dummyApp.exit(0)


# Generate docs for actions
class _actions:
    """ These functions are available at the global level. """
    pass


for subObjName in dir(_Actions):
    subObj = getattr(_Actions, subObjName)
    if hasattr(subObj, '_APIExport') and subObj._APIExport:
        setattr(_actions, subObjName, subObj)

writeDocs(_actions, isClass=False, displayName='Global-level functions')


# Generate docs for mainWindow
class mainWindow:
    """ These functions are available in the mainWindow object. """
    pass


for subObjName in dir(MultiModuleWindowController):
    subObj = getattr(MultiModuleWindowController, subObjName)
    if hasattr(subObj, '_APIExport') and subObj._APIExport:
        setattr(mainWindow, subObjName, subObj)

writeDocs(mainWindow)


# Copyright (C) 2020-2023 ImSwitch developers
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
