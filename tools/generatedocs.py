import os
import pydoc

from imswitch.imcommon import prepareApp, constants
from imswitch.imcommon.controller import ModuleCommunicationChannel

from imswitch import imreconstruct, imcontrol

# Create and set working directory
docsDir = os.path.join(constants.rootFolderPath, 'docs')
apiDocsDir = os.path.join(docsDir, 'api')
os.makedirs(apiDocsDir, exist_ok=True)
os.chdir(apiDocsDir)

# Generate docs
dummyApp = prepareApp()
dummyModuleCommChannel = ModuleCommunicationChannel()

modules = [imcontrol, imreconstruct]  # imscripting excluded
for modulePackage in modules:
    _, mainController = modulePackage.getMainViewAndController(dummyModuleCommChannel)
    if not hasattr(mainController, 'api'):
        continue

    class API:
        pass

    API.__name__ = modulePackage.__name__
    for key, value in mainController.api.items():
        setattr(API, key, value)

    pydoc.writedoc(API)

dummyApp.exit(0)


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
