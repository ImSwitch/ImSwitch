import os
import pydoc
import re

import html2text
import m2r

from imswitch.imcommon import prepareApp
from imswitch.imcommon.controller import ModuleCommunicationChannel, MultiModuleWindowController
from imswitch.imcontrol.model import Options
from imswitch.imcontrol.view import ViewSetupInfo
from imswitch.imscripting.model.actions import _Actions

from imswitch import imcontrol, imreconstruct


def writeDocs(cls):
    obj, name = pydoc.resolve(cls)
    html = pydoc.html.page(pydoc.describe(obj), pydoc.html.document(obj, name))  # Get Pydoc HTML
    html = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', html)  # Remove links

    markdown = html2text.html2text(html)  # Convert to markdown
    markdown = markdown.replace('`', '')  # Remove unnecessary backticks
    markdown = re.sub(r'^[ \t|]+', '', markdown, flags=re.MULTILINE)  # Remove unnecessary pipes

    rst = m2r.convert(markdown)  # Convert to reStructuredText

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
    if modulePackage == imcontrol:
        kwargs['overrideSetupInfo'] = ViewSetupInfo.from_json(
            """
            {
                "scan": {
                    "scanDesigner": "BetaScanDesigner",
                    "scanDesignerParams": {
                        "return_time": 0.01
                    },
                    "TTLCycleDesigner": "BetaTTLCycleDesigner",
                    "TTLCycleDesignerParams": {},
                    "sampleRate": 100000
                },
                "availableWidgets": true
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

    for key, value in mainController.api.items():
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

writeDocs(_actions)

# Generate docs for mainWindow
class mainWindow:
    """ These functions are available in the mainWindow object. """
    pass

for subObjName in dir(MultiModuleWindowController):
    subObj = getattr(MultiModuleWindowController, subObjName)
    if hasattr(subObj, '_APIExport') and subObj._APIExport:
        setattr(mainWindow, subObjName, subObj)

writeDocs(mainWindow)


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
