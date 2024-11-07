__imswitch_module__ = True
__title__ = 'Jupyter Notebook'

from imswitch import IS_HEADLESS
if not IS_HEADLESS:
    from .view import ImScrMainView
from .controller import ImScrMainController
from .view import LaunchNotebookServer


def getMainViewAndController(moduleCommChannel, multiModuleWindowController, moduleMainControllers,
                             *_args, **_kwargs):
    if IS_HEADLESS: 
        view = None
        notebookServer = LaunchNotebookServer()
        webaddr = notebookServer.startServer()
        print(webaddr)
    else:
        view = ImScrMainView()
    
    try:
        controller = ImScrMainController(
            view,
            moduleCommChannel=moduleCommChannel,
            multiModuleWindowController=multiModuleWindowController,
            moduleMainControllers=moduleMainControllers
        )
    except Exception as e:
        if not IS_HEADLESS: view.close()
        raise e

    return view, controller


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
